# Phase 1: Foundation & Data Ingestion - Pattern Map

**Mapped:** 2026-04-18
**Files analyzed:** 27
**Analogs found:** 0 / 27 (greenfield project -- no existing codebase)

## File Classification

### Infrastructure & Config

| New File | Role | Data Flow | Depends On | Notes |
|----------|------|-----------|------------|-------|
| `pyproject.toml` | config | -- | -- | Project metadata, dependencies, tool config (ruff, pytest) |
| `.env.example` | config | -- | -- | Environment variable template |
| `docker-compose.yml` | config | -- | -- | Qdrant, Redis, PostgreSQL services |
| `Dockerfile` | config | -- | `pyproject.toml` | Python runtime for API + Celery workers |

### Core Utilities (Foundation -- built first)

| New File | Role | Data Flow | Depends On | Notes |
|----------|------|-----------|------------|-------|
| `src/core/__init__.py` | utility | -- | -- | Package init |
| `src/core/config.py` | config | -- | `pydantic-settings` | Centralized settings (env vars, defaults) |
| `src/core/logging.py` | utility | -- | `src/core/config.py` | Structured logging setup |

### Data Models

| New File | Role | Data Flow | Depends On | Notes |
|----------|------|-----------|------------|-------|
| `src/models/__init__.py` | model | -- | -- | Package init |
| `src/models/source.py` | model | CRUD | `sqlalchemy` | Data source metadata (type, filename, status) |
| `src/models/ingest_job.py` | model | CRUD | `sqlalchemy` | Ingestion job status tracking |

### API Layer

| New File | Role | Data Flow | Depends On | Notes |
|----------|------|-----------|------------|-------|
| `src/api/__init__.py` | -- | -- | -- | Package init |
| `src/api/main.py` | route | request-response | `src/core/config.py`, `src/api/routes/ingest.py` | FastAPI app entry, middleware, lifespan |
| `src/api/deps.py` | utility | request-response | `src/core/config.py`, `src/models/` | Dependency injection (DB sessions, services) |
| `src/api/routes/__init__.py` | -- | -- | -- | Package init |
| `src/api/routes/ingest.py` | route | request-response | `src/tasks/ingest.py`, `src/api/deps.py` | POST /telegram, POST /pdf, GET /status/{job_id} |

### Pipeline -- Parsers

| New File | Role | Data Flow | Depends On | Notes |
|----------|------|-----------|------------|-------|
| `src/pipeline/__init__.py` | -- | -- | -- | Package init |
| `src/pipeline/parsers/__init__.py` | -- | -- | -- | Package init |
| `src/pipeline/parsers/telegram.py` | service | file-I/O | `beautifulsoup4` | Telegram JSON export parser (ING-02) |
| `src/pipeline/parsers/pdf.py` | service | file-I/O | `docling` | PDF text extraction to Markdown (ING-05) |
| `src/pipeline/parsers/voice.py` | service | event-driven | `groq` SDK | Groq Whisper transcription (ING-03) |

### Pipeline -- PII Anonymization

| New File | Role | Data Flow | Depends On | Notes |
|----------|------|-----------|------------|-------|
| `src/pipeline/anonymizer/__init__.py` | -- | -- | -- | Package init |
| `src/pipeline/anonymizer/engine.py` | service | transform | `presidio-analyzer`, `presidio-anonymizer`, `spacy` | Analyzer + Anonymizer setup (ING-01) |
| `src/pipeline/anonymizer/recognizers.py` | service | transform | `presidio-analyzer` | Custom Russian PII recognizers (phones, INN, SNILS) |
| `src/pipeline/anonymizer/token_mapping.py` | service | CRUD | -- | PII token <-> original value mapping storage |

### Pipeline -- Filters & Chunking

| New File | Role | Data Flow | Depends On | Notes |
|----------|------|-----------|------------|-------|
| `src/pipeline/filters/__init__.py` | -- | -- | -- | Package init |
| `src/pipeline/filters/noise.py` | service | transform | -- | Telegram noise filter (ING-04) |
| `src/pipeline/filters/grouping.py` | service | transform | -- | Chronological message grouping (D-15) |
| `src/pipeline/chunker/__init__.py` | -- | -- | -- | Package init |
| `src/pipeline/chunker/text_chunker.py` | service | transform | -- | Sentence-based chunking with overlap (D-12) |
| `src/pipeline/chunker/telegram_chunker.py` | service | transform | `src/pipeline/filters/grouping.py`, `src/pipeline/chunker/text_chunker.py` | Chrono-grouped chunking for Telegram (D-15) |

### Pipeline -- Indexing

| New File | Role | Data Flow | Depends On | Notes |
|----------|------|-----------|------------|-------|
| `src/pipeline/indexer/__init__.py` | -- | -- | -- | Package init |
| `src/pipeline/indexer/embedder.py` | service | batch | `fastembed` | Dense (e5-large) + sparse (BM42) embeddings |
| `src/pipeline/indexer/qdrant_store.py` | service | CRUD | `qdrant-client`, `src/pipeline/indexer/embedder.py` | Collection management, upsert, hybrid search |

### Celery Tasks

| New File | Role | Data Flow | Depends On | Notes |
|----------|------|-----------|------------|-------|
| `src/tasks/__init__.py` | -- | -- | -- | Package init |
| `src/tasks/ingest.py` | service | event-driven | All pipeline modules, `celery` | Task chain orchestration + progress tracking (ING-06) |

### Tests

