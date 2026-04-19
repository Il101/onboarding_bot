# Phase 3: Telegram Bot - Pattern Map

**Mapped:** 2026-04-18  
**Files analyzed:** 17  
**Analogs found:** 15 / 17

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `src/bot/telegram_app.py` | component | event-driven | `src/api/main.py` | role-match |
| `src/bot/presenters.py` | utility | transform | `src/ai/rag/attribution.py` | flow-match |
| `src/bot/auth.py` | middleware | request-response | `src/ai/extraction/publish_policy.py` | flow-match |
| `src/bot/feedback.py` | service | event-driven | `src/tasks/knowledge.py` | partial |
| `src/ai/langgraph/state.py` | model | transform | `src/ai/rag/contracts.py` | exact |
| `src/ai/langgraph/graph.py` | service | event-driven | `src/tasks/ingest.py` | flow-match |
| `src/ai/langgraph/nodes/retrieve_phase2.py` | service | request-response | `src/api/routes/knowledge.py` | exact |
| `src/ai/langgraph/nodes/decide.py` | service | transform | `src/ai/rag/synthesizer.py` | exact |
| `src/ai/langgraph/nodes/summarize.py` | service | transform | `src/ai/rag/retriever.py` | partial |
| `src/ai/langgraph/nodes/answer.py` | service | request-response | `src/api/routes/knowledge.py` | role-match |
| `src/models/feedback_event.py` *(implied)* | model | CRUD | `src/models/ingest_job.py` | exact |
| `src/core/config.py` *(modify)* | config | transform | `src/core/config.py` | exact |
| `tests/phase3/test_graph_fallback.py` | test | transform | `tests/phase2/test_low_relevance_fallback.py` | exact |
| `tests/phase3/test_source_block_always_present.py` | test | request-response | `tests/phase2/test_contracts_and_policy.py` | role-match |
| `tests/phase3/test_auth_gate.py` | test | request-response | `tests/api/test_ingest_routes.py` | role-match |
| `tests/phase3/test_multiturn_context.py` | test | event-driven | `tests/api/test_ingest_routes.py` | partial |
| `tests/phase3/test_feedback_capture.py` | test | event-driven | `tests/api/test_ingest_routes.py` | role-match |

## Pattern Assignments

### `src/bot/telegram_app.py` (component, event-driven)

**Analog:** `src/api/main.py`

**Imports + startup lifecycle pattern** (`src/api/main.py:1-7`):
```python
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.routes.ingest import router as ingest_router
from src.api.routes.knowledge import router as knowledge_router
from src.core.logging import setup_logging
```

**App bootstrap pattern** (`src/api/main.py:10-23`):
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    yield

app = FastAPI(
    title="V-Brain API",
    version="0.1.0",
    lifespan=lifespan,
)
app.include_router(ingest_router)
app.include_router(knowledge_router)
```

Use same startup style for Telegram app init/shutdown (initialize checkpointer/client once on startup, close on shutdown).

---

### `src/ai/langgraph/state.py` (model, transform)

**Analog:** `src/ai/rag/contracts.py`

**Pydantic contract pattern** (`src/ai/rag/contracts.py:3-11`):
```python
from pydantic import BaseModel, Field, model_validator

class AttributionItem(BaseModel):
    source_id: str = Field(min_length=1)
    excerpt: str = Field(min_length=1)
    score: float = Field(ge=0.0, le=1.0)
    timestamp: str | None = None
    page: int | None = None
```

**Cross-field validator pattern** (`src/ai/rag/contracts.py:13-17`):
```python
@model_validator(mode="after")
def validate_locator(self) -> "AttributionItem":
    if self.timestamp is None and self.page is None:
        raise ValueError("attribution requires timestamp or page for manual verification")
    return self
```

**Envelope model pattern** (`src/ai/rag/contracts.py:20-24`):
```python
class RagAnswer(BaseModel):
    answer: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    sources: list[AttributionItem] = Field(default_factory=list)
    fallback_used: bool = False
```

Use this for `SourceRef`, `BotAnswer`, and `BotState` schema constraints.

---

### `src/ai/langgraph/nodes/retrieve_phase2.py` (service, request-response)

**Analog:** `src/api/routes/knowledge.py`

**Request schema + config-bounded limits** (`src/api/routes/knowledge.py:12-15`):
```python
class KnowledgeQueryRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int | None = Field(default=None, ge=1, le=settings.rag_hybrid_top_k)
```

**Route call + envelope shape** (`src/api/routes/knowledge.py:20-47`):
```python
effective_top_k = payload.top_k or settings.rag_hybrid_top_k
...
result = synthesize_answer(
    payload.query,
    candidates=seed_candidates[:effective_top_k],
)
return {
    "answer": result.answer,
    "confidence": result.confidence,
    "sources": [item.model_dump() for item in result.sources],
    "fallback_used": result.fallback_used,
}
```

**Error masking pattern** (`src/api/routes/knowledge.py:48-49`):
```python
except Exception as exc:
    raise HTTPException(status_code=500, detail="Knowledge query failed") from exc
