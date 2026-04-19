---
phase: 6
slug: web-admin-panel
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-19
---

# Phase 6 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x + pytest-asyncio |
| **Config file** | pyproject.toml |
| **Quick run command** | `python -m pytest tests/test_admin.py -x -q --tb=short` |
| **Full suite command** | `python -m pytest tests/ -v --tb=short` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/test_admin.py -x -q --tb=short`
- **After every plan wave:** Run `python -m pytest tests/ -v --tb=short`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 06-01-01 | 01 | 1 | ADM-01 | T-6-01 | File upload validates type and size | integration | `python -m pytest tests/test_admin.py -x -q` | ❌ W0 | ⬜ pending |
| 06-01-02 | 01 | 1 | ADM-02 | T-6-01 | Telegram upload validates JSON + OGG | integration | `python -m pytest tests/test_admin.py -x -q` | ❌ W0 | ⬜ pending |
| 06-02-01 | 02 | 1 | ADM-03 | — | Knowledge list filtered correctly | integration | `python -m pytest tests/test_admin.py -x -q` | ❌ W0 | ⬜ pending |
| 06-02-02 | 02 | 2 | ADM-04, ADM-05 | — | Approve/reject changes knowledge status | integration | `python -m pytest tests/test_admin.py -x -q` | ❌ W0 | ⬜ pending |
| 06-03-01 | 03 | 2 | ADM-06 | T-6-02 | Admin auth required for all admin routes | integration | `python -m pytest tests/test_admin.py -x -q` | ❌ W0 | ⬜ pending |
| 06-03-02 | 03 | 2 | ADM-06 | — | User CRUD operations work | unit | `python -m pytest tests/test_admin.py -x -q` | ❌ W0 | ⬜ pending |
| 06-04-01 | 04 | 2 | ADM-07 | — | Analytics returns aggregate data | integration | `python -m pytest tests/test_admin.py -x -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_admin.py` — stubs for ADM-01..ADM-07
- [ ] `tests/conftest.py` — shared fixtures (admin client, test DB session, sample knowledge items)
- [ ] `src/models/knowledge_item.py` — new SQLAlchemy model for review queue (Wave 1 creates this, Wave 0 stubs tests against it)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Admin panel renders correctly in browser | All | Visual rendering needs human eye | Открыть админку в браузере, проверить layout sidebar + content |
| HTMX dynamic updates work end-to-end | ADM-01, ADM-02 | Requires browser with JS | Загрузить файл через форму, убедиться что статус обновляется без перезагрузки |
| Password auth login flow works | ADM-06 | Session/cookie management in real browser | Войти через форму логина, проверить что при неправильном пароле доступ закрыт |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