| New File | Role | Data Flow | Depends On | Notes |
|----------|------|-----------|------------|-------|
| `tests/__init__.py` | test | -- | -- | Package init |
| `tests/conftest.py` | test | -- | All pipeline modules | Shared fixtures (sample data, mock clients) |
| `tests/pipeline/__init__.py` | test | -- | -- | Package init |
| `tests/pipeline/test_telegram_parser.py` | test | -- | `src/pipeline/parsers/telegram.py` | ING-02 |
| `tests/pipeline/test_pdf_parser.py` | test | -- | `src/pipeline/parsers/pdf.py` | ING-05 |
| `tests/pipeline/test_anonymizer.py` | test | -- | `src/pipeline/anonymizer/` | ING-01 |
| `tests/pipeline/test_noise_filter.py` | test | -- | `src/pipeline/filters/noise.py` | ING-04 |
| `tests/pipeline/test_voice.py` | test | -- | `src/pipeline/parsers/voice.py` | ING-03 |
| `tests/pipeline/test_chunker.py` | test | -- | `src/pipeline/chunker/` | D-12, D-14 |
| `tests/pipeline/test_qdrant_indexer.py` | test | -- | `src/pipeline/indexer/` | Indexing verification |
| `tests/api/__init__.py` | test | -- | -- | Package init |
| `tests/api/test_ingest_routes.py` | test | request-response | `src/api/routes/ingest.py` | ING-06 |

## Pattern Assignments

> **Greenfield project:** No existing codebase to extract patterns from. All patterns below come from RESEARCH.md code examples and established library conventions. The planner should treat each file's "Reference Pattern" as the canonical template.

---

### `src/core/config.py` (config, --)

**Reference Pattern:** pydantic-settings BaseSettings

```python
# Canonical pattern from RESEARCH.md + CLAUDE.md stack
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    # Application
    app_name: str = "V-Brain"
    debug: bool = False

    # Qdrant
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333

    # Redis (Celery broker)
    redis_url: str = "redis://localhost:6379/0"

    # PostgreSQL
    database_url: str = "postgresql+psycopg2://vbrain:vbrain@localhost:5432/vbrain"

    # Groq (Whisper API)
    groq_api_key: str = ""

    # Embeddings
    dense_model_name: str = "intfloat/multilingual-e5-large"
    sparse_model_name: str = "Qdrant/bm42-all-MiniLM-L6-v2-quantized"

    # PII
    pii_confidence_threshold: float = 0.5

    # File storage
    upload_dir: str = "./data/uploads"
    max_file_size_mb: int = 100

    # Telegram grouping window (minutes)
    telegram_grouping_window_minutes: int = 30


settings = Settings()
```

**Why this pattern:** pydantic-settings is the standard for FastAPI projects. Single `settings` instance imported throughout the codebase. All configurable values in one place.

---

### `src/api/main.py` (route, request-response)

**Reference Pattern:** FastAPI app factory with lifespan

```python
# Canonical pattern from RESEARCH.md Pattern 1 (Celery + FastAPI)
from contextlib import asynccontextmanager
from fastapi import FastAPI
from src.api.routes.ingest import router as ingest_router
from src.core.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: init logging, verify connections
    setup_logging()
    yield
    # Shutdown: cleanup


app = FastAPI(
    title="V-Brain API",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(ingest_router)
```

**Why this pattern:** FastAPI lifespan context manager is the modern pattern for startup/shutdown logic. Router inclusion keeps the app clean.

---

### `src/api/routes/ingest.py` (route, request-response)

**Reference Pattern:** RESEARCH.md Pattern 1 (Celery + FastAPI async ingest)

```python
# Canonical pattern from RESEARCH.md Code Examples
from fastapi import APIRouter, UploadFile, File, HTTPException
from celery.result import AsyncResult
from src.tasks.ingest import ingest_telegram, ingest_pdf

router = APIRouter(prefix="/api/ingest", tags=["ingestion"])


@router.post("/telegram")
async def upload_telegram(
    json_file: UploadFile = File(...),
    voice_files: list[UploadFile] = File(default=[]),
):
    # Validate file type, save to disk, create source record
    # Launch async Celery task
    task = ingest_telegram.delay(source_id, json_file_path, voice_dir)
    return {"job_id": task.id, "status": "started"}


@router.post("/pdf")
async def upload_pdf(file: UploadFile = File(...)):
    # Validate file type (.pdf), save to disk
    task = ingest_pdf.delay(source_id, file_path)
    return {"job_id": task.id, "status": "started"}


@router.get("/status/{job_id}")
async def get_status(job_id: str):
    result = AsyncResult(job_id)
    if result.state == "PROGRESS":
        return {"status": "processing", **result.info}
    elif result.state == "SUCCESS":
        return {"status": "completed", **result.result}
    elif result.state == "FAILURE":
        return {"status": "failed", "error": str(result.result)}
    else:
        return {"status": result.state}
```

**Why this pattern:** API never runs pipeline synchronously -- always returns task_id immediately (RESEARCH.md Anti-Pattern 5). File type validation per security requirements.

---

### `src/tasks/ingest.py` (service, event-driven)

**Reference Pattern:** RESEARCH.md Pattern 1 (Celery Task Chain + Progress)

