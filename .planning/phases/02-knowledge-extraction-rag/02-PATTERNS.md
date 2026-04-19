# Phase 2: Knowledge Extraction & RAG - Pattern Map

**Mapped:** 2026-04-19  
**Files analyzed:** 14  
**Analogs found:** 14 / 14

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `src/ai/extraction/schemas.py` | model | transform | `src/models/source.py` | role-match |
| `src/ai/extraction/extractor.py` | service | batch | `src/tasks/ingest.py` | partial (task-orchestrator pattern) |
| `src/ai/extraction/publish_policy.py` | utility | transform | `src/pipeline/filters/noise.py` | partial (policy filter pattern) |
| `src/ai/sop/template.py` | utility | transform | `src/pipeline/chunker/text_chunker.py` | partial (pure function + constants) |
| `src/ai/sop/generator.py` | service | transform | `src/pipeline/chunker/telegram_chunker.py` | partial (structured transform + metadata) |
| `src/ai/rag/retriever.py` | service | request-response | `src/pipeline/indexer/qdrant_store.py` | role-match |
| `src/ai/rag/reranker.py` | service | transform | `src/pipeline/filters/grouping.py` | partial (deterministic ranking/grouping function) |
| `src/ai/rag/synthesizer.py` | service | request-response | `src/tasks/ingest.py` | partial (pipeline stage orchestration + guarded failure) |
| `src/ai/rag/attribution.py` | utility | transform | `src/pipeline/chunker/telegram_chunker.py` | partial (payload shaping with metadata fields) |
| `src/tasks/knowledge.py` | service | batch | `src/tasks/ingest.py` | exact |
| `src/api/routes/knowledge.py` | route | request-response | `src/api/routes/ingest.py` | exact |
| `src/core/config.py` (modify) | config | transform | `src/core/config.py` | exact |
| `tests/phase2/test_extraction_schema.py` | test | transform | `tests/pipeline/test_anonymizer.py` | role-match |
| `tests/phase2/test_sop_template.py` | test | transform | `tests/pipeline/test_chunker.py` | role-match |
| `tests/phase2/test_hybrid_retrieval.py` | test | request-response | `tests/pipeline/test_qdrant_indexer.py` | role-match |
| `tests/phase2/test_attribution_contract.py` | test | request-response | `tests/api/test_ingest_routes.py` | role-match |
| `tests/phase2/test_low_relevance_fallback.py` | test | request-response | `tests/api/test_ingest_routes.py` | role-match |

## Pattern Assignments

### `src/ai/extraction/schemas.py` (model, transform)
**Analog:** `src/models/source.py`

**Typed schema/enums pattern** (lines 1-13):
```python
import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

class SourceType(str, enum.Enum):
    TELEGRAM = "telegram"
    PDF = "pdf"
```

**Guidance to copy:** keep explicit typed fields and enum-like contracts (`confidence`, `topic`, `source_refs`) as strict types, same “contract-first” style.

---

### `src/ai/extraction/extractor.py` (service, batch)
**Analog:** `src/tasks/ingest.py`

**Pipeline stage orchestration pattern** (lines 21-59):
```python
@celery_app.task(bind=True, autoretry_for=(Exception,), max_retries=3)
def ingest_telegram(self, source_id: str, json_path: str, voice_dir: str):
    try:
        self.update_state(state="PROGRESS", meta={"stage": "parsing", "progress": 10})
        messages = parse_telegram_export(json_path)
        ...
        self.update_state(state="PROGRESS", meta={"stage": "indexing", "progress": 80})
        ...
        count = store.upsert_chunks(chunks)
        return {"status": "completed", "messages_processed": len(messages), "chunks_indexed": count}
    except Exception as exc:
        logger.error("Ingestion failed for source %s: %s", source_id, exc)
        self.update_state(state="FAILURE", meta={"error": str(exc)})
        raise
```

**Guidance to copy:** extraction should be explicit stage-by-stage (`extract -> validate -> confidence gate -> publish candidate`) with Celery progress updates and failure state update.

---

### `src/ai/sop/template.py` (utility, transform)
**Analog:** `src/pipeline/chunker/text_chunker.py`

**Constant-driven pure-function pattern** (lines 3-11, 39-48):
```python
CHARS_PER_TOKEN = 3.5
TARGET_TOKENS = 400
MAX_TOKENS = 500
MIN_TOKENS = 300

def chunk_text(text: str, overlap_sentences: int = 1) -> list[str]:
    if not text.strip():
        return []
```

