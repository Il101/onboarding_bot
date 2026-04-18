---
phase: 03-telegram-bot
plan: 03
subsystem: api
tags: [telegram, python-telegram-bot, langgraph, feedback, presenters]
requires:
  - phase: 03-telegram-bot
    provides: LangGraph policy workflow and bot contracts from 03-01/03-02
provides:
  - Telegram transport handlers for /start, message, and thumbs callbacks
  - Deterministic Telegram presenter with mandatory Источники block for every response
  - End-to-end integration tests for auth gate, message graph wiring, and feedback capture
affects: [phase-4, bot-runtime]
tech-stack:
  added: [python-telegram-bot]
  patterns: [auth-before-graph at transport edge, safe error masking in handlers, thread_id-bound graph invocation]
key-files:
  created: [src/bot/presenters.py, src/bot/telegram_app.py]
  modified: [tests/phase3/test_source_block_always_present.py, tests/phase3/test_graph_fallback.py, tests/phase3/test_auth_gate.py, tests/phase3/test_feedback_capture.py, pyproject.toml]
key-decisions:
  - "Kept presenter pure and deterministic: strips pre-rendered source text and always appends Источники from structured sources."
  - "Bound LangGraph calls to thread_id=tg:{chat_id}:{user_id} directly in transport handler."
  - "Stored feedback confidence keyed by thread/message in bot_data to persist vote events without raw answer text."
patterns-established:
  - "Telegram message flow: auth check -> graph invoke -> render_bot_message -> reply with thumbs keyboard."
  - "Callback flow: answer callback query in all paths and persist normalized vote when valid."
requirements-completed: [BOT-01, BOT-04, BOT-05]
duration: 17min
completed: 2026-04-19
---

# Phase 3 Plan 03: Telegram Transport Integration Summary

**Telegram runtime now executes LangGraph answers with mandatory Russian source attribution and captures thumbs feedback events through real transport handlers.**

## Performance

- **Duration:** 17 min
- **Started:** 2026-04-19T01:28:13Z
- **Completed:** 2026-04-19T01:45:54Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments
- Implemented `src/bot/presenters.py` with deterministic `render_bot_message` + `render_sources_block`, including safe truncation and stable source ordering.
- Implemented `src/bot/telegram_app.py` with `/start`, message, and callback handlers wired to Phase 3 graph and feedback service.
- Replaced placeholder phase-3 tests with transport-level async tests for auth gate, thread-scoped graph invocation, safe errors, and callback persistence.

## Task Commits

Each task was committed atomically:

1. **Task 1 (RED): Implement presenter for mandatory Russian response layout with source attribution** - `2e86d93` (test)
2. **Task 1 (GREEN): Implement presenter for mandatory Russian response layout with source attribution** - `e63538e` (feat)
3. **Task 2 (RED): Wire Telegram handlers (/start, message, callback) to graph and feedback services** - `b130ff2` (test)
4. **Task 2 (GREEN): Wire Telegram handlers (/start, message, callback) to graph and feedback services** - `41d4f3d` (feat)

## Files Created/Modified
- `src/bot/presenters.py` - Telegram envelope renderer with mandatory `Источники`, truncation, and deterministic sorting.
- `src/bot/telegram_app.py` - Application builder and async handlers integrating auth gate, LangGraph call, thumbs UI, and feedback persistence.
- `tests/phase3/test_source_block_always_present.py` - Presenter-focused source block behavior tests for answer/fallback/policy branches.
- `tests/phase3/test_graph_fallback.py` - Presenter + graph fallback/error rendering regressions.
- `tests/phase3/test_auth_gate.py` - Handler-level auth, graph invocation with thread_id, and safe error path tests.
- `tests/phase3/test_feedback_capture.py` - Callback ack and DB persistence tests for thumbs events.
- `pyproject.toml` - Added `python-telegram-bot` runtime dependency.

## Decisions Made
- Kept role resolution as a dedicated helper (`resolve_role_for_update`) to keep transport auth gate explicit and patchable in tests.
- Used `context.application.bot_data` for graph/session factory wiring to avoid duplicating business logic inside handlers.
- Sent safe Russian error envelope from transport handler on runtime exceptions, never exposing traceback text to end users.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Missing telegram runtime dependency prevented handler implementation**
- **Found during:** Task 2 (GREEN)
- **Issue:** `python-telegram-bot` was not available, blocking creation of real `Application` and handlers.
- **Fix:** Added `python-telegram-bot>=22.5,<23` to project dependencies.
- **Files modified:** `pyproject.toml`
- **Verification:** `uv run pytest tests/phase3/test_auth_gate.py tests/phase3/test_feedback_capture.py -q`
- **Committed in:** `41d4f3d`

**2. [Rule 1 - Bug] Message handler assumed message_id always present**
- **Found during:** Task 2 (GREEN) test run
- **Issue:** Handler raised `AttributeError` when `message_id` was missing in test update object, breaking feedback confidence key path.
- **Fix:** Added safe `message_id` fallback via `getattr(..., 0)` before storing confidence key.
- **Files modified:** `src/bot/telegram_app.py`
- **Verification:** `uv run pytest tests/phase3/test_auth_gate.py tests/phase3/test_feedback_capture.py -q`
- **Committed in:** `41d4f3d`

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 bug)
**Impact on plan:** Both deviations were correctness/runtime prerequisites; no architectural scope expansion.

## Issues Encountered
- Existing repository had unrelated modified/untracked files; execution was isolated by strict per-task staging.

## User Setup Required
None - no new manual setup beyond existing `TELEGRAM_BOT_TOKEN` requirement already declared in plan metadata.

## Next Phase Readiness
- Telegram transport is now callable as an application entrypoint (`build_application`) and ready for runtime boot wiring.
- Phase 4 analytics/admin work can consume persisted `feedback_events` without schema changes.

## TDD Gate Compliance
- RED and GREEN commits exist for both `tdd="true"` tasks.

## Self-Check: PASSED
- Found summary file: `.planning/phases/03-telegram-bot/03-03-SUMMARY.md`.
- Verified task commits exist: `2e86d93`, `e63538e`, `b130ff2`, `41d4f3d`.
