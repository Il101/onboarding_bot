# Stack Research

**Domain:** RAG-based Knowledge Extraction & AI Mentor System
**Researched:** 2026-04-17
**Confidence:** HIGH

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | 3.12+ | Runtime | All major RAG/ML libraries target Python. 3.12 has perf improvements and better type hints. Avoid 3.13+ until ecosystem catches up. |
| LlamaIndex | 0.14.x | RAG framework (indexing, retrieval, synthesis) | Purpose-built for RAG. Superior document ingestion, chunking strategies, and vector store integrations compared to LangChain for this use case. Has native QdrantVectorStore support. 200+ data connectors. The project's primary workflow is retrieve-then-synthesize -- LlamaIndex is the right abstraction level. |
| Qdrant | 1.17.x (server) / 1.17.x (client) | Vector database | Rust-native, production-grade vector DB. Supports hybrid search (dense + sparse), payload filtering, vector quantization for RAM reduction. Has both Docker deployment and in-memory mode for dev. First-class LlamaIndex integration. No external dependencies (unlike Chroma which needs SQLite). Russian embeddings work out of the box. |
| FastAPI | 0.136.x | Web API backend for admin panel | Industry standard for Python APIs. Native async, auto-generated OpenAPI docs, Pydantic v2 integration. Will serve both the web admin panel API and any future integrations. |
| python-telegram-bot | 22.7 | Telegram bot interface | Most mature Python Telegram library (v22.x = fully async). Clean handler architecture with Application/ApplicationBuilder pattern. Supports persistence, conversation handlers, and all Bot API features. |
| Docling | 2.90.x | PDF document parsing | IBM's open-source document converter. Superior to PyPDF/pdfplumber for structured extraction: handles tables, layout analysis, OCR for scanned documents, and exports directly to Markdown. Native LlamaIndex integration via DoclingReader. |

### Embedding Model (Critical for Russian)

| Model | Dimensions | Purpose | Why Recommended |
|-------|-----------|---------|-----------------|
| `intfloat/multilingual-e5-large` | 1024 | Text embeddings for Russian + 100+ languages | Top MTEB benchmark performer for multilingual retrieval including Russian. Excellent semantic search quality. Available via sentence-transformers and HuggingFace. Also supports `multilingual-e5-base` (768d) if GPU memory is constrained. **Confidence: MEDIUM** -- verified via MTEB benchmarks and community consensus, but not tested against this specific domain's Russian business jargon. |

**Embedding runner:** `sentence-transformers` 5.4.x -- the standard framework for loading and running embedding models locally.

### PII Anonymization

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Microsoft Presidio (analyzer + anonymizer) | 2.2.362 | PII detection and anonymization | Industry-standard de-identification SDK. Supports custom recognizers via regex, deny-lists, and NER. Pluggable NLP engine (spaCy or transformers). |
| spaCy `ru_core_news_md` | latest | Russian NER backend for Presidio | Russian-language spaCy model for detecting PERSON, ORG, LOC entities. Medium-sized model balances accuracy and speed. Required because Presidio does not natively support Russian. **Confidence: MEDIUM** -- Presidio + spaCy Russian works but requires custom recognizer mapping for Russian-specific PII (INN, SNILS, Russian phone formats). This needs a dedicated research spike. |

### Relational Database

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| PostgreSQL | 16+ | Application database (users, sources, audit logs, analytics) | Stores structured metadata: user accounts, data source configs, processing pipeline status, usage analytics. Not for vector data (Qdrant handles that). PG is the default choice -- reliable, well-understood, excellent SQLAlchemy support. |
| SQLAlchemy | 2.0.49 | ORM / database toolkit | Pydantic v2 compatible. Async session support. Works with Alembic for migrations. Standard choice for FastAPI projects. |
| Alembic | 1.18.x | Database migrations | The standard migration tool for SQLAlchemy. Auto-generates migration scripts from model changes. |
| psycopg2-binary | 2.9.11 | PostgreSQL adapter | The most reliable PostgreSQL driver for Python. Works with SQLAlchemy 2.0. |

