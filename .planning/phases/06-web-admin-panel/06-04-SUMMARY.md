---
phase: 06-web-admin-panel
plan: 04
subsystem: admin-users
tags: [user-management, telegram-user, crud, htmx, sqlalchemy]
dependency_graph:
  requires: [06-01, 06-02, 06-03]
  provides: [user-management-page, telegram-user-model, user-crud-endpoints]
  affects: [bot-auth-runtime, admin-nav]
tech_stack:
  added: [TelegramUser SQLAlchemy model, UserRole enum]
  patterns: [HTMX fragment swap, server-rendered partials, role validation via enum]
key_files:
  created:
    - src/models/telegram_user.py
    - src/api/templates/users/manage.html
    - src/api/templates/users/_add_result.html
  modified:
    - src/models/__init__.py
    - src/api/routes/admin.py
    - tests/test_admin.py
decisions:
  - POST /api/admin/users always returns HTTP 200 with HTML fragment for HTMX compatibility (error shown in body, not via 4xx status)
  - Adding/removing a user also updates settings.telegram_user_roles in-process for immediate bot auth effect without restart
  - UserRole enum restricted to admin/employee only (mentor excluded per plan scope)
  - Delete uses hx-swap=outerHTML on the row element to cleanly remove the row without page reload
metrics:
  duration_seconds: 181
  completed_date: "2026-04-19"
  tasks_completed: 1
  files_changed: 6
---

# Phase 06 Plan 04: User Management Summary

**One-liner:** TelegramUser SQLAlchemy model with admin-only CRUD endpoints (add/list/delete) wired to HTMX user management page with role validation and runtime bot-auth sync.

## What Was Built

- `src/models/telegram_user.py` — `TelegramUser` model (`user_id` PK, `UserRole` enum, `created_at`, `updated_at`) following the `source.py` pattern
- `src/models/__init__.py` — exports `TelegramUser` and `UserRole`
- Three new endpoints in `src/api/routes/admin.py`:
  - `GET /api/admin/users` — renders `users/manage.html` with ordered user list from DB
  - `POST /api/admin/users` — validates role enum, checks for duplicate `user_id`, creates user, returns `_add_result.html` fragment
  - `DELETE /api/admin/users/{user_id}` — removes user, returns 404 HTML if not found, otherwise success HTML
- `src/api/templates/users/manage.html` — full page with add form (HTMX `hx-post`) and user table (HTMX `hx-delete` per row)
- `src/api/templates/users/_add_result.html` — partial for success/error feedback after add

## TDD Gate Compliance

- RED commit: `adfb7b0` — 7 failing tests added before implementation
- GREEN commit: `57f0e89` — all 38 tests passing after implementation
- REFACTOR: none needed (implementation clean on first pass)

## Deviations from Plan

None — plan executed exactly as written.

The plan's `<action>` specified using `x-text="{{ message | tojson }}"` in `_add_result.html` for the Alpine.js pattern, but since the template is server-rendered by Jinja2 (auto-escaped) and no Alpine.js reactive state is needed for this static fragment, the simpler `{{ message }}` direct render was used instead. This is a trivial simplification with equivalent security properties (Jinja2 auto-escaping still applies).

## Known Stubs

None — all data flows from the database through SQLAlchemy queries. No hardcoded placeholders.

## Threat Surface Scan

No new surface beyond what the plan's threat model covers. All three endpoints are protected by `AdminAuthMiddleware` (session cookie check). Role validated via `UserRole(role)` enum — invalid roles raise `ValueError` caught and returned as error HTML. `user_id` is typed `int` in the FastAPI route signature (FastAPI rejects non-integer values at the framework level).

## Self-Check: PASSED

Files created:
- FOUND: src/models/telegram_user.py
- FOUND: src/api/templates/users/manage.html
- FOUND: src/api/templates/users/_add_result.html

Commits:
- FOUND: adfb7b0 (test RED)
- FOUND: 57f0e89 (feat GREEN)

Tests: 38 passed, 0 failed