```python
def _split_markdown_paragraphs(text: str) -> list[str]:
    return [part for part in re.split(r"\n(?=#{1,3}\s)", text) if part.strip()]
```

**Guidance to copy:** encode SOP template sections as constants + deterministic helper functions (no free-form generation path in template module).

---

### `src/ai/sop/generator.py` (service, transform)
**Analog:** `src/pipeline/chunker/telegram_chunker.py`

**Structured output with metadata pattern** (lines 5-22):
```python
def chunk_telegram_messages(messages: list, window_minutes: int = 30) -> list[dict]:
    groups = group_messages_chronologically(messages, window_minutes)
    chunks: list[dict] = []
    ...
    metadata = {
        "source_type": "telegram",
        "date_range": f"{group[0].date} - {group[-1].date}",
        "authors": list({m.author for m in group}),
        "chat": group[0].author,
    }
```

**Guidance to copy:** SOP generator should return structured artifact + metadata block (topic/confidence/source_refs summary), not plain markdown string only.

---

### `src/ai/rag/retriever.py` (service, request-response)
**Analog:** `src/pipeline/indexer/qdrant_store.py`

**Qdrant collection + payload conventions** (lines 5-27, 29-46):
```python
class QdrantStore:
    COLLECTION_NAME = "knowledge"
    ...
    def ensure_collection(self, dense_size: int = 1024):
        if not self.client.collection_exists(self.COLLECTION_NAME):
            self.client.create_collection(...)
```

```python
def upsert_chunks(self, chunks: list[dict]) -> int:
    ...
    payload={"text": chunk["text"], **chunk["metadata"]},
```

**Guidance to copy:** keep retrieval tied to same collection/payload contract and metadata keys (`source_id`, timestamps/pages when present) for KNW-04 attribution.

---

### `src/ai/rag/reranker.py` (service, transform)
**Analog:** `src/pipeline/filters/grouping.py`

**Deterministic transform pattern** (lines 4-24):
```python
def group_messages_chronologically(messages: list, window_minutes: int = 30) -> list[list]:
    if not messages:
        return []
    ...
    return groups
```

**Guidance to copy:** implement reranker as deterministic, testable function/class returning ordered candidates; keep empty-input fast return path.

---

### `src/ai/rag/synthesizer.py` (service, request-response)
**Analog:** `src/tasks/ingest.py`

**Guarded stage flow + exception logging** (lines 60-63, 97-100):
```python
except Exception as exc:
    logger.error("Ingestion failed for source %s: %s", source_id, exc)
    self.update_state(state="FAILURE", meta={"error": str(exc)})
    raise
```

**Guidance to copy:** synthesize only after retrieval/rerank gate; if relevance is low, return fallback payload (not exception); reserve exceptions for true runtime failures.

---

### `src/ai/rag/attribution.py` (utility, transform)
**Analog:** `src/pipeline/chunker/telegram_chunker.py` + `src/pipeline/indexer/qdrant_store.py`

**Metadata-preserving payload shape** (telegram_chunker.py lines 11-16; qdrant_store.py line 42):
```python
metadata = {
    "source_type": "telegram",
    "date_range": f"{group[0].date} - {group[-1].date}",
    "authors": list({m.author for m in group}),
    "chat": group[0].author,
}
```
```python
payload={"text": chunk["text"], **chunk["metadata"]}
```

**Guidance to copy:** attribution formatter must always output `source_id + excerpt + timestamp/page(+score)` from metadata-carrying nodes.

---

### `src/tasks/knowledge.py` (service, batch)
**Analog:** `src/tasks/ingest.py`

**Task registration and dependencies pattern** (lines 1-18):
```python
from celery import Celery
...
logger = get_logger(__name__)
celery_app = Celery("vbrain", broker=settings.redis_url, backend=settings.redis_url)
```

**Progress/status contract pattern** (lines 24, 27, 30, 36, 39, 42):
```python
self.update_state(state="PROGRESS", meta={"stage": "...", "progress": ...})
```

**Guidance to copy:** build `extract_knowledge`/`generate_sop` tasks with same bind/autoretry/progress/error style.

---

### `src/api/routes/knowledge.py` (route, request-response)
**Analog:** `src/api/routes/ingest.py`

