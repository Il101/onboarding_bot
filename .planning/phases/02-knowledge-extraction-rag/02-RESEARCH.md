# Phase 2: Knowledge Extraction & RAG - Research

**Researched:** 2026-04-19  
**Domain:** LLM knowledge extraction + SOP generation + hybrid RAG over existing Phase 1 Qdrant index  
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
### Knowledge Extraction Schema (KNW-01)
- **D-01:** Формат знания строго структурированный JSON.
- **D-02:** Базовые поля knowledge unit: `fact`, `topic`, `source_refs`, `confidence`.
- **D-03:** Одна knowledge unit = одна атомарная проверяемая мысль/правило.

### SOP Generation (KNW-02)
- **D-04:** SOP генерируется по фиксированному шаблону: `цель -> шаги -> исключения -> проверка результата`.
- **D-05:** Свободная генерация без структуры не используется в Phase 2.

### Confidence & Publishing Policy
- **D-06:** Low-confidence knowledge units не публикуются в knowledge-base до ревью.
- **D-07:** Confidence обязателен для каждого извлечённого знания и используется как gate публикации.

### Retrieval & Ranking (KNW-03)
- **D-08:** Retrieval пайплайн: hybrid search (dense+sparse) с последующим reranking top-K.
- **D-09:** Dense-only и sparse-only режимы не являются основным режимом для Phase 2.

### Source Attribution (KNW-04)
- **D-10:** В каждом ответе и SOP обязателен attribution: `source_id + excerpt + timestamp/page`.
- **D-11:** Attribution должен быть достаточно детальным для ручной верификации оператором.

### Low-Relevance Fallback
- **D-12:** При низкой релевантности retrieval система возвращает "недостаточно данных" + ближайшие найденные источники.
- **D-13:** "Генерировать любой ценой" при низкой релевантности запрещено.

### the agent's Discretion
- Точные пороги `confidence` и `relevance` (с обязательной документированной конфигурацией).
- Конкретная схема reranking (модель/эвристика), если соблюдены D-08 и D-12.
- Внутренняя структура хранения промежуточных артефактов extraction/SOP.

