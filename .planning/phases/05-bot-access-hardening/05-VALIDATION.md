---
phase: 5
slug: bot-access-hardening
status: verified
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-19
---

# Phase 5 — Validation Strategy

## Test Infrastructure

| Property | Value |
|---|---|
| Framework | pytest + pytest-asyncio |
| Config | `pyproject.toml` |
| Quick | `uv run pytest tests/phase5 -q` |
| Full | `uv run pytest tests/phase5 tests/phase3/test_auth_gate.py -q` |

## Per-Task Verification Map

| Task ID | Requirement Coverage | Automated Command | Deterministic Assertion | Status |
|---|---|---|---|---|
| 05-01-01 | BOT-05 (unauthorized deny) | `uv run pytest tests/phase5/test_access_policy.py::test_authorize_user_not_whitelisted_denied -q` | Unknown `user_id` returns deny (`allowed=False`, `reason=not_whitelisted`) | ✅ green |
| 05-01-02 | BOT-05 (deny before graph) | `uv run pytest tests/phase3/test_auth_gate.py::test_start_unauthorized_returns_deny_and_skips_graph -q` | Unauthorized `/start` sends deny response and `graph.ainvoke` is not awaited | ✅ green |
| 05-01-03 | BOT-05 (authorized allow) | `uv run pytest tests/phase3/test_auth_gate.py::test_authorized_message_invokes_graph_with_thread_id_and_sends_formatted_answer -q` | Whitelisted user passes gate and graph is invoked with resolved role/thread envelope | ✅ green |
| 05-01-04 | BOT-05 (no retrieve on deny) | `uv run pytest tests/phase3/test_auth_gate.py::test_unauthorized_role_short_circuits_before_retrieve -q` | Unauthorized path returns `decision=deny`; retrieve path is never executed | ✅ green |

## Wave 0 Requirements

- [x] `tests/phase5/test_access_policy.py` (new) exists with whitelist allow/deny policy tests for BOT-05
- [x] `tests/phase3/test_auth_gate.py` updated to use whitelist-backed authorization source instead of hardcoded role patching
- [x] `uv run pytest tests/phase5 -q` executes and passes against implemented whitelist behavior

## Manual-Only Verifications

No manual-only verification points are allowed for Phase 5; BOT-05 evidence must be fully automated via pytest.

## Validation Sign-Off

- [x] Every BOT-05 task has an automated verification command
- [x] Unauthorized users are denied deterministically by `user_id` whitelist source
- [x] Unauthorized deny-path performs no graph/retrieve invocation
- [x] Authorized users pass through normal bot workflow
- [x] `nyquist_compliant` switched to `true` after Wave 0 tests are green

## Validation Audit 2026-04-19

| Metric | Count |
|--------|-------|
| Gaps found | 0 |
| Resolved | 0 |
| Escalated | 0 |