```python
# Canonical pattern from RESEARCH.md Code Examples
from celery import Celery

app = Celery("vbrain", broker="redis://localhost:6379/0", backend="redis://localhost:6379/1")


@app.task(bind=True)
def ingest_telegram(self, source_id: str, json_path: str, voice_dir: str):
    # Stage 1: Parse
    self.update_state(state="PROGRESS", meta={"stage": "parsing", "progress": 10})
    messages = parse_telegram_export(json_path)

    # Stage 2: Transcribe voice messages
    self.update_state(state="PROGRESS", meta={"stage": "transcribing", "progress": 20})
    messages = transcribe_voice_messages(messages, voice_dir)

    # Stage 3: PII Anonymization (BEFORE any other processing -- D-07)
    self.update_state(state="PROGRESS", meta={"stage": "anonymizing", "progress": 35})
    messages = anonymize_messages(messages)

    # Stage 4: Noise filtering
    self.update_state(state="PROGRESS", meta={"stage": "filtering", "progress": 50})
    messages = filter_noise(messages)

    # Stage 5: Chronological grouping
    self.update_state(state="PROGRESS", meta={"stage": "grouping", "progress": 55})
    groups = group_messages_chronologically(messages)

    # Stage 6: Chunking
    self.update_state(state="PROGRESS", meta={"stage": "chunking", "progress": 65})
    chunks = chunk_messages(groups)

    # Stage 7: Embedding + Indexing
    self.update_state(state="PROGRESS", meta={"stage": "indexing", "progress": 80})
    index_chunks(chunks)

    return {"status": "completed", "messages_processed": len(messages), "chunks_indexed": len(chunks)}


@app.task(bind=True)
def ingest_pdf(self, source_id: str, file_path: str):
    # Stage 1: Parse PDF
    self.update_state(state="PROGRESS", meta={"stage": "parsing", "progress": 15})
    markdown = extract_pdf_text(file_path)

    # Stage 2: PII Anonymization
    self.update_state(state="PROGRESS", meta={"stage": "anonymizing", "progress": 30})
    markdown = anonymize_text(markdown)

    # Stage 3: Chunking (Markdown-aware per D-14)
    self.update_state(state="PROGRESS", meta={"stage": "chunking", "progress": 50})
    chunks = chunk_markdown(markdown)

    # Stage 4: Embedding + Indexing
    self.update_state(state="PROGRESS", meta={"stage": "indexing", "progress": 75})
    index_chunks(chunks)

    return {"status": "completed", "chunks_indexed": len(chunks)}
```

**Why this pattern:** Each stage independently trackable. PII is ALWAYS stage after parsing (D-07). Progress tracking via `self.update_state`. Note: PDF pipeline skips voice/noise/grouping stages.

---

### `src/pipeline/parsers/telegram.py` (service, file-I/O)

**Reference Pattern:** RESEARCH.md Pattern 4 (Telegram JSON Export Parser)

```python
# Canonical pattern from RESEARCH.md Code Examples
import json
from bs4 import BeautifulSoup
from dataclasses import dataclass
from typing import Optional


@dataclass
class TelegramMessage:
    id: int
    date: str
    author: str
    author_id: str
    text: str
    is_service: bool
    is_bot: bool
    media_type: Optional[str]
    voice_path: Optional[str]
    edit_date: Optional[str] = None


def parse_text_field(text_field) -> str:
    """Handle both string and rich-text array formats (Pitfall 2)."""
    if isinstance(text_field, str):
        return text_field
    if isinstance(text_field, list):
        parts = []
        for item in text_field:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                parts.append(item.get("text", ""))
        return "".join(parts)
    return ""


def parse_telegram_export(filepath: str) -> list[TelegramMessage]:
    """Parse Telegram Desktop result.json export."""
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    messages = []
    for msg in data.get("messages", []):
        msg_type = msg.get("type", "")
        if msg_type == "service":
            continue  # D-09: Skip service messages

        text = parse_text_field(msg.get("text", ""))
        if not text and msg.get("media_type") != "voice_message":
            continue  # Skip empty non-voice messages

        messages.append(TelegramMessage(
            id=msg["id"],
            date=msg.get("date", ""),
            author=msg.get("from", ""),
            author_id=msg.get("from_id", ""),
            text=BeautifulSoup(text, "html.parser").get_text(),
            is_service=msg_type == "service",
            is_bot="bot" in msg.get("from_id", "").lower(),
            media_type=msg.get("media_type"),
            voice_path=msg.get("file_name") if msg.get("media_type") == "voice_message" else None,
            edit_date=msg.get("edit_date"),
        ))
    return messages
```

**Key concerns:** Pitfall 2 -- `text` field can be string OR array. Handle both. Pitfall -- `edit_date` for edited messages (keep latest version). D-17 -- voice_path links to .ogg files.

---

### `src/pipeline/parsers/pdf.py` (service, file-I/O)

**Reference Pattern:** RESEARCH.md Pattern 5 (Docling PDF Parsing)

```python
# Canonical pattern from RESEARCH.md Code Examples
from docling.document_converter import DocumentConverter


def extract_pdf_text(filepath: str) -> str:
    """Extract text from PDF with Cyrillic support via Docling."""
    converter = DocumentConverter()
    result = converter.convert(filepath)
    markdown = result.document.export_to_markdown()
    return markdown
```

**Key concerns:** Docling natively supports Cyrillic (Assumption A5). Returns Markdown for D-14-aware chunking.

---

### `src/pipeline/parsers/voice.py` (service, event-driven)

**Reference Pattern:** Groq Whisper API SDK

```python
# Pattern based on groq SDK 1.2.0 + RESEARCH.md Pitfall 4
from groq import Groq


def transcribe_audio(client: Groq, file_path: str) -> str:
    """Transcribe .ogg voice message via Groq Whisper API."""
    with open(file_path, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            model="whisper-large-v3-turbo",
            file=audio_file,
            response_format="text",
            language="ru",
        )
    return transcription.text
```

