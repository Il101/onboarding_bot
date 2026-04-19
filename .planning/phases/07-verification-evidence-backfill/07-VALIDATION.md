---
phase: 7
slug: verification-evidence-backfill
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-19
---

# Phase 7 — Validation Strategy

## Test Infrastructure

| Property | Value |
|---|---|
| Framework | pytest + deterministic markdown reconciliation checks |
| Config | `pyproject.toml` |
| Quick | `python scripts/verify_backfill.py --changed-only` |
| Full | `python scripts/verify_backfill.py --phase 1 --phase 2 --phase 3 --phase 4 && uv run pytest tests/ -q` |

## Per-Task Verification Map

| Task ID | Plan | Requirement Coverage | Automated Command | Status |
|---|---|---|---|---|
| 07-01-01 | 07-01 | ING-01..ING-06 | `python scripts/verify_backfill.py --phase 1` | ⬜ pending |
| 07-01-02 | 07-01 | KNW-01..KNW-04 | `python scripts/verify_backfill.py --phase 2 --phase 4` | ⬜ pending |
| 07-01-03 | 07-01 | BOT-01..BOT-04 | `python scripts/verify_backfill.py --phase 3 --phase 4` | ⬜ pending |
| 07-01-04 | 07-01 | ING-01..ING-06, KNW-01..KNW-04, BOT-01..BOT-04 | `python scripts/verify_backfill.py --phase 1 --phase 2 --phase 3 --phase 4` | ⬜ pending |

## Wave 0 Requirements

- [ ] `scripts/verify_backfill.py` — deterministic 3-source evidence validator and status recompute engine
- [ ] `tests/planning/test_verification_backfill_rules.py` — parser/validator regression tests
- [ ] `tests/planning/test_traceability_reconcile.py` — requirements/audit/roadmap sync checks

## Manual-Only Verifications

All phase behaviors have automated verification.

## Validation Sign-Off

- [ ] Every task has automated verification
- [ ] No manual-only verification points
- [ ] All Phase 7 requirements mapped to verification checks
