# Architecture Research

**Domain:** RAG Knowledge Extraction + AI Mentor System (V-Brain)
**Researched:** 2026-04-17
**Confidence:** MEDIUM (web search rate-limited; findings based on multiple web searches + training data + project spec context; no official docs verification via Context7)

## Standard Architecture

### System Overview

V-Brain is a five-stage pipeline system. Data flows in one direction through the ingestion pipeline (left to right), then serves queries via a bidirectional RAG loop.

```
+------------------------------------------------------------------+
|                     INGESTION PIPELINE                             |
|                                                                    |
|  +----------+   +----------+   +----------+   +----------+        |
|  | Sources  |   |Anonymize |   | Extract  |   |  Index   |        |
|  |          |   |  (PII)   |   | (SOP/LLM)|   | (Vector) |        |
|  +----+-----+   +----+-----+   +----+-----+   +----+-----+        |
|       |              |              |              |               |
|  Telegram JSON    Presidio      LLM Chain     Embeddings +        |
|  PDF files        NER+Regex     Clustering    Vector DB          |
+------------------------------------------------------------------+
                          |
                     +----v-----+
                     | Knowledge |
                     |   Store   |
                     +----+-----+
                          |
+------------------------------------------------------------------+
|                     SERVING LAYER                                 |
|                                                                    |
|  +----------+   +----------+   +----------+   +----------+        |
|  |Telegram  |   |  Query   |   |Retrieval |   |Generate  |        |
|  |   Bot    +-->| Process  +-->|  Engine  +-->|  (LLM)   |        |
|  +----------+   +----------+   +----------+   +----------+        |
|                                                                    |
|  +----------+   +----------+   +----------+                        |
|  |   Web    |   |  Admin   |   |Analytics|                        |
|  |  Admin   |   |  CRUD    |   | Dashboard|                        |
|  +----------+   +----------+   +----------+                        |
+------------------------------------------------------------------+
                          |
+------------------------------------------------------------------+
|                     INFRASTRUCTURE                                |
|  +----------+   +----------+   +----------+   +----------+        |
|  | FastAPI  |   |  Celery  |   |  Redis   |   | PostgreSQL|       |
|  |  Server  |   | Workers  |   | (Queue)  |   | (Meta)    |       |
|  +----------+   +----------+   +----------+   +----------+        |
|  +----------+   +----------+                                       |
|  |  Vector  |   | LLM/API  |                                       |
|  |   DB     |   | Provider |                                       |
|  +----------+   +----------+                                       |
+------------------------------------------------------------------+
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| **Source Parser** | Read raw Telegram JSON exports and PDF files into normalized text | Custom Python parser for Telegram `result.json`; `pdfplumber` or `unstructured` for PDFs |
| **PII Anonymizer** | Detect and replace PII (names, phones, emails) with tokens before any downstream processing | Microsoft Presidio (AnalyzerEngine + AnonymizerEngine) with custom Russian-language recognizers |
| **Knowledge Extractor** | LLM-based extraction of procedures, decisions, and patterns from anonymized text; clustering by topic; SOP generation in Markdown | LLM chain (GPT-4o / Claude / local model) with prompt templates; `BERTopic` or LLM-based clustering |
| **Embedder** | Convert text chunks into vector embeddings for semantic search | `sentence-transformers` (BGE-M3 for local) or OpenAI API (`text-embedding-3-small`) |
| **Vector Store** | Store and query embeddings with metadata for RAG retrieval | Qdrant (self-hosted, strong filtering) or pgvector (simpler, PostgreSQL-native) |
| **Query Processor** | Transform user questions into optimized retrieval queries (rewrite, decompose, classify intent) | LLM-based query rewriting + intent classification |
| **Retrieval Engine** | Hybrid search: vector similarity + BM25 keyword search, with reranking | Qdrant hybrid search + cross-encoder reranker (`bge-reranker-v2-m3` or Cohere Rerank) |
| **Response Generator** | Construct prompts with retrieved context, generate answers with citations | LLM (same flexible provider) with system prompt enforcing mentor persona and Russian language |
| **Telegram Bot** | User-facing interface for employees to ask questions via Telegram | `python-telegram-bot` or `aiogram` library |
| **Web Admin** | Admin interface for managing sources, viewing/editing knowledge, user roles, analytics | Separate FastAPI endpoints serving a frontend (React/Next.js or simpler admin panel) |
| **Task Orchestrator** | Manage async pipeline jobs (ingestion, embedding, re-indexing) | Celery with Redis as broker; task chains for pipeline stages |
| **Metadata Store** | Track sources, processing status, user accounts, analytics, feedback | PostgreSQL |

## Recommended Project Structure

```
vbrain/
├── src/
│   ├── api/                    # FastAPI application
│   │   ├── main.py             # App entry, middleware, CORS
│   │   ├── routes/
│   │   │   ├── bot.py          # Telegram webhook endpoints
│   │   │   ├── admin.py        # Web admin CRUD endpoints
│   │   │   ├── sources.py      # Source upload/management
│   │   │   └── analytics.py    # Usage analytics endpoints
│   │   └── deps.py             # Dependency injection (DB, services)
│   │
│   ├── bot/                    # Telegram bot logic
│   │   ├── handler.py          # Message handler, conversation flow
│   │   ├── commands.py         # Bot commands (/start, /help, etc.)
│   │   └── feedback.py         # Thumbs up/down, rating collection
│   │
│   ├── pipeline/               # Ingestion pipeline
│   │   ├── __init__.py
│   │   ├── orchestrator.py     # Celery task chains
│   │   ├── parsers/
│   │   │   ├── telegram.py     # Telegram JSON export parser
│   │   │   └── pdf.py          # PDF document parser
│   │   ├── anonymizer/
│   │   │   ├── presidio.py     # Presidio analyzer + anonymizer
│   │   │   └── recognizers.py  # Custom Russian PII recognizers
│   │   ├── extractor/
│   │   │   ├── knowledge.py    # LLM-based knowledge extraction
│   │   │   ├── cluster.py      # Topic clustering
│   │   │   └── sop.py          # SOP/Markdown generation
│   │   └── indexer/
│   │       ├── chunker.py      # Text chunking strategies
│   │       ├── embedder.py     # Embedding generation (API or local)
│   │       └── vector_store.py # Vector DB upsert/query
│   │
│   ├── rag/                    # RAG serving pipeline
│   │   ├── query.py            # Query processing, rewriting, classification
│   │   ├── retriever.py        # Hybrid retrieval + reranking
│   │   ├── generator.py        # LLM response generation with context
│   │   ├── prompts.py          # System prompts, templates
│   │   └── guardrails.py       # Hallucination check, citation verification
│   │
│   ├── llm/                    # LLM provider abstraction
│   │   ├── base.py             # Abstract LLM interface
│   │   ├── openai.py           # OpenAI/compatible provider
│   │   ├── anthropic.py        # Anthropic provider
│   │   └── local.py            # Ollama/vLLM local model provider
│   │
│   ├── models/                 # SQLAlchemy/SQLModel models
│   │   ├── source.py           # Data sources (Telegram, PDF)
│   │   ├── document.py         # Extracted documents/knowledge entries
│   │   ├── user.py             # Users and roles
│   │   └── analytics.py        # Query logs, feedback, metrics
│   │
│   ├── core/                   # Shared utilities
│   │   ├── config.py           # Settings (pydantic-settings)
│   │   ├── database.py         # DB session management
│   │   └── logging.py          # Structured logging
│   │
│   └── tasks/                  # Celery tasks
│       ├── ingest.py           # Document ingestion task chain
│       ├── reindex.py          # Re-indexing tasks
│       └── cleanup.py          # Maintenance tasks
│
├── web/                        # Web admin frontend (if not using Dify)
│   └── ...
│
├── tests/
│   ├── pipeline/               # Pipeline unit tests
│   ├── rag/                    # RAG integration tests
│   └── api/                    # API endpoint tests
│
├── docker-compose.yml          # Full stack (API, worker, Redis, PostgreSQL, Qdrant)
├── Dockerfile
├── pyproject.toml
└── .env.example
```

### Structure Rationale

- **`pipeline/` is the largest module** -- it handles the entire ingestion chain. Separating parsers, anonymizer, extractor, and indexer into submodules keeps each concern isolated and independently testable.
- **`rag/` is separate from `pipeline/`** -- ingestion and serving are fundamentally different processes with different latency profiles (batch vs. real-time). They should evolve independently.
- **`llm/ abstraction layer** is critical -- the project explicitly requires flexible LLM provider support. A thin adapter pattern over raw SDKs (not LangChain/LlamaIndex) avoids framework lock-in while keeping provider switching simple.
- **`tasks/` at top level** -- Celery task definitions need to import from many modules. Keeping them at the top level avoids circular imports.

