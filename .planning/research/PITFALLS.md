# Pitfalls Research

**Domain:** RAG Knowledge Extraction & AI Mentor (Russian language, Telegram source, PDF source)
**Researched:** 2026-04-17
**Confidence:** MEDIUM (web search was rate-limited; findings combine training knowledge with partial web verification)

## Critical Pitfalls

### Pitfall 1: Garbage In, Garbage Out -- Skipping Data Quality Gates Before Embedding

**What goes wrong:**
Raw Telegram exports and PDFs are ingested directly into the vector index without cleaning. The result is a knowledge base polluted with greetings ("спасибо", "понял"), bot messages, service notifications (user joined/left), forwarded chain messages, PDF headers/footers/page numbers, and duplicated content. The AI mentor then retrieves noise and generates irrelevant or confusing answers. Users lose trust within the first few queries.

**Why it happens:**
Developers focus on the "exciting" parts (LLM generation, RAG pipeline) and treat data ingestion as a plumbing step. Telegram JSON exports look structured, so it feels like they should be clean. PDFs with text layers seem straightforward to extract. The impulse is to "just embed everything and let the LLM sort it out" -- but retrieval quality is 90% data quality.

**How to avoid:**
Build a dedicated preprocessing pipeline with explicit quality gates:
- Telegram: Filter out service messages, bot messages, messages shorter than N characters, forwarded chains without context, messages from excluded users (bots, spam). Deduplicate edited messages (keep latest version).
- PDFs: Strip headers, footers, page numbers. Detect and handle multi-column layouts. Use structure-aware extraction (not raw text dump). Flag low-confidence extractions for human review.
- Both: Compute a "knowledge density score" per chunk before embedding. Discard chunks below threshold or route them for manual review.
- Define acceptance criteria: every chunk entering the vector DB must have a source trace, a topic label, and a minimum information density score.

**Warning signs:**
- Vector DB contains more than 50% of total ingested messages/chunks (signal: most content is noise)
- Early QA tests show "not helpful" answers for common questions
- Retrieved chunks contain greetings, emoji-only messages, or raw PDF formatting artifacts
- Users say "it doesn't understand anything" after first interactions

**Phase to address:**
Phase 1 (Data Ingestion & Preprocessing) -- this is foundational. Every subsequent phase depends on clean data.

---

### Pitfall 2: Russian-Specific PII Anonymization Failure

**What goes wrong:**
Microsoft Presidio is configured with default settings, which are heavily English-centric. Russian names in declined forms ("Иванову", "Ивановой"), patronymics ("Александровна"), Russian phone formats ("+7", "8"), and Cyrillic addresses pass through unanonymized. The knowledge base contains real employee names, phone numbers, and other PII. When the AI mentor generates answers, it exposes this data to new employees -- a legal and trust disaster.

**Why it happens:**
Presidio's default recognizers are built for English. The spaCy models for Russian (`ru_core_news_sm`) have significantly lower NER F1 scores than English equivalents. Russian morphological complexity (6 cases, 3 genders, surname variations by gender) means a single person's name can appear in 10+ different forms. Regex patterns built for English phone/email formats miss Russian conventions. Developers assume "it works for English, it should work for Russian" without validation.

**How to avoid:**
- Use `ru_core_news_lg` (never `_sm`) for NER. Accept the performance cost.
- Build custom Russian recognizers for: patronymics, Russian phone formats (+7/8 prefixes, 10-digit local), INN (10-12 digits), SNILS (11 digits with check algorithm), Russian address patterns (ул., д., кв., г., обл.).
- Use a layered approach: NLP-based NER for names + regex for structured PII + custom rules for Russian-specific patterns.
- Consider complementing Presidio with Natasha or DeepPavlov for Russian NER, which have better Cyrillic coverage.
- Account for transliterated PII ("Ivanov" alongside "Иванов") if data contains both forms.
- Test with real Russian chat data, not translated English test cases. Measure recall/precision on a labeled sample before going to production.
- Set conservative confidence thresholds to avoid false negatives (missed PII is worse than false positives).

