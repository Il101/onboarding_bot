---
phase: 3
slug: telegram-bot
status: verified
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-19
---

# Phase 3 — Validation Strategy

> Nyquist compliance map for all execution tasks in `03-01/03-02/03-03-PLAN.md`.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x + pytest-asyncio |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `uv run pytest tests/phase3 -q` |
| **Full suite command** | `uv run pytest tests/ -v --tb=short` |

---

## Sampling Rate (Wave Continuity)

- **After every task commit:** run that task’s `<automated>` command from the map below.
- **After every wave merge:**
  - Wave 1 (`03-01`): `uv run pytest tests/phase3/test_auth_gate.py tests/phase3/test_multiturn_context.py tests/phase3/test_feedback_capture.py -q`
  - Wave 2 (`03-02`): `uv run pytest tests/phase3/test_graph_fallback.py tests/phase3/test_source_block_always_present.py tests/phase3/test_multiturn_context.py -q`
  - Wave 3 (`03-03`): `uv run pytest tests/phase3/test_auth_gate.py tests/phase3/test_source_block_always_present.py tests/phase3/test_feedback_capture.py -q`
- **Before `/gsd-verify-work`:** `uv run pytest tests/ -v --tb=short`

Continuity check: every task has explicit automated verification, so no blind 3-task window exists.

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement Coverage | Automated Command | File Exists | Status |
|---------|------|------|----------------------|-------------------|-------------|--------|
| 03-01-01 | 03-01 | 1 | BOT-01, BOT-02, BOT-03, BOT-04, BOT-05 | `uv run pytest tests/phase3 --collect-only -q` | verified by phase3 suite | ✅ green |
| 03-01-02 | 03-01 | 1 | BOT-03, BOT-05 | `uv run pytest tests/phase3/test_auth_gate.py tests/phase3/test_multiturn_context.py -q` | tests present and passing | ✅ green |
| 03-01-03 | 03-01 | 1 | BOT-04 | `uv run pytest tests/phase3/test_feedback_capture.py -q` | tests present and passing | ✅ green |
| 03-02-01 | 03-02 | 2 | BOT-01, BOT-03 | `uv run pytest tests/phase3/test_multiturn_context.py -q` | tests present and passing | ✅ green |
| 03-02-02 | 03-02 | 2 | BOT-01, BOT-02, BOT-03 | `uv run pytest tests/phase3/test_graph_fallback.py tests/phase3/test_source_block_always_present.py -q` | tests present and passing | ✅ green |
| 03-02-03 | 03-02 | 2 | BOT-01, BOT-02, BOT-03 | `uv run pytest tests/phase3/test_graph_fallback.py tests/phase3/test_multiturn_context.py -q` | tests present and passing | ✅ green |
| 03-03-01 | 03-03 | 3 | BOT-01 | `uv run pytest tests/phase3/test_source_block_always_present.py tests/phase3/test_graph_fallback.py -q` | tests present and passing | ✅ green |
| 03-03-02 | 03-03 | 3 | BOT-01, BOT-04, BOT-05 | `uv run pytest tests/phase3/test_auth_gate.py tests/phase3/test_feedback_capture.py -q` | tests present and passing | ✅ green |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Requirement Coverage Cross-Check

| Requirement | Planned verification points |
|-------------|-----------------------------|
| BOT-01 | 03-01-01, 03-02-01, 03-02-02, 03-02-03, 03-03-01, 03-03-02 |
| BOT-02 | 03-01-01, 03-02-02, 03-02-03 |
| BOT-03 | 03-01-01, 03-01-02, 03-02-01, 03-02-02, 03-02-03 |
| BOT-04 | 03-01-01, 03-01-03, 03-03-02 |
| BOT-05 | 03-01-01, 03-01-02, 03-03-02 |

---

## Validation Sign-Off

- [x] Every task has `<automated>` verification (Nyquist rule satisfied)
- [x] Wave sampling continuity defined
- [x] BOT-01..BOT-05 mapped to automated checks
- [x] No watch-mode or manual-only commands in task verifies

**Approval:** ready for execution

## Validation Audit 2026-04-19

| Metric | Count |
|--------|-------|
| Gaps found | 5 |
| Resolved | 5 |
| Escalated | 0 |