### LLM Integration

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| LlamaIndex LLM integrations | via llama-index | LLM abstraction layer | LlamaIndex's Settings.llm provides a unified interface. Switch between OpenAI, Anthropic, or local models (Ollama/vLLM) by changing one line. The project requirement says "flexible LLM provider" -- this abstraction is why we use LlamaIndex. |
| openai (SDK) | latest | OpenAI API integration | For GPT-4o / GPT-4o-mini when using cloud LLM. Also needed for `text-embedding-3-small` if using OpenAI embeddings instead of local. |
| anthropic (SDK) | latest | Anthropic API integration | For Claude models as an alternative LLM provider. |

### Telegram Data Processing

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Standard `json` module | builtin | Telegram JSON export parsing | Telegram's "Export Data" feature produces `result.json` with structured message arrays. No special library needed -- standard json parsing is sufficient. |
| beautifulsoup4 | 4.14.x | HTML content cleanup from Telegram exports | Telegram exports may include HTML-formatted messages (bold, italic, links). BeautifulSoup strips markup while preserving text content. |

### Web Admin Panel Frontend

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| HTMX + Alpine.js | latest | Interactive admin UI | Server-rendered HTML via Jinja2 templates with HTMX for dynamic updates. No separate build pipeline, no Node.js dependency. FastAPI serves everything. Ideal for an admin panel (CRUD operations, dashboards) where full SPA is overkill. This is the strongest trend in the Python/FastAPI community in 2025-2026 for admin interfaces. **Confidence: HIGH** -- this is the recommended default. |
| Jinja2 | latest | Template engine | FastAPI's default template engine. Ships with Starlette. |
| Tailwind CSS | latest | Styling | Utility-first CSS via CDN (no build step). Perfect for HTMX-based admin panels. |

### Background Task Processing

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Celery + Redis | latest | Async task queue for heavy processing | PDF parsing, PII anonymization, embedding generation, and knowledge extraction are CPU-intensive operations that must not block the API or bot. Celery is the Python standard for task queues. Redis is the message broker and result backend. |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| uv | Python package manager | Replaces pip/pip-tools. 10-100x faster dependency resolution. Lock files for reproducibility. `uv venv` for virtual environments. Standard in 2025-2026 Python projects. |
| ruff | Linter + formatter | Replaces flake8, black, isort. Extremely fast (Rust-based). Single tool for linting and formatting. |
| pytest + pytest-asyncio | Testing | Standard Python test framework. pytest-asyncio for testing async FastAPI endpoints and bot handlers. |
| Docker + docker-compose | Containerization | Qdrant runs as Docker container in dev and production. Also useful for consistent Python environment. |
| pre-commit | Git hooks | Run ruff and pytest on commit. Prevents broken code from entering the repo. |

## Installation

```bash
# Core RAG pipeline
pip install llama-index>=0.14.0
pip install llama-index-vector-stores-qdrant>=0.4.0
pip install llama-index-llms-openai>=0.3.0
pip install llama-index-llms-anthropic>=0.6.0
pip install llama-index-readers-docling>=0.4.0
pip install qdrant-client>=1.17.0
pip install sentence-transformers>=5.4.0

# Document processing
pip install docling>=2.90.0
pip install beautifulsoup4>=4.14.0

# PII anonymization
pip install presidio-analyzer>=2.2.360
pip install presidio-anonymizer>=2.2.360
python -m spacy download ru_core_news_md

# Web API
pip install fastapi[standard]>=0.136.0
pip install uvicorn[standard]>=0.44.0
pip install sqlalchemy>=2.0.49
pip install alembic>=1.18.0
pip install psycopg2-binary>=2.9.11
pip install pydantic>=2.13.0
pip install jinja2>=3.1.0

# Telegram bot
pip install python-telegram-bot>=22.7

# Background tasks
pip install celery[redis]>=5.4.0
pip install redis>=5.0.0

# LLM providers
pip install openai>=1.60.0
pip install anthropic>=0.40.0

# Dev dependencies
pip install ruff>=0.9.0
pip install pytest>=8.0.0
pip install pytest-asyncio>=0.24.0
pip install httpx>=0.28.0  # for FastAPI TestClient
```

