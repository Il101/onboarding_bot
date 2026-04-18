---
phase: 03-telegram-bot
plan: 01
subsystem: testing
tags: [telegram, langgraph, auth, feedback, contracts]
requires:
  - phase: 02-knowledge-extraction-rag
    provides: knowledge query envelope and fallback policy
provides:
  - Phase 3 contract test harness for BOT policy decisions
  - Typed bot state/auth contracts for deterministic gate behavior
  - Feedback persistence model/service with callback validation
affects: [03-02, 03-03, phase-4]
tech-stack:
  added: []
  patterns: [contract-first bot envelope validation, auth-before-retrieval gate, callback payload normalization]
key-files:
  created: [src/ai/langgraph/state.py, src/bot/auth.py, src/models/feedback_event.py, src/bot/feedback.py, tests/phase3/test_graph_fallback.py, tests/phase3/test_source_block_always_present.py, tests/phase3/test_auth_gate.py, tests/phase3/test_multiturn_context.py, tests/phase3/test_feedback_capture.py]
  modified: [src/core/config.py, src/models/__init__.py, src/bot/__init__.py]
key-decisions:
  - "BotAnswer requires at least one typed source for fallback/deny/normal responses."
  - "Authorization is a pure allowlist gate with deterministic reason codes and deny payload."
  - "Feedback callback data is strictly normalized to feedback:up|feedback:down before DB write."
patterns-established:
  - "Use build_thread_id(chat_id,user_id) for deterministic conversation thread keys."
  - "Persist feedback events with linkage-only fields (thread/message/chat/user/confidence), no raw answer text."
requirements-completed: [BOT-03, BOT-04, BOT-05]
duration: 2min
completed: 2026-04-18
---

# Phase 3 Plan 01: Telegram Bot Contracts Foundation Summary

**Shipped typed Telegram bot contracts and policy guardrails that lock deterministic auth gating, source-backed answer envelopes, and feedback event persistence before transport/graph wiring.**

## Performance

- **Duration:** 2 min
- **Started:** 2026-04-18T23:27:44Z
- **Completed:** 2026-04-18T23:29:45Z
- **Tasks:** 3
- **Files modified:** 12

## Accomplishments
- Added `tests/phase3` scenario harness covering D-01..D-12 policy constraints in executable checks.
- Implemented typed `SourceRef`/`BotAnswer`/`BotState` contracts and deterministic role gate primitives.
- Added `feedback_events` SQLAlchemy model + save service with callback tamper validation.

## Task Commits

1. **Task 1: Create Phase 3 test harness and requirement-mapped scenario files** - `83a562a` (test)
2. **Task 2 (RED): Implement state contracts and auth gate policy primitives** - `b857380` (test)
3. **Task 2 (GREEN): Implement state contracts and auth gate policy primitives** - `416a45b` (feat)
4. **Task 3 (RED): Add feedback persistence model and save service** - `abadb98` (test)
5. **Task 3 (GREEN): Add feedback persistence model and save service** - `28547e5` (feat)

## Files Created/Modified
- `src/core/config.py` - Added Telegram/runtime settings for bot auth and context budget.
- `src/ai/langgraph/state.py` - Added typed bot state and answer/source contracts plus deterministic thread id builder.
- `src/bot/auth.py` - Added pure role authorization policy and deterministic denied answer payload builder.
- `src/models/feedback_event.py` - Added `feedback_events` persistence model.
- `src/bot/feedback.py` - Added callback vote normalization and feedback save service.
- `tests/phase3/test_graph_fallback.py` - Fallback phrase and source requirement tests.
- `tests/phase3/test_source_block_always_present.py` - Mandatory “Источники” block tests for regular/fallback/deny answers.
- `tests/phase3/test_auth_gate.py` - Retrieval short-circuit and deny payload determinism tests.
- `tests/phase3/test_multiturn_context.py` - Deterministic thread id, state contract, and settings override tests.
- `tests/phase3/test_feedback_capture.py` - Vote normalization, schema guardrails, and persistence tests.

## Decisions Made
- Kept auth gate implementation side-effect free (`is_authorized_role`) to guarantee pre-retrieval denial checks.
- Required `sources` as `min_length=1` in `BotAnswer` to enforce D-04/D-05 at contract level.
- Stored only analytics join fields in feedback table to satisfy D-12 while minimizing sensitive payload storage.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `gsd-sdk` command unavailable in executor environment**
- **Found during:** Plan bootstrap and state update steps
- **Issue:** Required `gsd-sdk query ...` commands failed with `gsd-sdk: command not found`, blocking automated state/roadmap requirement handlers.
- **Fix:** Performed equivalent manual updates to `.planning/STATE.md`, `.planning/ROADMAP.md`, and `.planning/REQUIREMENTS.md` directly.
- **Files modified:** `.planning/STATE.md`, `.planning/ROADMAP.md`, `.planning/REQUIREMENTS.md`
- **Verification:** Planning files reflect plan completion and requirement status updates.
- **Committed in:** metadata docs commit

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** No scope creep; manual metadata updates replaced unavailable helper CLI.

## Issues Encountered
- `datetime.utcnow` deprecation warning appears from SQLAlchemy default invocation path inherited from existing model pattern; non-blocking for this plan.

## User Setup Required
- None - no external service configuration required in this plan.

## Next Phase Readiness
- Phase 3 workflow plan (`03-02`) can wire graph nodes against stable `BotState`/`BotAnswer` contracts.
- Telegram transport plan (`03-03`) can consume deterministic auth deny payloads and feedback save service.

## TDD Gate Compliance
- RED and GREEN commits exist for both `tdd="true"` tasks (`b857380`→`416a45b`, `abadb98`→`28547e5`).

## Self-Check: PASSED
- Found summary and all required implementation files.
- Verified task commits exist: `83a562a`, `b857380`, `416a45b`, `abadb98`, `28547e5`.
