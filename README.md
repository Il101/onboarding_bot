# V-Brain — AI Knowledge Extractor & Mentor

A system that converts company Telegram chats and PDF documents into a searchable knowledge base and a Telegram assistant for faster onboarding.

New employees ask questions in the bot and receive grounded answers with source citations based on internal materials.

---

## Recruiter quick read (30 seconds)

- **Problem:** operational knowledge is fragmented across chats and documents.
- **Solution:** end-to-end AI pipeline: ingestion -> PII anonymization -> extraction -> RAG -> Telegram assistant.
- **Outcome:** fast, source-backed answers in chat instead of constant manual mentoring.
- **Engineering scope:** production-style architecture with workers, vector search, admin panel, tests, and CI.

---

## Core capabilities

- Ingests Telegram JSON exports and PDF files via web admin panel
- Performs PII anonymization before LLM/indexing stages
- Extracts structured knowledge units and groups them by topic
- Runs hybrid retrieval (dense + sparse) with reranking
- Returns Telegram bot answers with source attribution
- Restricts bot access with Telegram user role whitelist
- Captures answer feedback (thumbs up/down)

---

## Architecture (high level)

```text
Telegram/PDF -> Ingestion API -> Celery workers -> PII + Parsing + Chunking
                                   |-> Embeddings -> Qdrant
                                   |-> Knowledge extraction -> PostgreSQL

Telegram user -> Bot (python-telegram-bot) -> LangGraph orchestration
                                           -> Retrieval API (FastAPI)
                                           -> RAG answer + source attribution
```

---

## Tech stack

**Backend / AI:** Python 3.12, FastAPI, LangGraph, OpenAI-compatible clients  
**Data / Infra:** PostgreSQL, Redis, Celery, Qdrant  
**Ingestion / NLP:** Docling, Presidio, fastembed  
**Bot / UI:** python-telegram-bot, Jinja2 templates  
**Quality:** pytest, ruff, GitHub Actions

---

## Quick start

### 1. Requirements

- Python 3.12+
- Docker + Docker Compose
- `uv` (`pip install uv`)

### 2. Install dependencies

```bash
uv sync --extra dev
```

### 3. Configure `.env`

Copy `.env.example` to `.env` and fill required values:

```env
LLM_PROVIDER=openai
LLM_MODEL=gpt-4o-mini
LLM_API_KEY=

ADMIN_PASSWORD=
TELEGRAM_BOT_TOKEN=
TELEGRAM_USER_ROLES={}

DATABASE_URL=postgresql+psycopg2://vbrain:vbrain@localhost:5432/vbrain
REDIS_URL=redis://localhost:6379/0
QDRANT_HOST=localhost
QDRANT_PORT=6333
```

`ADMIN_PASSWORD` should be a bcrypt hash (see `.env.example`).

### 4. Start infrastructure

```bash
docker compose up -d
mkdir -p data/uploads
```

### 5. Apply migrations

```bash
uv run alembic upgrade head
```

### 6. Run services

In three terminals:

```bash
# API + admin panel
uv run uvicorn src.api.main:app --reload --port 8000

# Celery worker
uv run celery -A src.tasks.ingest worker --loglevel=info

# Telegram bot
uv run python -m src.bot.telegram_app
```

---

## Entry points

- **Admin panel:** `http://localhost:8000/admin`
- **API docs:** `http://localhost:8000/docs`
- **Bot:** Telegram (requires user ID in `TELEGRAM_USER_ROLES`)

---

## Quality checks

```bash
uv run ruff check .
uv run pytest -q
```

CI runs the same checks on push/pull requests:

- `.github/workflows/ci.yml`

---

## Security and MVP constraints

- PII anonymization is part of the ingestion pipeline
- Bot access is restricted by role whitelist
- MVP data sources: Telegram JSON + PDF
- Primary data/answer language is currently configured in prompts and policies

