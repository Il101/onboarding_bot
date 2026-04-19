# Phase 6: Web Admin Panel - Context

**Gathered:** 2026-04-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Администратор управляет всей системой через веб-интерфейс: загружает источники (PDF, Telegram JSON), рецензирует знания перед публикацией, управляет пользователями и отслеживает аналитику использования. Это финальная функциональная фаза перед Phase 7 (Verification Backfill).

Требования: ADM-01, ADM-02, ADM-03, ADM-04, ADM-05, ADM-06, ADM-07

</domain>

<decisions>
## Implementation Decisions

### Навигация и структура
- **D-01:** Sidebar + content layout (не tab-based)
- **D-02:** 4 секции в sidebar: Sources (источники), Knowledge (знания), Users (пользователи), Analytics (аналитика)
- Sidebar фиксированный слева, content area справа

### Source upload (ADM-01, ADM-02)
- Форма загрузки встроена в Sources section
- PDF upload — один файл за раз
- Telegram upload — JSON файл + опциональные .ogg voice files (множественный upload)
- Статус ingest job отображается в таблице sources (pending/processing/completed/failed)
- Переиспользуем существующие `POST /api/ingest/telegram`, `POST /api/ingest/pdf`, `GET /api/ingest/status/{job_id}`

### Knowledge review gate (ADM-03, ADM-04, ADM-05)
- **D-03:** Авто-публикация при `confidence >= threshold` + ручной review gate для ручного управления
- Auto-published knowledge сразу доступно в RAG
- Knowledge с `confidence < threshold` идёт в review queue
- **D-04:** Knowledge отображается как таблица с фильтрами (по topic, source, status) и bulk-операциями (approve/reject/delete)
- Каждая запись: fact, topic, confidence score, source attribution, status (published/pending/rejected)
- Admin может редактировать fact перед публикацией
- Bulk approve/reject через checkboxes

### User management (ADM-06)
- **D-05:** Ручное добавление Telegram user_id администратором
- Нет само-регистрации — admin вводит user_id и назначает роль (admin/employee)
- Список текущих пользователей с ролями
- **D-06:** Простая password auth для веб-админки (env переменная)
- Один admin пароль из `.env`, без сложной системы авторизации
- Все страницы защищены одной password-проверкой (session cookie)

### Dashboard & Analytics (ADM-07)
- **D-07:** Базовые метрики на одной странице
- Популярные вопросы (топ-N по частоте запросов)
- Средняя оценка ответов (из FeedbackEvent.vote)
- Количество знаний (total, published, pending, rejected)
- Статусы ingest jobs (completed/failed counts)
- Активные пользователи (уникальные user_id за период)

### Claude's Discretion
- Точное оформление sidebar (иконки, ширину, collapse-поведение)
- Детали реализации password auth (middleware vs dependency, session duration)
- UI фильтров и поиска в knowledge table
- Layout dashboard (карточки vs таблицы vs графики)
- Empty states и error states
- Responsive breakpoints (admin panel — desktop-first)
- Tailwind utility classes и конкретные цвета

</decisions>

<specifics>
## Specific Ideas

- "Линейный стиль" — чистый, без перегрузки интерфейс
- Knowledge table похож на Linear issues — компактный, с inline-действиями
- Dashboard — один экран с ключевыми цифрами, не набор графиков

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Requirements
- `.planning/REQUIREMENTS.md` — ADM-01..ADM-07 определения и acceptance criteria
- `.planning/ROADMAP.md` §Phase 6 — goal, success criteria, depends-on chain

### Stack decision (locked)
- `CLAUDE.md` §Recommended Stack → Web Admin Panel — HTMX + Alpine.js + Jinja2 + Tailwind CSS

### Existing API contracts (reuse, don't rewrite)
- `src/api/routes/ingest.py` — POST /api/ingest/telegram, POST /api/ingest/pdf, GET /api/ingest/status/{job_id}
- `src/api/routes/knowledge.py` — POST /api/knowledge/query
- `src/api/deps.py` — get_db_session(), get_celery_result()
- `src/core/config.py` — Settings (database_url, upload_dir, thresholds, telegram settings)

### Data models (existing SQLAlchemy)
- `src/models/source.py` — Source (id, type, filename, status, messages_count, chunks_indexed)
- `src/models/ingest_job.py` — IngestJob (celery_task_id, progress tracking)
- `src/models/feedback_event.py` — FeedbackEvent (thread_id, vote, answer_confidence, user_id, chat_id)

### AI pipeline schemas
- `src/ai/extraction/schemas.py` — KnowledgeUnit, SourceRef, KnowledgeBatch
- `src/ai/extraction/publish_policy.py` — PublishDecision, should_publish_knowledge()

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/api/main.py` — FastAPI app instance, уже подключены ingest_router и knowledge_router
- `src/api/deps.py` — SQLAlchemy session dependency, Celery result helper
- `src/api/routes/ingest.py` — Полностью готовые endpoints для загрузки файлов (PDF + Telegram JSON + voice)
- `src/core/config.py` — Pydantic Settings с env-backed конфигурацией, добавить admin_password здесь
- `src/models/` — Source, IngestJob, FeedbackEvent модели (knowledge model для review queue нужно создать)

### Established Patterns
- FastAPI routers с prefix/tags в `src/api/routes/`
- SQLAlchemy ORM модели в `src/models/` с Base class
- Celery tasks в `src/tasks/` для тяжёлых операций
- Pydantic Settings для конфигурации из env

### Integration Points
- New admin routes → `src/api/routes/admin.py` (новый router, подключить к `main.py`)
- Knowledge review → нужна новая SQLAlchemy модель (KnowledgeItem с status field: published/pending/rejected)
- Dashboard queries → aggregate queries на FeedbackEvent + Source + KnowledgeItem
- Admin auth → middleware или dependency в FastAPI, password из Settings
- Templates → `src/api/templates/` для Jinja2 (создать директорию)
- Static files → `src/api/static/` для Tailwind CDN + Alpine.js (или inline)

</code_context>

<deferred>
## Deferred Ideas

- Графики и чарты (Chart.js или подобное) — можно добавить позже, MVP без графиков
- RBAC (разные роли с разными правами в админке) — MVP: один admin пароль
- Real-time updates (WebSocket/SSE для ingest status) — polling достаточен для MVP
- Audit log для действий admin — можно добавить в backlog
- Self-service registration для сотрудников — admin вручную добавляет user_id

</deferred>

---
*Phase: 06-web-admin-panel*
*Context gathered: 2026-04-19*
