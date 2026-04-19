from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def test_requirements_traceability_reconciled_for_phases_1_to_4() -> None:
    requirements = (ROOT / ".planning" / "REQUIREMENTS.md").read_text(encoding="utf-8")

    expected_rows = [
        "| ING-01 | Phase 1 | Satisfied (01-VERIFICATION) |",
        "| ING-02 | Phase 1 | Satisfied (01-VERIFICATION) |",
        "| ING-03 | Phase 1 | Satisfied (01-VERIFICATION) |",
        "| ING-04 | Phase 1 | Satisfied (01-VERIFICATION) |",
        "| ING-05 | Phase 1 | Satisfied (01-VERIFICATION) |",
        "| ING-06 | Phase 1 | Satisfied (01-VERIFICATION) |",
        "| KNW-01 | Phase 2 / 4 | Satisfied (02-VERIFICATION, 04-VERIFICATION) |",
        "| KNW-02 | Phase 2 / 4 | Satisfied (02-VERIFICATION, 04-VERIFICATION) |",
        "| KNW-03 | Phase 2 / 4 | Satisfied overall (partial delegation in 04-VERIFICATION) |",
        "| KNW-04 | Phase 2 / 4 | Satisfied overall (partial delegation in 04-VERIFICATION) |",
        "| BOT-01 | Phase 3 / 4 | Satisfied (03-VERIFICATION, 04-VERIFICATION) |",
        "| BOT-02 | Phase 3 / 4 | Satisfied overall (partial delegation in 04-VERIFICATION) |",
        "| BOT-03 | Phase 3 | Satisfied (03-VERIFICATION) |",
        "| BOT-04 | Phase 3 | Satisfied (03-VERIFICATION) |",
    ]

    for row in expected_rows:
        assert row in requirements


def test_roadmap_progress_reconciled_for_completed_phases() -> None:
    roadmap = (ROOT / ".planning" / "ROADMAP.md").read_text(encoding="utf-8")

    assert "- [x] **Phase 3: Telegram Bot" in roadmap
    assert "- [x] **Phase 4: Runtime Integration Hardening" in roadmap
    assert "- [x] **Phase 7: Verification Evidence Backfill" in roadmap
    assert "| 4. Runtime Integration Hardening | 2/2 | Completed | 2026-04-19 |" in roadmap
    assert "| 7. Verification Evidence Backfill | 3/3 | Completed | 2026-04-19 |" in roadmap


def test_milestone_audit_no_longer_reports_phase_1_to_4_orphaned_requirements() -> None:
    audit = (ROOT / ".planning" / "v1-MILESTONE-AUDIT.md").read_text(encoding="utf-8")

    assert "id: \"ING-01..ING-06, KNW-01..KNW-04, BOT-01..BOT-04\"" not in audit
    assert "| VERIFICATION.md per phase | Present for phases 1-4 |" in audit
    assert "No-orphaned assertion for phases 1-4 passes" in audit
    assert "requirements: 14/22" in audit


def test_verify_backfill_no_orphaned_assertion_for_phases_1_to_4_passes() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/verify_backfill.py",
            "--phase",
            "1",
            "--phase",
            "2",
            "--phase",
            "3",
            "--phase",
            "4",
            "--assert-no-orphaned-phases",
            "1,2,3,4",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr + result.stdout
