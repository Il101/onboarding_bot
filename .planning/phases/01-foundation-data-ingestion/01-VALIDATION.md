---
phase: 1
slug: foundation-data-ingestion
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-18
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x + pytest-asyncio |
| **Config file** | pyproject.toml (Wave 0 installs) |
| **Quick run command** | `python -m pytest tests/ -x -q --tb=short` |
| **Full suite command** | `python -m pytest tests/ -v --tb=short` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/ -x -q --tb=short`
- **After every plan wave:** Run `python -m pytest tests/ -v --tb=short`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | ING-02 | T-1-01 | N/A | unit | `python -m pytest tests/ -x -q` | ❌ W0 | ⬜ pending |
| 01-01-02 | 01 | 1 | ING-04 | — | N/A | unit | `python -m pytest tests/ -x -q` | ❌ W0 | ⬜ pending |
| 01-02-01 | 02 | 1 | ING-03 | — | N/A | unit | `python -m pytest tests/ -x -q` | ❌ W0 | ⬜ pending |
| 01-03-01 | 03 | 2 | ING-01 | T-1-02 | PII tokens replace real data | unit | `python -m pytest tests/ -x -q` | ❌ W0 | ⬜ pending |
| 01-04-01 | 04 | 2 | ING-05 | — | N/A | unit | `python -m pytest tests/ -x -q` | ❌ W0 | ⬜ pending |
| 01-05-01 | 05 | 3 | ING-06, ING-01 | T-1-03 | PII runs before indexing | unit | `python -m pytest tests/ -x -q` | ❌ W0 | ⬜ pending |
| 01-06-01 | 06 | 3 | ING-06 | T-1-03 | API auth required | integration | `python -m pytest tests/ -x -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/conftest.py` — shared fixtures (sample Telegram JSON, sample PDF, PII test data)
- [ ] `tests/test_telegram_parser.py` — stubs for ING-02
- [ ] `tests/test_noise_filter.py` — stubs for ING-04
- [ ] `tests/test_pii_anonymizer.py` — stubs for ING-01
- [ ] `tests/test_pdf_parser.py` — stubs for ING-05
- [ ] `tests/test_chunking.py` — stubs for chunking logic
- [ ] `pytest` + `pytest-asyncio` install in pyproject.toml

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Groq Whisper transcription quality | ING-03 | External API — requires real .ogg file and API key | Запустить скрипт с реальным голосовым файлом, проверить транскрипцию |
| Qdrant hybrid search relevance | ING-06 | Requires running Qdrant instance + embeddings | Загрузить тестовые данные, выполнить поиск, оценить релевантность вручную |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
