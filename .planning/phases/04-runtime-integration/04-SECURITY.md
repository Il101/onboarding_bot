---
phase: 04-runtime-integration
slug: runtime-integration
status: verified
threats_open: 0
asvs_level: 1
created: 2026-04-19
---

# Phase 04 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| ingest task payload -> extraction orchestration | Untrusted source content crosses into async pipeline dispatch | source_id, chunks payload |
| extraction output -> indexing | Generated units cross from model output to persistent vector store | publishable knowledge units |
| user query -> retrieval backend | Untrusted input enters retrieval and synthesis path | query text, retrieval candidates |
| retrieval metadata -> API response | Internal source payload is exposed to bot/API consumers | source attribution fields |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-04-01 | T | `src/tasks/ingest.py` | mitigate | Validate source_id/chunks before dispatch via `_validate_source_id` and `_validate_chunks_for_dispatch`; fail task on malformed payload. | closed |
| T-04-02 | I | `src/tasks/knowledge.py` | mitigate | Enforce confidence gate (`publishable` only), and dispatch SOP only when grouped publishable units exist. | closed |
| T-04-03 | D | `src/tasks/ingest.py` | mitigate | Bounded retries (`max_retries=3`) and explicit `FAILURE` state on exceptions. | closed |
| T-04-04 | I | `src/api/routes/knowledge.py` | mitigate | Preserve attribution contract (`source_id`, `excerpt`, locator fields) in response sources. | closed |
| T-04-05 | T | `src/ai/rag/retriever.py` | mitigate | Remove static seed path; build candidates from retrieval backend only. | closed |
| T-04-06 | D | `src/api/routes/knowledge.py` | mitigate | Enforce bounded `top_k` validation and return safe fallback envelope on retrieval errors. | closed |

*Status: open · closed*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

No accepted risks.

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-04-19 | 6 | 6 | 0 | gsd-security-auditor + Copilot CLI |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-04-19
