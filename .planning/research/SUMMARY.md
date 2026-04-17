# Project Research Summary

**Project:** V-Brain -- AI Knowledge Extraction & RAG Mentor System
**Domain:** RAG-based knowledge management for Russian-speaking SMBs via Telegram
**Researched:** 2026-04-17
**Confidence:** MEDIUM

## Executive Summary

V-Brain is a RAG (Retrieval-Augmented Generation) system that extracts organizational knowledge from Telegram chat logs and PDF documents, builds a searchable knowledge base, and serves answers to employees via a Telegram bot. The product targets Russian-speaking SMBs (5-50 employees) where institutional knowledge lives in work chats and scattered documents rather than formal wikis. No existing product serves this specific niche -- Guru/Slite/Tettra target English-speaking enterprises with manual wiki authoring, while Glean is enterprise-grade and English-first.

The recommended approach is a code-first Python pipeline built on LlamaIndex for RAG orchestration, Qdrant for vector storage, Microsoft Presidio for PII anonymization, and FastAPI for the web admin layer. The frontend should use HTMX + Alpine.js (server-rendered, no Node.js build step) for the admin panel. The Telegram bot uses python-telegram-bot (v22.x, fully async). All heavy processing (PDF parsing, embedding, LLM calls) runs as Celery tasks with Redis as the broker. Dify.ai is explicitly NOT recommended as the core pipeline because the project requires custom PII preprocessing, Telegram JSON parsing, and Russian-language-specific NLP that a visual workflow engine cannot accommodate.

The two biggest risks are (1) Russian PII anonymization failure -- Presidio's default recognizers are English-centric and will miss declined Russian names, patronymics, and +7/8 phone formats, requiring custom recognizers and testing on real Russian data, and (2) hallucinated answers destroying user trust -- the bot MUST have programmatic "I don't know" fallbacks with similarity thresholds, not just a system prompt instruction. Both require dedicated validation during Phase 1. A secondary risk is embedding model quality for Russian: `intfloat/multilingual-e5-large` is the recommended choice (MEDIUM confidence, not benchmarked on domain-specific Russian business jargon), and switching embedding models later requires a full reindex.

## Key Findings

### Recommended Stack

A Python-centric stack chosen for RAG capability maturity, Russian language support, and self-hosted data perimeter compliance.

**Core technologies:**
- **Python 3.12+** -- runtime; all RAG/ML libraries target Python, 3.12 has performance and type hint improvements
- **LlamaIndex 0.14.x** -- RAG framework; purpose-built for retrieve-then-synthesize workflows, native Qdrant integration, 200+ data connectors
- **Qdrant 1.17.x** -- vector database; Rust-native, production-grade, hybrid search (dense + sparse), self-hosted Docker deployment
- **FastAPI 0.136.x** -- web API backend; async-native, auto OpenAPI docs, Pydantic v2 integration
- **python-telegram-bot 22.7** -- Telegram bot; most mature Python Telegram library, fully async
- **Docling 2.90.x** -- PDF parsing; IBM open-source, superior table/layout extraction, OCR for scanned docs, native LlamaIndex integration
- **Microsoft Presidio 2.2.x + spaCy ru_core_news_md** -- PII anonymization; industry standard, requires custom Russian recognizers
- **sentence-transformers 5.4.x with intfloat/multilingual-e5-large** -- embeddings; top MTEB benchmark for multilingual retrieval including Russian
- **PostgreSQL 16+ / SQLAlchemy 2.0 / Alembic** -- relational DB for metadata, users, analytics
- **Celery + Redis** -- async task queue for CPU-intensive pipeline stages
- **HTMX + Alpine.js + Tailwind CSS** -- admin panel frontend; no build step, server-rendered, ideal for CRUD admin UI

**What NOT to use:** LangChain (shallow RAG abstractions), ChromaDB (not production-grade), OpenAI-only embeddings (violates data perimeter), React SPA (overkill for admin panel), Dify.ai as core pipeline (insufficient customization for Russian NLP and custom preprocessing).

