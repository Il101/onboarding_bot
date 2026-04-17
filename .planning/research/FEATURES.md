# Feature Research

**Domain:** AI Knowledge Extraction & RAG Mentor System (V-Brain)
**Researched:** 2026-04-17
**Confidence:** MEDIUM (web search rate-limited; based on training data, competitor analysis, project spec, and domain expertise)

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Telegram Q&A Bot** | Core value proposition: employees ask questions and get answers | HIGH | RAG pipeline + conversational memory + Telegram Bot API integration. Multi-turn context is essential -- new hires ask follow-up questions. |
| **Document Ingestion (PDF)** | Explicitly in spec; users have SOPs, manuals, policies in PDF | MEDIUM | PDF parsing with table extraction. Libraries: Unstructured.io, PyMuPDF, pdfplumber. |
| **Telegram Chat Log Parsing** | Primary data source -- knowledge lives in work chats | MEDIUM | Parse JSON export, filter noise (system messages, join/leave), reconstruct threads via `reply_to_message_id`, concatenate multi-part messages. |
| **PII Anonymization** | Legal requirement (152-FZ) and explicit spec requirement | MEDIUM | Microsoft Presidio for detecting/replacing names, phones, emails with tokens. Must run BEFORE any LLM processing. |
| **Vector Search / RAG** | Without retrieval, the bot hallucinates. Non-negotiable. | HIGH | Embedding model + vector DB (ChromaDB/Qdrant) + retrieval + generation pipeline. Hybrid search (keyword + semantic) needed for policy queries with exact terms. |
| **Basic Web Admin Panel** | Admin needs to manage system without touching code | MEDIUM | Source management, user list, basic knowledge base view. CRUD for knowledge entries. |
| **Knowledge Base Viewing** | Admin must verify what the bot knows before it answers | LOW | Read-only view of extracted knowledge (Markdown Wiki pages). |
| **Source Citation in Answers** | Users need to trust answers; "source: SOP_Sales_v3.md" builds confidence | MEDIUM | Display which document/chunk the answer was generated from. Critical for trust and for manual verification. |
| **Confidence Threshold** | Bot must say "I don't know" when it doesn't know | MEDIUM | If retrieval score falls below threshold, return fallback instead of hallucinated answer. Explicitly required by spec (85% accuracy target). |

### Differentiators (Competitive Advantage)

Features that set the product apart. Not required, but valuable.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Auto-Generated SOP Wiki** | Unique value: turns chaotic chat history into structured instructions. No competitor does this for Telegram-centric SMBs in Russian. | HIGH | LLM-driven clustering of messages by topic, extraction of action sequences, generation of Markdown SOPs. This IS the core innovation. |
| **Topic Clustering of Chat Logs** | Discovers organizational knowledge structure from raw communication | HIGH | BERTopic or LLM-based clustering. Groups messages into themes (Sales, Support, CRM workflows). Feeds into Wiki generation. |
| **Conversation Thread Reconstruction** | Preserves context: "how to handle X" from back-and-forth discussion | MEDIUM | Use `reply_to_message_id` to rebuild threads. Turn threaded discussions into coherent knowledge entries rather than disconnected messages. |
| **Incremental Knowledge Updates** | New chat messages and documents update the knowledge base without full reindex | MEDIUM | Delta ingestion: detect new/changed sources, process only what changed. Essential for operational use -- admins won't re-run full pipeline daily. |
| **Analytics Dashboard** | Proves ROI: tracks questions asked, answer accuracy, knowledge gaps | MEDIUM | Most-searched topics, unanswered questions, thumbs up/down on answers, usage by employee. Data for "40% reduction in owner questions" KPI from spec. |
| **Knowledge Gap Detection** | Identifies what the bot CANNOT answer -- tells admin what knowledge is missing | MEDIUM | Track low-confidence/failed queries. Surface "top 10 questions the bot couldn't answer" to admin. Actionable insight for content creation. |
| **Multi-LLM Flexibility** | Switch between API models (OpenAI, Anthropic) and local models (Gemma, Qwen) | MEDIUM | Explicitly in spec: "not tied to specific model." Requires abstraction layer over LLM provider. Valuable for cost control and data locality. |
| **Human-in-the-Loop Review** | Admin reviews and edits extracted knowledge before it goes live | MEDIUM | Draft -> Review -> Published pipeline for Wiki entries. Prevents garbage in = garbage out. Critical for trust in auto-generated content. |
| **Feedback Loop** | Users rate answers, data flows back to improve retrieval | LOW | Thumbs up/down on bot answers. Store feedback, use for monitoring and future fine-tuning. |
| **Russian Language NLP** | All data, extraction, and answers in Russian | MEDIUM | Embedding models must support Russian well (multilingual-e5, LaBSE, or fine-tuned models). LLM prompt engineering for Russian output. |