### pyproject.toml (recommended)

```toml
[project]
name = "v-brain"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    # Core RAG
    "llama-index>=0.14.0",
    "llama-index-vector-stores-qdrant",
    "llama-index-llms-openai",
    "llama-index-llms-anthropic",
    "llama-index-readers-docling",
    "qdrant-client>=1.17.0",
    "sentence-transformers>=5.4.0",
    # Documents
    "docling>=2.90.0",
    "beautifulsoup4>=4.14.0",
    # PII
    "presidio-analyzer>=2.2.360",
    "presidio-anonymizer>=2.2.360",
    # Web API
    "fastapi[standard]>=0.136.0",
    "uvicorn[standard]>=0.44.0",
    "sqlalchemy>=2.0.49",
    "alembic>=1.18.0",
    "psycopg2-binary>=2.9.11",
    # Telegram
    "python-telegram-bot>=22.7",
    # Tasks
    "celery[redis]>=5.4.0",
    "redis>=5.0.0",
    # LLM
    "openai>=1.60.0",
    "anthropic>=0.40.0",
]

[dependency-groups]
dev = [
    "ruff>=0.9.0",
    "pytest>=8.0.0",
    "pytest-asyncio>=0.24.0",
    "httpx>=0.28.0",
]
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| **LlamaIndex** | LangChain + LangGraph | If you need complex multi-agent orchestration with branching logic beyond RAG. For this project's retrieve-then-synthesize workflow, LlamaIndex is simpler and more focused. |
| **LlamaIndex** | Dify.ai | If the team has no ML engineers and wants a visual workflow builder. Dify provides a working RAG pipeline in minutes but limits customization depth. Our project needs custom PII pipeline, Telegram-specific parsing, and SOP generation -- all of which require code-level control. |
| **Qdrant** | ChromaDB | Chroma is simpler for prototyping (embedded, zero-config) but not production-grade. Qdrant offers better filtering, hybrid search, quantization, and horizontal scaling. Chroma is fine for a weekend demo, not for a deployed system. |
| **Qdrant** | PostgreSQL + pgvector | pgvector is a reasonable choice if you want to minimize infrastructure (one DB for everything). However, Qdrant is purpose-built for vector search with better performance at scale and more advanced retrieval features. Keep pgvector as a fallback option. |
| **Qdrant** | Milvus | Milvus is more enterprise-grade with k8s-native deployment, but significantly more complex to operate. Overkill for a single-tenant system. |
| **Docling** | LlamaParse | LlamaParse (LlamaIndex's commercial parser) has excellent quality but requires a paid API. Docling is open-source and runs locally, which matters for the data-perimeter requirement. |
| **Docling** | PyPDF2 / pdfplumber | These are simpler but lack table extraction, layout analysis, and OCR capabilities. Docling is strictly superior for structured document understanding. |
| **HTMX + Alpine.js** | React + Refine | If the admin panel grows to be very complex (real-time charts, complex state management, drag-and-drop). For MVP CRUD + analytics dashboards, HTMX eliminates an entire build pipeline. |
| **HTMX + Alpine.js** | Vue + Vben Admin | Similar tradeoff to React. Vue is a good middle-ground but still requires a separate Node.js build step. |
| **multilingual-e5-large** | OpenAI text-embedding-3-small | If using OpenAI as LLM provider anyway. OpenAI embeddings are excellent and save GPU resources, but add API costs and a dependency on external service. Local model keeps data in-perimeter. |
| **multilingual-e5-large** | paraphrase-multilingual-MiniLM-L12-v2 | If GPU memory is very limited (384d vs 1024d). Acceptable quality for MVP but noticeably worse retrieval quality for Russian business text. |
| **Presidio** | Custom regex-only PII pipeline | If Presidio proves too heavy or Russian NER is insufficient. A regex-only approach (Russian phone numbers, emails, INN patterns) would catch the most common PII types but miss names/orgs that NER provides. Use as fallback. |
| **Celery + Redis** | ARQ (async Redis queue) | If Celery is too complex for the task volume. ARQ is simpler and fully async but less feature-rich (no retry policies, no monitoring UI). |
| **PostgreSQL** | SQLite | Only for development/testing. SQLite cannot handle concurrent writes from Celery workers and does not support the JSON query features needed for analytics. |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| **LangChain** (as primary framework) | LangChain is a general-purpose LLM framework, not RAG-specific. Its RAG abstractions are shallower than LlamaIndex's. The API has changed significantly across versions, causing migration pain. LangGraph is good for orchestration but that is not our primary need. | **LlamaIndex** for RAG. If you later need multi-agent orchestration, add LangGraph on top. |
| **Dify.ai** (as core platform) | The project spec mentions Dify.ai, but our requirements -- custom PII pipeline, Telegram JSON parsing, SOP generation, Russian NER -- all require code-level control that a visual workflow engine cannot provide. Dify also introduces vendor coupling and limits retrieval strategy customization. | **LlamaIndex** (code-first). Dify could be used as a supplementary evaluation/annotation tool, not as the core pipeline. |
| **ChromaDB** (for production) | Not designed for production workloads. No built-in replication, limited filtering, no hybrid search out of the box. The Python client can corrupt data under concurrent writes. | **Qdrant** -- production-native, Docker-deployable, feature-complete. |
| **OpenAI-only embeddings** | Violates the data-perimeter constraint. Embeddings sent to OpenAI API leave the company network. Also creates a hard dependency on external service availability. | **Local multilingual-e5-large** via sentence-transformers. Switch to OpenAI embeddings only if the perimeter constraint is relaxed. |
| **Gemma** (as default LLM) | The project spec originally mentioned Gemma, but quality is significantly behind GPT-4o-class models for Russian language tasks. Gemma can be the local fallback, but should not be the primary model. | **GPT-4o-mini** for quality/cost balance, or **Claude 3.5 Haiku** as alternative. Keep Gemma/Ollama as local fallback option. |
| **React SPA** (for admin panel) | Adds unnecessary complexity for an internal admin tool. Separate Node.js build pipeline, state management boilerplate, deployment complexity. The admin panel is CRUD + charts, not a complex interactive app. | **HTMX + Alpine.js** -- server-rendered, no build step, FastAPI serves everything. |
| **pinecone** / Weaviate Cloud | Hosted vector DB services that store embeddings outside the company perimeter. Violates the data security constraint. | **Qdrant** (self-hosted via Docker). All vector data stays in-perimeter. |
| **LangSmith** (for observability) | Requires sending trace data to LangChain's cloud service. May contain sensitive business knowledge from the RAG pipeline. | **LangFuse** (self-hostable) or **Arize Phoenix** (open-source, self-hosted). Both provide equivalent RAG tracing without data exfiltration. |

## Stack Patterns by Variant

**If deploying fully local (no external API):**
- Use Ollama or vLLM to serve LLM locally (Llama 3, Qwen 2.5, or Mistral)
- Use local `multilingual-e5-large` embeddings via sentence-transformers
- Use Qdrant in Docker with local storage
- Accept lower quality for Russian language generation compared to GPT-4o

**If using cloud LLM (recommended for quality):**
- Use GPT-4o-mini as primary LLM (best quality/cost for Russian)
- Claude 3.5 Haiku as fallback provider
- Still use local embeddings (multilingual-e5-large) to keep vector data in-perimeter
- The only data leaving perimeter: user questions and retrieved context sent to LLM API

**If GPU is available:**
- Run embeddings on GPU (sentence-transformers auto-detects CUDA/MPS)
- Consider `multilingual-e5-large` (1024d) for best quality
- Docling OCR can use GPU acceleration

**If only CPU is available:**
- Use `multilingual-e5-base` (768d) for embeddings -- 50% smaller, slightly lower quality
- Consider `paraphrase-multilingual-MiniLM-L12-v2` (384d) if memory is very constrained
- Docling works on CPU but PDF processing will be slower
- Disable Docling OCR if all PDFs are text-based (not scanned)

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| `llama-index>=0.14.0` | `qdrant-client>=1.17.0` | LlamaIndex's QdrantVectorStore requires qdrant-client. Works with both sync and async clients. |
| `llama-index>=0.14.0` | `sentence-transformers>=5.0.0` | LlamaIndex's HuggingFaceEmbedding wraps sentence-transformers. v5.x introduced breaking changes -- use LlamaIndex 0.14.x which handles this. |
| `fastapi>=0.136.0` | `pydantic>=2.13.0` | FastAPI 0.126+ dropped Pydantic v1 support entirely. Must use Pydantic v2. |
| `fastapi>=0.136.0` | `sqlalchemy>=2.0.49` | FastAPI + SQLAlchemy 2.0 is the standard combination. SQLAlchemy 1.4 is EOL. |
| `presidio-analyzer>=2.2.360` | `spacy>=3.7.0` | Presidio 2.x requires spaCy 3.x. The `ru_core_news_md` model requires spaCy 3.x. |
| `python-telegram-bot>=22.0` | Python 3.9+ | v20+ is fully async. v22.x requires Python 3.9+. We target 3.12+ so no issue. |
| `docling>=2.90.0` | Python 3.10+ | Docling requires Python 3.10+. We target 3.12+. |
| `celery>=5.4.0` | `redis>=5.0.0` | Celery 5.x uses Redis as broker. Redis 5.x+ recommended for performance. |

## Architecture Note: Why Not Dify.ai

The project spec lists Dify.ai as a potential orchestration platform. After research, **Dify.ai is not recommended as the core pipeline** for V-Brain:

1. **Custom pipeline requirements**: Our system needs a PII anonymization step that runs BEFORE documents enter the RAG pipeline. Dify's visual workflows assume documents go directly from upload to chunking to indexing. Inserting a custom preprocessing step is awkward.

2. **Telegram JSON parsing**: The system ingests Telegram chat exports (JSON format), not standard document uploads. This requires custom parsing logic that Dify's document connectors do not support.

3. **SOP generation**: The system needs to generate structured SOP instructions from extracted knowledge -- this is a multi-step LLM process (extract, cluster, structure, format) that does not fit Dify's standard RAG template.

4. **Data perimeter**: While Dify can be self-hosted, the visual workflow abstraction makes it harder to audit exactly where data flows. A code-first approach makes security review straightforward.

5. **Vendor coupling**: Dify workflows are stored in Dify's internal format. If we need to add features that Dify does not support (e.g., custom retrieval strategies, knowledge graph enhancement), migration to code would be expensive.

**Dify.ai could be useful** as a supplementary tool for non-technical stakeholders to experiment with prompts and evaluate RAG quality, but it should not be the production pipeline.

## Sources

- Context7: `/websites/developers_llamaindex_ai_python` -- LlamaIndex RAG pipeline, QdrantVectorStore integration, DoclingReader
- Context7: `/qdrant/qdrant` -- Qdrant features, filtering, hybrid search, Python client API
- Context7: `/microsoft/presidio` -- Presidio analyzer/anonymizer, custom recognizers, NLP engine configuration
- Context7: `/python-telegram-bot/python-telegram-bot` -- async bot handlers, Application architecture, persistence
- Context7: `/fastapi/fastapi` -- Pydantic v2 migration, version management, deployment
- Context7: `/huggingface/sentence-transformers` -- multilingual models, Russian embeddings
- Context7: `/docling-project/docling` -- PDF parsing pipeline, OCR, table extraction, Markdown export
- PyPI: All version numbers verified via `pip index versions` on 2026-04-17
- MTEB Benchmark: Multilingual embedding model rankings (MEDIUM confidence -- benchmark data, not domain-tested)

---
*Stack research for: RAG Knowledge Extraction & AI Mentor System (V-Brain)*
*Researched: 2026-04-17*
