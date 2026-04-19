# Phase 6 Discussion Log

**Date:** 2026-04-19
**Phase:** 06 - Web Admin Panel
**Participant:** User (admin/developer)
**Mode:** discuss (interactive Q&A)

---

## Discussion Areas Presented

4 gray areas were identified and presented to the user:

### Area 1: Navigation & Layout
**Question:** Как организовать навигацию в админке — sidebar, tabs, или что-то другое?
**Decision:** Sidebar + content area, 4 секции (Sources, Knowledge, Users, Analytics)

### Area 2: Knowledge Review Gate (ADM-03, ADM-04, ADM-05)
**Question:** Как организовать рецензирование знаний — авто-публикация, ручной review, или смешанный подход?
**Decision:** Смешанный — авто-публикация при высоком confidence, review queue для низкого. Table с фильтрами и bulk-операциями.

### Area 3: User Management (ADM-06)
**Question:** Как управлять пользователями — само-регистрация, admin вручную, импорт?
**Decision:** Ручное добавление user_id admin-ом. Простая password auth для веб-админки (env переменная).

### Area 4: Dashboard & Analytics (ADM-07)
**Question:** Какие метрики и какой уровень детализации аналитики?
**Decision:** Базовые метрики на одной странице — популярные вопросы, средняя оценка, количество знаний, ingest статусы, активные пользователи.

---

## Claude's Discretion Areas

User explicitly delegated these to implementation judgment:
- Sidebar styling (icons, width, collapse)
- Password auth implementation details (middleware vs dependency)
- Filter/search UI specifics
- Dashboard layout (cards vs tables vs charts)
- Empty/error states
- Responsive behavior (desktop-first)

---

## No External Specs Referenced

All ADM-01..ADM-07 requirements are captured in REQUIREMENTS.md. No external design docs, ADRs, or feature specs exist for this phase. Stack decision (HTMX + Alpine.js + Tailwind) is locked in CLAUDE.md.