**Key concerns:** Pitfall 4 -- file size limit (25MB). Must check size before sending. .ogg natively supported.

---

### `src/pipeline/anonymizer/engine.py` (service, transform)

**Reference Pattern:** RESEARCH.md Pattern 2 (Presidio Setup + Custom Recognizers)

```python
# Canonical pattern from RESEARCH.md Code Examples
from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine, OperatorConfig
from src.pipeline.anonymizer.recognizers import (
    RussianPhoneRecognizer,
    RussianINNRecognizer,
    RussianSNILSRecognizer,
)


def create_analyzer():
    """Create Presidio analyzer with spaCy Russian NER + custom recognizers."""
    configuration = {
        "nlp_engine_name": "spacy",
        "models": [{"lang_code": "ru", "model_name": "ru_core_news_md"}],
    }
    provider = NlpEngineProvider(nlp_configuration=configuration)
    nlp_engine = provider.create_engine()

    registry = RecognizerRegistry()
    registry.load_predefined_recognizers(languages=["en", "ru"])

    # Add custom Russian recognizers
    registry.add_recognizer(RussianPhoneRecognizer())
    registry.add_recognizer(RussianINNRecognizer())
    registry.add_recognizer(RussianSNILSRecognizer())

    return AnalyzerEngine(
        registry=registry,
        nlp_engine=nlp_engine,
        supported_languages=["ru", "en"],
    )


def create_anonymizer():
    """Create Presidio anonymizer with D-05 token format."""
    return AnonymizerEngine()


# Token format per D-05: <PERSON_1>, <PHONE_1>, etc.
ANONYMIZATION_OPERATORS = {
    "PERSON": OperatorConfig("replace", {"new_value": "<PERSON_>"}),
    "PHONE_NUMBER": OperatorConfig("replace", {"new_value": "<PHONE_>"}),
    "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": "<EMAIL_>"}),
    "LOCATION": OperatorConfig("replace", {"new_value": "<ADDRESS_>"}),
    "RUSSIAN_INN": OperatorConfig("replace", {"new_value": "<DOC_>"}),
    "RUSSIAN_SNILS": OperatorConfig("replace", {"new_value": "<DOC_>"}),
}
```

**Key concerns:** D-07 -- PII BEFORE any processing. Pitfall 3 -- Russian NER misses oblique cases; complementary custom regex needed. spaCy `ru_core_news_md` must be downloaded.

---

### `src/pipeline/anonymizer/recognizers.py` (service, transform)

**Reference Pattern:** RESEARCH.md Pattern 2 (Custom Russian Recognizers)

```python
# Canonical pattern from RESEARCH.md Code Examples
from presidio_analyzer import Pattern, PatternRecognizer


class RussianPhoneRecognizer(PatternRecognizer):
    """Russian phone: +7(XXX)XXX-XX-XX, 8XXXXXXXXXX, +7XXXXXXXXXX."""

    PATTERNS = [
        Pattern(
            name="russian_phone_intl",
            regex=r"(?:\+7|8)[\s\-\(]*\d{3}[\s\-\)]*\d{3}[\s\-]*\d{2}[\s\-]*\d{2}",
            score=0.7,
        ),
        Pattern(
            name="russian_phone_short",
            regex=r"\b\d{10}\b",
            score=0.3,
        ),
    ]

    def __init__(self):
        super().__init__(
            supported_entity="PHONE_NUMBER",
            patterns=self.PATTERNS,
            supported_language="ru",
        )


class RussianINNRecognizer(PatternRecognizer):
    """INN: 10 digits (individual) or 12 digits (legal entity)."""

    def __init__(self):
        super().__init__(
            supported_entity="RUSSIAN_INN",
            patterns=[
                Pattern(
                    name="russian_inn",
                    regex=r"\b\d{10}\b|\b\d{12}\b",
                    score=0.4,  # Low score -- many 10/12 digit numbers are not INN
                ),
            ],
            supported_language="ru",
        )


class RussianSNILSRecognizer(PatternRecognizer):
    """SNILS: XXX-XXX-XXX YY (11 digits with optional dashes/space)."""

    def __init__(self):
        super().__init__(
            supported_entity="RUSSIAN_SNILS",
            patterns=[
                Pattern(
                    name="russian_snils",
                    regex=r"\b\d{3}[\-\s]?\d{3}[\-\s]?\d{3}[\-\s]?\d{2}\b",
                    score=0.6,
                ),
            ],
            supported_language="ru",
        )
```