## Architectural Patterns

### Pattern 1: Pipeline-as-Task-Chain (Ingestion)

**What:** Each ingestion stage is a Celery task. Stages are chained together so the output of one feeds into the next. Failed stages can be retried independently.

**When to use:** Batch processing of documents where each stage is CPU-bound or I/O-heavy (LLM calls, embedding API calls).

**Trade-offs:** Excellent fault isolation and retryability. But adds latency (serialization between tasks) and requires Redis as broker. Overkill for processing a single small document in real-time.

**Example:**
```python
from celery import chain

# In tasks/ingest.py
ingest_pipeline = chain(
    parse_source.s(source_id),           # Parse raw file
    anonymize_pii.s(),                   # PII detection + replacement
    extract_knowledge.s(),               # LLM extraction + clustering
    generate_sops.s(),                   # Markdown SOP generation
    chunk_and_embed.s(),                 # Chunk + embed + vector store upsert
    mark_completed.s(source_id),         # Update source status
)
ingest_pipeline.apply_async(task_id=f"ingest-{source_id}")
```

### Pattern 2: LLM Provider Adapter (Flexible Provider)

**What:** Define an abstract base class for LLM interactions. Each provider (OpenAI, Anthropic, local via Ollama) implements the interface. Configuration selects the provider at runtime.

