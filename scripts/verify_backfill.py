from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Iterable


REQUIRED_FRONTMATTER_KEYS = {
    "phase",
    "status",
    "updated",
    "requirements_total",
    "requirements_satisfied",
    "requirements_partial",
    "requirements_unsatisfied",
    "requirements_orphaned",
}

REQUIRED_TABLE_COLUMNS = [
    "requirement_id",
    "summary_ref",
    "test_or_command_ref",
    "code_or_contract_ref",
    "status",
]

VALID_ROW_STATUS = {"satisfied", "partial", "unsatisfied", "orphaned"}

PHASE_DIR_PATTERN = re.compile(r"^(\d+)-")
HEADING_PATTERN = re.compile(r"^\s*#+\s+(.+?)\s*$")


@dataclass
class VerificationRow:
    requirement_id: str
    summary_ref: str
    test_or_command_ref: str
    code_or_contract_ref: str
    status: str


@dataclass
class PhaseReport:
    phase: int
    verification_file: Path | None
    rows: list[VerificationRow]
    counts: dict[str, int]
    orphaned: bool
    errors: list[str]
    functional_gaps: list[tuple[str, str, str, str, str]]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify strict verification-evidence backfill artifacts.")
    parser.add_argument("--phase", type=int, action="append", default=[], help="Phase number to validate (repeatable).")
    parser.add_argument(
        "--changed-only",
        action="store_true",
        help="Validate only phases with changed verification files in git working tree.",
    )
    parser.add_argument("--strict-schema", action="store_true", help="Enforce strict frontmatter and table schema.")
    parser.add_argument(
        "--assert-resolvable-anchors",
        action="store_true",
        help="Ensure summary_ref anchors resolve to existing headings.",
    )
    parser.add_argument(
        "--assert-no-orphaned-phases",
        type=str,
        default="",
        help="Comma-separated phases that must not be orphaned (missing verification artifact).",
    )
    return parser.parse_args()


def project_root() -> Path:
    return Path.cwd()


def discover_phase_dir(root: Path, phase: int) -> Path | None:
    phases_dir = root / ".planning" / "phases"
    if not phases_dir.exists():
        return None

    prefix = f"{phase:02d}-"
    for candidate in sorted(phases_dir.iterdir()):
        if candidate.is_dir() and candidate.name.startswith(prefix):
            return candidate
    return None


def discover_verification_file(root: Path, phase: int) -> Path | None:
    phase_dir = discover_phase_dir(root, phase)
    if phase_dir is None:
        return None

    expected = phase_dir / f"{phase:02d}-VERIFICATION.md"
    if expected.exists():
        return expected

    for candidate in sorted(phase_dir.glob("*-VERIFICATION.md")):
        return candidate
    return None


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text

    raw = text[4:end]
    body = text[end + 5 :]
    data: dict[str, str] = {}
    for line in raw.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip()
    return data, body


def parse_requirements_table(body: str) -> tuple[list[str], list[VerificationRow]]:
    lines = body.splitlines()
    for idx, line in enumerate(lines):
        if not line.strip().startswith("|"):
            continue
        header_cols = [col.strip().lower() for col in line.strip().strip("|").split("|")]
        if header_cols == REQUIRED_TABLE_COLUMNS:
            if idx + 1 >= len(lines):
                return header_cols, []
            rows: list[VerificationRow] = []
            for raw in lines[idx + 2 :]:
                if not raw.strip().startswith("|"):
                    break
                values = [col.strip() for col in raw.strip().strip("|").split("|")]
                if len(values) != len(REQUIRED_TABLE_COLUMNS):
                    continue
                rows.append(
                    VerificationRow(
                        requirement_id=values[0],
                        summary_ref=values[1],
                        test_or_command_ref=values[2],
                        code_or_contract_ref=values[3],
                        status=values[4].lower(),
                    )
                )
            return header_cols, rows
    return [], []