### Expected Features

**Must have for launch (P1 -- table stakes):**
- PDF Document Ingestion & Parsing -- primary structured knowledge source (SOPs, manuals, policies)
- Telegram Chat Log Parsing -- core differentiator; parse JSON export, filter noise, reconstruct threads via reply_to_message_id
- PII Anonymization -- legal requirement (152-FZ), must run BEFORE any LLM processing
- Vector Search / RAG Pipeline -- embedding + hybrid retrieval (vector + BM25) + LLM generation with reranking
- Telegram Q&A Bot -- multi-turn context, source citation, confidence threshold fallback ("I don't know")
- Source Citation in Answers -- display which document/chunk the answer came from (trust builder)
- Basic Web Admin Panel -- source management (upload PDFs, import Telegram exports), user management, knowledge base view
- Admin Review Gate -- preview auto-extracted knowledge before it goes live in RAG

**Should have after validation (P2 -- differentiators):**
- SOP Wiki Auto-Generation -- LLM-driven clustering + structured SOP generation from chat logs (THE core innovation)
- Topic Clustering -- BERTopic or LLM-based grouping of messages by theme (Sales, CRM workflows, etc.)
- Incremental Knowledge Updates -- delta ingestion without full reindex
- Analytics Dashboard -- question tracking, answer accuracy, knowledge gaps (proves ROI)
- Feedback Loop -- thumbs up/down on answers, feeds back to improve retrieval
- Knowledge Gap Detection -- surface "top 10 questions the bot couldn't answer" to admin

**Defer to v2+ (P3):**
- Real-Time Telegram Integration (live streaming) -- JSON export is sufficient for MVP
- Video/Audio Transcription -- explicitly out of scope
- Multi-Tenant Architecture -- premature optimization
- Mobile App -- Telegram bot IS the mobile interface
- Custom LLM Fine-Tuning -- RAG-first approach, fine-tuning only if RAG proves insufficient

### Architecture Approach

V-Brain is a five-stage pipeline system with unidirectional ingestion flow and bidirectional RAG serving. The architecture cleanly separates concerns: `pipeline/` (batch ingestion), `rag/` (real-time query serving), `bot/` (Telegram interface), `api/` (FastAPI admin), and `tasks/` (Celery orchestration).

**Major components:**
1. **Source Parser** -- reads Telegram JSON exports and PDF files into normalized text
2. **PII Anonymizer** -- Presidio-based detection and token replacement before any downstream processing
3. **Knowledge Extractor** -- LLM-based extraction of procedures, decisions, and patterns; topic clustering; SOP generation
4. **Embedder + Vector Store** -- converts text chunks to embeddings via sentence-transformers, stores in Qdrant
5. **RAG Serving Layer** -- hybrid retrieval (vector + BM25 with RRF fusion), cross-encoder reranking, LLM response generation with citations and guardrails
6. **Telegram Bot** -- user-facing interface with multi-turn conversation context
7. **Web Admin** -- FastAPI + HTMX admin panel for source management, knowledge review, analytics
8. **Task Orchestrator** -- Celery task chains for async pipeline execution with per-stage retryability

**Key architectural patterns:**
- **Pipeline-as-Task-Chain**: Each ingestion stage is an independent Celery task, chained for fault isolation and retryability
- **LLM Provider Adapter**: Abstract base class over OpenAI/Anthropic/local models, switched via config (not framework lock-in)
- **Hybrid Retrieval with Reranking**: Dense vector + sparse BM25 via RRF fusion, then cross-encoder reranking on top-k results
- **PII-First Pipeline**: All data anonymized before any LLM call; reversible mapping stored locally for admin review

**Anti-patterns to avoid:** Framework lock-in (using LangChain/LlamaIndex for everything), skipping reranking, English-only embeddings, PII after LLM processing, monolithic ingestion function.

### Critical Pitfalls