**When to use:** When the system must support multiple LLM providers without changing business logic.

**Trade-offs:** Slightly more code upfront. But enables seamless switching between API and local models, which is a hard project requirement.

**Example:**
```python
# In llm/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class LLMResponse:
    text: str
    tokens_used: int
    model: str

class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, prompt: str, system: str = "", temperature: float = 0.3) -> LLMResponse:
        ...

    @abstractmethod
    async def embed(self, texts: list[str]) -> list[list[float]]:
        ...

# In llm/openai.py
class OpenAIProvider(LLMProvider):
    def __init__(self, model: str = "gpt-4o", embed_model: str = "text-embedding-3-small"):
        self.model = model
        self.embed_model = embed_model
        # Initialize OpenAI client

    async def generate(self, prompt, system="", temperature=0.3) -> LLMResponse:
        # Implementation using openai SDK
        ...

# Selection via config
def get_llm_provider(settings: Settings) -> LLMProvider:
    if settings.llm_provider == "openai":
        return OpenAIProvider(model=settings.llm_model)
    elif settings.llm_provider == "anthropic":
        return AnthropicProvider(model=settings.llm_model)
    elif settings.llm_provider == "local":
        return LocalProvider(base_url=settings.llm_base_url, model=settings.llm_model)
```

### Pattern 3: Hybrid Retrieval with Reranking

**What:** Combine dense vector similarity search with sparse BM25 keyword search using Reciprocal Rank Fusion (RRF), then rerank top-k results with a cross-encoder model.

**When to use:** Always. This is the standard production RAG retrieval pattern for 2025-2026. Single-vector search misses exact keyword matches; BM25 misses semantic matches.

**Trade-offs:** Requires both a vector index and a keyword index (Qdrant supports both natively). Reranking adds latency (~100-200ms for cross-encoder on top-k results). But retrieval quality improvement is significant.

**Example:**
```python
# In rag/retriever.py
def retrieve(query: str, top_k: int = 20) -> list[RetrievedChunk]:
    # Step 1: Hybrid search (Qdrant native)
    hybrid_results = qdrant_client.query_points(
        collection_name="knowledge",
        prefetch=[
            models.Prefetch(query=models.DenseVector(embed(query)), limit=top_k),
            models.Prefetch(query=models.SparseVector(query), limit=top_k),
        ],
        query=models.FusionQuery(fusion=models.Fusion.RRF),
        limit=top_k,
    )

    # Step 2: Rerank top results with cross-encoder
    texts = [r.payload["text"] for r in hybrid_results.points]
    scores = reranker.compute_score([[query, t] for t in texts])

    # Step 3: Return reranked results
    ranked = sorted(zip(hybrid_results.points, scores), key=lambda x: x[1], reverse=True)
    return ranked[:5]  # Top 5 after reranking
```

### Pattern 4: PII-Anonymization-First Pipeline

**What:** Anonymize all source data BEFORE any LLM processing or embedding. PII tokens are stored in a reversible mapping so original data can be restored if needed (for admin review).

**When to use:** When processing sensitive corporate communications containing personal data. This is a hard requirement for V-Brain.

**Trade-offs:** Anonymization can slightly degrade LLM extraction quality (replaced names lose context). Russian-language PII detection is harder than English. But it is non-negotiable for compliance and data perimeter requirements.