**Warning signs:**
- QA review finds unredacted names in anonymized output
- Anonymization recall < 95% on test data
- Using `ru_core_news_sm` or no Russian spaCy model at all
- No test suite with real Russian PII examples
- Phone numbers appearing in "anonymized" text in formats not covered by default recognizers

**Phase to address:**
Phase 1 (Data Ingestion & Preprocessing) -- anonymization must happen before any data enters the pipeline. No downstream component should ever see raw PII.

---

### Pitfall 3: Naive Chunking Destroys Russian Semantic Coherence

**What goes wrong:**
Fixed-size character or token chunking splits Russian text mid-sentence, breaks apart inflected forms of the same concept, and separates verbs from their complements across chunk boundaries. Retrieval returns chunks that are semantically incomplete, leading to the AI mentor giving fragmented or incorrect answers. Queries about multi-step processes retrieve only partial steps.

**Why it happens:**
Russian is a free-word-order language with rich morphology. A single concept can be expressed across a longer span than in English (due to case markers, participles, subordinate clauses). Fixed-size chunking optimized for English text lengths produces worse results for Russian. Tokenizers (even multilingual ones) are less efficient with Cyrillic, so a "500 token" chunk contains fewer Russian words than 500 English words.

**How to avoid:**
- Use semantic chunking (embedding-based) rather than fixed-size character/token chunking.
- If using sentence-level splitting, use a Russian-aware sentence splitter (spaCy with `ru_core_news_lg` or DeepPavlov) -- not `nltk.sent_tokenize` which is English-optimized.
- Include overlap windows between chunks (20-30%) to preserve context across boundaries.
- Use token-count-based limits (not character-count) to account for Cyrillic tokenization inefficiency.
- Validate chunk quality: after chunking, check that each chunk is a self-contained semantic unit. Discard or merge chunks that are clearly fragments.
- For SOP-like content (step-by-step processes), use structure-aware chunking that keeps complete procedures together.

**Warning signs:**
- Retrieved chunks end mid-sentence or mid-thought
- Users ask follow-up questions because initial answers feel incomplete
- Embedding similarity scores are lower than expected for clearly relevant content
- Chunks contain dangling prepositions, orphaned verbs, or incomplete procedures

**Phase to address:**
Phase 1 (Data Ingestion & Preprocessing) -- chunking strategy must be validated before indexing.

---

### Pitfall 4: English-Centric Embedding Model for Russian Content

**What goes wrong:**
The system uses an English-focused embedding model (or even a multilingual model without Russian-specific tuning) to embed Russian text. Vector similarity search returns irrelevant chunks because the model doesn't capture Russian semantic nuances. Questions phrased differently from the source text ("как оформить возврат?" vs "процесс возврата товара") fail to match despite being semantically identical.

**Why it happens:**
Multilingual embedding models advertise "100+ languages" support, but quality varies dramatically. Some models essentially translate to English before embedding, losing Russian-specific meaning. Developers pick a popular model (e.g., `text-embedding-ada-002`) without benchmarking on Russian retrieval tasks.

**How to avoid:**
- Use embeddings specifically validated for Russian: `intfloat/multilingual-e5-large`, `LaBSE`, Cohere multilingual embed v3, or OpenAI `text-embedding-3-large` (which has improved multilingual support).
- Benchmark at least 2-3 embedding models on a held-out set of Russian question-chunk pairs before committing.
- Measure retrieval quality with Russian-specific queries, not just similarity scores on random chunks.
- If using a local LLM deployment, ensure the embedding model matches the deployment strategy (some models require API access).

**Warning signs:**
- Retrieval returns chunks with high cosine similarity that are clearly irrelevant to the query
- Paraphrased questions ("другими словами") fail to retrieve relevant content
- Users report "it doesn't find things I know are in the knowledge base"
- Benchmark retrieval recall@5 is below 0.7 on Russian test queries