```

In bot node: keep strict envelope consumption (`answer/confidence/sources/fallback_used`) and shield raw exceptions from user-facing output.

---

### `src/ai/langgraph/nodes/decide.py` (service, transform)

**Analog:** `src/ai/rag/synthesizer.py`

**Fallback constant pattern** (`src/ai/rag/synthesizer.py:10`):
```python
FALLBACK_MESSAGE = "Недостаточно данных для уверенного ответа. Проверьте ближайшие источники."
```

**Deterministic threshold branch** (`src/ai/rag/synthesizer.py:18-24`):
```python
if not should_answer_for_relevance(float(top_score)):
    return RagAnswer(
        answer=FALLBACK_MESSAGE,
        confidence=float(top_score),
        sources=sources,
        fallback_used=True,
    )
```

**Grounded-answer branch** (`src/ai/rag/synthesizer.py:26-32`):
```python
grounded_text = reranked[0].get("text", "") if reranked else FALLBACK_MESSAGE
return RagAnswer(
    answer=grounded_text,
    confidence=float(top_score),
    sources=sources,
    fallback_used=False,
)
```

For Phase 3, replace message text with exact locked phrase from context (`"Я не знаю — обратитесь к коллеге."`) but keep deterministic branch structure.

---

### `src/bot/auth.py` (middleware, request-response)

**Analog:** `src/ai/extraction/publish_policy.py`

**Policy gate function style** (`src/ai/extraction/publish_policy.py:14-23`):
```python
def should_publish_knowledge(unit: KnowledgeUnit) -> PublishDecision:
    if unit.confidence < settings.knowledge_confidence_threshold:
        return PublishDecision(
            publish=False,
            reason=(
                f"low_confidence: {unit.confidence:.3f} < "
                f"{settings.knowledge_confidence_threshold:.3f}"
            ),
        )
    return PublishDecision(publish=True, reason="publishable")
```

**Threshold helper style** (`src/ai/extraction/publish_policy.py:26-27`):
```python
def should_answer_for_relevance(score: float) -> bool:
    return score >= settings.rag_relevance_threshold
```

Apply same “small pure function + explicit reason” style for `is_authorized_role(role) -> AuthDecision`.

---

### `src/bot/presenters.py` (utility, transform)

**Analog:** `src/ai/rag/attribution.py`

**Pure mapping function pattern** (`src/ai/rag/attribution.py:6-19`):
```python
def format_attribution(nodes: list[dict]) -> list[AttributionItem]:
    output: list[AttributionItem] = []
    for node in nodes:
        metadata = node.get("metadata", {})
        output.append(
            AttributionItem(
                source_id=metadata.get("source_id", ""),
                excerpt=node.get("text", "")[:240],
                score=float(node.get("score", 0.0)),
                timestamp=metadata.get("timestamp"),
                page=metadata.get("page"),
            )
        )
    return output
```

Use same single-responsibility transform style for message text rendering:
1) main answer block, 2) mandatory `Источники` block, 3) safe truncation.

---

### `src/ai/langgraph/graph.py` (service, event-driven)

**Analog:** `src/tasks/ingest.py`

**Module logger + app-level wiring** (`src/tasks/ingest.py:16-19`):
```python
logger = get_logger(__name__)

celery_app = Celery("vbrain", broker=settings.redis_url, backend=settings.redis_url)
```

**Step-wise orchestration with progress checkpoints** (`src/tasks/ingest.py:24-43`):
```python
self.update_state(state="PROGRESS", meta={"stage": "parsing", "progress": 10})
...
self.update_state(state="PROGRESS", meta={"stage": "indexing", "progress": 80})
embedder = Embedder()
store = QdrantStore(QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port))
store.ensure_collection()
```

**Central failure logging pattern** (`src/tasks/ingest.py:60-63`):
```python
except Exception as exc:
    logger.error("Ingestion failed for source %s: %s", source_id, exc)
    self.update_state(state="FAILURE", meta={"error": str(exc)})
    raise
```

Use equivalent staged graph-node tracing/logging (`auth -> retrieve -> decide -> answer`) with one centralized error log format.

---

### `src/models/feedback_event.py` (model, CRUD)

**Analog:** `src/models/ingest_job.py`

**SQLAlchemy model style** (`src/models/ingest_job.py:3-4,9-21`):
```python
from sqlalchemy import JSON, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

class IngestJob(Base):
    __tablename__ = "ingest_jobs"
    id: Mapped[str] = mapped_column(String, primary_key=True)
    source_id: Mapped[str] = mapped_column(String, index=True)
    ...
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

Follow same declarative style for `feedback_events` table (`thread_id`, `message_id`, `vote`, `answer_confidence`, `created_at`).

---

### `src/core/config.py` (config, transform) — modification pattern

**Analog:** `src/core/config.py` (existing pattern to extend)

**Settings class pattern** (`src/core/config.py:1-8`):
```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )
```

**Typed defaults pattern** (`src/core/config.py:25-37`):
```python
pii_confidence_threshold: float = 0.5
knowledge_confidence_threshold: float = 0.7
rag_relevance_threshold: float = 0.35
rag_similarity_top_k: int = 8
rag_sparse_top_k: int = 12
rag_hybrid_top_k: int = 6
rag_rerank_top_k: int = 5
```