**Example:**
```python
# In pipeline/anonymizer/presidio.py
from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
from presidio_anonymizer import AnonymizerEngine, OperatorConfig

# Russian-specific configuration
registry = RecognizerRegistry()
registry.load_predefined_recognizers(languages=["en", "ru"])
# Add custom Russian recognizers for:
# - Russian names (patronymic patterns: Ivan Ivanovich Ivanov)
# - Russian phone formats (+7, 8, etc.)
# - Russian email domains
analyzer = AnalyzerEngine(registry=registry, supported_languages=["en", "ru"])

anonymizer = AnonymizerEngine()

operators = {
    "PERSON": OperatorConfig("replace", {"new_value": "[СОТРУДНИК]"}),
    "PHONE_NUMBER": OperatorConfig("replace", {"new_value": "[ТЕЛЕФОН]"}),
    "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": "[EMAIL]"}),
}
```

## Data Flow

### Ingestion Flow (Batch, Async)

```
Admin uploads source (Telegram JSON or PDF)
    |
    v
[FastAPI endpoint] --> Save to file storage (local/S3)
    |
    v
[Celery task chain launched with task_id]
    |
    v
[1. Parse] --> Normalized messages/documents
    |
    v
[2. Anonymize] --> PII replaced with tokens, mapping stored
    |
    v
[3. Extract] --> LLM identifies procedures, decisions, patterns
    |
    v
[4. Cluster] --> Group extracted knowledge by topic
    |
    v
[5. Generate SOPs] --> Structured Markdown knowledge entries
    |
    v
[6. Chunk + Embed] --> Text split into chunks, embedded
    |
    v
[7. Index] --> Upsert to Vector DB + metadata to PostgreSQL
    |
    v
[8. Complete] --> Source status updated to "indexed"
```

### Query Flow (Real-time, Sync)

```
Employee sends question via Telegram bot
    |
    v
[Bot Handler] --> Receive message, extract user context
    |
    v
[Query Processor] --> Rewrite/optimize query for retrieval
    |                    Classify intent (factual, procedural, conversational)
    v
[Retrieval Engine] --> Hybrid search (vector + BM25)
    |                    Rerank results
    |                    Filter by user role/permissions (future)
    v
[Response Generator] --> Build prompt: system + retrieved context + question
    |                    Call LLM provider
    |                    Generate answer with source citations
    v
[Guardrails] --> Check for hallucinations, off-topic responses
    |
    v
[Bot Handler] --> Send answer to employee
    |
    v
[Analytics] --> Log query, response, feedback (async)
```

### State Management

```
PostgreSQL (source of truth):
  - sources table: {id, type, filename, status, created_at}
  - documents table: {id, source_id, content, sop_markdown, topic, created_at}
  - users table: {id, telegram_id, role, created_at}
  - query_logs table: {id, user_id, question, answer, sources_used, feedback, created_at}

Vector DB (Qdrant):
  - Collection "knowledge": vectors + metadata {document_id, source_id, topic, chunk_index}

Redis:
  - Celery task state
  - Rate limiting
  - Query cache (optional, semantic caching for repeated questions)

File Storage:
  - Raw uploaded files (Telegram JSON, PDFs)
  - PII token mapping tables (for admin reversible de-anonymization)
```

### Key Data Flows

1. **Source-to-Knowledge:** Raw file --> PII-cleaned text --> LLM-extracted knowledge entries --> Chunked vectors in Vector DB + Markdown in PostgreSQL. This is a one-way pipeline with intermediate state tracked in PostgreSQL.
2. **Question-to-Answer:** User question --> Query processing --> Hybrid retrieval from Vector DB --> LLM generation with context --> Answer with citations. This is a real-time request-response flow.
3. **Feedback Loop:** User rates answer --> Stored in query_logs --> Aggregated in analytics dashboard --> Used for future retrieval quality evaluation. This is asynchronous.

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 1-10 sources, <100 users | Single server, Docker Compose. Celery with 1-2 workers. Qdrant single node. Everything runs on one machine. |
| 10-100 sources, 100-1000 users | Separate API server and Celery worker(s). Qdrant with replication. Redis for caching. PostgreSQL connection pooling. |
| 100+ sources, 1000+ users | Horizontal Celery workers (autoscale). Qdrant cluster or managed (Qdrant Cloud). Separate embedding service (batch processing). Rate limiting on bot queries. |

### Scaling Priorities