1. **Garbage In, Garbage Out** -- Raw Telegram exports contain greetings, service messages, bot messages, and noise. Build explicit quality gates with knowledge density scoring before embedding. Every chunk entering the vector DB must have a source trace and minimum information density.
2. **Russian PII Anonymization Failure** -- Presidio defaults are English-centric. Russian names appear in 10+ declined forms, patronymics need custom detection, phone formats (+7/8) differ from English. Use `ru_core_news_lg` (never `_sm`), build custom recognizers for INN/SNILS/Russian addresses, test with real Russian chat data. Anonymization recall must be >= 95%.
3. **Naive Chunking Destroys Russian Semantics** -- Russian is free-word-order with rich morphology; fixed-size chunking splits mid-concept. Use semantic or Russian-aware sentence splitting (spaCy `ru_core_news_lg`), 20-30% overlap windows, token-count limits not character-count.
4. **English-Centric Embeddings** -- Even "multilingual" models vary wildly in Russian quality. Benchmark at least 2-3 models on Russian question-chunk pairs before committing. Switching later requires full reindex. Recall@5 must be >= 0.7.
5. **No "I Don't Know" Fallback** -- LLMs confidently hallucinate. Implement multi-layer confidence pipeline: retrieval similarity threshold (>0.65), context relevance check, structured `has_answer` field in LLM output, cascading fallbacks. Bot must gracefully decline on >= 9/10 out-of-scope questions.

## Implications for Roadmap

Based on the combined research, the project has a clear dependency chain: `llm/` -> `pipeline/` -> `rag/` -> `bot/` -> `analytics/`. The following phase structure respects these dependencies while delivering incremental value.

### Phase 1: Foundation & Data Ingestion

**Rationale:** Everything depends on clean, anonymized, well-chunked data entering the vector store. This phase builds the LLM abstraction layer, source parsers, PII anonymization, and chunking/embedding pipeline. It is the highest-risk phase because Russian PII anonymization and embedding quality are both MEDIUM confidence and must be validated with real data before anything else can proceed.

**Delivers:** Working data ingestion pipeline that can take a Telegram JSON export and a PDF, clean them, anonymize PII, chunk intelligently, and produce quality embeddings in Qdrant. Admin can upload sources via a minimal API.

**Addresses:** PDF Ingestion, Telegram Chat Log Parsing, PII Anonymization, Vector DB Setup, Embedding Model (P1 features)

**Avoids:** Garbage In/Garbage Out (quality gates), Russian PII failure (custom recognizers), naive chunking (semantic splitting), English-centric embeddings (multilingual-e5-large benchmark)

**Verification:** Ingest a real Telegram export and a real company PDF. Manually review 100 random chunks -- zero noise tolerance. Run PII anonymization on 100 labeled Russian messages -- recall >= 95%. Benchmark 20 Russian question-chunk pairs -- recall@5 >= 0.7.

### Phase 2: RAG Serving & Telegram Bot

**Rationale:** With a clean vector store in place, this phase builds the query serving layer and the user-facing Telegram bot. This is the moment of truth -- employees can ask questions and get answers. The bot must include confidence fallbacks from day one, or trust will be destroyed before it can be built.

**Delivers:** Working Telegram Q&A bot with multi-turn context, source citations, hybrid retrieval with reranking, and "I don't know" fallback. Users can ask questions and get trustworthy answers from the knowledge base.

**Addresses:** RAG Pipeline, Telegram Q&A Bot, Source Citation, Confidence Threshold, Conversation Context (P1 features)

**Avoids:** No-fallback hallucination (similarity threshold + has_answer check), skipping reranking (hybrid search + cross-encoder)

**Verification:** Ask 10 questions NOT in the knowledge base -- bot must gracefully decline on >= 9/10. Ask 20 questions that ARE in the knowledge base -- correct source must be cited on >= 90%.

### Phase 3: Web Admin & Knowledge Review