Add Phase 3 flags in same typed/default style (bot token, auth role set, clarify limits, source display max).

---

### `tests/phase3/*.py` (tests) — structure patterns

**Primary analogs:** `tests/api/test_ingest_routes.py`, `tests/phase2/test_contracts_and_policy.py`, `tests/phase2/test_low_relevance_fallback.py`

**Patch-heavy integration test style** (`tests/api/test_ingest_routes.py:10-18,145-153`):
```python
@patch("src.tasks.ingest.parse_telegram_export")
...
@patch("src.api.routes.ingest.ingest_telegram")
def test_upload_telegram_returns_job_id(mock_task, client):
    mock_task.delay.return_value = MagicMock(id="test-job-123")
    response = client.post(
        "/api/ingest/telegram",
        files={"json_file": ("result.json", b'{"messages": []}', "application/json")},
    )
    assert response.status_code == 200
```

**FastAPI client fixture style** (`tests/api/test_ingest_routes.py:138-142`):
```python
@pytest.fixture
def client():
    from src.api.main import app
    return TestClient(app)
```

**Policy-branch assertions** (`tests/phase2/test_low_relevance_fallback.py:6-13`):
```python
result = synthesize_answer("как оформить заказ", candidates=candidates)
assert result.fallback_used is True
assert "Недостаточно данных" in result.answer
assert result.sources
```

**Stable envelope assertions** (`tests/phase2/test_low_relevance_fallback.py:32-40`):
```python
response = client.post("/api/knowledge/query", json={"query": "как оформить заказ"})
assert response.status_code == 200
data = response.json()
assert set(data.keys()) == {"answer", "confidence", "sources", "fallback_used"}
```

**Config override test style** (`tests/phase2/test_contracts_and_policy.py:111-115`):
```python
monkeypatch.setenv("KNOWLEDGE_CONFIDENCE_THRESHOLD", "0.81")
monkeypatch.setenv("RAG_RELEVANCE_THRESHOLD", "0.41")
overridden = Settings()
assert overridden.knowledge_confidence_threshold == 0.81
```

Map to Phase 3 tests:
- `test_graph_fallback.py`: exact fallback phrase + fallback_used branch
- `test_source_block_always_present.py`: mandatory `Источники` block for answer/fallback/deny
- `test_auth_gate.py`: denied user never reaches retrieval call (patch retrieve node and assert not called)
- `test_multiturn_context.py`: same `thread_id` preserves context and enforce single clarify turn
- `test_feedback_capture.py`: callback event persisted with linkage fields

## Shared Patterns

### API route pattern (request/response + validation + error masking)
**Sources:** `src/api/routes/knowledge.py`, `src/api/routes/ingest.py`
```python
@router.post("/query")
async def query_knowledge(payload: KnowledgeQueryRequest):
    try:
        ...
        return {"answer": ..., "confidence": ..., "sources": ..., "fallback_used": ...}
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Knowledge query failed") from exc
```
```python
if not filename.endswith(".pdf"):
    raise HTTPException(status_code=400, detail="Invalid PDF file type")
```

### Config pattern (centralized typed settings)
**Source:** `src/core/config.py`
```python
class Settings(BaseSettings):
    ...
    knowledge_confidence_threshold: float = 0.7
    rag_relevance_threshold: float = 0.35
```

### Task orchestration pattern (stages, retries, logging)
**Sources:** `src/tasks/ingest.py`, `src/tasks/knowledge.py`
```python
@celery_app.task(bind=True, autoretry_for=(Exception,), max_retries=3)
def extract_knowledge_task(...):
    try:
        self.update_state(state="PROGRESS", meta={"stage": "extracting", "progress": 20})
        ...
    except Exception as exc:
        logger.error("Knowledge extraction failed for source %s: %s", source_id, exc)
        self.update_state(state="FAILURE", meta={"error": str(exc)})
        raise
```

### DB/session dependency pattern
**Source:** `src/api/deps.py`
```python
engine = create_engine(settings.database_url, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)

def get_db_session() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### Logging pattern
**Source:** `src/core/logging.py`
```python
def setup_logging(level: str = "INFO"):
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
```

## No Analog Found

| File | Role | Data Flow | Reason |
|---|---|---|---|
| `src/bot/telegram_app.py` (Telegram handlers wiring) | component | event-driven | No existing `python-telegram-bot` handler module in repo; use AI-SPEC entrypoint skeleton + project lifecycle/logging patterns. |
| `src/ai/langgraph/nodes/summarize.py` | service | transform | No existing LangGraph summarization/checkpointer node in codebase; use AI-SPEC + RESEARCH guidance, but keep Pydantic/config/error conventions from repo. |

## Metadata

**Analog search scope:** `src/api`, `src/ai`, `src/tasks`, `src/core`, `src/models`, `tests/api`, `tests/phase2`  
**Files scanned:** 17  
**Pattern extraction date:** 2026-04-18