**Phase to address:**
Phase 1 (Data Ingestion & Preprocessing) -- embedding model choice is locked in at indexing time. Switching later requires full reindex.

---

### Pitfall 5: No "I Don't Know" Fallback -- Hallucinated Answers Destroy Trust

**What goes wrong:**
When a new employee asks a question not covered by the knowledge base, the AI mentor fabricates a plausible-sounding answer instead of admitting it doesn't know. The employee acts on incorrect information, causing real business mistakes (wrong CRM workflow, incorrect pricing, violated compliance). After 2-3 such incidents, users stop trusting the bot entirely and go back to asking the owner directly -- defeating the product's core value.

**Why it happens:**
LLMs are biased toward being "helpful" and will confidently generate answers even with zero relevant context. Simply prompting "answer only from the provided context" is insufficient -- models routinely ignore this instruction under pressure. Developers don't implement programmatic checks because the demo looks better when the bot "always has an answer."

**How to avoid:**
Implement a multi-layered confidence pipeline:
1. **Retrieval quality gate**: If no chunk exceeds a similarity threshold (e.g., 0.65-0.7), return a fallback response immediately -- do not send to the LLM.
2. **Context relevance check**: Before generation, verify that retrieved chunks are topically relevant to the query (can be a lightweight classifier or LLM-based check).
3. **Structured output**: Force the LLM to output JSON with a `has_answer: bool` field. Only surface the answer if `has_answer === true`.
4. **Cascading fallbacks**: Tier 1 -- confident answer from context. Tier 2 -- "I found partial information..." with caveat. Tier 3 -- "I don't have this information. Please ask [owner/manager]." Optionally log the unanswered question for knowledge base enrichment.
5. **Post-generation verification**: Use faithfulness scoring (RAGAS or similar) on a sample of responses in production.

**Warning signs:**
- Demo works perfectly but production users report incorrect answers
- No similarity threshold configured on retrieval
- System prompt says "answer from context" but there's no programmatic enforcement
- No logging of unanswered or low-confidence queries
- Users stop using the bot after initial enthusiasm

**Phase to address:**
Phase 2 (RAG Pipeline & Bot) -- the fallback must be built into the bot from day one, not bolted on after users complain.

---

### Pitfall 6: SOP Generation from Chat Logs Produces Unusable or Wrong Procedures

**What goes wrong:**
The LLM synthesizes SOPs from Telegram conversations that contain incomplete information, outdated practices, contradictory instructions from different people, and implicit context that doesn't survive extraction. The generated SOPs look professional in Markdown but contain wrong steps, missing prerequisites, or describe how things used to work (not how they work now). New employees follow these SOPs and make mistakes.

**Why it happens:**
Chat logs capture work-in-progress discussions, not finalized procedures. Person A says "we do X" but Person B later says "actually we changed to Y." The LLM has no way to determine temporal ordering or authority. It averages conflicting information or picks whichever was stated more confidently. Moreover, critical steps are often implicit ("everyone knows you need to do Z first") and never mentioned in chat.

**How to avoid:**
- Treat LLM-generated SOPs as drafts, not final documents. Build a human review workflow into the pipeline.
- Include confidence scores and source traces with every generated SOP. Flag SOPs assembled from few or conflicting sources.
- Implement temporal awareness: weight more recent messages higher. If the same process is described differently over time, note the evolution.
- Define minimum evidence thresholds: an SOP should not be generated from a single message or a single conversation thread.
- Include a "gaps" section in each SOP that explicitly lists assumptions and information that could not be verified from sources.
- Build feedback mechanism: allow employees to flag incorrect SOP steps, creating a correction loop.

**Warning signs:**
- Generated SOPs have no source attribution
- SOPs are published to the knowledge base without human review
- No confidence scores or quality metrics on generated content
- Single conversation thread produces a full SOP
- No mechanism for employees to report incorrect procedures

**Phase to address:**
Phase 1 (Data Ingestion & Preprocessing) for the extraction logic, Phase 3 (Web Admin) for the review workflow. The review workflow is what makes generated SOPs safe for consumption.