def extract_heading_anchors(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8")
    anchors: set[str] = set()
    for line in text.splitlines():
        match = HEADING_PATTERN.match(line)
        if not match:
            continue
        heading = match.group(1).strip().lower()
        anchor = re.sub(r"[^\w\s-]", "", heading, flags=re.UNICODE)
        anchor = re.sub(r"\s+", "-", anchor).strip("-")
        anchors.add(anchor)
    return anchors


def parse_summary_ref(value: str) -> tuple[str, str] | None:
    if value == "-" or "#" not in value:
        return None
    path_part, anchor = value.split("#", 1)
    if not path_part or not anchor:
        return None
    return path_part.strip(), anchor.strip()


def classify_row_status(row: VerificationRow) -> str:
    if row.status in {"orphaned", "unsatisfied"}:
        return row.status
    missing = [row.summary_ref, row.test_or_command_ref, row.code_or_contract_ref].count("-")
    if missing == 0:
        return "satisfied"
    if missing in {1, 2}:
        return "partial"
    return "unsatisfied"


def parse_phase_numbers(raw: str) -> list[int]:
    if not raw.strip():
        return []
    phases = []
    for token in raw.split(","):
        token = token.strip()
        if not token:
            continue
        phases.append(int(token))
    return phases


def git_changed_phases(root: Path) -> list[int]:
    try:
        output = subprocess.check_output(
            ["git", "--no-pager", "status", "--short"],
            cwd=root,
            text=True,
        )
    except Exception:
        return []

    phases: set[int] = set()
    for line in output.splitlines():
        if "-VERIFICATION.md" not in line:
            continue
        parts = line.split()
        if not parts:
            continue
        path = parts[-1]
        match = re.search(r"\.planning/phases/(\d+)-[^/]+/", path)
        if match:
            phases.add(int(match.group(1)))
    return sorted(phases)


def validate_phase(
    root: Path,
    phase: int,
    strict_schema: bool,
    assert_resolvable_anchors: bool,
) -> PhaseReport:
    verification_file = discover_verification_file(root, phase)
    if verification_file is None:
        return PhaseReport(
            phase=phase,
            verification_file=None,
            rows=[],
            counts={key: 0 for key in VALID_ROW_STATUS},
            orphaned=True,
            errors=[f"Missing verification file for phase {phase}"],
            functional_gaps=[],
        )

    text = verification_file.read_text(encoding="utf-8")
    frontmatter, body = parse_frontmatter(text)
    header, rows = parse_requirements_table(body)
    errors: list[str] = []

    if strict_schema:
        missing_keys = sorted(REQUIRED_FRONTMATTER_KEYS - set(frontmatter))
        if missing_keys:
            errors.append(
                f"{verification_file}: Missing required frontmatter keys: {', '.join(missing_keys)}"
            )
        if header != REQUIRED_TABLE_COLUMNS:
            errors.append(f"{verification_file}: Missing strict requirements table with required columns")
        if not rows:
            errors.append(f"{verification_file}: Requirements table has no rows")

    counts = {key: 0 for key in VALID_ROW_STATUS}
    functional_gaps: list[tuple[str, str, str, str, str]] = []
    for row in rows:
        if row.status not in VALID_ROW_STATUS:
            errors.append(f"{verification_file}: Invalid status '{row.status}' for {row.requirement_id}")
            continue

        computed_status = classify_row_status(row)
        counts[computed_status] += 1
        if strict_schema and row.status != computed_status:
            errors.append(
                f"{verification_file}: Status mismatch for {row.requirement_id}; "
                f"declared={row.status} computed={computed_status}"
            )

        if assert_resolvable_anchors and row.summary_ref != "-":
            parsed = parse_summary_ref(row.summary_ref)
            if parsed is None:
                errors.append(
                    f"{verification_file}: summary_ref for {row.requirement_id} must use path#anchor format"
                )
            else:
                summary_path_str, anchor = parsed
                summary_path = root / summary_path_str
                if not summary_path.exists():
                    errors.append(
                        f"{verification_file}: Summary path does not exist for {row.requirement_id}: {summary_path_str}"
                    )
                else:
                    anchors = extract_heading_anchors(summary_path)
                    if anchor not in anchors:
                        errors.append(
                            f"{verification_file}: Unresolvable anchor '{anchor}' in {summary_path_str} "
                            f"for {row.requirement_id}"
                        )

        if row.status == "unsatisfied" and row.summary_ref != "-":
            functional_gaps.append(
                (
                    row.requirement_id,
                    str(phase),
                    f"{row.summary_ref}; {row.test_or_command_ref}; {row.code_or_contract_ref}",
                    "high",
                    "TBD-gap-phase",
                )
            )

    return PhaseReport(
        phase=phase,
        verification_file=verification_file,
        rows=rows,
        counts=counts,
        orphaned=False,
        errors=errors,
        functional_gaps=functional_gaps,
    )


def ensure_functional_gap_register(root: Path) -> None:
    path = root / ".planning" / "functional-gaps.md"
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "# Functional Gaps Register\n\n"
        "| requirement_id | phase | evidence | severity | target_gap_phase |\n"
        "| --- | --- | --- | --- | --- |\n",
        encoding="utf-8",
    )