**Rationale:** The admin panel is needed for operational use but does not block user-facing functionality. This phase adds the HTMX admin panel for source management, knowledge base viewing, and the critical admin review gate for auto-extracted content. This is also where SOP generation logic lands (deferred from Phase 1 because it requires working extraction validated in Phase 2).

**Delivers:** Full web admin panel with source upload/management, knowledge base browsing, admin review workflow (draft -> review -> published), and basic SOP generation from clustered chat logs.

**Addresses:** Basic Web Admin Panel, Admin Review Gate, Topic Clustering, SOP Wiki Auto-Generation (P1 + P2 features)

**Avoids:** Unreviewed SOP publishing (human review gate), Dify workflow complexity (custom code for Russian preprocessing)

**Verification:** Domain expert reviews 5 generated SOPs -- at least 80% of steps accurate, all have source traces. Admin can review and approve/reject knowledge entries through the web UI.

### Phase 4: Analytics & Operational Hardening

**Rationale:** Only after the bot is live with real users generating query logs can analytics be meaningful. This phase adds the feedback loop, analytics dashboard, knowledge gap detection, incremental updates, and operational concerns (monitoring, deployment hardening, error handling).

**Delivers:** Analytics dashboard with question tracking and accuracy metrics. Feedback loop (thumbs up/down) influencing retrieval quality monitoring. Incremental knowledge updates. Knowledge gap detection surfacing unanswered questions to admin. Production deployment with Docker Compose.

**Addresses:** Analytics Dashboard, Feedback Loop, Knowledge Gap Detection, Incremental Knowledge Updates (P2 features)

**Avoids:** Re-embedding entire corpus on every update (incremental indexing), no evaluation framework (RAGAS metrics)

**Verification:** 5 real users test the bot; collect feedback on clarity and helpfulness. Retrieval recall@5 and answer faithfulness scores are logged for every test query.

### Phase Ordering Rationale

- **Phase 1 first** because all four critical pitfalls (data quality, PII, chunking, embeddings) are foundational -- they cannot be retroactively fixed without a full reindex. This is the highest-risk phase and should consume the most research time.
- **Phase 2 second** because it delivers the core user value (ask a question, get an answer) and enables real-user testing. The bot must include fallbacks from day one to prevent trust destruction.
- **Phase 3 third** because the admin panel is operationally necessary but can be prototyped alongside Phase 2. SOP generation depends on validated extraction from Phases 1-2. The review workflow is what makes generated content safe.
- **Phase 4 last** because analytics require real usage data. Incremental updates and gap detection are optimizations that matter only after the system is operational.

**Parallelization possible:**
- Web Admin API can be built in parallel with the RAG serving layer (both depend only on `core/` and `models/` from Phase 1)
- Telegram Bot can be prototyped with mock responses while RAG is being built

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 1 (PII Anonymization):** Russian-specific Presidio configuration, custom recognizer development for INN/SNILS/patronymics. Natasha and DeepPavlov as alternative NER options need evaluation. This is the highest-risk research area.
- **Phase 1 (Embedding Quality):** `multilingual-e5-large` must be benchmarked against alternatives (LaBSE, Cohere multilingual, OpenAI text-embedding-3-large) on domain-specific Russian business text. The chosen model is locked in at index time.
- **Phase 3 (SOP Generation):** LLM prompting strategies for extracting structured procedures from informal Russian chat logs. Sparse documentation on this specific task. Needs prompt engineering research.