---

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Embed everything without quality filtering | Faster time to first demo | Polluted vector DB, low retrieval quality, expensive to clean later | Never -- even in MVP, basic filtering (service messages, very short messages) is essential |
| Use Dify.ai visual workflows for the entire pipeline | No code needed, fast prototyping | Becomes unmaintainable for complex logic, hard to debug, limited customization for Russian-specific needs | MVP prototyping only. Production pipeline should use code with Dify for orchestration, not the entire logic |
| Skip evaluation framework | Saves 1-2 weeks of development | No way to measure if changes improve or degrade quality, invisible regressions | First MVP demo only. Implement basic retrieval evaluation (recall@5 on test queries) before any user testing |
| Use a single LLM for all tasks (extraction, SOP generation, answering) | Simpler architecture, one model to manage | Different tasks need different prompting strategies, temperature settings, and model sizes. One-size-fits-all produces mediocre results everywhere | Only if using a strong API model (GPT-4, Claude). Dangerous with local models that have limited capability |
| Hard-code LLM provider | Faster integration, less abstraction | Cannot switch providers, locked into pricing/viability of one vendor, cannot compare models | Never -- the project explicitly requires flexible LLM provider. Build an abstraction layer from day one |
| Store all embeddings in a flat namespace | Simpler retrieval logic | Cannot filter by source type, topic, date, or access level. All future features require reindex | Acceptable for MVP with <10k chunks. Must add metadata filtering before scaling |
| Ignore Telegram message threading | Simpler parsing | Loses conversation context, cannot determine which messages are related, produces fragmented knowledge extraction | Never -- reply chains contain critical context. At minimum, group messages by reply_to_message_id |

## Integration Gotchas

Common mistakes when connecting to external services.

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| Telegram JSON export | Assuming all messages have `text` field. Media messages, service messages, deleted messages have no text or different structure. | Check `type` field. Only process `text`-containing messages. Handle `photo`, `document`, `voice` separately or skip. Handle edited messages by keeping latest `edit_date` version. |
| Telegram JSON export | Not handling the `from_id` format variations (user vs group vs channel). | Parse `from_id` type prefix. Map to consistent internal user identifiers. Handle anonymous admins. |
| PDF parsing (pdfplumber/PyMuPDF) | Extracting raw text without detecting multi-column layouts, tables, headers/footers. Reading across columns instead of down. | Use layout-aware extraction (Unstructured.io, LlamaParse). For simple PDFs, validate extraction quality by checking reading order. |
| PDF parsing (scanned PDFs) | Attempting text extraction from image-only PDFs, getting empty results. | Detect if PDF has text layer (check `extract_text()` output). Route image-only pages to OCR (Tesseract with Russian language pack, or cloud OCR with Cyrillic support). |
| Microsoft Presidio | Using default English recognizers without adding Russian patterns. | Register custom recognizers for Russian phone, email, address, name patterns. Use `ru_core_news_lg` spaCy model. Test on real Russian data. |
| Vector DB (Qdrant/Chroma/pgvector) | Not setting HNSW parameters (`ef_search`, `ef_construction`, `M`) appropriately. Default parameters may be suboptimal for your data size. | Tune HNSW parameters based on dataset size. For <100k vectors, increase `ef_search` for better recall. For >1M vectors, consider quantization. |
| Dify.ai | Using Dify as the entire application instead of just the orchestration layer. | Use Dify for workflow orchestration and LLM calling. Keep custom preprocessing, PII anonymization, and Russian-specific logic in Python code. |
| LLM API (OpenAI/Anthropic) | Not handling rate limits, token limits, and API errors gracefully. The bot crashes or returns cryptic errors to users. | Implement retry with exponential backoff. Handle context length limits by truncating or summarizing. Return user-friendly error messages in Russian. |

## Performance Traps