**Key concerns:** Confidence scores matter -- low scores for ambiguous patterns to avoid false positives. Tradeoff between recall and precision (Claude's Discretion).

---

### `src/pipeline/anonymizer/token_mapping.py` (service, CRUD)

**Reference Pattern:** Reversible PII token mapping

```python
# Pattern for D-05 token format with sequential numbering
# <PERSON_1>, <PERSON_2>, <PHONE_1>, etc.
from collections import defaultdict


class TokenMapper:
    """Maps PII tokens (<PERSON_1>) back to original values for admin review."""

    def __init__(self):
        self._mappings: dict[str, dict[str, str]] = defaultdict(dict)
        self._counters: dict[str, int] = defaultdict(int)

    def get_or_create_token(self, entity_type: str, original_value: str) -> str:
        """Return existing token or create new one for this original value."""
        for token, value in self._mappings[entity_type].items():
            if value == original_value:
                return token

        self._counters[entity_type] += 1
        token = f"<{entity_type}_{self._counters[entity_type]}>"
        self._mappings[entity_type][token] = original_value
        return token

    def resolve(self, token: str) -> str | None:
        """Resolve token back to original value."""
        # Parse <ENTITY_TYPE_N> format
        for entity_type, mappings in self._mappings.items():
            if token in mappings:
                return mappings[token]
        return None

    def get_all_mappings(self) -> dict[str, dict[str, str]]:
        """Return all mappings (for persistence)."""
        return dict(self._mappings)
```

**Key concerns:** Security -- PII mapping stored unencrypted is a risk (RESEARCH.md Security Domain). Consider encryption at rest. Never log raw PII.

---

### `src/pipeline/filters/noise.py` (service, transform)

**Reference Pattern:** Rule-based noise filter per D-09/D-10

```python
# Pattern based on D-09 (filter) + D-10 (keep short messages)
import re

# Service message types to skip (D-09)
SERVICE_MESSAGE_TYPES = {"service"}

# Bot message pattern
BOT_AUTHOR_PATTERN = re.compile(r"bot", re.IGNORECASE)

# Noise patterns -- greetings, confirmations (D-09)
NOISE_PATTERNS = [
    re.compile(r"^\s*$"),                     # Empty
    re.compile(r"^[.\-]+$", re.IGNORECASE),   # Dots/dashes only
    re.compile(r"^[+\-]$", re.IGNORECASE),    # Single + or -
]

# Stop words -- NOT a length filter (D-10: short messages may be valuable)
NOISE_EXACT = {"ok", "oki", "ok!", "ok.", "spasibo", "thanks", "thx"}


def is_noise(message_text: str, is_service: bool, is_bot: bool, author: str) -> bool:
    """Return True if message should be filtered out."""
    if is_service:
        return True
    if is_bot:
        return True

    stripped = message_text.strip().lower()
    if stripped in NOISE_EXACT:
        return True
    for pattern in NOISE_PATTERNS:
        if pattern.match(stripped):
            return True

    return False
```

**Key concerns:** D-10 explicitly says short messages are NOT filtered -- "звони Ивану" is valuable. Claude's Discretion on exact noise threshold.

---

### `src/pipeline/filters/grouping.py` (service, transform)

**Reference Pattern:** Chronological message grouping per D-15

```python
# Pattern for D-15: group messages by time window before chunking
from datetime import datetime, timedelta


def group_messages_chronologically(
    messages: list,
    window_minutes: int = 30,
) -> list[list]:
    """Group messages into conversation windows by time gap.

    Messages within `window_minutes` of each other are grouped together.
    A gap > window_minutes starts a new group.
    """
    if not messages:
        return []

    groups = []
    current_group = [messages[0]]
    prev_time = _parse_date(messages[0].date)

    for msg in messages[1:]:
        msg_time = _parse_date(msg.date)
        if (msg_time - prev_time) > timedelta(minutes=window_minutes):
            groups.append(current_group)
            current_group = [msg]
        else:
            current_group.append(msg)
        prev_time = msg_time

    if current_group:
        groups.append(current_group)

    return groups


def _parse_date(date_str: str) -> datetime:
    """Parse Telegram date string to datetime."""
    # Telegram export format: "2024-01-15T14:30:00" or similar ISO-like
    return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
```

**Key concerns:** Claude's Discretion on window size (30 min default from D-15, adjustable via config).

---

### `src/pipeline/chunker/text_chunker.py` (service, transform)

**Reference Pattern:** Sentence-based chunking per D-12/D-14

```python
# Pattern for D-12 (5-10 sentences, 300-500 tokens, 1 sentence overlap)
# D-14: Markdown-aware -- respect headings and paragraphs
import re

# Approximate token count (Russian: ~1 token per 3.5 characters)
CHARS_PER_TOKEN = 3.5
TARGET_TOKENS = 400  # ~300-500 range midpoint
MAX_TOKENS = 500
MIN_TOKENS = 300


def chunk_text(text: str, overlap_sentences: int = 1) -> list[str]:
    """Split text into chunks by sentence boundaries with overlap.

    For Markdown: split on heading boundaries first, then chunk paragraphs.
    """
    paragraphs = _split_markdown_paragraphs(text)
    sentences = _split_into_sentences(paragraphs)

    chunks = []
    i = 0
    while i < len(sentences):
        chunk_sentences = []
        char_count = 0

        while i < len(sentences):
            s = sentences[i]
            if char_count + len(s) > MAX_TOKENS * CHARS_PER_TOKEN and chunk_sentences:
                break
            chunk_sentences.append(s)
            char_count += len(s)
            i += 1

        if chunk_sentences:
            chunks.append(" ".join(chunk_sentences))

        # Overlap: go back N sentences for next chunk
        if i < len(sentences):
            i = max(i - overlap_sentences, i - len(chunk_sentences) + 1)

    return chunks


def _split_markdown_paragraphs(text: str) -> list[str]:
    """Split Markdown text on heading boundaries."""
    return re.split(r"\n(?=#{1,3}\s)", text)


def _split_into_sentences(paragraphs: list[str]) -> list[str]:
    """Split paragraphs into sentences. Simple Russian-aware splitter."""
    sentences = []
    for p in paragraphs:
        # Split on sentence-ending punctuation followed by space or end
        parts = re.split(r"(?<=[.!?])\s+", p.strip())
        sentences.extend(s.strip() for s in parts if s.strip())
    return sentences
```

**Key concerns:** Pitfall from PITFALLS.md -- do NOT use `nltk.sent_tokenize` for Russian (English-optimized). Use simple regex or `razdel` library. RESEARCH.md explicitly lists this as deprecated.

---

### `src/pipeline/chunker/telegram_chunker.py` (service, transform)

**Reference Pattern:** Combines grouping + chunking for Telegram

```python
# Pattern: chronological grouping (D-15) + sentence chunking (D-12)
from src.pipeline.filters.grouping import group_messages_chronologically
from src.pipeline.chunker.text_chunker import chunk_text


def chunk_telegram_messages(
    messages: list,
    window_minutes: int = 30,
) -> list[dict]:
    """Group messages chronologically, then chunk each group.

    Returns list of dicts with chunk text + metadata (D-13).
    """
    groups = group_messages_chronologically(messages, window_minutes)

    chunks = []
    for group in groups:
        # Concatenate group text with author prefixes
        group_text = "\n".join(
            f"[{m.author}]: {m.text}" for m in group if m.text
        )

        # Metadata for all chunks in this group
        metadata = {
            "source_type": "telegram",
            "date_range": f"{group[0].date} - {group[-1].date}",
            "authors": list({m.author for m in group}),
            "chat": group[0].author,  # or chat name if available
        }

        text_chunks = chunk_text(group_text)
        for idx, chunk_text in enumerate(text_chunks):
            chunks.append({
                "text": chunk_text,
                "metadata": {**metadata, "chunk_index": idx},
            })

    return chunks
```

**Key concerns:** D-13 -- each chunk carries metadata (date, author, source, type). Metadata is critical for source attribution (KNW-04 in later phases).

---

### `src/pipeline/indexer/embedder.py` (service, batch)

**Reference Pattern:** RESEARCH.md Pattern 3 (FastEmbed dense + sparse)

```python
# Canonical pattern from RESEARCH.md Code Examples (Qdrant hybrid setup)
from fastembed import TextEmbedding, SparseTextEmbedding


class Embedder:
    """Manages dense + sparse embedding generation."""

    def __init__(
        self,
        dense_model: str = "intfloat/multilingual-e5-large",
        sparse_model: str = "Qdrant/bm42-all-MiniLM-L6-v2-quantized",
    ):
        self._dense = TextEmbedding(model_name=dense_model)
        self._sparse = SparseTextEmbedding(model_name=sparse_model)

    def embed_batch(self, texts: list[str]) -> tuple[list[list[float]], list]:
        """Generate dense and sparse embeddings for a batch of texts.

        Returns:
            (dense_vectors, sparse_vectors)
            sparse_vectors are objects with .indices and .values attributes
        """
        dense_vectors = list(self._dense.embed(texts, batch_size=32))
        sparse_vectors = list(self._sparse.embed(texts))
        return dense_vectors, sparse_vectors
```

**Key concerns:** Assumption A1 -- BM42 multilingual support for Russian. Need to benchmark on real data. Fallback: Qdrant-native BM25.

---

### `src/pipeline/indexer/qdrant_store.py` (service, CRUD)

**Reference Pattern:** RESEARCH.md Pattern 3 (Qdrant Hybrid Search Setup)

```python
# Canonical pattern from RESEARCH.md Code Examples
from qdrant_client import QdrantClient, models
from qdrant_client.models import SparseVectorParams


class QdrantStore:
    """Manages Qdrant collection and upsert/query operations."""

    COLLECTION_NAME = "knowledge"

    def __init__(self, client: QdrantClient):
        self.client = client

    def ensure_collection(self, dense_size: int = 1024):
        """Create collection with dense + sparse vectors if not exists."""
        if not self.client.collection_exists(self.COLLECTION_NAME):
            self.client.create_collection(
                collection_name=self.COLLECTION_NAME,
                vectors_config={
                    "dense": models.VectorParams(
                        size=dense_size,  # multilingual-e5-large = 1024
                        distance=models.Distance.COSINE,
                        hnsw_config=models.HnswConfigDiff(m=16, ef_construct=100),
                    ),
                },
                sparse_vectors_config={
                    "sparse": SparseVectorParams(
                        index=models.SparseIndexParams(on_init=False),
                    ),
                },
            )

    def upsert_chunks(self, chunks: list[dict]) -> int:
        """Upsert chunks with dense + sparse vectors and payload metadata.

        Each chunk dict must have: text, dense_vector, sparse_vector, metadata.
        Returns count of points upserted.
        """
        points = []
        for i, chunk in enumerate(chunks):
            points.append(
                models.PointStruct(
                    id=chunk["id"],  # Composite: source_type:source_id:chunk_idx
                    vector={
                        "dense": chunk["dense_vector"],
                        "sparse": models.SparseVector(
                            indices=chunk["sparse_vector"].indices,
                            values=chunk["sparse_vector"].values,
                        ),
                    },
                    payload={
                        "text": chunk["text"],
                        **chunk["metadata"],
                    },
                )
            )
        self.client.upsert(self.COLLECTION_NAME, points=points)
        return len(points)

    def delete_by_source(self, source_id: str):
        """Delete all points for a source before re-ingest (Pitfall 5)."""
        self.client.delete(
            self.COLLECTION_NAME,
            models.Filter(
                must=[
                    models.FieldCondition(
                        key="source_id",
                        match=models.MatchValue(value=source_id),
                    )
                ]
            ),
        )
```

**Key concerns:** Pitfall 5 -- ID conflicts on re-ingest. Strategy: delete old source points before upsert. ID format: `{source_type}:{source_id}:{chunk_index}`.

---

### `src/models/source.py` (model, CRUD)

**Reference Pattern:** SQLAlchemy 2.0 model

```python
# Standard SQLAlchemy 2.0 model pattern for FastAPI
from datetime import datetime
from sqlalchemy import String, DateTime, Enum
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
import enum


class Base(DeclarativeBase):
    pass


class SourceType(str, enum.Enum):
    TELEGRAM = "telegram"
    PDF = "pdf"


class IngestStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    type: Mapped[SourceType] = mapped_column(Enum(SourceType))
    filename: Mapped[str] = mapped_column(String)
    file_path: Mapped[str] = mapped_column(String)
    status: Mapped[IngestStatus] = mapped_column(
        Enum(IngestStatus), default=IngestStatus.PENDING
    )
    messages_count: Mapped[int | None] = mapped_column(default=None)
    chunks_indexed: Mapped[int | None] = mapped_column(default=None)
    error_message: Mapped[str | None] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
```

---

### `src/models/ingest_job.py` (model, CRUD)

**Reference Pattern:** SQLAlchemy 2.0 model

```python
# Standard model for Celery task tracking
from datetime import datetime
from sqlalchemy import String, DateTime, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from src.models.source import Base


class IngestJob(Base):
    __tablename__ = "ingest_jobs"

    id: Mapped[str] = mapped_column(String, primary_key=True)  # Celery task_id
    source_id: Mapped[str] = mapped_column(String, index=True)
    celery_task_id: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="PENDING")
    current_stage: Mapped[str | None] = mapped_column(default=None)
    progress: Mapped[int] = mapped_column(default=0)
    result: Mapped[dict | None] = mapped_column(JSON, default=None)
    error: Mapped[str | None] = mapped_column(Text, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
```

---

### `tests/conftest.py` (test, --)

**Reference Pattern:** pytest shared fixtures

```python
# Pattern: shared fixtures for all pipeline tests
import json
import pytest
from unittest.mock import MagicMock


@pytest.fixture
def sample_telegram_messages():
    """Sample Telegram JSON export data for parser tests."""
    return [
        {
            "id": 1,
            "type": "message",
            "date": "2024-01-15T10:00:00",
            "from": "Иван Иванов",
            "from_id": "user123",
            "text": "Позвони Александру по номеру +7(903)123-45-67",
        },
        {
            "id": 2,
            "type": "service",
            "date": "2024-01-15T10:01:00",
            "from": "Иван Иванов",
            "from_id": "user123",
            "text": "Иван Иванов joined the group",
        },
        {
            "id": 3,
            "type": "message",
            "date": "2024-01-15T10:05:00",
            "from": "SomeBot",
            "from_id": "bot456",
            "text": "Reminder: meeting at 15:00",
        },
    ]


@pytest.fixture
def sample_telegram_json(tmp_path, sample_telegram_messages):
    """Create a temporary result.json file."""
    data = {"name": "Test Chat", "messages": sample_telegram_messages}
    path = tmp_path / "result.json"
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return str(path)


@pytest.fixture
def sample_pii_text():
    """Russian text with various PII types for anonymizer tests."""
    return (
        "Позвони Иванову Ивану Ивановичу по номеру +7(903)123-45-67, "
        "его email ivan@company.ru. ИНН: 7707083893."
    )


@pytest.fixture
def mock_qdrant_client():
    """Mock Qdrant client for indexer tests."""
    client = MagicMock()
    client.collection_exists.return_value = True
    return client


@pytest.fixture
def mock_groq_client():
    """Mock Groq client for voice transcription tests."""
    client = MagicMock()
    mock_result = MagicMock()
    mock_result.text = "Транскрибированный текст голосового сообщения"
    client.audio.transcriptions.create.return_value = mock_result
    return client
```

---

### `src/core/logging.py` (utility, --)

**Reference Pattern:** Python stdlib structured logging

```python
# Standard logging setup for FastAPI + Celery
import logging
import sys


def setup_logging(level: str = "INFO"):
    """Configure structured logging for the application."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    # Suppress noisy libraries in production
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("celery").setLevel(logging.INFO)
    logging.getLogger("presidio").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
```

---

## Shared Patterns

### 1. PII-First Pipeline (Critical Architectural Constraint)

**Apply to:** `src/tasks/ingest.py`, all pipeline consumers
**Source:** CONTEXT.md D-07, RESEARCH.md Anti-Pattern 4

PII anonymization MUST happen immediately after parsing and BEFORE any other processing (filtering, chunking, embedding). This is non-negotiable.

```python
# WRONG -- PII after processing (Anti-Pattern 4)
messages = filter_noise(messages)
messages = anonymize_messages(messages)  # TOO LATE

# CORRECT -- PII immediately after parse (D-07)
messages = parse_telegram_export(filepath)
messages = anonymize_messages(messages)  # FIRST
messages = filter_noise(messages)
```

### 2. Async-Only API Endpoints (Non-Blocking)

**Apply to:** `src/api/routes/ingest.py`, all future API routes
**Source:** RESEARCH.md Anti-Pattern 5

API endpoints never run pipeline synchronously. Always dispatch to Celery and return task_id immediately.

```python
# WRONG -- synchronous pipeline in endpoint
@router.post("/telegram")
async def upload(file: UploadFile):
    result = run_full_pipeline(file)  # BLOCKS for minutes!
    return result

# CORRECT -- always async via Celery
@router.post("/telegram")
async def upload(file: UploadFile):
    task = ingest_telegram.delay(source_id, path)
    return {"job_id": task.id, "status": "started"}
```

### 3. Telegram JSON text field: String OR Array

**Apply to:** `src/pipeline/parsers/telegram.py`, any code consuming Telegram text
**Source:** RESEARCH.md Pitfall 2

Telegram export `text` field can be a plain string OR a list of rich-text objects. Always check type.

### 4. Composite IDs for Qdrant (Re-ingest Safety)

**Apply to:** `src/pipeline/indexer/qdrant_store.py`, all indexing code
**Source:** RESEARCH.md Pitfall 5

Use `{source_type}:{source_id}:{chunk_index}` for stable, conflict-free IDs. Delete all points for a source before re-ingest.

### 5. File Upload Security

**Apply to:** `src/api/routes/ingest.py`
**Source:** RESEARCH.md Security Domain

- Validate file type (magic bytes, not just extension)
- Limit file size (100MB per CLAUDE.md)
- Use UUID for filenames (never user-supplied paths)
- Save to isolated directory

### 6. Error Handling in Celery Tasks

**Apply to:** `src/tasks/ingest.py`
**Source:** RESEARCH.md Pattern 1

```python
@app.task(bind=True, autoretry_for=(Exception,), max_retries=3)
def ingest_telegram(self, source_id: str, json_path: str, voice_dir: str):
    try:
        # ... pipeline stages ...
    except Exception as exc:
        self.update_state(
            state="FAILURE",
            meta={"error": str(exc), "stage": "unknown"},
        )
        raise
```

## No Analog Found

All files are greenfield -- no existing codebase to compare against. All patterns sourced from RESEARCH.md code examples, library documentation (Context7 citations), and established conventions for the tech stack.

## Inter-File Dependency Graph

```
Layer 0 (no dependencies):
  pyproject.toml, .env.example, docker-compose.yml, Dockerfile

Layer 1 (foundation):
  src/core/config.py          -- depends on: pydantic-settings
  src/core/logging.py         -- depends on: src/core/config.py

Layer 2 (data models):
  src/models/source.py        -- depends on: sqlalchemy
  src/models/ingest_job.py    -- depends on: src/models/source.py (shared Base)

Layer 3 (pipeline components -- no inter-dependencies):
  src/pipeline/parsers/telegram.py     -- depends on: beautifulsoup4, json
  src/pipeline/parsers/pdf.py          -- depends on: docling
  src/pipeline/parsers/voice.py        -- depends on: groq SDK
  src/pipeline/filters/noise.py        -- depends on: nothing
  src/pipeline/filters/grouping.py     -- depends on: nothing
  src/pipeline/anonymizer/recognizers.py -- depends on: presidio-analyzer
  src/pipeline/anonymizer/engine.py    -- depends on: recognizers.py, presidio
  src/pipeline/anonymizer/token_mapping.py -- depends on: nothing
  src/pipeline/chunker/text_chunker.py -- depends on: nothing
  src/pipeline/indexer/embedder.py     -- depends on: fastembed
  src/pipeline/indexer/qdrant_store.py -- depends on: qdrant-client

Layer 4 (composite pipeline components):
  src/pipeline/chunker/telegram_chunker.py -- depends on: grouping.py, text_chunker.py

Layer 5 (API + tasks -- orchestration):
  src/api/deps.py              -- depends on: config, models
  src/api/routes/ingest.py     -- depends on: tasks/ingest.py, deps.py
  src/api/main.py              -- depends on: routes/ingest.py, logging
  src/tasks/ingest.py          -- depends on: ALL pipeline components

Layer 6 (tests):
  tests/conftest.py            -- depends on: all pipeline modules (mock fixtures)
  tests/pipeline/test_*.py     -- depends on: corresponding pipeline module
  tests/api/test_ingest_routes.py -- depends on: api/routes/ingest.py
```

## Build Order Recommendation

For the planner, files should be created in dependency order. Group into waves:

| Wave | Files | Rationale |
|------|-------|-----------|
| Wave 0: Infrastructure | `pyproject.toml`, `.env.example`, `docker-compose.yml`, `Dockerfile` | Must exist before any code runs |
| Wave 1: Foundation | `src/core/config.py`, `src/core/logging.py`, `src/models/source.py`, `src/models/ingest_job.py` | All other modules depend on these |
| Wave 2: Parsers | `src/pipeline/parsers/telegram.py`, `src/pipeline/parsers/pdf.py`, `src/pipeline/parsers/voice.py` | Can be built/tested independently |
| Wave 3: PII | `src/pipeline/anonymizer/recognizers.py`, `src/pipeline/anonymizer/engine.py`, `src/pipeline/anonymizer/token_mapping.py` | Critical path -- D-07 requires PII before anything else |
| Wave 4: Filters & Chunking | `src/pipeline/filters/noise.py`, `src/pipeline/filters/grouping.py`, `src/pipeline/chunker/text_chunker.py`, `src/pipeline/chunker/telegram_chunker.py` | Transform pipeline |
| Wave 5: Indexing | `src/pipeline/indexer/embedder.py`, `src/pipeline/indexer/qdrant_store.py` | Requires Qdrant running (Docker) |
| Wave 6: Orchestration | `src/api/deps.py`, `src/api/routes/ingest.py`, `src/api/main.py`, `src/tasks/ingest.py` | Ties everything together |
| Wave 7: Tests | `tests/conftest.py`, all `tests/pipeline/test_*.py`, `tests/api/test_ingest_routes.py` | Validates entire pipeline |

## Metadata

**Analog search scope:** Full project directory (confirmed empty -- no .py files exist)
**Files scanned:** 0 (greenfield)
**Pattern extraction date:** 2026-04-18
**Pattern sources:** RESEARCH.md code examples (Context7-cited), CLAUDE.md stack recommendations, established library conventions
