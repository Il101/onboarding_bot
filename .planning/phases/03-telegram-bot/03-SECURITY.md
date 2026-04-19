---
phase: 3
slug: telegram-bot
status: verified
threats_open: 0
asvs_level: 2
created: 2026-04-19
---

# Phase 3 — Security

> Per-phase security contract: threat register, accepted risks, and audit trail.

---

## Trust Boundaries

| Boundary | Description | Data Crossing |
|----------|-------------|---------------|
| Telegram user input -> auth policy | Untrusted chat/user metadata enters authorization logic | `chat_id`, `user_id`, message/update payload |
| callback payload -> feedback persistence | User-controlled callback data reaches DB write path | vote payload + linkage metadata |
| graph state -> retrieval API | Thread-scoped state crosses network boundary to knowledge API | query text, top_k, context metadata |
| retrieval payload -> decision/answer nodes | Partially trusted retrieval envelope enters policy-critical logic | `answer`, `confidence`, `sources`, `fallback_used` |
| Telegram transport -> user-visible output | Internal exceptions and policy outputs become external responses | rendered response text and source snippets |

---

## Threat Register

| Threat ID | Category | Component | Disposition | Mitigation | Status |
|-----------|----------|-----------|-------------|------------|--------|
| T-03-01 | E | `src/bot/auth.py` | mitigate | Role allowlist gate before retrieval/LLM invocation; deny-first flow | closed |
| T-03-02 | T | `src/bot/feedback.py` | mitigate | Validate callback payload and reject malformed/replayed callback events before DB write | closed |
| T-03-03 | I | `src/ai/langgraph/state.py` | mitigate | Strict Pydantic contracts (`SourceRef` locator, `BotAnswer.sources`) for grounded response envelopes | closed |
| T-03-04 | T | `src/ai/langgraph/nodes/decide.py` | mitigate | Deterministic branch order and locked fallback phrase before any answer generation | closed |
| T-03-05 | I | `src/ai/langgraph/nodes/summarize.py` | mitigate | Per-thread isolation + bounded context trimming with latest user message retention | closed |
| T-03-06 | D | `src/ai/langgraph/nodes/retrieve_phase2.py` | mitigate | Timeout/retry bounds and `top_k` cap for retrieval calls | closed |
| T-03-07 | R | `src/ai/langgraph/nodes/answer.py` | mitigate | Preserve source metadata and conflict markers for post-hoc traceability | closed |
| T-03-08 | S | `src/bot/telegram_app.py` | mitigate | `/start` role validation before graph path + thread binding by chat/user | closed |
| T-03-09 | T | `src/bot/presenters.py` | mitigate | Centralized formatter always appends `Источники` and preserves locked fallback text | closed |
| T-03-10 | R | `src/bot/feedback.py` | mitigate | Persist vote with thread/message linkage and timestamp for auditability | closed |
| T-03-11 | I | `src/bot/telegram_app.py` | mitigate | Mask runtime exceptions with safe Russian error response (no traceback leaks) | closed |

*Status: open · closed*
*Disposition: mitigate (implementation required) · accept (documented risk) · transfer (third-party)*

---

## Accepted Risks Log

No accepted risks.

---

## Security Audit Trail

| Audit Date | Threats Total | Closed | Open | Run By |
|------------|---------------|--------|------|--------|
| 2026-04-19 | 11 | 9 | 2 | gsd-security-auditor |
| 2026-04-19 | 11 | 11 | 0 | gsd-security-auditor |

---

## Open Threats (Blockers)

None.

---

## Sign-Off

- [x] All threats have a disposition (mitigate / accept / transfer)
- [x] Accepted risks documented in Accepted Risks Log
- [x] `threats_open: 0` confirmed
- [x] `status: verified` set in frontmatter

**Approval:** verified — threats mitigated, security gate passed
