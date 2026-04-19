# Phase 2: Knowledge Extraction & RAG - Context

**Gathered:** 2026-04-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Из проиндексированных и анонимизированных данных Phase 1 извлекать структурированные knowledge units, генерировать SOP в Markdown и построить RAG retrieval/synthesis с обязательным source attribution. Бот и веб-UI не входят в эту фазу.

</domain>

<decisions>
## Implementation Decisions

### Knowledge Extraction Schema (KNW-01)
- **D-01:** Формат знания строго структурированный JSON.
- **D-02:** Базовые поля knowledge unit: `fact`, `topic`, `source_refs`, `confidence`.
- **D-03:** Одна knowledge unit = одна атомарная проверяемая мысль/правило.

### SOP Generation (KNW-02)
- **D-04:** SOP генерируется по фиксированному шаблону: `цель -> шаги -> исключения -> проверка результата`.
- **D-05:** Свободная генерация без структуры не используется в Phase 2.

### Confidence & Publishing Policy
- **D-06:** Low-confidence knowledge units не публикуются в knowledge-base до ревью.
- **D-07:** Confidence обязателен для каждого извлечённого знания и используется как gate публикации.

### Retrieval & Ranking (KNW-03)
- **D-08:** Retrieval пайплайн: hybrid search (dense+sparse) с последующим reranking top-K.
- **D-09:** Dense-only и sparse-only режимы не являются основным режимом для Phase 2.

### Source Attribution (KNW-04)
- **D-10:** В каждом ответе и SOP обязателен attribution: `source_id + excerpt + timestamp/page`.
- **D-11:** Attribution должен быть достаточно детальным для ручной верификации оператором.

### Low-Relevance Fallback
- **D-12:** При низкой релевантности retrieval система возвращает "недостаточно данных" + ближайшие найденные источники.
- **D-13:** "Генерировать любой ценой" при низкой релевантности запрещено.

### the agent's Discretion
- Точные пороги `confidence` и `relevance` (с обязательной документированной конфигурацией).
- Конкретная схема reranking (модель/эвристика), если соблюдены D-08 и D-12.
- Внутренняя структура хранения промежуточных артефактов extraction/SOP.

</decisions>

<specifics>
## Specific Ideas

- Фокус на проверяемости: каждый knowledge unit должен быть трассируем к источнику.
- SOP должен быть пригоден для онбординга без "домысливания" шагов сотрудником.
- При сомнительной релевантности важнее честный отказ и прозрачные источники, чем галлюцинированный ответ.

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase scope and requirements
- `.planning/ROADMAP.md` — Goal/Success Criteria для Phase 2 (KNW-01..KNW-04).
- `.planning/REQUIREMENTS.md` — Формулировки KNW-01..KNW-04 и трассировка по фазам.
- `.planning/PROJECT.md` — Ограничения по безопасности, периметру данных и языку (русский).

### Upstream implementation constraints (Phase 1 outputs)
- `.planning/phases/01-foundation-data-ingestion/01-CONTEXT.md` — Зафиксированные решения по ingestion/anonymization/chunking.
- `.planning/phases/01-foundation-data-ingestion/01-06-SUMMARY.md` — API/Celery orchestration как вход для Phase 2.
- `.planning/phases/01-foundation-data-ingestion/01-SECURITY.md` — Security constraints и accepted risks, влияющие на Phase 2.

### Research baseline
- `.planning/research/STACK.md` — Базовый стек и ограничения по инструментам RAG.
- `.planning/research/ARCHITECTURE.md` — Сквозной pipeline-контекст.
- `.planning/research/PITFALLS.md` — Риски extraction/SOP/RAG для русского домена.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/tasks/ingest.py` — существующий Celery orchestration pattern для тяжелых пайплайнов.
- `src/pipeline/indexer/qdrant_store.py` — готовый hybrid index storage слой в Qdrant.
- `src/pipeline/indexer/embedder.py` — dense+sparse embeddings, совместимые с текущим индексом.
- `src/pipeline/anonymizer/engine.py` — готовый PII-first preprocessing блок.

### Established Patterns
- Async API + Celery background tasks как основной execution pattern.
- Конфигурация через `src/core/config.py` (все пороги/флаги — в settings).
- Тестирование через pytest с отдельными pipeline/api test модулями.

### Integration Points
- Phase 2 должен потреблять чанки/метаданные из Phase 1 (Qdrant + source metadata).
- Результаты extraction/SOP станут входом для Phase 3 (бот) и Phase 4 (админка/ревью).
- Attribution contract должен быть совместим с `source_id` и metadata, уже формируемыми в ingestion pipeline.

</code_context>

<deferred>
## Deferred Ideas

- UI-слой ревью low-confidence knowledge (перенесено в админский контур Phase 4).
- Диалоговые fallback-механики бота при низкой релевантности (детализация в Phase 3).

</deferred>

---

*Phase: 02-knowledge-extraction-rag*
*Context gathered: 2026-04-18*
