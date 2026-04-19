---
phase: 06-web-admin-panel
plan: "05"
subsystem: web-admin
tags: [analytics, dashboard, sqlalchemy, aggregate-queries, jinja2, htmx]
dependency_graph:
  requires: [06-01, 06-02, 06-03, 06-04]
  provides: [ADM-07, analytics-dashboard]
  affects: [src/api/routes/admin.py, src/api/templates/analytics/]
tech_stack:
  added: []
  patterns:
    - SQLAlchemy func.count / func.avg / func.distinct aggregate queries
    - SQLAlchemy case() expression for conditional averaging
    - Jinja2 server-rendered metric cards with division-by-zero guards
key_files:
  created:
    - src/api/templates/analytics/dashboard.html
  modified:
    - src/api/routes/admin.py
    - tests/test_admin.py
decisions:
  - Used `{% if avg_rating is not none %}` (lowercase) instead of `is not None` — Jinja2 uses Python-style `none` keyword
  - avg_rating stored as 0.0–1.0 float (ratio of up-votes); displayed as percentage via `* 100`
  - Popular questions query goes directly to group_by (no filter clause) — all-time top threads, not filtered by date
  - Jinja2 division-by-zero protected by `{% if knowledge_total > 0 %}` and `{% if ingest_total > 0 %}` guards
  - Fixed test mock: popular_questions chain is `db.query().group_by().order_by().limit().all()` not via `.filter()`
metrics:
  duration_seconds: 182
  completed_date: "2026-04-19"
  tasks_completed: 1
  files_modified: 3
---

# Phase 06 Plan 05: Analytics Dashboard Summary

**One-liner:** Server-side analytics dashboard with SQLAlchemy aggregate queries for knowledge counts, answer ratings, active users, popular questions, and ingest job stats.

## What Was Built

Single-page analytics dashboard at `GET /api/admin/analytics` delivering ADM-07. All metrics computed via SQLAlchemy aggregate queries against existing models (KnowledgeItem, FeedbackEvent, IngestJob, Source) and rendered server-side via Jinja2.

### Endpoint: `GET /api/admin/analytics`

Runs 12 aggregate queries:
1. `func.count(KnowledgeItem.id)` — total knowledge items
2-4. Same filtered by `status == PUBLISHED/PENDING/REJECTED`
5. `func.avg(case((vote=="up", 1), (vote=="down", 0)))` — approval rate 0.0–1.0
6. `func.count(FeedbackEvent.id)` — total feedback votes
7. `func.count(func.distinct(FeedbackEvent.user_id))` filtered by `created_at >= week_ago` — active users
8. `group_by(thread_id).order_by(desc("count")).limit(10)` — top 10 popular threads
9-10. `func.count(IngestJob.id)` filtered by `status == SUCCESS/FAILURE`
11. `func.count(IngestJob.id)` — total ingest jobs
12-13. `func.count(Source.id)` filtered by `type == PDF/TELEGRAM`

### Template: `analytics/dashboard.html`

- 5 metric cards (total, published, pending, rejected knowledge + active users)
- Average rating card with progress bar (hidden when no data, shows N/A)
- Ingest stats card with success/failure counts and progress bar
- Popular questions list (top 10 thread_ids with counts)
- Knowledge distribution with 3 progress bars (guarded by `knowledge_total > 0`)
- Extends `base.html` sidebar layout — consistent with all other admin pages

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| RED | Failing analytics tests | dc096a0 | tests/test_admin.py |
| GREEN | Analytics endpoint + template | d90ff10 | src/api/routes/admin.py, src/api/templates/analytics/dashboard.html, tests/test_admin.py |

## Test Results

All 45 tests pass (38 prior plans + 7 new analytics tests):
- `test_analytics_page_renders` — 200 with all metric labels
- `test_analytics_shows_knowledge_counts` — total=50 appears in response
- `test_analytics_shows_popular_questions` — thread_ids and counts rendered
- `test_analytics_handles_empty_data_gracefully` — N/A for missing avg_rating
- `test_analytics_requires_auth` — 302 redirect without session
- `test_analytics_shows_ingest_stats` — "Обработка источников" section present
- `test_analytics_shows_active_users_section` — "Активные пользователи" card present

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed test mock chain for popular_questions query**
- **Found during:** GREEN phase — test_analytics_shows_popular_questions failing
- **Issue:** Test set up mock on `db.query().filter().group_by()` but the actual query uses `db.query(FeedbackEvent.thread_id, ...).group_by()` without `.filter()` in between
- **Fix:** Rewired test mock to `db_session.query.return_value.group_by.return_value.order_by.return_value.limit.return_value.all.return_value`
- **Files modified:** tests/test_admin.py
- **Commit:** d90ff10

**2. [Rule 2 - Correctness] Used Starlette request-first TemplateResponse signature**
- **Found during:** Implementation — matching existing pattern in admin.py
- **Applied:** `templates.TemplateResponse(request, "analytics/dashboard.html", {...})` (request-first, not name-first) — consistent with all other endpoints in admin.py

## Known Stubs

None — all metric values are wired to live database queries. Empty-state messages ("N/A", "Нет данных") display when tables are empty, which is correct behavior not a stub.

## Threat Flags

No new threat surface. `GET /api/admin/analytics` is read-only, session-protected (AdminAuthMiddleware), and returns only aggregate counts — no PII exposed (thread_ids are conversation keys, not personal data). Per threat model: T-6-17 (accept), T-6-18 (accept).

## Self-Check: PASSED