Patterns that work at small scale but fail as usage grows.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Synchronous RAG pipeline (embed query -> search -> generate -> respond) | Users wait 5-15 seconds for answers. Telegram request times out. | Pre-compute common queries. Use streaming responses. Cache frequent Q&A pairs. Implement semantic caching (similar queries hit cache). | >10 concurrent users or >1000 indexed chunks |
| Re-embedding entire corpus on every update | Ingestion takes hours. System is unavailable during reindex. | Implement incremental indexing. Only embed and index new/changed chunks. Track chunk versions in metadata. | >500 chunks or updates more frequent than daily |
| Loading full conversation history for context | Context window fills up. API costs explode. Response quality degrades ("lost in the middle"). | Keep conversation context to last N turns (3-5). Use summarization for longer conversations. Each query should be self-contained enough for retrieval. | After 10+ messages in a single conversation |
| No pagination in vector search | Returning top-50 chunks when 5 would suffice. LLM gets confused by too much context. Slow generation. | Use top-k with k=5-10 for most queries. Implement re-ranking to find the best 3-5 chunks. Let the LLM ask for more context if needed. | Any scale -- this is about quality, not just performance |
| SQLite or flat file storage for metadata | Concurrent writes fail. Data corruption under load. No query flexibility for admin features. | Use PostgreSQL from the start (even for MVP). pgvector gives you both relational data and vector search in one DB. | >100 chunks or any concurrent access |

## Security Mistakes

Domain-specific security issues beyond general web security.

| Mistake | Risk | Prevention |
|---------|------|------------|
| PII in vector embeddings | Even after anonymizing source text, embeddings may encode PII patterns. An adversary with embedding access could potentially reverse-engineer personal data. | Anonymize BEFORE embedding. Never embed raw text. Ensure anonymization is irreversible (one-way token mapping). |
| Anonymization mapping stored in plaintext | If the PII-to-token mapping is stored insecurely, anyone with DB access can de-anonymize all data. | Encrypt the mapping table. Restrict access. Consider if the mapping needs to persist at all (one-way hashing may suffice for most use cases). |
| Telegram bot token in code repository | Bot token compromised. Attacker can impersonate the bot, read all messages, send spam. | Store in environment variables or secrets manager. Never commit to git. Rotate tokens regularly. |
| No rate limiting on bot queries | A user (or attacker) can flood the bot with queries, exhausting LLM API quota or running up costs. | Implement per-user rate limiting. Set daily/monthly query budgets. Return "too many requests" gracefully. |
| Web admin panel without authentication | Anyone with the URL can view/edit the knowledge base, manage users, or access analytics. | Implement authentication from day one (even simple username/password for MVP). Use HTTPS. |
| Knowledge base accessible to unauthorized employees | New employees can query any knowledge, including restricted information (salaries, disciplinary actions, executive discussions). | Implement document-level or topic-level access control. Not all extracted knowledge should be available to all users. |
| LLM API key exposure | If using cloud LLM APIs, exposed keys allow unlimited usage on your account. | Same as bot token: environment variables, secrets manager, never in git. Monitor API usage for anomalies. |
| Log retention of raw queries | User queries may themselves contain sensitive information. Logging everything creates a privacy liability. | Sanitize or hash query logs. Define retention policies. Auto-delete old logs. |

## UX Pitfalls