### Anti-Features (Commonly Requested, Often Problematic)

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| **Real-Time Telegram Integration** (live message streaming) | "Connect to active channel and learn continuously" | Adds massive complexity: webhooks, incremental processing, message ordering, rate limits. JSON export is deterministic and sufficient for MVP. | Periodic manual JSON export + scheduled ingestion. Add live integration post-validation. |
| **Video/Audio Transcription** (Loom, recordings) | Spec mentions it as future; seems like natural extension | Whisper is good but error-prone on domain-specific Russian. Audio parsing significantly increases pipeline complexity. Client noise, accents, background. | Explicitly out of scope for MVP. Text-only sources (Telegram + PDF) validate the core loop first. |
| **Mobile App** | "Employees want a mobile interface" | Telegram bot IS the mobile interface. Building a separate app duplicates functionality. | Telegram bot covers mobile use case completely. Web admin panel for desktop management. |
| **Multi-Tenant Architecture** | "Could sell this to other businesses" | Premature optimization. Adds auth complexity, data isolation, billing. One tenant = simpler code, faster iteration. | Deploy for one business. Architect code to be tenant-aware later (namespacing IDs, separate DB schemas), but don't build the multi-tenant layer. |
| **OAuth / SSO Integration** | "Enterprise-grade authentication" | Overkill for an SMB with 5-50 employees. Adds dependency on external IdP. | Simple username/password login for MVP. Add OAuth later if needed. |
| **Automatic Knowledge Publishing** (no human review) | "Fully automated, set and forget" | LLM-generated SOPs will contain errors, hallucinations, outdated info. Publishing without review = broken trust. | Draft pipeline with admin review gate. Admin approves before knowledge goes live in RAG. |
| **Open-Ended Chatbot** (general conversation) | "Make it like ChatGPT" | Destroys the value proposition. If the bot can chat about anything, it will hallucinate company policies. Scope creep into general AI assistant. | Strictly scoped: bot ONLY answers from knowledge base. "I can only help with questions about company processes and procedures." |
| **Custom Fine-Tuning of LLM** | "Fine-tune a model on company data for better answers" | Expensive, fragile, hard to update. Fine-tuning captures patterns that may become outdated. RAG with good retrieval is more maintainable and equally effective for this use case. | RAG-first approach. Fine-tuning only if RAG proves insufficient after validation. |

## Feature Dependencies

```
[PDF Ingestion]
    |--requires--> [PII Anonymization]
    |--requires--> [Document Parser]
    |--produces--> [Raw Text Chunks]
                    |--requires--> [Embedding Model]
                    |--requires--> [Vector DB Setup]
                    |--produces--> [Indexed Knowledge]

[Telegram Chat Log Parsing]
    |--requires--> [PII Anonymization]
    |--requires--> [Thread Reconstruction]
    |--requires--> [Noise Filtering]
    |--produces--> [Clean Chat Data]
                    |--requires--> [Topic Clustering]
                    |--produces--> [Clustered Conversations]
                                    |--requires--> [SOP Generation LLM]
                                    |--produces--> [Wiki Markdown Pages]
                                                    |--requires--> [Admin Review Gate]
                                                    |--produces--> [Published Knowledge]

[Published Knowledge]
    |--requires--> [Embedding Model]
    |--requires--> [Vector DB Setup]
    |--produces--> [Indexed Knowledge]

[Indexed Knowledge]
    |--requires--> [RAG Retrieval Pipeline]
    |--requires--> [LLM Answer Generation]
    |--produces--> [Telegram Q&A Bot]
                    |--enhances--> [Feedback Loop]
                    |--enhances--> [Analytics Dashboard]

[Web Admin Panel]
    |--requires--> [Knowledge Base Viewing]
    |--enhances--> [Admin Review Gate]
    |--enhances--> [Analytics Dashboard]
    |--enhances--> [Source Management]

[Knowledge Gap Detection]
    |--requires--> [Telegram Q&A Bot] (needs query logs)
    |--requires--> [Analytics Dashboard]
```