1. **First bottleneck: LLM API rate limits and latency.** Embedding generation and LLM calls are the slowest parts. Mitigate with: batching embedding requests, using faster/smaller models for initial retrieval quality testing, and caching repeated queries.
2. **Second bottleneck: Vector DB query latency at large corpus sizes.** Qdrant handles millions of vectors well with HNSW indexing. Add metadata filtering to reduce search space before vector search. Consider collection sharding by topic/source if needed.
3. **Third bottleneck: Telegram bot concurrency.** `aiogram` handles this natively with async. Use `python-telegram-bot` with `ApplicationBuilder().concurrent_updates(True)` if preferred.

## Anti-Patterns

### Anti-Pattern 1: LLM Framework Lock-in (LangChain/LlamaIndex everywhere)

**What people do:** Build the entire system on top of LangChain or LlamaIndex abstractions, using their document loaders, chunkers, retrievers, and chains.

**Why it's wrong:** These frameworks evolve rapidly, break on version updates, add abstraction overhead that hides bugs, and make debugging difficult. For production systems, direct SDK usage with thin wrappers is more maintainable.

**Do this instead:** Use raw OpenAI/Anthropic/Ollama SDKs behind your own `LLMProvider` abstraction. Use LangChain only for a specific utility if it saves significant time (e.g., text splitters), but isolate it so it can be replaced.

### Anti-Pattern 2: Skipping Reranking

**What people do:** Use only vector similarity search (or only BM25) without a reranking step.

**Why it's wrong:** Reranking is the single highest-impact improvement to RAG quality. A cross-encoder reranker on top-20 results dramatically improves relevance compared to raw vector search.

**Do this instead:** Always implement hybrid search (vector + BM25) with Reciprocal Rank Fusion, then rerank top results with a cross-encoder. This should be part of the MVP, not a "later optimization."

### Anti-Pattern 3: Embedding Without Russian Language Support

**What people do:** Use an English-only embedding model (e.g., early `all-MiniLM`) for Russian-language documents.

**Why it's wrong:** Embedding quality degrades significantly for unsupported languages. Retrieval becomes unreliable.

**Do this instead:** Use a multilingual embedding model. For local/self-hosted: BGE-M3 (best open-source multilingual, strong Russian). For API: OpenAI `text-embedding-3-small/large` or Cohere `embed-v3`. For Russian-specific optimization: `deepvk/USER-bge-m3` (Russian-adapted BGE-M3).

### Anti-Pattern 4: PII Anonymization After LLM Processing

**What people do:** Send raw text to LLM for extraction, then anonymize the output.

**Why it's wrong:** PII has already been exposed to the LLM (and potentially to external API if using cloud LLM). This violates the data perimeter requirement.

**Do this instead:** Anonymize BEFORE any LLM call. The entire pipeline operates on anonymized data. Only the reversible mapping (stored locally) can restore originals.

### Anti-Pattern 5: Monolithic Ingestion Function

**What people do:** Write a single function that parses, anonymizes, extracts, embeds, and indexes a document all at once.

**Why it's wrong:** No retryability, no observability, no progress tracking. If the LLM call fails at step 4 of 7, the entire document must be reprocessed from scratch.

**Do this instead:** Use Celery task chains (Pattern 1 above). Each stage is independent, observable, and retryable. Failed stages can be retried without re-running earlier stages.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| **OpenAI API** | HTTP REST via `openai` SDK | Rate limits vary by tier. Batch embedding requests (100+ chunks per call). |
| **Anthropic API** | HTTP REST via `anthropic` SDK | Slower but often better for Russian text generation. |
| **Ollama (local)** | HTTP REST via `ollama` SDK or raw HTTP | No rate limits. Requires GPU for reasonable speed. Model quality varies. |
| **Telegram Bot API** | Long polling or webhook via `python-telegram-bot` or `aiogram` | Webhook preferred for production. Long polling simpler for development. |
| **Presidio** | Local Python library | No external API calls. NER model download required on first run. Russian NER needs custom recognizers. |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| `api/` <-> `pipeline/` | Celery task dispatch (async) | API never runs pipeline synchronously. Always returns task_id immediately. |
| `api/` <-> `rag/` | Direct function call (sync) | Query serving is synchronous -- user waits for answer. Keep this path fast. |
| `api/` <-> `models/` | SQLAlchemy sessions (sync) | Standard ORM pattern. Connection pooling via SQLAlchemy. |
| `pipeline/` <-> `llm/` | Synchronous function calls | Pipeline tasks are sync Celery functions calling sync LLM methods. |
| `rag/` <-> `llm/` | Async function calls (FastAPI context) | RAG serving is async. LLM adapter must support both sync and async. |
| `pipeline/` <-> `rag/` | Shared Vector DB (no direct code dependency) | They share the Qdrant collection but no Python imports. Decoupled by design. |