def resolve_phases(args: argparse.Namespace, root: Path) -> list[int]:
    phases = sorted(set(args.phase))
    if args.changed_only:
        changed = git_changed_phases(root)
        phases = sorted(set(phases + changed))
    if not phases:
        phases = sorted(
            int(match.group(1))
            for entry in (root / ".planning" / "phases").glob("*")
            if entry.is_dir() and (match := PHASE_DIR_PATTERN.match(entry.name))
        )
    return phases


def print_report(report: PhaseReport) -> None:
    if report.verification_file is None:
        print(f"Phase {report.phase}: orphaned (verification missing)")
        return
    print(
        f"Phase {report.phase}: satisfied={report.counts['satisfied']} "
        f"partial={report.counts['partial']} unsatisfied={report.counts['unsatisfied']} "
        f"orphaned={report.counts['orphaned']}"
    )


def append_functional_gaps(root: Path, rows: Iterable[tuple[str, str, str, str, str]]) -> None:
    rows = list(rows)
    if not rows:
        return
    path = root / ".planning" / "functional-gaps.md"
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    additions = []
    for requirement_id, phase, evidence, severity, target_gap_phase in rows:
        line = f"| {requirement_id} | {phase} | {evidence} | {severity} | {target_gap_phase} |"
        if line not in existing:
            additions.append(line)
    if not additions:
        return
    with path.open("a", encoding="utf-8") as handle:
        handle.write("\n")
        handle.write(f"<!-- updated: {date.today().isoformat()} -->\n")
        for line in additions:
            handle.write(f"{line}\n")


def main() -> int:
    args = parse_args()
    root = project_root()
    ensure_functional_gap_register(root)

    phases = resolve_phases(args, root)
    if not phases:
        print("No phases to validate", file=sys.stderr)
        return 1

    reports = [
        validate_phase(
            root=root,
            phase=phase,
            strict_schema=args.strict_schema,
            assert_resolvable_anchors=args.assert_resolvable_anchors,
        )
        for phase in phases
    ]

    all_errors: list[str] = []
    functional_gap_rows: list[tuple[str, str, str, str, str]] = []
    orphaned_assertion_set = set(parse_phase_numbers(args.assert_no_orphaned_phases))

    explicitly_scoped = bool(args.phase or args.changed_only)

    for report in reports:
        print_report(report)
        if report.orphaned and not explicitly_scoped and report.phase not in orphaned_assertion_set:
            # Non-scoped scans should not fail on future phases unless explicitly asserted.
            pass
        else:
            all_errors.extend(report.errors)
        functional_gap_rows.extend(report.functional_gaps)
        if report.phase in orphaned_assertion_set and report.orphaned:
            all_errors.append(f"Phase {report.phase} is orphaned but --assert-no-orphaned-phases requires evidence.")

    append_functional_gaps(root, functional_gap_rows)

    if all_errors:
        for error in all_errors:
            print(error, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