### Dependency Notes

- **PII Anonymization is a hard prerequisite** for both PDF and Telegram ingestion. Must run first, before any data enters the pipeline.
- **SOP Generation requires Topic Clustering** -- you cannot generate coherent procedures from unclustered messages. Clustering groups related discussions together.
- **Admin Review Gate is the bridge** between auto-generated content and the RAG pipeline. Without it, garbage knowledge pollutes answers.
- **Analytics Dashboard enhances everything** but depends on the bot being live and collecting usage data. Build core features first, add analytics after.
- **Feedback Loop depends on the bot** -- can't collect feedback without users asking questions. Add thumbs up/down early (low cost) but analyze data later.

## MVP Definition

### Launch With (v1)

Minimum viable product -- what's needed to validate the concept.

- [ ] **PDF Document Ingestion** -- Primary document source. Most structured knowledge lives in PDFs (instructions, policies).
- [ ] **PII Anonymization (Presidio)** -- Legal requirement, must be in place before any processing.
- [ ] **Telegram Chat Log Parsing** -- Core differentiator. Parse JSON export, filter noise, reconstruct threads.
- [ ] **Vector Search / RAG Pipeline** -- Without this, the bot cannot answer questions. Embedding + retrieval + generation.
- [ ] **Telegram Q&A Bot** -- The user-facing product. Multi-turn context, source citation, confidence threshold fallback.
- [ ] **Basic Web Admin Panel** -- Source management (upload PDFs, import Telegram exports), user management, knowledge base view.
- [ ] **Admin Review Gate** -- Preview auto-extracted knowledge before it goes live. Even if minimal (approve/reject), this prevents trust-destroying errors.

### Add After Validation (v1.x)

Features to add once core pipeline works and real users interact with the system.

- [ ] **SOP Wiki Auto-Generation** -- Trigger: core RAG pipeline validated, admin confirms extracted knowledge is useful. Then invest in clustering + structured SOP generation.
- [ ] **Topic Clustering** -- Trigger: enough chat data ingested (weeks of logs). BERTopic or LLM-based clustering to auto-discover knowledge themes.
- [ ] **Incremental Knowledge Updates** -- Trigger: admin is manually re-running full pipeline on new data. Automate delta detection and incremental indexing.
- [ ] **Analytics Dashboard** -- Trigger: bot has active users generating query logs. Track questions, accuracy, knowledge gaps.
- [ ] **Feedback Loop (thumbs up/down)** -- Trigger: bot is live and answering real questions. Low effort, add early in v1.x.
- [ ] **Knowledge Gap Detection** -- Trigger: analytics data shows patterns of unanswered/low-confidence queries.

### Future Consideration (v2+)

Features to defer until product-market fit is established.

- [ ] **Multi-LLM Provider Switching** -- Defer: start with one proven provider (e.g., OpenAI API). Add abstraction layer when switching need is proven.
- [ ] **Real-Time Telegram Integration** (live streaming) -- Defer: JSON export workflow is sufficient. Add when periodic export becomes a bottleneck.
- [ ] **Video/Audio Transcription** -- Defer: explicitly out of scope. Add when text sources are exhausted and customers demand it.
- [ ] **Advanced Analytics** (trend analysis, predictive gaps) -- Defer: basic dashboard first. Advanced analytics when there's enough data history.
- [ ] **API for External Integrations** -- Defer: build for internal use first. API when customers want to integrate with their tools.
- [ ] **Multi-Tenant Architecture** -- Defer: single tenant validates the model. Multi-tenant when scaling to multiple customers.

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| PII Anonymization | HIGH (legal + trust) | MEDIUM | P1 |
| PDF Ingestion & Parsing | HIGH (primary source) | MEDIUM | P1 |
| Telegram Chat Log Parsing | HIGH (differentiator) | MEDIUM | P1 |
| Vector Search / RAG Pipeline | HIGH (core capability) | HIGH | P1 |
| Telegram Q&A Bot | HIGH (user-facing product) | HIGH | P1 |
| Source Citation in Answers | HIGH (trust) | MEDIUM | P1 |
| Confidence Threshold (fallback) | HIGH (safety) | LOW | P1 |
| Basic Web Admin Panel | HIGH (operability) | MEDIUM | P1 |
| Admin Review Gate | MEDIUM (quality control) | LOW | P1 |
| Topic Clustering | MEDIUM (enables SOP) | HIGH | P2 |
| SOP Wiki Auto-Generation | MEDIUM (core innovation) | HIGH | P2 |
| Incremental Knowledge Updates | MEDIUM (operational) | MEDIUM | P2 |
| Feedback Loop (thumbs) | MEDIUM (improvement signal) | LOW | P2 |
| Analytics Dashboard | MEDIUM (ROI proof) | MEDIUM | P2 |
| Knowledge Gap Detection | MEDIUM (actionable insights) | MEDIUM | P2 |
| Multi-LLM Flexibility | LOW (future-proofing) | MEDIUM | P3 |
| Real-Time Telegram Integration | LOW (nice to have) | HIGH | P3 |
| Video/Audio Transcription | LOW (out of scope) | HIGH | P3 |
| API for External Integrations | LOW (future) | MEDIUM | P3 |
| Multi-Tenant Architecture | LOW (scaling) | HIGH | P3 |