### Deferred Ideas (OUT OF SCOPE)
- UI-слой ревью low-confidence knowledge (перенесено в админский контур Phase 4).
- Диалоговые fallback-механики бота при низкой релевантности (детализация в Phase 3).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| KNW-01 | LLM извлекает структурированные знания из анонимизированного текста и группирует по темам | Structured extraction contract with Pydantic schema + confidence gate + topic field + Celery batch flow reuse from Phase 1 [VERIFIED: src/tasks/ingest.py] [CITED: https://developers.llamaindex.ai/python/framework-api-reference/output_parsers/pydantic] |
| KNW-02 | LLM генерирует SOP инструкции (Markdown) из кластеризованных знаний на основе чатов | Fixed SOP template enforcement (`цель -> шаги -> исключения -> проверка результата`) + generation from extracted units (not raw chat dump) [VERIFIED: .planning/phases/02-knowledge-extraction-rag/02-CONTEXT.md] [CITED: https://developers.llamaindex.ai/python/framework/module_guides/querying/structured_outputs] |
| KNW-03 | Система индексирует извлечённые знания в векторной БД (Qdrant) с hybrid search (векторный + BM25 для русского) | Existing dense+sparse collection pattern in repo + Qdrant hybrid retrieval via LlamaIndex `enable_hybrid=True` and hybrid query mode [VERIFIED: src/pipeline/indexer/qdrant_store.py] [CITED: https://developers.llamaindex.ai/python/examples/vector_stores/qdrant_hybrid] |
| KNW-04 | Каждый фрагмент знания хранит source attribution (ссылка на оригинальное сообщение/документ) | Metadata contract (`source_id`, `timestamp/page`, `excerpt`) and response source node extraction through `response.source_nodes` [VERIFIED: src/tasks/ingest.py] [CITED: https://developers.llamaindex.ai/python/examples/vector_stores/VertexAIVectorSearchDemo] |
</phase_requirements>

## Summary

Phase 2 should be implemented as an extension of the already-working Phase 1 ingestion pipeline, not a parallel rewrite. The codebase already anonymizes content, chunks text, creates dense+sparse vectors, and upserts into Qdrant collection `knowledge`; these are strong integration anchors for extraction/SOP/RAG tasks. [VERIFIED: src/tasks/ingest.py] [VERIFIED: src/pipeline/indexer/qdrant_store.py]

The core implementation decision is to treat Phase 2 as two linked pipelines: (1) **offline extraction pipeline** (knowledge units + SOP drafts with confidence gating), and (2) **online retrieval pipeline** (hybrid retrieve -> rerank -> synthesize -> attribution/fallback). This directly matches locked decisions D-01..D-13 and avoids destabilizing Phase 1 interfaces. [VERIFIED: .planning/phases/02-knowledge-extraction-rag/02-CONTEXT.md]

Primary risks are not in library availability but in contract integrity: losing source metadata, publishing low-confidence units, and answering when relevance is low. These are mitigated by explicit schema validation, threshold config in `src/core/config.py`, and guardrail tests mapped to KNW requirements. [VERIFIED: src/core/config.py] [VERIFIED: tests/api/test_ingest_routes.py]

**Primary recommendation:** Keep Qdrant as the single retrieval substrate, add a dedicated `src/ai/{extraction,rag}` layer with strict schema/fallback gates, and validate every KNW requirement via explicit tests before Phase 3 dependencies. [VERIFIED: src/pipeline/indexer/qdrant_store.py] [VERIFIED: .planning/ROADMAP.md]

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Knowledge unit extraction (KNW-01) | API / Backend | Database / Storage | LLM orchestration + schema validation are backend concerns; results persist as metadata/records and indexed text [VERIFIED: src/tasks/ingest.py] |
| SOP generation (KNW-02) | API / Backend | Database / Storage | SOP templating/generation is compute logic; markdown artifacts must be stored/versioned for later review and serving [ASSUMED] |
| Hybrid retrieval (KNW-03) | Database / Storage | API / Backend | Qdrant owns dense+sparse search primitives; backend controls query mode/top-k/rerank policy [VERIFIED: src/pipeline/indexer/qdrant_store.py] [CITED: https://developers.llamaindex.ai/python/examples/vector_stores/qdrant_hybrid] |
| Source attribution (KNW-04) | API / Backend | Database / Storage | Backend assembles `source_id + excerpt + timestamp/page`; storage must preserve metadata in payload [VERIFIED: src/pipeline/indexer/qdrant_store.py] [VERIFIED: src/tasks/ingest.py] |
| Low-relevance refusal path (D-12/D-13) | API / Backend | — | Threshold comparison and final response policy belong in backend application logic [VERIFIED: .planning/phases/02-knowledge-extraction-rag/02-CONTEXT.md] |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| llama-index | 0.14.20 (published 2026-04-03) | Retrieval/synthesis orchestration, structured outputs | Direct hybrid Qdrant patterns and `response.source_nodes` support match KNW-03/04 contracts [VERIFIED: PyPI API query] [CITED: https://developers.llamaindex.ai/python/examples/vector_stores/qdrant_hybrid] |
| llama-index-vector-stores-qdrant | 0.10.0 (published 2026-03-12) | Qdrant adapter for LlamaIndex | Canonical bridge for `QdrantVectorStore` with `enable_hybrid=True` [VERIFIED: PyPI API query] [CITED: https://developers.llamaindex.ai/python/examples/vector_stores/QdrantIndexDemo] |
| qdrant-client | 1.17.1 (published 2026-03-13) | Vector DB client (dense+sparse payload queries) | Already aligned with Phase 1 code and supports payload filtering + hybrid capabilities [VERIFIED: pyproject.toml] [VERIFIED: PyPI API query] [CITED: https://github.com/qdrant/qdrant/blob/master/README.md] |
| fastembed | 0.8.0 (published 2026-03-23) | Dense + sparse embedding inference (BM25-style sparse options) | Existing project embedder already uses `TextEmbedding` + `SparseTextEmbedding` [VERIFIED: src/pipeline/indexer/embedder.py] [VERIFIED: PyPI API query] [CITED: https://context7.com/qdrant/fastembed/llms.txt] |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pydantic | 2.13.2 (published 2026-04-17) | Enforce strict knowledge-unit schema | Validate KNW-01 JSON output before publish (D-01..D-03, D-06..D-07) [VERIFIED: pyproject.toml] [VERIFIED: PyPI API query] |
| pytest | 9.0.3 (published 2026-04-07) | Requirement-level regression tests | Build guardrail suite for fallback, attribution, schema validity [VERIFIED: tests/ directory] [VERIFIED: PyPI API query] |
| celery[redis] | 5.6.0+ (project pinned range) | Background extraction/SOP jobs | Reuse existing async orchestration pattern for long extraction runs [VERIFIED: pyproject.toml] [VERIFIED: src/tasks/ingest.py] |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| LlamaIndex retrieval adapter | Direct qdrant-client + custom retriever | More control but slower delivery and higher bug risk for KNW-03/04 contracts [ASSUMED] |
| Local cross-encoder reranker | Hosted reranker API | Faster startup, but may violate perimeter constraints depending on deployment mode [VERIFIED: .planning/PROJECT.md] [ASSUMED] |
| Pure model confidence gate | Retrieval-score gate + model confidence gate | Hybrid gate is safer; model confidence alone is not sufficient for D-12/D-13 behavior [ASSUMED] |

**Installation:**
```bash
uv add llama-index==0.14.20 \
  llama-index-vector-stores-qdrant==0.10.0 \
  qdrant-client==1.17.1 \
  fastembed==0.8.0
```

**Version verification:**  
- `llama-index 0.14.20` — published 2026-04-03 [VERIFIED: PyPI API query]  
- `llama-index-vector-stores-qdrant 0.10.0` — published 2026-03-12 [VERIFIED: PyPI API query]  
- `qdrant-client 1.17.1` — published 2026-03-13 [VERIFIED: PyPI API query]  
- `fastembed 0.8.0` — published 2026-03-23 [VERIFIED: PyPI API query]

## Architecture Patterns

### System Architecture Diagram

```text
[Phase 1 Ingestion Output: anonymized chunks + metadata in Qdrant "knowledge"]
                               |
                               v
                  [Phase 2 Extraction Worker (Celery)]
                  - pull source slices
                  - LLM structured extraction (JSON)
                  - confidence scoring + topic grouping
                               |
                               +------------------> [Low-confidence queue / review-needed]
                               |                    (not published) [D-06]
                               v
                    [Published Knowledge Artifacts]
                    - knowledge units
                    - SOP markdown (template-fixed)
                    - source_refs with trace fields
                               |
                               v
                      [RAG Query API / Service]
                 query -> hybrid retrieve -> rerank -> synthesize
                               |
                 +-------------+-------------+
                 |                           |
                 v                           v
      [relevance >= threshold]      [relevance < threshold]
      answer + full attribution      "недостаточно данных" +
      source_id/excerpt/time/page    nearest sources (D-12)
```

### Recommended Project Structure
```text
src/
├── ai/
│   ├── extraction/            # KNW-01 extraction schema + confidence/topic logic
│   │   ├── schemas.py         # Pydantic models for knowledge units
│   │   ├── extractor.py       # LLM extraction + validation loop
│   │   └── publish_policy.py  # D-06/D-07 publish gate
│   ├── sop/
│   │   ├── generator.py       # KNW-02 SOP markdown generation
│   │   └── template.py        # goal->steps->exceptions->verification
│   └── rag/
│       ├── retriever.py       # hybrid retrieval + metadata filters
│       ├── reranker.py        # top-K rerank strategy
│       ├── synthesizer.py     # grounded answer generation
│       └── attribution.py     # KNW-04 response contract formatter
├── tasks/
│   └── knowledge.py           # Celery tasks for extraction/SOP indexing
└── api/routes/
    └── knowledge.py           # endpoints for run/status/query
```

### Pattern 1: Contract-First Knowledge Extraction
**What:** LLM output must parse into strict schema (`fact`, `topic`, `source_refs`, `confidence`) before it is accepted. [VERIFIED: .planning/phases/02-knowledge-extraction-rag/02-CONTEXT.md]  
**When to use:** Every extraction batch for KNW-01 and pre-SOP materialization for KNW-02.  
**Example:**
```python
# Source: https://developers.llamaindex.ai/python/framework-api-reference/output_parsers/pydantic
from pydantic import BaseModel, Field

class KnowledgeUnit(BaseModel):
    fact: str = Field(min_length=5)
    topic: str
    confidence: float = Field(ge=0, le=1)
    source_refs: list[dict]
```

### Pattern 2: Hybrid Retrieval as Default Query Path
**What:** Use dense+sparse retrieval (`vector_store_query_mode="hybrid"`) then rerank top-K before synthesis. [CITED: https://developers.llamaindex.ai/python/examples/vector_stores/QdrantIndexDemo]  
**When to use:** Every user-facing question path for Phase 2 and downstream Phase 3 bot dependence.  
**Example:**
```python
# Source: https://developers.llamaindex.ai/python/examples/vector_stores/QdrantIndexDemo
query_engine = index.as_query_engine(
    vector_store_query_mode="hybrid",
    similarity_top_k=8,
    sparse_top_k=12,
    hybrid_top_k=6,
)
```

### Pattern 3: Attribution-First Response Assembly
**What:** Build response payload from `response.source_nodes` metadata for operator-verifiable links. [CITED: https://developers.llamaindex.ai/python/examples/vector_stores/VertexAIVectorSearchDemo]  
**When to use:** All Phase 2 outputs (RAG answer + SOP references).  
**Example:**
```python
# Source: https://developers.llamaindex.ai/python/examples/vector_stores/VertexAIVectorSearchDemo
sources = [
    {
        "source_id": n.node.metadata.get("source_id"),
        "excerpt": n.text[:240],
        "timestamp": n.node.metadata.get("timestamp"),
        "page": n.node.metadata.get("page"),
        "score": n.get_score(),
    }
    for n in response.source_nodes
]
```

### Anti-Patterns to Avoid
- **Generate SOP directly from raw chat chunks:** Loses atomic verification chain and weakens D-10/D-11 traceability; generate from validated knowledge units instead. [ASSUMED]
- **Hardcode thresholds in business code:** Prevents calibration and violates discretion requirement for configurable confidence/relevance thresholds. [VERIFIED: .planning/phases/02-knowledge-extraction-rag/02-CONTEXT.md]
- **Drop metadata during reindex:** Breaks KNW-04 and manual verification path. [VERIFIED: src/pipeline/indexer/qdrant_store.py]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Hybrid retrieval fusion | Custom dense+sparse merging math from scratch | Qdrant hybrid primitives + LlamaIndex QdrantVectorStore | Existing tested path already matches project stack and reduces ranking bugs [CITED: https://github.com/qdrant/qdrant/blob/master/README.md] [CITED: https://developers.llamaindex.ai/python/examples/vector_stores/qdrant_hybrid] |
| LLM JSON parsing | Regex-based JSON sanitizers | Pydantic validation + structured output parser | Guarantees schema compliance for KNW-01 and clean failure handling [CITED: https://developers.llamaindex.ai/python/framework-api-reference/output_parsers/pydantic] |
| Source attribution formatting | Ad-hoc string concatenation without structured fields | Typed attribution payload (`source_id/excerpt/timestamp/page`) | Required for D-10/D-11 and deterministic testing [VERIFIED: .planning/phases/02-knowledge-extraction-rag/02-CONTEXT.md] |
| Async job orchestration | New queue layer for Phase 2 | Existing Celery+Redis task pattern | Phase 1 already established and tested in repo [VERIFIED: src/tasks/ingest.py] [VERIFIED: tests/api/test_ingest_routes.py] |

**Key insight:** Phase 2 is mainly a contract-and-quality extension over existing foundations; hand-rolling infrastructure increases regression risk without adding requirement coverage. [VERIFIED: src/tasks/ingest.py] [ASSUMED]

## Common Pitfalls

### Pitfall 1: Metadata Erosion Between Retrieval and Answer
**What goes wrong:** Source chunks are retrieved, but response serialization omits `timestamp/page` fields, making attribution unverifiable. [VERIFIED: .planning/phases/02-knowledge-extraction-rag/02-CONTEXT.md]  
**Why it happens:** Developers only keep `text` + score from source nodes. [ASSUMED]  
**How to avoid:** Formalize attribution DTO and test KNW-04 contract fields for every answer/SOP unit. [ASSUMED]  
**Warning signs:** QA can’t trace answer claim to original message within 1 minute. [ASSUMED]

### Pitfall 2: In-memory Qdrant Sync/Async Test Mismatch
**What goes wrong:** Async retrieval tests fail or return empty results while sync path passes. [CITED: https://developers.llamaindex.ai/python/examples/vector_stores/qdrant_hybrid]  
**Why it happens:** In-memory mode does not share data between sync and async Qdrant clients. [CITED: https://developers.llamaindex.ai/python/examples/vector_stores/qdrant_hybrid]  
**How to avoid:** In tests, use consistent client mode per scenario or a shared non-memory Qdrant service container. [ASSUMED]  
**Warning signs:** Same collection appears populated in sync calls and empty in async calls. [CITED: https://developers.llamaindex.ai/python/examples/vector_stores/qdrant_hybrid]

### Pitfall 3: No Dual Gate (confidence + relevance)
**What goes wrong:** System publishes low-confidence knowledge or answers on low-relevance retrieval, violating D-06 and D-12. [VERIFIED: .planning/phases/02-knowledge-extraction-rag/02-CONTEXT.md]  
**Why it happens:** Teams gate only one stage (either extraction or retrieval). [ASSUMED]  
**How to avoid:** Separate publish gate for extraction confidence and answer gate for retrieval relevance. [ASSUMED]  
**Warning signs:** "Helpful-looking" outputs with thin sources or uncertain extraction provenance. [ASSUMED]

### Pitfall 4: Embedding Dimension Drift During Reindex
**What goes wrong:** New embedding model dimensions mismatch existing collection vector config (`size=1024`) and upserts fail or force full rebuild. [VERIFIED: src/pipeline/indexer/qdrant_store.py]  
**Why it happens:** Model changes are applied without collection migration plan. [ASSUMED]  
**How to avoid:** Lock dense model per phase; if changed, perform explicit new collection migration with backfill. [ASSUMED]  
**Warning signs:** Qdrant rejects inserts after model/config change. [ASSUMED]

## Code Examples

Verified patterns from official sources:

### Hybrid Qdrant Retrieval Setup
```python
# Source: https://developers.llamaindex.ai/python/examples/vector_stores/QdrantIndexDemo
from qdrant_client import QdrantClient, AsyncQdrantClient
from llama_index.vector_stores.qdrant import QdrantVectorStore

vector_store = QdrantVectorStore(
    client=QdrantClient(host="localhost", port=6333),
    aclient=AsyncQdrantClient(host="localhost", port=6333),
    collection_name="knowledge",
    enable_hybrid=True,
    fastembed_sparse_model="Qdrant/bm25",
)
```

### Metadata Filtering for Scoped Retrieval
```python
# Source: https://github.com/run-llama/llama_index/blob/main/docs/examples/vector_stores/Qdrant_metadata_filter.ipynb
from llama_index.core.vector_stores import MetadataFilters, MetadataFilter, FilterOperator

filters = MetadataFilters(
    filters=[
        MetadataFilter(key="source_id", operator=FilterOperator.EQ, value="source-123"),
    ]
)
```

### Dense + Sparse Embedding Generation
```python
# Source: https://context7.com/qdrant/fastembed/llms.txt
from fastembed import TextEmbedding, SparseTextEmbedding

dense = TextEmbedding(model_name="intfloat/multilingual-e5-large")
sparse = SparseTextEmbedding(model_name="Qdrant/bm42-all-minilm-l6-v2-attentions")
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Dense-only retrieval | Hybrid dense+sparse retrieval with fusion | Qdrant 2024 roadmap + current docs | Better lexical recall for exact terms/abbreviations alongside semantic match [CITED: https://github.com/qdrant/qdrant/blob/master/docs/roadmap/roadmap-2024.md] |
| Free-form LLM extraction | Structured extraction with schema validation | Became mainstream in modern LLM app frameworks [ASSUMED] | Lower downstream parsing errors and safer publish gating |
| "Always answer" behavior | Explicit low-relevance refusal fallback | Locked in D-12/D-13 for this phase [VERIFIED: .planning/phases/02-knowledge-extraction-rag/02-CONTEXT.md] | Reduces hallucination risk and aligns with phase safety posture |

**Deprecated/outdated:**
- Dense-only as primary mode for this phase: conflicts with locked D-08/D-09 decisions. [VERIFIED: .planning/phases/02-knowledge-extraction-rag/02-CONTEXT.md]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | SOP artifacts should be persisted/versioned in storage for later review workflows | Architectural Responsibility Map | Could require redesign in Phase 4 integration if storage pattern differs |
| A2 | Direct qdrant-client custom retrieval would materially increase bug risk vs adapter path | Standard Stack / Alternatives | Might over-constrain implementation freedom |
| A3 | Dual gating (confidence+relevance) should be implemented as two separate mechanisms | Common Pitfalls | Could produce redundant complexity if one gate already fully sufficient |
| A4 | Structured extraction is now mainstream and superior to free-form extraction for this domain | State of the Art | Might bias planner against simpler approaches where acceptable |
| A5 | Testing strategy should include dedicated attribution DTO contract tests | Common Pitfalls / Validation Architecture | Could add extra test workload with marginal gain if existing tests already cover it |

## Resolved Questions

1. **Threshold defaults for `confidence_threshold` and `relevance_threshold`**
   - **Resolution:** Use conservative defaults in `src/core/config.py` and keep both fully env-configurable per D-06/D-07/D-12/D-13. Initial calibration is validated by Phase 2 contract tests, then tuned with golden-set regression in execution summaries.
   - **Status:** ✅ Resolved for planning scope (implementation + tests enforce configurability; value tuning remains operational data task, not a planning blocker).

2. **Persistence target for extracted knowledge artifacts**
   - **Resolution:** Phase 2 persists publishable extraction output into Qdrant through explicit index writer wiring (`extractor -> knowledge_writer -> QdrantStore`) to satisfy KNW-03 retrieval readiness. Relational lifecycle state (review/edit workflows) is deferred to later admin/review phases.
   - **Status:** ✅ Resolved for Phase 2 scope (single persistence path defined and test-mapped).

3. **Reranker standardization path**
   - **Resolution:** Implement deterministic reranker stage as a pluggable module in `src/ai/rag/reranker.py` with contract tests verifying invocation/truncation behavior; concrete model strategy remains discretionary and can evolve without changing API contracts.
   - **Status:** ✅ Resolved for planning scope (interface + behavior locked, backend choice intentionally pluggable).

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | All Phase 2 code | ✓ | 3.12.4 | — [VERIFIED: local command output] |
| uv | Dependency/test execution | ✓ | 0.8.22 | pip (slower) [VERIFIED: local command output] |
| Docker CLI | Running local Qdrant/Redis stack | ✓ (CLI) | 29.2.1 | External managed services (policy dependent) [VERIFIED: local command output] |
| Docker daemon | Running local containers now | ✗ | — | Start Docker Desktop before execution [VERIFIED: local command output] |
| redis-cli | Celery broker diagnostics | ✓ (CLI) | 8.2.1 | `celery inspect` + logs [VERIFIED: local command output] |
| Redis service | Celery runtime | ✗ (current) | — | Start via docker-compose [VERIFIED: local command output] |
| Qdrant service (6333) | Hybrid retrieval/index tests | ✗ (current) | — | Start via docker-compose [VERIFIED: local command output] |

**Missing dependencies with no fallback:**
- None; all missing runtime services can be started locally before execution. [VERIFIED: docker-compose.yml exists]

**Missing dependencies with fallback:**
- Docker daemon, Redis service, Qdrant service are currently down; planner should include startup/health-check tasks before implementation tests. [VERIFIED: local command output]

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.3 + pytest-asyncio (configured) [VERIFIED: pyproject.toml] [VERIFIED: PyPI API query] |
| Config file | `pyproject.toml` (`[tool.pytest.ini_options]`) [VERIFIED: pyproject.toml] |
| Quick run command | `uv run pytest tests/pipeline/test_qdrant_indexer.py tests/pipeline/test_chunker.py -q` [VERIFIED: tests/ tree] |
| Full suite command | `uv run pytest tests/ -v --tb=short` [VERIFIED: .planning/phases/01-foundation-data-ingestion/01-06-SUMMARY.md] |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| KNW-01 | Structured JSON extraction with required fields + confidence | unit | `uv run pytest tests/phase2/test_extraction_schema.py -q` | ❌ Wave 0 |
| KNW-02 | SOP template sections enforced (`цель/шаги/исключения/проверка`) | unit | `uv run pytest tests/phase2/test_sop_template.py -q` | ❌ Wave 0 |
| KNW-03 | Hybrid retrieve path (dense+sparse + rerank stage invoked) | integration | `uv run pytest tests/phase2/test_hybrid_retrieval.py -q` | ❌ Wave 0 |
| KNW-04 | Attribution payload includes `source_id/excerpt/timestamp/page` | unit/integration | `uv run pytest tests/phase2/test_attribution_contract.py -q` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/phase2/test_extraction_schema.py tests/phase2/test_attribution_contract.py -q`  
- **Per wave merge:** `uv run pytest tests/phase2 -v`  
- **Phase gate:** `uv run pytest tests/ -v --tb=short` full suite green before `/gsd-verify-work` [VERIFIED: .planning/config.json]

### Wave 0 Gaps
- [ ] `tests/phase2/test_extraction_schema.py` — covers KNW-01
- [ ] `tests/phase2/test_sop_template.py` — covers KNW-02
- [ ] `tests/phase2/test_hybrid_retrieval.py` — covers KNW-03
- [ ] `tests/phase2/test_attribution_contract.py` — covers KNW-04
- [ ] `tests/phase2/test_low_relevance_fallback.py` — covers D-12/D-13 policy behavior

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no (Phase 2 core pipeline only) | Auth concerns deferred to bot/admin phases; keep internal endpoints non-public by deployment policy [VERIFIED: .planning/ROADMAP.md] [ASSUMED] |
| V3 Session Management | no (no user session workflow in phase scope) | Stateless pipeline/service calls [VERIFIED: .planning/phases/02-knowledge-extraction-rag/02-CONTEXT.md] |
| V4 Access Control | yes | Restrict extraction/reindex operations to trusted internal operators/services [ASSUMED] |
| V5 Input Validation | yes | Pydantic schema validation for extraction outputs + existing file/content checks from Phase 1 ingestion interfaces [VERIFIED: src/api/routes/ingest.py] |
| V6 Cryptography | no (no new crypto primitive in scope) | Reuse platform/storage defaults; never hand-roll crypto [ASSUMED] |

### Known Threat Patterns for Python + Qdrant + LLM RAG

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Hallucinated answer under low relevance | Tampering | Hard relevance threshold + refusal fallback (D-12/D-13) [VERIFIED: .planning/phases/02-knowledge-extraction-rag/02-CONTEXT.md] |
| Broken/forged attribution | Repudiation | Enforce source field contract and traceability tests (KNW-04) [VERIFIED: .planning/REQUIREMENTS.md] |
| PII leakage into generated artifacts | Information Disclosure | Preserve Phase 1 anonymization-first rule before extraction/synthesis [VERIFIED: src/tasks/ingest.py] [VERIFIED: .planning/phases/01-foundation-data-ingestion/01-SECURITY.md] |
| Prompt injection in retrieved context | Tampering | Constrain synthesis to retrieved evidence and structured output checks [ASSUMED] |
| Excessive retrieval context causing accidental disclosure | Information Disclosure | Metadata filters + top-K limits + rerank truncation before synthesis [CITED: https://github.com/qdrant/qdrant/blob/master/README.md] [ASSUMED] |

## Sources

### Primary (HIGH confidence)
- `/run-llama/llama_index` (Context7 CLI) — hybrid Qdrant setup, source_nodes usage, metadata filtering, async caveat  
- `/qdrant/qdrant` (Context7 CLI) — hybrid search and payload filtering capabilities  
- `/qdrant/fastembed` (Context7 CLI) — dense/sparse embedding API patterns  
- `src/tasks/ingest.py`, `src/pipeline/indexer/qdrant_store.py`, `src/pipeline/indexer/embedder.py`, `src/core/config.py` — existing integration contracts  
- `pyproject.toml`, `tests/` tree — current dependencies and test framework  
- PyPI JSON + `pip index versions` (local commands) — package versions and publish dates

### Secondary (MEDIUM confidence)
- `.planning/phases/02-knowledge-extraction-rag/02-AI-SPEC.md` — phase-level framework/eval guidance (project-internal, not official vendor docs)  
- `.planning/research/STACK.md`, `.planning/research/PITFALLS.md` — prior project research baseline

### Tertiary (LOW confidence)
- None (all nontrivial stack claims above are either code-verified, config-verified, or doc-cited in-session)

## Metadata

**Confidence breakdown:**
- Standard stack: **HIGH** — versions and capabilities verified via PyPI + Context7 + repo code.
- Architecture: **HIGH** — constrained by locked decisions and existing Phase 1 interfaces.
- Pitfalls: **MEDIUM** — several mitigations are best-practice assumptions requiring phase-specific validation.

**Research date:** 2026-04-19  
**Valid until:** 2026-05-19 (30 days; libs are active and fast-moving)
