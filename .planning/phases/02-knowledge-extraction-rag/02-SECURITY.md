---
phase: 2
slug: knowledge-extraction-rag
status: verified
threats_open: 0
asvs_level: 1
created: 2026-04-18
---

# Phase 2 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Qdrant indexed knowledge -> Extraction pipeline | Retrieved indexed knowledge becomes LLM extraction input | Internal anonymized chunks/metadata |
| Extraction/SOP services -> API response | Generated SOP and answers returned to callers | Potentially sensitive internal business procedures |
| User query -> Knowledge endpoint | Untrusted request payload into RAG stack | Query text and retrieval parameters |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-02-01 | T | `src/ai/extraction/schemas.py` | mitigate | Strict schema validation with locator requirement (`timestamp` or `page`) | closed |
| T-02-02 | R | `src/ai/rag/contracts.py` | mitigate | Typed attribution contract enforces `source_id`, `excerpt`, `score`, locator fields | closed |
| T-02-03 | I | `src/ai/extraction/publish_policy.py` | mitigate | Confidence gate blocks low-confidence knowledge publication with explicit reason | closed |
| T-02-04 | T | `src/ai/extraction/extractor.py` | mitigate | All extraction outputs validated through `KnowledgeUnit.model_validate` before grouping/publish | closed |
| T-02-05 | I | `src/ai/sop/generator.py` | mitigate | SOP generated from publishable validated units with attribution for every operational reference | closed |
| T-02-06 | D | `src/tasks/knowledge.py` | mitigate | Celery retries + progress/failure states prevent silent stalls and support recovery | closed |
| T-02-07 | T | `src/ai/rag/synthesizer.py` | mitigate | Relevance threshold gate blocks low-relevance answer generation and returns fallback path | closed |
| T-02-08 | I | `src/ai/rag/attribution.py` | mitigate | Attribution formatter emits complete source fields; contract tests enforce coverage | closed |
| T-02-09 | D | `src/api/routes/knowledge.py` | mitigate | Request schema validates `top_k` with config-bound upper limit (`rag_hybrid_top_k`) to constrain expensive queries | closed |

*Status: open · closed*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

No accepted risks.

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-04-18 | 9 | 8 | 1 | gsd-security-auditor |
| 2026-04-18 | 9 | 9 | 0 | copilot-cli + gsd-security-auditor |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-04-18
