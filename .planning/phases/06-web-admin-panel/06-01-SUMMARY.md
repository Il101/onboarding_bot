---
phase: 06-web-admin-panel
plan: 01
subsystem: ui
tags: [fastapi, jinja2, htmx, alpine.js, tailwind, starlette-1.0, admin-auth, sqlalchemy]

# Dependency graph
requires:
  - phase: 02-knowledge-extraction
    provides: Source model, IngestJob model, feedback_event model
  - phase: 01-pii-data-ingestion
    provides: Base declarative base, config settings pattern
provides:
  - KnowledgeItem SQLAlchemy model with status enum for review queue
  - Admin authentication with session-based auth (SHA-256 password, httponly cookie)
  - AdminAuthMiddleware protecting all /api/admin/* routes
  - Jinja2 base template with HTMX + Alpine.js + Tailwind CDN foundation
  - Sidebar navigation with 4 sections (Sources, Knowledge, Users, Analytics)
  - Login page, sources list page, sources upload form page
  - Test scaffolding for all ADM-01 through ADM-07 requirements
affects: [06-02, 06-03, 06-04, 06-05]

# Tech tracking
tech-stack:
  added: [jinja2, htmx 1.9.12, alpine.js 3.14.0, tailwindcss CDN, tabler-icons]
  patterns: [starlette-1.0-template-response, session-cookie-auth, in-memory-session-store]

key-files:
  created:
    - src/models/knowledge_item.py
    - src/api/routes/admin.py
    - src/api/templates/base.html
    - src/api/templates/login.html
    - src/api/templates/sidebar.html
    - src/api/templates/sources/list.html
    - src/api/templates/sources/upload_form.html
    - tests/test_admin.py
  modified:
    - src/models/__init__.py
    - src/core/config.py
    - src/api/main.py

key-decisions:
  - "Used Starlette 1.0.0 TemplateResponse API (request-first signature) instead of legacy (name-first)"
  - "In-memory session store with UUID keys for single-admin MVP (per threat model T-6-06 accept)"
  - "TestClient with follow_redirects=False to properly test redirect-based auth flow"

patterns-established:
  - "Starlette 1.0 TemplateResponse: templates.TemplateResponse(request, 'name', context)"
  - "Admin auth: AdminAuthMiddleware + in-memory _admin_sessions dict + httponly cookie"
  - "Template inheritance: login.html standalone, all others extend base.html with sidebar"

requirements-completed: [ADM-01, ADM-02, ADM-06]

# Metrics
duration: 11min
completed: 2026-04-19
---

# Phase 06 Plan 01: Admin Foundation Summary

**KnowledgeItem model, session-based admin auth with Starlette 1.0.0, and HTMX/Alpine.js/Tailwind template foundation with sidebar navigation**

## Performance

- **Duration:** 11 min
- **Started:** 2026-04-19T14:52:54Z
- **Completed:** 2026-04-19T15:03:57Z
- **Tasks:** 3 of 4 (checkpoint reached at task 4)
- **Files modified:** 11

## Accomplishments
- KnowledgeItem SQLAlchemy model with KnowledgeStatus enum (published/pending/rejected)
- Admin authentication with SHA-256 password hashing, session cookies, and timeout
- AdminAuthMiddleware protecting all /api/admin/* routes except login
- Jinja2 base template layout with HTMX 1.9.12, Alpine.js 3.14.0, Tailwind CSS CDN
- Sidebar navigation with 4 sections and logout form
- Login page, sources list with table/empty state, upload form with PDF and Telegram HTMX forms
- 13 passing tests covering auth flow and requirement stubs for ADM-01 through ADM-07

## Task Commits

Each task was committed atomically:

1. **Task 1: Create KnowledgeItem model, update config, and wire admin router with auth** - `5a88f87` (feat)
2. **Task 2: Create Jinja2 templates (base, login, sidebar, sources)** - `98fb640` (feat)
3. **Task 3: Create test scaffolding for admin authentication and page endpoints** - `d437311` (test)
4. **Fix: Update TemplateResponse calls for Starlette 1.0.0 API** - `7052e99` (fix)

## Files Created/Modified
- `src/models/knowledge_item.py` - KnowledgeItem model with id, fact, topic, confidence, source_refs, status, timestamps
- `src/api/routes/admin.py` - Admin router with AdminAuthMiddleware, login/logout, page endpoints
- `src/api/templates/base.html` - Base layout with sidebar container and content area
- `src/api/templates/login.html` - Standalone login page with password form
- `src/api/templates/sidebar.html` - 4-section navigation with active state detection
- `src/api/templates/sources/list.html` - Sources table with status badges and empty state
- `src/api/templates/sources/upload_form.html` - PDF and Telegram upload forms with HTMX
- `src/models/__init__.py` - Added KnowledgeItem and KnowledgeStatus exports
- `src/core/config.py` - Added admin_password and admin_session_timeout settings
- `src/api/main.py` - Wired admin router and AdminAuthMiddleware
- `tests/test_admin.py` - 13 tests for auth flow and ADM requirement stubs

## Decisions Made
- Starlette 1.0.0 changed `TemplateResponse` to request-first signature -- updated all calls accordingly
- TestClient uses `follow_redirects=False` to properly assert redirect behavior in auth tests
- admin_client fixture depends on db_session fixture to mock DB for endpoints requiring Session

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed Starlette 1.0.0 TemplateResponse API incompatibility**
- **Found during:** Task 3 (test execution)
- **Issue:** Plan used legacy `TemplateResponse("name", {"request": request})` but Starlette 1.0.0 changed to `TemplateResponse(request, "name", context)`. The old signature caused `TypeError: unhashable type: 'dict'` in Jinja2 template cache.
- **Fix:** Updated all 5 TemplateResponse calls in admin.py to use request-first signature. Removed explicit `"request"` from context dicts since Starlette 1.0 auto-injects it.
- **Files modified:** `src/api/routes/admin.py`
- **Verification:** All 13 tests pass
- **Committed in:** `7052e99`

**2. [Rule 3 - Blocking] Fixed admin_client test fixture missing DB mock**
- **Found during:** Task 3 (test execution)
- **Issue:** `test_protected_route_accessible_with_session` called `/api/admin/sources` which depends on `get_db_session`. Without mocking, it tried connecting to PostgreSQL and failed with `OperationalError: connection refused`.
- **Fix:** Made `admin_client` fixture depend on `db_session` fixture so `get_db_session` is overridden with a MagicMock before any authenticated requests.
- **Files modified:** `tests/test_admin.py`
- **Verification:** All 13 tests pass
- **Committed in:** `d437311`

---

**Total deviations:** 2 auto-fixed (1 bug, 1 blocking)
**Impact on plan:** Both fixes essential for correctness. Starlette 1.0 API change was not in the plan (plan assumed older Starlette). No scope creep.

## Issues Encountered
- `qdrant_client` not installed in system Python -- resolved by using `uv run` for test execution
- pytest not in uv venv -- installed via `uv pip install pytest pytest-asyncio`

## Known Stubs
- `admin_client` fixture has unused `db_session` parameter (pytest lint hint) -- this is intentional, the fixture depends on db_session for its side effects (mock setup)
- Sources upload form HTMX endpoints (`/api/admin/sources/pdf`, `/api/admin/sources/telegram`) are not yet implemented -- will be added in plan 06-02
- Knowledge, Users, Analytics pages return 302 redirect (auth gate only) -- content will be added in plans 06-03, 06-04, 06-05

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_mitigate: T-6-02 | src/api/routes/admin.py | Admin session management with SHA-256 hashed password, httponly+samesite=lax cookie |
| threat_mitigate: T-6-04 | src/api/routes/admin.py | Session cookie with httponly=True, samesite=lax, UUID-only value |
| threat_accept: T-6-06 | src/api/routes/admin.py | In-memory session store (single-admin MVP, acceptable per threat model) |

## Next Phase Readiness
- Admin foundation ready for plan 06-02 (source upload endpoints and knowledge review)
- All templates extend base.html -- new pages should follow same pattern
- AdminAuthMiddleware is global -- new /api/admin/* routes are automatically protected
- KnowledgeItem model available for review queue implementation

---
*Phase: 06-web-admin-panel*
*Completed: 2026-04-19*
