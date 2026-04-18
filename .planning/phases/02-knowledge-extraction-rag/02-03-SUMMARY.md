---
phase: 02-knowledge-extraction-rag
plan: 03
subsystem: api
tags: [rag, retrieval, rerank, attribution, fastapi]
requires:
  - phase: 02-knowledge-extraction-rag
    provides: indexed knowledge units and extraction contracts from 02-02
provides:
  - Hybrid retriever and deterministic reranker
  - Attribution formatter preserving source locator and score
  - Synthesis policy with low-relevance fallback
  - Knowledge query API endpoint with stable response envelope
affects: [phase-3, phase-4]
tech-stack:
  added: []
  patterns: [fallback-first synthesis gate, attribution-first response envelope]
key-files:
  created: [src/ai/rag/retriever.py, src/ai/rag/reranker.py, src/ai/rag/attribution.py, src/ai/rag/synthesizer.py, src/api/routes/knowledge.py, tests/phase2/test_hybrid_retrieval.py, tests/phase2/test_attribution_contract.py, tests/phase2/test_low_relevance_fallback.py]
  modified: [src/api/main.py]
key-decisions:
  - "Fallback path returns nearest sources with explicit insufficient-data message below relevance threshold."
  - "Knowledge API returns deterministic envelope: answer/confidence/sources/fallback_used."
patterns-established:
  - "Retrieve -> rerank -> relevance gate -> synthesize with required attribution."
  - "API route uses validated input model and safe server error masking."
requirements-completed: [KNW-01, KNW-03, KNW-04]
duration: n/a
completed: 2026-04-18
---

# Phase 2 Plan 03: Online RAG Query Path and API Summary

**Shipped hybrid retrieval/reranking with attribution-preserving synthesis and low-relevance fallback exposed via `/api/knowledge/query`.**

## Performance

- **Duration:** n/a
- **Started:** 2026-04-18T22:25:38Z
- **Completed:** 2026-04-18T22:37:33Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments
- Implemented hybrid retriever abstraction with deterministic rerank stage.
- Implemented attribution formatter aligned with contract (`source_id`, `excerpt`, `timestamp/page`, `score`).
- Implemented synthesis fallback policy and knowledge query API response envelope.

## Task Commits

1. **Task 1 (RED):** `eb9d04e` (test)
2. **Task 1 (GREEN):** `f414b9e` (feat)
3. **Task 2 (RED):** `b14775c` (test)
4. **Task 2 (GREEN):** `5c76a70` (feat)

## Files Created/Modified
- `src/ai/rag/retriever.py` - Hybrid retriever default and rerank integration point.
- `src/ai/rag/reranker.py` - Deterministic score-based reranker.
- `src/ai/rag/attribution.py` - Retrieval-node to typed attribution formatter.
- `src/ai/rag/synthesizer.py` - Relevance-gated synthesis and fallback behavior.
- `src/api/routes/knowledge.py` - `/api/knowledge/query` endpoint and response envelope.
- `src/api/main.py` - Registered knowledge router.
- `tests/phase2/test_hybrid_retrieval.py` - Retrieval/reranking tests.
- `tests/phase2/test_attribution_contract.py` - Attribution contract tests.
- `tests/phase2/test_low_relevance_fallback.py` - Fallback and API contract tests.

## Decisions Made
- Low-relevance path intentionally refuses operational guidance and returns nearest sources.
- API route returns typed stable envelope for downstream bot/admin consumers.

## Deviations from Plan

None - plan executed exactly as written.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: new_network_endpoint | `src/api/routes/knowledge.py` | Added new knowledge query endpoint (`POST /api/knowledge/query`) with synthesis output crossing trust boundary. |

## Issues Encountered
- None.

## User Setup Required
- None - no external service configuration required.

## Next Phase Readiness
- Phase 3 bot integration can call `/api/knowledge/query` with fallback-safe and attribution-rich responses.

## Self-Check: PASSED