Phases with standard patterns (skip research-phase):
- **Phase 2 (RAG Pipeline):** Hybrid retrieval with reranking is a well-documented 2025-2026 pattern. Qdrant + LlamaIndex integration is standard. Telegram bot API integration is well-established.
- **Phase 3 (Web Admin):** FastAPI + HTMX + Tailwind is the standard Python admin stack. CRUD operations and Jinja2 templating are well-documented.
- **Phase 4 (Analytics):** Standard dashboard patterns. RAGAS evaluation framework provides established metrics.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Based on official library docs via Context7, verified PyPI versions, well-established patterns in RAG ecosystem. LlamaIndex + Qdrant + FastAPI is the standard Python RAG stack for 2025-2026. |
| Features | MEDIUM | Feature categorization is HIGH confidence (derived from first principles and project spec), but competitor feature details are based on training data (web search was rate-limited). MVP definition is well-grounded. |
| Architecture | MEDIUM | Architectural patterns (hybrid retrieval, Celery pipelines, PII-first) are well-established and HIGH confidence. Dify.ai integration assessment is LOW confidence (needs validation of plugin capabilities). Build order is sound. |
| Pitfalls | MEDIUM | Pitfall identification is HIGH confidence (well-documented RAG failure modes). Prevention strategies are MEDIUM confidence for Russian-specific issues (PII, chunking, embeddings) -- they need validation with real Russian data, not just English-adapted approaches. |

**Overall confidence:** MEDIUM

### Gaps to Address

- **Russian PII anonymization recall:** Presidio + ru_core_news_md will miss declined name forms and Russian-specific PII without custom recognizers. No benchmark data exists for this specific domain. **Handle:** Dedicated research spike in Phase 1 planning. Test with real Russian chat data. Consider Natasha/DeepPavlov as complementary NER.
- **Embedding model quality on Russian business jargon:** `multilingual-e5-large` performs well on MTEB benchmarks but has not been tested against domain-specific Russian business language (CRM terminology, sales processes, internal company shorthand). **Handle:** Benchmark 2-3 models on 20+ real question-chunk pairs during Phase 1 before committing.
- **Dify.ai integration feasibility:** Architecture research recommends against Dify as core pipeline but acknowledges LOW confidence on whether Dify's plugin system could accommodate custom preprocessing. **Handle:** Not blocking -- code-first approach is the recommendation. Dify evaluation can happen later if desired.
- **SOP generation prompting strategy:** No established patterns for generating structured SOPs from informal Russian Telegram conversations. This is a novel task with sparse documentation. **Handle:** Research spike during Phase 3 planning. Expect significant prompt iteration.
- **Telegram JSON export format variations:** Export format may vary across Telegram clients and export dates. Edge cases (deleted messages, edited messages, media messages without text) need real export validation. **Handle:** Test with multiple real exports during Phase 1.

## Sources

### Primary (HIGH confidence)
- Context7: `/websites/developers_llamaindex_ai_python` -- LlamaIndex RAG pipeline, QdrantVectorStore integration, DoclingReader
- Context7: `/qdrant/qdrant` -- Qdrant features, filtering, hybrid search, Python client API
- Context7: `/microsoft/presidio` -- Presidio analyzer/anonymizer, custom recognizers, NLP engine configuration
- Context7: `/python-telegram-bot/python-telegram-bot` -- async bot handlers, Application architecture
- Context7: `/fastapi/fastapi` -- Pydantic v2 migration, version management
- Context7: `/huggingface/sentence-transformers` -- multilingual models, Russian embeddings
- Context7: `/docling-project/docling` -- PDF parsing pipeline, OCR, table extraction
- PyPI: All version numbers verified via `pip index versions` on 2026-04-17
- Project spec: `Spec_V-Brain_AI_Automation.pdf` (technical requirements)

### Secondary (MEDIUM confidence)
- MTEB Benchmark: Multilingual embedding model rankings (benchmark data, not domain-tested)
- Competitor analysis (training data): Guru, Slite, Tettra, Glean feature comparisons
- Natasha / DeepPavlov: Russian NLP library capabilities for NER
- RAGAS evaluation framework: retrieval quality metrics
- Dify.ai (training data): Knowledge base features, RAG capabilities, workflow engine limitations

### Tertiary (LOW confidence)
- Web search results (rate-limited, partial): RAG architecture patterns, Dify.ai limitations, PDF parsing challenges
- Russian business domain jargon embedding quality: no benchmark data exists, needs real-world validation

---
*Research completed: 2026-04-17*
*Ready for roadmap: yes*
