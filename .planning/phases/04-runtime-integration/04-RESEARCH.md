# Phase 4: Runtime Integration Hardening - Research

**Researched:** 2026-04-19  
**Domain:** ingestion -> extraction/SOP -> retrieval runtime wiring  
**Confidence:** HIGH

## Source Constraints

- Phase goal from ROADMAP: close integration gaps so bot answers are grounded on real indexed knowledge.
- Requirements in scope: `KNW-01`, `KNW-02`, `KNW-03`, `KNW-04`, `BOT-01`.
- Milestone audit blockers:
  - Ingestion does not trigger extraction/SOP runtime path.
  - `/api/knowledge/query` uses seed candidates instead of real retrieval.
  - Bot is wired to endpoint but receives non-grounded payload.

## Existing Runtime Anchors (Verified)

- `src/tasks/ingest.py` already builds anonymized chunks and indexes them into Qdrant.
- `src/tasks/knowledge.py` already contains `extract_knowledge_task` and `generate_sop_task`.
- `src/pipeline/indexer/knowledge_writer.py` writes publishable knowledge units into `knowledge` collection.
- `src/api/routes/knowledge.py` already returns stable envelope (`answer`, `confidence`, `sources`, `fallback_used`) expected by Phase 3 retrieval node.

## Integration Strategy

1. **Wire ingestion -> extraction/SOP orchestration** inside ingestion task flow so no manual trigger is required (closes KNW-01/02 runtime gap).
2. **Replace seed-based query path with real retriever-backed query** while preserving existing response envelope contract (closes KNW-03/04 and BOT-01 grounding gap).
3. **Keep bot-facing contract unchanged** to avoid regressions in Phase 3 transport and policy graph.

## Risks and Guardrails

- Risk: background orchestration failure can silently drop extraction.
  - Guardrail: explicit task status metadata + test for dispatch path.
- Risk: retrieval migration can break envelope consumed by bot.
  - Guardrail: contract tests on `/api/knowledge/query` and integration test via `retrieve_phase2_payload`.
- Risk: metadata loss (`source_id`, `excerpt`, `timestamp/page`) during retrieval format conversion.
  - Guardrail: attribution contract tests must assert required fields.

## Out of Scope (for this phase)

- Telegram role whitelist integration (`BOT-05`) — moved to Phase 5.
- Admin review UI and moderation workflow (`ADM-*`) — Phase 6.
