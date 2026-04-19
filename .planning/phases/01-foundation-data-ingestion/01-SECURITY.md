---
phase: 1
slug: foundation-data-ingestion
status: verified
threats_open: 0
asvs_level: 1
created: 2026-04-18
---

# Phase 1 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| User -> REST API upload | Admin uploads JSON/PDF/OGG over API endpoints | Untrusted file content (potentially malformed or malicious) |
| API -> Celery tasks | API dispatches ingestion work with file paths | Task metadata and internal filesystem paths |
| Raw text/audio -> Anonymization/Transcription | Telegram/PDF/audio content enters preprocessing | Sensitive business text and possible PII |
| Application -> Qdrant/Redis/PostgreSQL | Internal service-to-service communication in dev stack | Anonymized chunks, vectors, task/job metadata |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-01-01 | Tampering | File upload endpoints | mitigate | Extension + content validation, size checks, UUID filenames in `src/api/routes/ingest.py` | closed |
| T-01-02 | Denial of Service | File upload endpoints | mitigate | Global upload size guard via `settings.max_file_size_mb` and `_validate_size` | closed |
| T-01-03 | Information Disclosure | docker-compose.yml | accept | Local dev credentials only; production overrides required (see accepted risk A-01) | closed |
| T-01-04 | Information Disclosure | .env file | mitigate | `.env` excluded by `.gitignore`; only `.env.example` committed | closed |
| T-01-05 | Tampering | docker-compose exposed ports | accept | Local dev exposure accepted; production requires network hardening (A-02) | closed |
| T-01-06 | Tampering | Telegram JSON parser | mitigate | Malformed JSON handling + schema checks + `telegram_max_messages` cap in parser | closed |
| T-01-07 | Information Disclosure | Telegram parser output | mitigate | PII anonymization enforced before filter/chunk/index in ingestion task flow | closed |
| T-01-08 | Tampering | PDF parser | mitigate | Parser-level `.pdf` check + size limit + `%PDF-` signature validation before Docling | closed |
| T-01-09 | Information Disclosure | Groq Whisper API | accept | External audio processing accepted for Phase 1 (A-03) | closed |
| T-01-10 | Denial of Service | Groq API calls | mitigate | Celery retry policy + large audio chunking/fallback path | closed |
| T-01-11 | Information Disclosure | token_mapping.py | mitigate | Token mapping remains in-memory; no persistence implemented | closed |
| T-01-12 | Information Disclosure | Logging | mitigate | Presidio logs suppressed to WARNING, no raw payload logging in ingestion path | closed |
| T-01-13 | Tampering | PII false negatives | accept | Residual recall gap accepted pending real-data validation (A-04) | closed |
| T-01-14 | Denial of Service | Embedding generation | accept | Heavy embedding load accepted for async worker path in Phase 1 (A-05) | closed |
| T-01-15 | Tampering | Qdrant data integrity | accept | Single-tenant trust model accepted; reingest overwrite pattern used (A-06) | closed |
| T-01-16 | Information Disclosure | Qdrant payload | mitigate | Only anonymized text enters indexing payload | closed |
| T-01-17 | Tampering | File upload endpoints | mitigate | Strict type/content validation for JSON/PDF/OGG + explicit 400/413 responses | closed |
| T-01-18 | Tampering | File path traversal | mitigate | UUID storage names and isolated upload directory prevent traversal | closed |
| T-01-19 | Denial of Service | Concurrent uploads | accept | No rate limiting in Phase 1 accepted for single-tenant admin usage (A-07) | closed |
| T-01-20 | Information Disclosure | API error messages | mitigate | Failure status masks internal exception details to generic `"Task failed"` | closed |
| T-01-21 | Tampering | job_id in status endpoint | accept | Unauthenticated status endpoint accepted for Phase 1; auth deferred to later phases (A-08) | closed |

*Status: open · closed*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

| Risk ID | Threat Ref | Rationale | Accepted By | Date |
|---------|------------|-----------|-------------|------|
| A-01 | T-01-03 | Default postgres credentials are used only for local development docker stack; production deploy must override secrets. | project owner | 2026-04-18 |
| A-02 | T-01-05 | Exposed service ports are acceptable in local single-operator environment; production network policy out of Phase 1 scope. | project owner | 2026-04-18 |
| A-03 | T-01-09 | Groq Whisper is external processing; accepted for MVP with later option to move to fully local stack. | project owner | 2026-04-18 |
| A-04 | T-01-13 | Russian NER/regex may miss edge-case PII; mitigated later by real-data validation cycle. | project owner | 2026-04-18 |
| A-05 | T-01-14 | Embedding CPU load is handled asynchronously and acceptable for current usage profile. | project owner | 2026-04-18 |
| A-06 | T-01-15 | Qdrant integrity relies on single-tenant trust and delete/upsert strategy in MVP scope. | project owner | 2026-04-18 |
| A-07 | T-01-19 | Upload concurrency/rate-limits deferred; acceptable for internal admin-only usage at this stage. | project owner | 2026-04-18 |
| A-08 | T-01-21 | Job status endpoint authorization deferred to auth phase; UUID job IDs considered sufficient interim control. | project owner | 2026-04-18 |

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-04-18 | 21 | 12 | 9 | gsd-security-auditor |
| 2026-04-18 | 21 | 21 | 0 | copilot-cli + gsd-security-auditor |

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified 2026-04-18
