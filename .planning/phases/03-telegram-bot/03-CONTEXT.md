# Phase 3: Telegram Bot - Context

**Gathered:** 2026-04-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Новый сотрудник задаёт вопрос в Telegram-боте и получает ответ на русском из knowledge base (Phase 2) с обязательным блоком источников, защитой от галлюцинаций, учётом контекста диалога и записью feedback (thumbs up/down). Доступ только для авторизованных сотрудников.

</domain>

<decisions>
## Implementation Decisions

### Bot Answer Policy (BOT-01, BOT-02)
- **D-01:** При низкой уверенности бот использует строгий fallback: **«Я не знаю — обратитесь к коллеге»**.
- **D-02:** Ответы всегда на русском языке.
- **D-03:** Формат ответа: кратко и по шагам (3-6 пунктов), без лишних пояснений.

### Source Attribution UX (BOT-01/BOT-02)
- **D-04:** Ответ пользователю: короткий основной ответ + отдельный блок **«Источники»** списком.
- **D-05:** Источники показываются в каждом ответе по умолчанию (не только по запросу).

### Multi-turn Context Handling (BOT-03)
- **D-06:** Логически хранится весь диалог пользователя с ботом в рамках сессии.
- **D-07:** Для вызова LLM используется динамическое контекстное окно с суммаризацией старых сообщений (оптимизация стоимости/латентности без потери смысла диалога).
- **D-08:** Если запрос двусмысленный/слишком общий, бот задаёт ровно 1 уточняющий вопрос перед финальным ответом.

### Conflict Resolution & Safety (BOT-02)
- **D-09:** При конфликте источников бот приоритизирует более свежую инструкцию и явно помечает, что есть конфликт.
- **D-10:** Для off-topic вопросов бот кратко отказывает и возвращает пользователя к рабочей теме.

### Access Control & Feedback (BOT-04, BOT-05)
- **D-11:** Доступ к боту только для авторизованных сотрудников; при `/start` обязательна проверка роли.
- **D-12:** Пользовательский feedback (thumbs up/down) сохраняется для последующей аналитики и улучшения качества ответов.

### the agent's Discretion
- Конкретный механизм хранения сессий и summaries (таблица БД/кэш/гибрид), при соблюдении D-06 и D-07.
- Формат UI-деталей у блока «Источники» (эмодзи, разделители, truncation), если не нарушает D-04/D-05.
- Точные пороги и триггеры для запуска уточняющего вопроса (при соблюдении D-08).

</decisions>

<specifics>
## Specific Ideas

- Пользовательский приоритет: лучше честный отказ, чем потенциальная галлюцинация.
- Ответ должен быть операционно полезным для онбординга: короткие, практичные шаги.
- Прозрачность обязательна: источник ответа должен быть виден сразу, без дополнительных команд.

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope and requirements
- `.planning/ROADMAP.md` — Goal/Success Criteria для Phase 3 (BOT-01..BOT-05).
- `.planning/REQUIREMENTS.md` — Формулировки BOT-01..BOT-05 и требования к fallback/auth/feedback.
- `.planning/PROJECT.md` — Глобальные ограничения: русский язык, безопасность и data perimeter.

### Upstream AI/RAG contracts (mandatory integration)
- `.planning/phases/02-knowledge-extraction-rag/02-CONTEXT.md` — Зафиксированные retrieval/fallback/attribution решения, которые бот должен соблюдать.
- `.planning/phases/02-knowledge-extraction-rag/02-AI-SPEC.md` — AI-контракты для retrieval/synthesis/evaluation.
- `.planning/phases/02-knowledge-extraction-rag/02-SECURITY.md` — Security guardrails, влияющие на bot query surface.

### Existing backend integration points
- `src/api/routes/knowledge.py` — Текущая knowledge query API surface, envelope и ограничения `top_k`.
- `src/ai/rag/synthesizer.py` — Политика synthesis/fallback и confidence behavior (источник для BOT-02 wiring).
- `src/core/config.py` — Конфигурационные паттерны для порогов, лимитов и runtime toggles.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/api/routes/knowledge.py` — готовый endpoint для получения ответа/confidence/sources/fallback, который бот может вызывать как backend contract.
- `src/tasks/ingest.py` и phase-2 RAG слой — уже настроенный pipeline знаний, на который бот опирается без дублирования retrieval-логики.
- `src/core/config.py` — централизованный settings-паттерн для порогов confidence, лимитов контекста и bot policy flags.

### Established Patterns
- FastAPI routes + Pydantic contracts для явных API границ.
- Явный fallback-контракт с source attribution из Phase 2 (без "answer at any cost").
- Тестовые паттерны через pytest по сценариям policy/guardrails.

### Integration Points
- Новый Telegram bot слой должен вызывать knowledge query контракт и форматировать ответ в Telegram UX (основной ответ + «Источники»).
- Нужен storage для диалогового контекста и feedback событий, совместимый с текущей backend архитектурой.
- Auth check при `/start` должен быть связан с user/role моделью проекта (или её Phase 3 минимальным внедрением).

</code_context>

<deferred>
## Deferred Ideas

- Расширенные режимы ответа (кнопка "развернуть подробно") — потенциально в Phase 4 UX-полировке.
- Более сложная стратегия конфликтов (показывать оба варианта с explainability UI) — кандидат в отдельную future phase.

</deferred>

---

*Phase: 03-telegram-bot*
*Context gathered: 2026-04-18*