Common user experience mistakes in this domain.

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Bot responds with wall of text | New employees are overwhelmed, can't find the specific answer. TL;DR effect. | Keep answers concise. Use formatting (bold, lists). Offer "tell me more" for detail. Structure: short answer first, then supporting details. |
| Bot speaks in formal/bureaucratic Russian | Feels like reading a manual, not talking to a helpful mentor. Users disengage. | Use natural conversational Russian. Match the tone of the company's communication style. Avoid excessive passive voice and compound sentences. |
| No feedback mechanism | Users can't report wrong answers. Incorrect information persists indefinitely. | Add "Was this helpful?" buttons. Allow "This is wrong" reports with optional correction. Route feedback to knowledge base curator. |
| Bot doesn't remember conversation context | User asks follow-up question ("а если клиент не отвечает?") and bot treats it as a new query. | Maintain conversation context for 3-5 turns. Reference previous messages when processing follow-ups. |
| No onboarding for the bot itself | New employees don't know what the bot can do, what kinds of questions to ask, or how to phrase them. | Show a welcome message with example questions. Suggest question categories ("Попробуйте спросить: ..."). Handle vague queries by offering categories. |
| Bot is silent during processing | User sends a question, nothing happens for 5-10 seconds. User thinks it's broken and asks again (creating duplicate queries). | Send a "typing" indicator (Telegram supports this). Or send an immediate acknowledgment ("Ищу информацию..."). Stream the answer if possible. |
| Generic "I don't know" with no guidance | User gets "Я не нашёл ответ" and has no idea what to do next. | Always provide next steps: "Попробуйте переформулировать вопрос" or "Этот вопрос лучше задать [имя]" or offer related topics the bot CAN answer. |
| No search history or favorites | User found a great answer last week but can't find it again. Has to re-ask. | Save conversation history. Allow bookmarking useful answers. Provide "recent questions" for quick access. |

## "Looks Done But Isn't" Checklist

Things that appear complete but are missing critical pieces.