**Router and endpoint style** (lines 11, 42-46, 95-106):
```python
router = APIRouter(prefix="/api/ingest", tags=["ingestion"])
...
@router.post("/telegram")
async def upload_telegram(...):
```
```python
@router.get("/status/{job_id}")
async def get_status(job_id: str):
    result = AsyncResult(job_id)
    if result.state == "PROGRESS":
        return {"status": "processing", **(result.info or {})}
```

**Validation + safe failure messages** (lines 20-24, 31-34, 102-103):
```python
if len(content) > max_bytes:
    raise HTTPException(status_code=413, detail="File too large")
```
```python
if result.state == "FAILURE":
    return {"status": "failed", "error": "Task failed"}
```

**Guidance to copy:** knowledge routes should follow same response envelope and error masking pattern.

---

### `src/core/config.py` (config, transform) — modify
**Analog:** `src/core/config.py`

**Settings declaration pattern** (lines 4-34):
```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    ...
    pii_confidence_threshold: float = 0.5
    upload_dir: str = "./data/uploads"
```

**Guidance to copy:** add Phase-2 fields here (e.g., `knowledge_confidence_threshold`, `rag_relevance_threshold`, `rag_top_k`) as typed settings only; avoid hardcoding in services.

---

### Phase 2 tests (`tests/phase2/*.py`)

#### `test_extraction_schema.py`
**Analog:** `tests/pipeline/test_anonymizer.py`  
**Pattern:** focused deterministic unit tests with explicit assertions (e.g., lines 81-87, 106-111).

#### `test_sop_template.py`
**Analog:** `tests/pipeline/test_chunker.py`  
**Pattern:** input-output tests for pure functions (lines 6-11, 37-38).

#### `test_hybrid_retrieval.py`
**Analog:** `tests/pipeline/test_qdrant_indexer.py`  
**Pattern:** mock clients/classes, assert config and payload (lines 34-42, 44-57, 82-96).

#### `test_attribution_contract.py`
**Analog:** `tests/api/test_ingest_routes.py`  
**Pattern:** API contract checks for response keys/status (lines 197-203, 206-213).

#### `test_low_relevance_fallback.py`
**Analog:** `tests/api/test_ingest_routes.py`  
**Pattern:** enforce safe fallback message policy similar to masked failures (lines 206-213).

## Shared Patterns

### Logging
**Source:** `src/core/logging.py` (lines 5-14, 17-18)
```python
def setup_logging(level: str = "INFO"):
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
```
Apply to: all new services/tasks (`src/ai/*`, `src/tasks/knowledge.py`).

### Config-driven thresholds
**Source:** `src/core/config.py` (lines 4-34)  
Apply to: extraction publish gate and RAG relevance fallback (D-06/D-07/D-12).

### Celery long-running orchestration
**Source:** `src/tasks/ingest.py` (lines 21-23, 24-63, 66-100)  
Apply to: `src/tasks/knowledge.py` for extraction/SOP background jobs.

### Metadata persistence for attribution
**Source:** `src/pipeline/indexer/qdrant_store.py` (line 42) + `src/pipeline/chunker/telegram_chunker.py` (lines 11-16)  
Apply to: retriever + attribution formatter; never drop `source_id/timestamp/page` metadata.

### API validation and safe error policy
**Source:** `src/api/routes/ingest.py` (lines 20-40, 47-49, 77-89, 95-106)  
Apply to: `src/api/routes/knowledge.py` endpoints.

## No Analog Found

| File | Role | Data Flow | Reason |
|---|---|---|---|
| `src/ai/rag/retriever.py` (hybrid query via LlamaIndex query engine) | service | request-response | Repo has Qdrant upsert/delete patterns, but no existing query-time hybrid retrieval implementation. |
| `src/ai/rag/synthesizer.py` | service | request-response | No existing LLM synthesis module in codebase yet. |
| `src/ai/extraction/extractor.py` (LLM structured JSON extraction) | service | batch | No existing LLM extraction module; only ingestion preprocessing/indexing exists. |

## Metadata

- **Analog search scope:** `src/`, `tests/`, `.planning/phases/02-knowledge-extraction-rag/`
- **Files scanned:** 45 Python files (tree scan) + Phase 2 context/research docs
- **Pattern extraction date:** 2026-04-19

