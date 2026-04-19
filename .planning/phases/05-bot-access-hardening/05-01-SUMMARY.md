---
phase: 05-bot-access-hardening
plan: 01
subsystem: testing
tags: [pytest, telegram, auth, whitelist]
requires:
  - phase: 03-telegram-bot
    provides: auth gate handlers and graph deny routing baselines
provides:
  - BOT-05 Wave 1 whitelist-policy test scaffolding
  - whitelist-backed auth-gate test refactor anchored on user_id identity
affects: [phase-05-implementation, bot-auth, langgraph-auth-gate]
tech-stack:
  added: []
  patterns: [deny-before-graph assertions, whitelist user_id fixture-driven tests]
key-files:
  created: [tests/phase5/test_access_policy.py]
  modified: [tests/phase3/test_auth_gate.py]
key-decisions:
  - "Keep Wave 1 scope test-only: define BOT-05 contract without implementing production auth policy APIs."
  - "Use deterministic user_id->role test fixture to represent whitelist source semantics in transport tests."
patterns-established:
  - "Policy tests assert both AuthDecision.allowed and AuthDecision.reason for all expected branches."
  - "Unauthorized transport paths must deny and never invoke graph."
requirements-completed: [BOT-05]
duration: 32min
completed: 2026-04-19
---

# Phase 5 Plan 01: BOT-05 Wave 1 Test Scaffolding Summary

**Whitelist-first BOT-05 authorization behavior is now locked into test scaffolding with deterministic deny/allow contracts and deny-before-graph regression assertions.**

## Performance

- **Duration:** 32 min
- **Started:** 2026-04-19T14:24:00Z
- **Completed:** 2026-04-19T14:56:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Added new Phase 5 unit test scaffold for whitelist access policy contract (`not_whitelisted`, `role_not_allowed`, `allowed`) with explicit `allowed` + `reason` assertions.
- Refactored Phase 3 auth-gate tests to anchor authorization intent on deterministic `user_id` whitelist fixture behavior instead of role-only monkeypatches.
- Preserved and reinforced defense-in-depth deny path assertion that unauthorized identity short-circuits before retrieval.

## Executed Verification Commands and Outcomes

1. `uv run pytest tests/phase5/test_access_policy.py -q`  
   **Outcome:** failed (expected for Wave 1 scaffolding before BOT-05 implementation; `authorize_telegram_user` not yet implemented).
2. `uv run pytest tests/phase3/test_auth_gate.py -q`  
   **Outcome:** passed (`4 passed`).

## Task Commits

1. **Task 1: Add BOT-05 unit policy tests for whitelist-based authorization** - `2511c2b` (test)
2. **Task 2: Refactor transport/graph auth tests to use whitelist user_id source** - `55ddf6d` (test)

## Files Created/Modified
- `tests/phase5/test_access_policy.py` - New BOT-05 policy contract tests asserting explicit reason codes and allow/deny outcomes.
- `tests/phase3/test_auth_gate.py` - Refactored auth-gate regression tests to whitelist `user_id` semantics and payload assertions.

## Decisions Made
- Kept implementation untouched per Wave 1 scope; only test scaffolding/refactor was performed.
- Encoded whitelist semantics in tests via deterministic fixture mapping (`WHITELIST_USER_ROLES`) to avoid role-only test signals.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed graph invocation assertion shape in auth-gate test**
- **Found during:** Task 2 verification
- **Issue:** Test incorrectly asserted `graph.ainvoke` payload via keyword arg `input` while handler uses positional payload.
- **Fix:** Switched assertions to inspect positional call args (`await_args.args[0]`) and kept thread envelope assertion via kwargs.
- **Files modified:** `tests/phase3/test_auth_gate.py`
- **Verification:** `uv run pytest tests/phase3/test_auth_gate.py -q` -> `4 passed`
- **Committed in:** `55ddf6d`

## Issues Encountered
- Accidental broad repository commit occurred due pre-existing staged changes; commit was immediately rolled back and re-committed using file-scoped `git commit --only ...` to preserve atomic task boundaries.

## Known Stubs
- `tests/phase5/test_access_policy.py:17,35,53` — assertions intentionally fail until `authorize_telegram_user` is implemented in a later BOT-05 implementation plan.

## Next Phase Readiness
- Wave 1 test scaffolding is in place to drive BOT-05 implementation.
- Implementation phase must add production whitelist auth API and make Phase 5 policy tests pass.

## Self-Check: PASSED
- Confirmed summary file exists: `.planning/phases/05-bot-access-hardening/05-01-SUMMARY.md`
- Confirmed task commit exists: `2511c2b`
- Confirmed task commit exists: `55ddf6d`