- [ ] **PII Anonymization:** Often missing Russian patronymics, declined name forms, and +7/8 phone variants -- verify with real Russian chat data, not English test cases
- [ ] **Telegram Parsing:** Often missing handling of edited messages (keeps old version), deleted messages (empty entries), service messages (join/leave/pin), and reply threading -- verify by exporting a real active chat and checking edge cases
- [ ] **PDF Extraction:** Often missing multi-column layout detection, table extraction, header/footer stripping, and scanned page OCR routing -- verify by testing on the actual company PDFs, not clean digital documents
- [ ] **Chunking:** Often missing overlap windows, sentence boundary validation, and Russian-specific splitting -- verify by manually inspecting 50+ random chunks for semantic completeness
- [ ] **Embedding Quality:** Often missing benchmark on Russian queries -- verify by creating 20 real user questions and measuring whether correct chunks appear in top-5 retrieval results
- [ ] **RAG Fallback:** Often missing retrieval similarity threshold, "I don't know" logic, and low-confidence handling -- verify by asking questions definitely NOT in the knowledge base and checking bot response
- [ ] **SOP Quality:** Often missing source attribution, confidence scores, and human review workflow -- verify by having a domain expert review 5 generated SOPs for accuracy
- [ ] **Bot Error Handling:** Often missing graceful handling of LLM API errors, timeouts, and rate limits -- verify by temporarily breaking the API connection and checking what the user sees
- [ ] **Conversation Context:** Often missing multi-turn context handling -- verify by having a conversation: ask a question, then ask a follow-up referencing the previous answer
- [ ] **Evaluation Pipeline:** Often missing entirely -- verify by asking "how do we know if a change improved or degraded answer quality?"

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Polluted vector DB (noise in embeddings) | MEDIUM | 1. Identify noise patterns (service messages, short messages, etc.). 2. Build filter criteria. 3. Delete matching vectors. 4. Re-ingest clean data. 5. Validate retrieval quality after cleanup. |
| PII leaked into knowledge base | HIGH | 1. Immediately disable bot access. 2. Identify scope of exposure (which documents, which users saw what). 3. Re-run anonymization on all source data with improved rules. 4. Full reindex. 5. Notify affected parties if required by policy. 6. Add anonymization quality tests to prevent recurrence. |
| Wrong embedding model chosen | MEDIUM-HIGH | 1. Benchmark alternative models on held-out Russian test set. 2. Select better model. 3. Full reindex (this is the expensive part -- cannot update embeddings in place). 4. Validate retrieval quality. Mitigation: test multiple models before first index to avoid this. |
| Users lost trust due to hallucinations | HIGH | 1. Implement "I don't know" fallback and confidence thresholds immediately. 2. Audit all previously generated answers for accuracy (sample-based). 3. Communicate transparently about improvements. 4. Add feedback mechanism. 5. Trust recovery takes weeks -- prevention is critical. |
| SOPs contain incorrect procedures | HIGH | 1. Remove all auto-generated SOPs from active knowledge base. 2. Route through human review workflow. 3. Mark reviewed SOPs as "verified." 4. Implement versioning -- old versions should be accessible but not active. 5. Add employee feedback mechanism for reporting errors. |
| Dify.ai workflow becomes unmaintainable | MEDIUM | 1. Extract critical custom logic (Russian preprocessing, PII rules) into Python code. 2. Use Dify only for high-level orchestration (LLM calls, workflow steps). 3. Test that extraction doesn't break functionality. 4. Keep Dify workflows simple and well-documented. |
| Chat log context lost (no threading) | MEDIUM | 1. Re-parse source data with threading awareness (group by reply_to_message_id). 2. Re-extract knowledge from threaded conversations. 3. Re-index. Mitigation: always parse threads from the start. |

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Garbage In, Garbage Out (data quality) | Phase 1: Data Ingestion & Preprocessing | Ingest a real Telegram export and a real company PDF. Manually review 100 random chunks entering the vector DB. Zero noise tolerance. |
| Russian PII anonymization failure | Phase 1: Data Ingestion & Preprocessing | Run anonymization on a labeled Russian test set (100 messages with known PII). Recall must be >= 95%, precision >= 90%. |
| Naive chunking destroys coherence | Phase 1: Data Ingestion & Preprocessing | Manually inspect 50 random chunks. Every chunk must be a self-contained semantic unit. No mid-sentence splits. |
| English-centric embeddings | Phase 1: Data Ingestion & Preprocessing | Benchmark: create 20 Russian question-chunk pairs. Recall@5 must be >= 0.7. |
| No "I don't know" fallback | Phase 2: RAG Pipeline & Telegram Bot | Ask 10 questions NOT in the knowledge base. Bot must gracefully decline on >= 9/10. |
| SOP generation quality | Phase 1 (extraction logic), Phase 3 (review workflow) | Domain expert reviews 5 generated SOPs. At least 80% of steps must be accurate. All must have source traces. |
| Dify workflow complexity | Phase 2: RAG Pipeline & Telegram Bot | Custom logic (PII, preprocessing, Russian-specific) lives in Python code, not Dify visual workflows. |
| No evaluation framework | Phase 2: RAG Pipeline & Telegram Bot | Retrieval recall@5 and answer faithfulness scores are computed and logged for every test query. |
| Bot UX problems | Phase 2: RAG Pipeline & Telegram Bot | 5 real users (not developers) test the bot. Collect feedback on clarity, helpfulness, and frustration points. |
| Missing error handling | Phase 2: RAG Pipeline & Telegram Bot | Simulate API failure, timeout, and rate limit. Bot must return user-friendly Russian error messages. |
| Security gaps (auth, rate limiting) | Phase 3: Web Admin | Admin panel requires login. Bot has per-user rate limiting. API keys are in env vars, not code. |
| No access control on knowledge | Phase 3: Web Admin | Verify that document-level or topic-level restrictions can be applied to retrieved knowledge. |

## Sources

- Web search (rate-limited; partial results): RAG pitfalls 2025-2026, Dify.ai limitations, PDF parsing challenges, vector DB comparisons
- Microsoft Presidio GitHub: language support documentation, recognizer patterns
- Natasha / DeepPavlov: Russian NLP library capabilities for NER
- RAGAS evaluation framework: retrieval quality metrics
- Project spec: `Spec_V-Brain_AI_Automation.pdf` -- technical requirements, architecture
- PROJECT.md: project constraints, validated requirements, key decisions
- Training knowledge: RAG system design patterns, production failure modes, Russian NLP challenges

---
*Pitfalls research for: V-Brain AI Knowledge Extractor & Mentor*
*Researched: 2026-04-17*