## Dify.ai Consideration

The project spec mentions Dify.ai as the orchestration layer. Here is an honest assessment:

**What Dify provides that V-Brain needs:**
- Visual workflow builder for the RAG pipeline
- Built-in RAG engine (chunking, embedding, retrieval, reranking)
- Multi-model LLM provider switching
- Web admin UI for knowledge base management
- Self-hosted deployment (Docker Compose)
- Observability and logging

**What Dify does NOT provide (V-Brain must build):**
- Telegram JSON export parser with conversation structure analysis
- PII anonymization pipeline (Presidio integration)
- Russian-language-specific processing (custom NER, lemmatization)
- SOP generation from extracted knowledge
- Topic clustering of knowledge entries
- Custom Telegram bot with mentor persona
- Analytics dashboard specific to onboarding use case

**Recommendation:** Use Dify as the **RAG serving and knowledge base management layer**, but build custom pipeline components for ingestion, anonymization, and extraction. This hybrid approach avoids reinventing the RAG engine while maintaining control over the domain-specific pipeline.

Alternative: Build everything custom (no Dify). This gives full control but significantly more development work, especially for the web admin interface and model provider management.

**Confidence:** LOW on Dify recommendation -- this needs validation. Check whether Dify's plugin/extension system can accommodate custom pipeline stages, or whether the custom ingestion pipeline must feed into Dify's knowledge base via API.

## Build Order Implications

Components have clear dependencies. Suggested build order:

```
Phase 1: Foundation
  LLM Provider Abstraction (llm/)     <-- Everything depends on this
  Config & Database Setup (core/, models/)

Phase 2: Ingestion Pipeline
  Source Parsers (pipeline/parsers/)   <-- Telegram JSON + PDF
  PII Anonymizer (pipeline/anonymizer/) <-- Presidio + custom recognizers
  Knowledge Extractor (pipeline/extractor/) <-- Depends on LLM abstraction
  Chunker & Embedder (pipeline/indexer/)   <-- Depends on extraction output

Phase 3: RAG Serving
  Vector DB Setup + Indexing            <-- Needs embeddings from Phase 2
  Query Processor + Retriever           <-- Core RAG loop
  Response Generator + Guardrails       <-- Needs retriever

Phase 4: User Interfaces
  Telegram Bot (bot/)                   <-- Needs RAG serving from Phase 3
  Web Admin API (api/)                  <-- Needs models from Phase 1
  Web Admin Frontend                    <-- Needs admin API

Phase 5: Operations
  Celery Task Orchestration (tasks/)    <-- Ties pipeline into async jobs
  Analytics & Feedback Loop             <-- Needs query logging from Phase 4
  Monitoring & Deployment               <-- Docker Compose, health checks
```

**Key dependency chain:** `llm/` --> `pipeline/` --> `rag/` --> `bot/` --> `analytics/`

**Parallelization possible:**
- Web Admin API can be built in parallel with Ingestion Pipeline (both depend only on `core/` and `models/`)
- Telegram Bot UI can be prototyped with mock responses while RAG is being built

## Sources

- Web search: RAG architecture patterns 2025-2026 (rate-limited, no direct URLs available)
- Web search: Microsoft Presidio architecture (rate-limited, training data supplemented)
- Web search: Dify.ai architecture and components (rate-limited, training data supplemented)
- Web search: Russian language RAG and multilingual embeddings (rate-limited, training data supplemented)
- Web search: FastAPI + Celery async pipeline architecture (rate-limited, training data supplemented)
- Project context: `.planning/PROJECT.md` (V-Brain requirements and constraints)
- Project spec: `Spec_V-Brain_AI_Automation.pdf` (referenced in PROJECT.md, not fully parsed due to rate limits)

**Note on confidence:** Multiple web searches were rate-limited (HTTP 429). Findings are supplemented by training data knowledge. Key architectural patterns (RAG, hybrid retrieval, Celery pipelines, Presidio) are well-established and unlikely to have changed significantly. However, specific version numbers, API details, and Dify.ai integration capabilities should be verified with official documentation before implementation.

---
*Architecture research for: RAG Knowledge Extraction + AI Mentor System (V-Brain)*
*Researched: 2026-04-17*
