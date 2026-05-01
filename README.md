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

```mermaid
flowchart LR
    A["Telegram JSON / PDF"] --> B["FastAPI ingestion API"]
    B --> C["Celery workers"]
    C --> D["PII anonymization"]
    D --> E["Parsing and chunking"]
    E --> F["Dense + sparse embeddings"]
    E --> G["Knowledge extraction"]
    F --> H["Qdrant"]
    G --> I["PostgreSQL"]

    J["Telegram user"] --> K["Telegram bot"]
    K --> L["LangGraph orchestration"]
    L --> M["FastAPI retrieval API"]
    M --> H
    M --> I
    L --> N["Grounded answer with citations"]
```

---

## Demo surfaces

### Admin panel

![Sources page](screenshots/admin-sources.png)
![Knowledge review page](screenshots/admin-knowledge.png)
![Users page](screenshots/admin-users.png)
![Analytics page](screenshots/admin-analytics.png)

### Typical reviewer flow

1. Upload a Telegram export or PDF in the admin panel.
2. Let Celery parse, anonymize, chunk, and index the content.
3. Review extracted knowledge items and publish only high-confidence facts.
4. Ask the Telegram bot an onboarding question and receive a grounded answer with source attribution.

### Example product outcome

**Question:** "How do I book a meeting room?"  
**Answer shape:** a concise instruction derived from published knowledge, followed by source references from the indexed corpus.

This repository includes demo-data scripts so the admin panel can be evaluated without internal company data.

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

## Demo Data

To populate the admin panel with demo data (fake users, feedback events, analytics):

```bash
# Create test knowledge items
uv run python scripts/create_test_data.py

# Index knowledge into Qdrant
uv run python scripts/index_knowledge.py

# Add demo users and feedback for analytics
uv run python scripts/add_demo_data.py
```

This will show realistic usage patterns in the admin panel for demonstration purposes.

---

## Engineering decisions

- **PII before LLM/indexing:** chat and document content is anonymized before downstream extraction or retrieval stages.
- **Asynchronous ingestion:** parsing, transcription, extraction, and indexing run in Celery workers to keep the admin API responsive.
- **Hybrid retrieval contract:** dense embeddings are paired with sparse vectors and reranked before answer synthesis.
- **Human review gate:** extracted facts land in review before publication, which keeps the bot grounded on curated knowledge instead of raw ingestion output.

---

## Security and MVP constraints

- **PII anonymization** is built into the ingestion pipeline (phones, emails, names are masked)
- **Bot access** is restricted to whitelisted Telegram users
- **Data sources** (MVP): Telegram JSON exports and PDF documents
- **Language** primarily Russian, configured in prompts and policies
- **Admin auth** is intentionally lightweight for MVP/local deployment; session storage is not yet designed for multi-admin or distributed deployment
