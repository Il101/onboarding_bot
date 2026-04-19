---
phase: 06-web-admin-panel
plan: "02"
subsystem: admin-upload
tags: [fastapi, htmx, upload, celery, tdd]
requires: [06-01]
provides: [PDF-upload-endpoint, Telegram-upload-endpoint, sources-list-with-delete]
affects: [src/api/routes/admin.py, src/api/templates/sources/]
tech_stack_added: []
tech_stack_patterns: [HTMX-innerHTML-swap, TemplateResponse-partial, mock-celery-task-in-tests]
key_files_created:
  - src/api/templates/sources/_upload_status.html
key_files_modified:
  - src/api/routes/admin.py
  - src/api/templates/sources/upload_form.html
  - src/api/templates/sources/list.html
  - tests/test_admin.py
decisions:
  - "Catch HTTPException separately in upload handlers to convert 413/400 into HTMX error fragments instead of raising (avoids non-200 responses that HTMX won't swap)"
  - "Use hx-swap=innerHTML on status divs (not outerHTML) so target div persists across multiple uploads"
  - "voice_files loop validates each .ogg before writing; invalid file returns error fragment before any DB write"
metrics:
  duration_seconds: 229
  completed_date: "2026-04-19"
  tasks_completed: 1
  files_changed: 5
---

# Phase 06 Plan 02: Sources Upload Endpoints Summary

**One-liner:** PDF and Telegram file upload endpoints with HTMX error/success fragments, Celery task dispatch, and auto-refreshing sources list with delete.

## What Was Built

Added two POST upload endpoints to the admin router (`/api/admin/sources/pdf` and `/api/admin/sources/telegram`) that validate files, persist `Source` + `IngestJob` DB records, dispatch the existing `ingest_pdf` / `ingest_telegram` Celery tasks, and return HTMX partial fragments for inline status updates. Also added a DELETE endpoint for source removal. Updated the sources list template with `data-status` attributes, a `#sources-table-wrapper` for HTMX refresh, and Alpine.js polling that auto-refreshes every 5 seconds while any source has `processing` status.

## Tasks Completed

| # | Name | Commit | Files |
|---|------|--------|-------|
| 1 RED | Add failing upload tests | d3e77d5 | tests/test_admin.py |
| 1 GREEN | Implement upload endpoints + templates | 1ce8f3c | admin.py, _upload_status.html, upload_form.html, list.html |

## Verification

- `uv run pytest tests/test_admin.py` — 21/21 passed (13 Plan 01 + 8 new Plan 02 tests)
- PDF upload: extension check (.pdf) + magic bytes check (%PDF-) + size validation via `_validate_size`
- Telegram upload: extension check (.json) + JSON structure check (must have "messages" key) + .ogg magic bytes (OggS/ID3)
- Invalid files return 200 HTMX error fragments (not 4xx) — correct for HTMX swap behavior
- Sources list shows status badges with color coding and auto-refresh for processing sources

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] HTTPException converted to HTMX fragment instead of re-raised**

- **Found during:** Task 1 GREEN
- **Issue:** The plan's pseudocode had `except HTTPException: raise` which would return a 413/400 status code. HTMX does not swap content on non-2xx responses by default — the user would see no feedback.
- **Fix:** Catch `HTTPException` and return an error HTMX fragment with `exc.detail` as the message, same as other error paths.
- **Files modified:** src/api/routes/admin.py
- **Commit:** 1ce8f3c

## Known Stubs

None — all upload endpoints wire to real `ingest_pdf.delay` / `ingest_telegram.delay` Celery tasks. DB records are created before task dispatch. No hardcoded placeholders.

## Threat Surface Scan

All mitigations from the plan's threat model are implemented:
- T-6-07 (PDF Tampering): magic bytes check `content.startswith(b"%PDF-")`, extension check, UUID filename, `_validate_size`
- T-6-08 (Telegram Tampering): JSON structure validation (`"messages"` key required), OggS/ID3 magic bytes for voice files, UUID filenames
- T-6-09 (DoS): `_validate_size` applies `max_file_size_mb` limit (inherited from ingest router)

No new threat surface introduced beyond what the plan's threat model covers.

## Self-Check: PASSED

- [x] `src/api/routes/admin.py` exists and contains `admin_upload_pdf`, `admin_upload_telegram`, `delete_source`
- [x] `src/api/templates/sources/_upload_status.html` exists (new file)
- [x] `src/api/templates/sources/upload_form.html` uses `hx-swap="innerHTML"`
- [x] `src/api/templates/sources/list.html` has `#sources-table-wrapper` and `data-status` attrs
- [x] RED commit d3e77d5 exists
- [x] GREEN commit 1ce8f3c exists
- [x] 21/21 tests pass
