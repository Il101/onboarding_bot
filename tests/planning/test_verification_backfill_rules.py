from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = ROOT / "scripts" / "verify_backfill.py"


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _valid_verification_file() -> str:
    return """---
phase: 1
status: partial
updated: 2026-04-19
requirements_total: 3
requirements_satisfied: 1
requirements_partial: 1
requirements_unsatisfied: 1
requirements_orphaned: 0
---

# 01-VERIFICATION

## requirements-table

| requirement_id | summary_ref | test_or_command_ref | code_or_contract_ref | status |
| --- | --- | --- | --- | --- |
| ING-01 | .planning/phases/01-foundation-data-ingestion/01-01-SUMMARY.md#phase-1-plan-01-foundation-bootstrap-summary | uv run pytest tests/pipeline/test_telegram_parser.py -q | src/pipeline/parsers/telegram.py | satisfied |
| ING-02 | .planning/phases/01-foundation-data-ingestion/01-01-SUMMARY.md#phase-1-plan-01-foundation-bootstrap-summary | uv run pytest tests/pipeline/test_pdf_parser.py -q | - | partial |
| ING-03 | - | - | - | unsatisfied |

## gate-verdict

partial
"""


def _create_repo_with_phase_1(tmp_path: Path, *, verification_body: str | None = None) -> None:
    _write(
        tmp_path / ".planning/phases/01-foundation-data-ingestion/01-01-SUMMARY.md",
        "# Phase 1 Plan 01: Foundation Bootstrap Summary\n",
    )
    _write(tmp_path / "src/pipeline/parsers/telegram.py", "def parse_telegram_export(path: str):\n    return []\n")
    _write(tmp_path / "tests/pipeline/test_telegram_parser.py", "def test_stub():\n    assert True\n")
    _write(tmp_path / "tests/pipeline/test_pdf_parser.py", "def test_stub():\n    assert True\n")
    _write(
        tmp_path / ".planning/phases/01-foundation-data-ingestion/01-VERIFICATION.md",
        verification_body if verification_body is not None else _valid_verification_file(),
    )


def _run_cli(tmp_path: Path, *args: str) -> subprocess.CompletedProcess[str]:
    command = [sys.executable, str(SCRIPT_PATH), *args]
    return subprocess.run(command, cwd=tmp_path, text=True, capture_output=True, check=False)


def test_cli_strict_schema_and_status_classification(tmp_path: Path) -> None:
    _create_repo_with_phase_1(tmp_path)

    result = _run_cli(tmp_path, "--phase", "1", "--strict-schema")

    assert result.returncode == 0, result.stderr + result.stdout
    assert "satisfied=1" in result.stdout
    assert "partial=1" in result.stdout
    assert "unsatisfied=1" in result.stdout
    assert "orphaned=0" in result.stdout


def test_cli_fails_on_missing_required_frontmatter_keys(tmp_path: Path) -> None:
    invalid = _valid_verification_file().replace("requirements_partial: 1\n", "")
    _create_repo_with_phase_1(tmp_path, verification_body=invalid)

    result = _run_cli(tmp_path, "--phase", "1", "--strict-schema")

    assert result.returncode == 1
    assert "requirements_partial" in (result.stderr + result.stdout)


def test_cli_fails_when_anchor_is_not_resolvable(tmp_path: Path) -> None:
    invalid = _valid_verification_file().replace(
        "#phase-1-plan-01-foundation-bootstrap-summary",
        "#missing-anchor",
    )
    _create_repo_with_phase_1(tmp_path, verification_body=invalid)

    result = _run_cli(tmp_path, "--phase", "1", "--strict-schema", "--assert-resolvable-anchors")

    assert result.returncode == 1
    assert "Unresolvable anchor" in (result.stderr + result.stdout)


def test_cli_fails_assert_no_orphaned_when_phase_verification_missing(tmp_path: Path) -> None:
    _create_repo_with_phase_1(tmp_path)
    # phase 2 does not exist -> orphaned
    result = _run_cli(tmp_path, "--phase", "1", "--phase", "2", "--assert-no-orphaned-phases", "1,2")

    assert result.returncode == 1
    assert "orphaned" in (result.stderr + result.stdout)
