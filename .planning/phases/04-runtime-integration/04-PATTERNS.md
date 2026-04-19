# Phase 4: Runtime Integration Hardening - Pattern Map

## Pattern Assignments

| Target file | Pattern source | Why |
|---|---|---|
| `src/tasks/ingest.py` | `src/tasks/ingest.py` + `src/tasks/knowledge.py` | Celery staged progress + explicit error logging + retry boundaries already standardized. |
| `src/tasks/knowledge.py` | existing file | Reuse extraction/SOP APIs directly; avoid new orchestration abstraction. |
| `src/api/routes/knowledge.py` | existing file + `tests/phase2/test_low_relevance_fallback.py` | Stable response envelope contract must remain unchanged for Phase 3 bot consumer. |
| `src/ai/rag/retriever.py` | existing file | Extend retriever implementation instead of adding alternative query stack. |
| `tests/phase4/*.py` | `tests/phase2/*.py` + `tests/phase3/test_multiturn_context.py` | Contract-first, deterministic, patch-friendly tests with no external network dependency. |

## Reuse Rules

1. Keep FastAPI route shape and safe error behavior from existing `/api/knowledge/query`.
2. Keep Qdrant collection contract `knowledge` from `QdrantStore.COLLECTION_NAME`.
3. Keep synthesis output model (`RagAnswer`) and attribution item semantics unchanged.
4. Use Celery task chaining/grouping already present in project task style; do not introduce new queue framework.

## Anti-Patterns to Avoid

- Adding a second query API contract for bot-only path.
- Re-introducing seed fallback candidates in production query route.
- Triggering extraction only via manual scripts instead of ingestion runtime flow.
