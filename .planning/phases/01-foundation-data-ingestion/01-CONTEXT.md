# Phase 1: Foundation & Data Ingestion - Context

**Gathered:** 2026-04-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Система принимает Telegram JSON export (текст + голосовые) и PDF документы, очищает от шума и PII, и индексирует в Qdrant с hybrid search и source attribution. Включает REST API для ингеста (на который Phase 4 добавит веб-форму загрузки).
</domain>

<decisions>
## Implementation Decisions

### Data Intake Flow
- **D-01:** Ингест через REST API (FastAPI endpoints), Phase 4 добавит веб-форму поверх этого API
- **D-02:** Конечные точки API: `/api/ingest/telegram` (JSON + .ogg файлы), `/api/ingest/pdf` (multipart upload), `/api/ingest/status/{job_id}` (прогресс)
- **D-03:** Пакетная обработка через Celery + Redis — тяжелые задачи (PII, эмбеддинг) не блокируют API

### PII Anonymization
- **D-04:** Распознаваемые типы: имена людей (ФИО, отчества, сокращённые имена, никнеймы), телефоны (все форматы: +7, 8, скобки, дефисы), email (личные и рабочие), адреса, номера документов
- **D-05:** Формат токенов: читаемые — `<PERSON_1>`, `<PHONE_1>`, `<EMAIL_1>`, `<ADDRESS_1>`, `<DOC_1>`
- **D-06:** Presidio + кастомные русские regex-распознаватели для телефонов, ИНН, СНИЛС; spaCy `ru_core_news_md` для NER
- **D-07:** PII анонимизация происходит ДО любой дальнейшей обработки (критическое архитектурное требование)
- **D-08:** Нужна валидация качества Presidio на реальных русских данных — отдельная задача в Phase 1

### Noise Filtering (Telegram)
- **D-09:** Отсеиваем: service messages (вступил/вышел, фото удалено, pinned), bot messages, приветствия/подтверждения ("привет", "ок", "да", "спасибо", "+")
- **D-10:** Короткие сообщения НЕ отсекаем — в них может быть ценная информация ("звони Ивану", "проверь накладную")
- **D-11:** Решение о фильтрации принимает whoever implements — Claude's Discretion

### Chunking Strategy
- **D-12:** Medium chunks: 5-10 предложений, ~300-500 токенов, перекрытие 1 предложение между чанками
- **D-13:** Метаданные к каждому чанку: дата, автор, чат/источник, тип (текст/голос/PDF)
- **D-14:** Markdown-aware разбиение: учитываем заголовки и параграфы, сохраняем структуру документа
- **D-15:** Для Telegram: группируем сообщения по хронологии (окно, например 30 минут) перед чанкированием

### Test Data
- **D-16:** Нужны оба варианта: реальный Telegram чат (экспорт из Telegram Desktop) для валидации формата + синтетические данные с PII для тестирования edge cases
- **D17:** Voice messages: при Telegram export .ogg файлы лежат рядом с JSON — парсер должен уметь связывать их с сообщениями

### Claude's Discretion
- Фильтрация шума: какие конкретно сообщения ниже порога считаются шумом (решает разработчик на основе тестовых данных)
- Порог confidence для PII: минимальная длина совпадения, tradeoff между recall и precision
- Размер окна хронологической группировки для Telegram сообщений перед чанкированием

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Research
- `.planning/research/STACK.md` — Recommended stack with versions and rationale
- `.planning/research/ARCHITECTURE.md` — 5-stage pipeline architecture, data flow
- `.planning/research/PITFALLS.md` — Russian PII pitfalls, Telegram noise ratio, hallucination risks

### Project Specs
- `.planning/PROJECT.md` — Core value, constraints, key decisions
- `.planning/REQUIREMENTS.md` — ING-01 through ING-06 acceptance criteria
- `.planning/ROADMAP.md` — Phase 1 goal, success criteria

### Data Sources
- `.planning/research/STACK.md` §Presidio — Russian NER setup details
- `.planning/research/PITFALLS.md` §PII Anonymization — Russian-specific challenges

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- Greenfield project — no existing code. All patterns established during this phase.

### Established Patterns
- None yet — this phase establishes the foundational patterns for data pipeline, API structure, and error handling.

### Integration Points
- REST API endpoints will become the ingestion interface for Phase 4 web admin
- Celery task queue will be used by Phase 2 for LLM-based extraction tasks
- Qdrant collection schema defined here will be consumed by Phase 2 RAG pipeline and Phase 3 bot

</code_context>

<specifics>
## Specific Ideas

- Dify.ai rejected for core pipeline — custom Python code for all pipeline stages
- Groq Whisper API key доступен для транскрибации голосовых
- Telegram JSON export format (`result.json` из Telegram Desktop) — нужно верифицировать актуальную схему
- Использовать multilingual-e5-large для эмбеддингов (рекомендация из research), но бенчмаркнуть на реальных данных в рамках Phase 1

</specifics>

<deferred>
## Deferred Ideas

### Review Phase 1 UI
- Пользователь хочет drag & drop загрузку в вебке — это Phase 4 (REST API уже будет готов). Заметил на случай если понадобится прототип.

None — discussion stayed within phase scope

</deferred>

---

*Phase: 01-foundation-data-ingestion*
*Context gathered: 2026-04-18*
