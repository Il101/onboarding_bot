# Phase 7: Verification Evidence Backfill - Context

**Gathered:** 2026-04-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Закрыть orphaned verification evidence gaps для фаз 1-4: создать/обновить phase-level `*-VERIFICATION.md`, провести строгую 3-source верификацию требований и синхронизировать audit/traceability артефакты без изменения продуктового scope.

</domain>

<decisions>
## Implementation Decisions

### Verification format policy
- **D-01:** Для фаз 1-4 используется единый строгий шаблон `VERIFICATION.md` без произвольных упрощений.
- **D-02:** В каждом `VERIFICATION.md` обязательны: status, requirement map/table, evidence links, gate verdict.

### Evidence requirements policy
- **D-03:** Для каждой requirement-строки обязательна 3-source доказательная база: `SUMMARY` + `test/command` + `code/contract artifact`.
- **D-04:** Requirement без полного 3-source набора не может считаться satisfied.

### Status and gate policy
- **D-05:** Политика статусов строгая: отсутствие `VERIFICATION.md` трактуется как `orphaned/unsatisfied` в milestone gate.
- **D-06:** `SUMMARY-only` подтверждение без verification evidence запрещено.

### Artifact synchronization policy
- **D-07:** В рамках Phase 7 после backfill обновляются `REQUIREMENTS.md`, `.planning/v1-MILESTONE-AUDIT.md` и прогресс в `ROADMAP.md`.
- **D-08:** Обновления делаются детерминированно от verification evidence, а не вручную "по ощущениям".

### Gap handling policy
- **D-09:** Если найден реальный functional gap (не evidence gap), Phase 7 не чинит код; gap фиксируется и маршрутизируется в отдельную gap-phase.

### the agent's Discretion
- Конкретный формат таблиц внутри строгого шаблона (при сохранении обязательных секций D-02).
- Порядок обхода фаз 1-4 во время backfill (по риску или по номеру).
- Детали формулировок evidence notes, если они остаются проверяемыми и трассируемыми.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Milestone gates and scope
- `.planning/ROADMAP.md` — Phase 7 boundary, dependencies, success criteria.
- `.planning/REQUIREMENTS.md` — Traceability table и текущие статусы REQ.
- `.planning/v1-MILESTONE-AUDIT.md` — Orphaned/unsatisfied gaps, gate logic.
- `.planning/STATE.md` — Текущая milestone execution позиция.

### Upstream phase evidence (inputs for backfill)
- `.planning/phases/01-foundation-data-ingestion/*-SUMMARY.md` — факты о выполненных deliverables.
- `.planning/phases/02-knowledge-extraction-rag/*-SUMMARY.md` — факты по KNW coverage.
- `.planning/phases/03-telegram-bot/*-SUMMARY.md` — факты по BOT coverage.
- `.planning/phases/04-runtime-integration/*-SUMMARY.md` — gap-closure результаты runtime integration.
- `.planning/phases/01-foundation-data-ingestion/01-VALIDATION.md`
- `.planning/phases/02-knowledge-extraction-rag/02-VALIDATION.md`
- `.planning/phases/03-telegram-bot/03-VALIDATION.md`
- `.planning/phases/04-runtime-integration/04-VALIDATION.md`
- `.planning/phases/01-foundation-data-ingestion/01-SECURITY.md`
- `.planning/phases/02-knowledge-extraction-rag/02-SECURITY.md`
- `.planning/phases/03-telegram-bot/03-SECURITY.md`
- `.planning/phases/04-runtime-integration/04-SECURITY.md`
- `.planning/phases/01-foundation-data-ingestion/01-UAT.md`
- `.planning/phases/02-knowledge-extraction-rag/02-UAT.md`
- `.planning/phases/03-telegram-bot/03-UAT.md`
- `.planning/phases/04-runtime-integration/4-UAT.md`

### Existing decision context
- `.planning/phases/01-foundation-data-ingestion/01-CONTEXT.md`
- `.planning/phases/02-knowledge-extraction-rag/02-CONTEXT.md`
- `.planning/phases/03-telegram-bot/03-CONTEXT.md`

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- Existing `*-SUMMARY.md` frontmatter `requirements-completed` fields already map many requirements.
- Existing `*-VALIDATION.md`, `*-SECURITY.md`, `*-UAT.md` provide supporting evidence anchors for verification backfill.

### Established Patterns
- Phase artifacts live under `.planning/phases/{NN}-{slug}/` and are phase-scoped.
- Gate decisions are persisted in structured markdown with frontmatter and machine-readable sections.

### Integration Points
- New/updated `*-VERIFICATION.md` for phases 1-4 feed directly into milestone audit recomputation.
- `REQUIREMENTS.md` traceability and top-level checkbox state must align with new verification outcomes.
- `ROADMAP.md` progress rows must reflect post-backfill reality.

</code_context>

<specifics>
## Specific Ideas

- Focus first on evidence integrity, not feature implementation.
- Keep Phase 7 deterministic and auditable: every status change must cite concrete artifacts.

</specifics>

<deferred>
## Deferred Ideas

- Functional fixes discovered during backfill are deferred into separate gap phases (out of scope for Phase 7 execution).

</deferred>

---

*Phase: 07-verification-evidence-backfill*
*Context gathered: 2026-04-19*
