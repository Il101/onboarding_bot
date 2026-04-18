# Phase 1: Foundation & Data Ingestion - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-18
**Phase:** 1-foundation-data-ingestion
**Areas discussed:** Data intake flow, PII strategy, Noise filtering, Chunking strategy

---

## Data Intake Flow

| Option | Description | Selected |
|--------|-------------|----------|
| REST API | API endpoints for ingestion, Phase 4 adds web form on top | ✓ |
| File watcher | Auto-detect files in directory | |
| Manual script | Throw files in folder, run script | |
| All of the above | Every option available | |

**User's choice:** Пользователь хочет drag & drop загрузку в вебку
**Follow-up:** Предложены варианты: API first (рекомендовано), simple web upload in P1, merge phases
**Decision:** API first — Phase 1 строит REST API, Phase 4 добавляет веб-форму

## PII Strategy

| Question | Options | Decision |
|----------|---------|----------|
| PII types | Names, Phones, Email, Addresses, Doc numbers | All selected + Doc numbers |
| Token format | Readable tokens, Generic tokens, Reversible tokens | Readable: `<PERSON_1>`, `<PHONE_1>`, etc. |

**User's choice:** Все типы PII + readable tokens
**Notes:** User explicitly added "номера документов" as additional PII type

## Noise Filtering

| Option | Description | Selected |
|--------|-------------|----------|
| Service messages | "user joined", "photo deleted" | ✓ |
| Bot messages | Bot auto-replies, pinned | ✓ |
| Short messages | <5 words | ✗ |
| Greetings | "привет", "ок", "да", "спасибо", "+" | ✓ |

**User's choice:** Service, bots, greetings — но НЕ короткие сообщения
**Rationale:** В коротких сообщениях может быть ценная информация ("звони Ивану", "проверь накладную 453")

## Chunking Strategy

| Question | Options | Decision |
|----------|---------|----------|
| Chunk size | Small (100-200), Medium (300-500), Large (500-1000) | Medium |
| Metadata | With metadata (date, author, chat, source type) | With metadata |
| Structure | Markdown-aware, Fixed size | Markdown-aware |

**User's choice:** Medium chunks + metadata + Markdown-aware
**Notes:** Все три рекомендации приняты как есть

## Claude's Discretion
- Конкретные пороги фильтрации шума (что именно считать "приветом")
- PII confidence threshold
- Размер хронологического окна для группировки Telegram сообщений

## Deferred Ideas

### Review Phase 1 UI
- Пользователь хочет drag & drop загрузку — это Phase 4 (REST API готов)
