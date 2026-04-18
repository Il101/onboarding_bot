---
phase: 03-telegram-bot
plan: 02
subsystem: api
tags: [langgraph, telegram, policy, fallback, rag]
requires:
  - phase: 03-telegram-bot
    provides: typed bot state/auth contracts and feedback persistence from 03-01
  - phase: 02-knowledge-extraction-rag
    provides: /api/knowledge/query envelope and fallback confidence policy
provides:
  - Deterministic LangGraph routing for deny/offtopic/fallback/clarify/conflict/answer branches
  - Phase 2 retrieval adapter with bounded top_k and strict payload envelope reuse
  - Multi-turn summarization and thread-scoped state continuity with one-clarify cap
affects: [03-03, phase-4]
tech-stack:
  added: [langgraph, langchain-core]
  patterns: [auth-before-retrieve routing, safe error envelope masking, deterministic policy branch ordering]
key-files:
  created: [src/ai/langgraph/nodes/__init__.py, src/ai/langgraph/nodes/retrieve_phase2.py, src/ai/langgraph/nodes/summarize.py, src/ai/langgraph/nodes/decide.py, src/ai/langgraph/nodes/answer.py, src/ai/langgraph/graph.py]
  modified: [tests/phase3/test_multiturn_context.py, tests/phase3/test_graph_fallback.py, tests/phase3/test_source_block_always_present.py, pyproject.toml]
key-decisions:
  - "Kept D-01 fallback text locked to exact phrase without punctuation variant: 'Я не знаю — обратитесь к коллеге'."
  - "Handled low-confidence branch in graph fallback node directly to avoid invoking answer synthesis path."
  - "Compiled graph with InMemorySaver per build and required configurable.thread_id for continuity-safe invocation."
patterns-established:
  - "Decision branch order: auth-deny -> off-topic -> low-confidence fallback -> clarify -> conflict -> answer."
  - "Every branch response includes mandatory 'Источники' block and non-empty SourceRef list."
requirements-completed: [BOT-01, BOT-02, BOT-03]
duration: 5min
completed: 2026-04-18
---

# Phase 3 Plan 02: LangGraph Policy Workflow Summary

**Delivered deterministic LangGraph policy orchestration that reuses Phase 2 RAG envelope, enforces exact Russian fallback behavior, and preserves multi-turn thread context with safe error handling.**

## Performance

- **Duration:** 5 min
- **Started:** 2026-04-18T23:35:23Z
- **Completed:** 2026-04-18T23:40:29Z
- **Tasks:** 3
- **Files modified:** 10

## Accomplishments
- Implemented retrieval and summarization nodes with bounded `top_k`, strict envelope validation, deterministic trimming, and latest-user-message retention.
- Implemented policy decision and answer composition nodes covering fallback/clarify/off-topic/conflict/answer with mandatory `Источники`.
- Compiled full LangGraph routing with conditional edges, checkpointer-compatible `thread_id` invocation, and masked error envelope path.

## Task Commits

Each task was committed atomically:

1. **Task 1 (RED): Implement retrieve + summarize nodes for multi-turn context handling** - `385b883` (test)
2. **Task 1 (GREEN): Implement retrieve + summarize nodes for multi-turn context handling** - `aa88791` (feat)
3. **Task 2 (RED): Implement decision and answer nodes with strict policy branches** - `2f4b5e3` (test)
4. **Task 2 (GREEN): Implement decision and answer nodes with strict policy branches** - `08ba589` (feat)
5. **Task 3 (RED): Wire full LangGraph routing and checkpoint-safe execution paths** - `5aca6f9` (test)
6. **Task 3 (GREEN): Wire full LangGraph routing and checkpoint-safe execution paths** - `9a5995a` (feat)

## Files Created/Modified
- `src/ai/langgraph/nodes/retrieve_phase2.py` - Async adapter to `/api/knowledge/query` with bounded `top_k`, timeout, and strict envelope checks.
- `src/ai/langgraph/nodes/summarize.py` - Deterministic message trimming with summary carry-forward and latest user message retention.
- `src/ai/langgraph/nodes/decide.py` - Deterministic policy router for deny/offtopic/fallback/clarify/conflict/answer branches.
- `src/ai/langgraph/nodes/answer.py` - Branch response composition with Russian step format and mandatory `Источники`.
- `src/ai/langgraph/graph.py` - Compiled `StateGraph` wiring with conditional edges, checkpointer, and safe error masking.
- `tests/phase3/test_multiturn_context.py` - Retrieval/summarization + single-clarify graph behavior tests.
- `tests/phase3/test_graph_fallback.py` - Branch policy and graph routing regression tests.
- `tests/phase3/test_source_block_always_present.py` - Mandatory source block tests across response branches.
- `pyproject.toml` - Added `langgraph` and `langchain-core` dependencies required for graph runtime.

## Decisions Made
- Kept locked fallback phrase exactly `Я не знаю — обратитесь к коллеге` in all low-confidence branch outputs.
- Enforced branch ordering and prevented answer synthesis from running on fallback branch.
- Used explicit safe error result with masked text and source placeholder to avoid leaking internal exception details.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] `langgraph` runtime dependency missing in project environment**
- **Found during:** Task 3 (graph wiring)
- **Issue:** `src.ai.langgraph.graph` could not be imported because `langgraph` package was absent.
- **Fix:** Added `langgraph>=0.6,<0.7` and `langchain-core>=0.3,<0.4` to project dependencies.
- **Files modified:** `pyproject.toml`, `uv.lock`
- **Verification:** Graph tests invoked and passed with compiled `StateGraph`.
- **Committed in:** `9a5995a`

**2. [Rule 1 - Bug] Graph returned wrong branch/state shape after retrieve failures**
- **Found during:** Task 3 test run (`test_graph_low_confidence_skips_answer_synthesis`, `test_graph_masks_internal_errors_with_safe_envelope`)
- **Issue:** Error/fallback paths could still route to answer node and final state omitted `decision` keys.
- **Fix:** Introduced typed graph state, explicit `decision` assignment per terminal node, dedicated `error` branch mapping, and low-confidence fallback short-circuit node.
- **Files modified:** `src/ai/langgraph/graph.py`
- **Verification:** `uv run pytest tests/phase3/test_graph_fallback.py tests/phase3/test_multiturn_context.py -q`
- **Committed in:** `9a5995a`

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 bug)
**Impact on plan:** Changes were required for correctness and execution viability; no architectural scope expansion.

## Issues Encountered
- Existing repository had unrelated modified/untracked files in API/pipeline/planning paths; execution was isolated by staging only task files.

## User Setup Required
None - no external manual configuration required for this plan.

## Next Phase Readiness
- `03-03` can bind Telegram handlers directly to compiled graph entrypoint and presentation data.
- Policy branch behavior and source formatting are now regression-covered and stable for transport integration.

## TDD Gate Compliance
- RED and GREEN commits exist for all `tdd="true"` tasks in plan order.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: network_timeout | src/ai/langgraph/nodes/retrieve_phase2.py | New outbound HTTP path to knowledge API introduced timeout bounds and top_k cap as mitigation. |

## Self-Check: PASSED
- Found summary file: `.planning/phases/03-telegram-bot/03-02-SUMMARY.md`.
- Verified task commits exist: `385b883`, `aa88791`, `2f4b5e3`, `08ba589`, `5aca6f9`, `9a5995a`.