**Priority key:**
- P1: Must have for launch -- validates the core value proposition
- P2: Should have, add when possible -- enhances and proves value
- P3: Nice to have, future consideration -- premature before validation

## Competitor Feature Analysis

| Feature | Guru / Slite / Tettra | Glean | Dify.ai + Custom | V-Brain (Our Approach) |
|---------|----------------------|-------|-------------------|----------------------|
| Knowledge source | Manual wiki authoring | 100+ integrations (Slack, Confluence, etc.) | Any (custom pipeline) | **Telegram chats + PDFs** (auto-extracted) |
| Knowledge creation | Human-written articles | Indexes existing tools | Custom workflows | **Auto-generated from chat logs** (unique) |
| AI Q&A | Yes (from KB articles) | Yes (RAG across all sources) | Yes (RAG pipeline) | Yes (RAG from extracted + curated knowledge) |
| Language | English-first | English-first | Configurable | **Russian-first** |
| Target market | Mid-to-large enterprise | Enterprise (100+ seats) | Developers / technical teams | **SMB (5-50 employees)** |
| Deployment | Cloud SaaS | Cloud SaaS | Self-hosted or cloud | **Self-hosted / private cloud** |
| Admin panel | Yes (web) | Yes (enterprise admin) | Yes (Dify UI) | Yes (custom web admin) |
| PII handling | Enterprise-grade | SOC2, permissions | User responsibility | **Built-in Presidio anonymization** |
| Analytics | Basic (views, search) | Advanced (usage, permissions) | Pipeline metrics | **Question tracking, accuracy, gaps** |
| Pricing | $8-10/user/month | $12-30+/user/month (custom) | Open-source (infra cost) | **Custom deployment (one-time + infra)** |

**V-Brain's unique position:** No existing product auto-extracts knowledge from Telegram chats and generates structured SOPs for Russian-speaking SMBs. The closest comparison is a custom Dify.ai pipeline, but V-Brain is a purpose-built product, not a generic toolkit.

## Sources

- **Project Spec:** `Spec_V-Brain_AI_Automation.pdf` (technical specification v1.0, 2026)
- **Project Context:** `.planning/PROJECT.md` (requirements, constraints, decisions)
- **Competitor Analysis (training data):** Guru, Slite, Tettra, Glean feature comparisons
- **Dify.ai (training data):** Knowledge base features, RAG capabilities, workflow engine
- **Domain Knowledge (training data):** RAG system architecture, chat log NLP processing, SOP generation patterns
- **Web Search:** Partially rate-limited; supplemented with training data knowledge (MEDIUM confidence)

**Confidence note:** Web search was rate-limited during research. Competitor feature details and ecosystem patterns are based on training data (cutoff ~2025). Verify current features against live product pages before final decisions. The feature categorization (table stakes vs. differentiators) is HIGH confidence because it's derived from first principles of the RAG knowledge management domain and the specific V-Brain use case.

---
*Feature research for: AI Knowledge Extraction & RAG Mentor System (V-Brain)*
*Researched: 2026-04-17*
