---
phase: 2
slug: knowledge-extraction-rag
status: revised
nyquist_compliant: true
wave_0_complete: true
created: 2026-04-19
---

# Phase 2 — Validation Strategy

> Nyquist compliance map for all execution tasks in `02-01/02-02/02-03-PLAN.md`.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.x + pytest-asyncio (`uv run pytest ...`) |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `uv run pytest tests/phase2 -q` |
| **Full suite command** | `uv run pytest tests/ -v --tb=short` |

---

## Sampling Rate (Wave Continuity)

- **After every task commit:** run that task’s `<automated>` command from the map below.
- **After every wave merge:**
  - Wave 1 (`02-01`): `uv run pytest tests/phase2/test_contracts_and_policy.py -q`
  - Wave 2 (`02-02`): `uv run pytest tests/phase2/test_extraction_pipeline.py tests/phase2/test_knowledge_indexing.py tests/phase2/test_sop_generation.py -q`
  - Wave 3 (`02-03`): `uv run pytest tests/phase2/test_hybrid_retrieval.py tests/phase2/test_attribution_contract.py tests/phase2/test_low_relevance_fallback.py -q`
- **Before `/gsd-verify-work`:** `uv run pytest tests/ -v --tb=short`

Continuity check: there are **no gaps** in automated feedback; every task has explicit `<automated>` verify, so no 3-task blind run window exists.

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement Coverage | Automated Command | File Exists | Status |
|---------|------|------|----------------------|-------------------|-------------|--------|
| 02-01-01 | 02-01 | 1 | KNW-01, KNW-04 | `uv run pytest tests/phase2/test_contracts_and_policy.py::test_knowledge_unit_contract tests/phase2/test_contracts_and_policy.py::test_rag_answer_contract -q` | planned in task | ⬜ pending |
| 02-01-02 | 02-01 | 1 | KNW-01, KNW-03 | `uv run pytest tests/phase2/test_contracts_and_policy.py::test_publish_policy_threshold tests/phase2/test_contracts_and_policy.py::test_phase2_threshold_settings -q` | planned in task | ⬜ pending |
| 02-02-01 | 02-02 | 2 | KNW-01 | `uv run pytest tests/phase2/test_extraction_pipeline.py -q` | planned in task | ⬜ pending |
| 02-02-02 | 02-02 | 2 | KNW-03 | `uv run pytest tests/phase2/test_knowledge_indexing.py -q` | planned in task | ⬜ pending |
| 02-02-03 | 02-02 | 2 | KNW-02, KNW-04 | `uv run pytest tests/phase2/test_sop_generation.py -q` | planned in task | ⬜ pending |
| 02-03-01 | 02-03 | 3 | KNW-03, KNW-04 | `uv run pytest tests/phase2/test_hybrid_retrieval.py tests/phase2/test_attribution_contract.py -q` | planned in task | ⬜ pending |
| 02-03-02 | 02-03 | 3 | KNW-03, KNW-04 | `uv run pytest tests/phase2/test_low_relevance_fallback.py -q` | planned in task | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Requirement Coverage Cross-Check

| Requirement | Planned verification points |
|-------------|-----------------------------|
| KNW-01 | 02-01-01, 02-01-02, 02-02-01 |
| KNW-02 | 02-02-03 |
| KNW-03 | 02-01-02, 02-02-02, 02-03-01, 02-03-02 |
| KNW-04 | 02-01-01, 02-02-03, 02-03-01, 02-03-02 |

---

## Validation Sign-Off

- [x] Every task has `<automated>` verification (Nyquist rule satisfied)
- [x] Wave sampling continuity defined
- [x] KNW-01..KNW-04 mapped to automated checks
- [x] No watch-mode or manual-only commands in task verifies

**Approval:** ready for execution
