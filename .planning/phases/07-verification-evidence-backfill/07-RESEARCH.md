# Phase 7: Verification Evidence Backfill - Research

**Researched:** 2026-04-19  
**Domain:** Verification evidence backfill, deterministic milestone gate reconciliation  
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
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

### Deferred Ideas (OUT OF SCOPE)
- Functional fixes discovered during backfill are deferred into separate gap phases (out of scope for Phase 7 execution).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| ING-01 | PII anonymization before processing | 3-source row in 01-VERIFICATION with SUMMARY + validation command + code artifact; deterministic satisfied/orphaned rule |
| ING-02 | Telegram JSON parsing with metadata | Same evidence contract; phase-scope mapping in verification table |
| ING-03 | Voice transcription via Groq Whisper | Evidence row must include command/test proving transcription path |
| ING-04 | Telegram noise filtering | Evidence row must include filter test/contract + source file anchor |
| ING-05 | PDF text extraction | Evidence row must include parser evidence and validation command |
| ING-06 | Batch processing with progress tracking | Evidence row must include orchestration artifacts and runtime checks |
| KNW-01 | Structured knowledge extraction and grouping | Cross-phase verification row (Phase 2 + 4 evidence allowed) |
| KNW-02 | SOP generation | Must be evidenced in strict row; if missing third source -> unsatisfied |
| KNW-03 | Hybrid indexing/retrieval | Verified by API/tests + code artifact link in verification row |
| KNW-04 | Source attribution persistence | Must include attribution contract/test + code artifact |
| BOT-01 | Telegram Q&A over RAG | Cross-phase evidence from Phase 3/4 accepted if 3-source complete |
| BOT-02 | Low-confidence safe fallback | Must include deterministic fallback test/command + code path |
| BOT-03 | Multi-turn context | Must include context test + handler/graph code anchor |
| BOT-04 | Thumbs feedback capture | Must include feedback persistence test + code artifact |
</phase_requirements>

## Summary

Phase 7 — это не feature-delivery, а контрольная фаза консистентности доказательств: нужно превратить «есть SUMMARY и тесты где-то» в формально проверяемый слой `*-VERIFICATION.md` для фаз 1–4 с одинаковым шаблоном и одинаковым fail-правилом. [VERIFIED: .planning/phases/07-verification-evidence-backfill/07-CONTEXT.md]  
Текущий milestone audit явно фиксирует, что отсутствие `*-VERIFICATION.md` трактуется как orphaned/unsatisfied для ING/KNW/BOT(01-04), даже при наличии SUMMARY-артефактов. [VERIFIED: .planning/v1-MILESTONE-AUDIT.md]

Для планирования важно разделять два типа разрывов: evidence gaps и functional gaps. В рамках Phase 7 разрешено закрывать только evidence gaps и синхронизировать статусы в `REQUIREMENTS.md`, `v1-MILESTONE-AUDIT.md`, `ROADMAP.md` строго по evidence-таблицам; функциональные проблемы (например BOT-05 hardcoded role) должны только фиксироваться и маршрутизироваться в отдельные gap phases. [VERIFIED: .planning/phases/07-verification-evidence-backfill/07-CONTEXT.md] [VERIFIED: .planning/v1-MILESTONE-AUDIT.md]

**Primary recommendation:** Build a deterministic “verification-first reconciliation” workflow: generate/normalize 01-04 `*-VERIFICATION.md` first, then recompute traceability and milestone gate artifacts from those files only. [VERIFIED: .planning/phases/07-verification-evidence-backfill/07-CONTEXT.md]

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Build strict `*-VERIFICATION.md` for phases 1-4 | API / Backend | Database / Storage | Generation/reconciliation logic belongs to deterministic processing; markdown artifacts are persisted state. [ASSUMED] |
| Enforce 3-source requirement evidence gate | API / Backend | — | Rule evaluation is programmatic policy enforcement, not manual editing. [ASSUMED] |
| Recompute requirement statuses in REQUIREMENTS.md | API / Backend | Database / Storage | Status is derived from verification evidence and stored in docs. [VERIFIED: .planning/phases/07-verification-evidence-backfill/07-CONTEXT.md] |
| Recompute milestone gate in v1-MILESTONE-AUDIT.md | API / Backend | Database / Storage | Audit already encodes deterministic gate logic; Phase 7 extends inputs. [VERIFIED: .planning/v1-MILESTONE-AUDIT.md] |
| Update roadmap progress consistency | API / Backend | Database / Storage | ROADMAP progress is a derived reporting artifact after evidence reconciliation. [VERIFIED: .planning/phases/07-verification-evidence-backfill/07-CONTEXT.md] |
| Route functional gaps out-of-scope | API / Backend | — | Needs explicit branching decision in execution pipeline. [VERIFIED: .planning/phases/07-verification-evidence-backfill/07-CONTEXT.md] |

## Project Constraints (from copilot-instructions.md)

`./copilot-instructions.md` not found in repository root; no additional project-specific directives were discovered from that file. [VERIFIED: missing file check `/copilot-instructions.md`]

## Standard Stack

### Core
| Library/Tool | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Markdown phase artifacts (`*-VERIFICATION.md`, `REQUIREMENTS.md`, `ROADMAP.md`, `v1-MILESTONE-AUDIT.md`) | n/a | Canonical evidence and gate state | Existing milestone gate already consumes markdown artifacts and treats missing verification as fail. [VERIFIED: .planning/v1-MILESTONE-AUDIT.md] |
| Python | 3.12.4 | Deterministic parsing/reconciliation scripts | Available locally; good fit for structured markdown/frontmatter checks. [VERIFIED: `python3 --version`] |
| Git | 2.50.1 | Traceable evidence-change commits | Required for auditable deterministic updates. [VERIFIED: `git --version`] |

### Supporting
| Library/Tool | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| uv | 0.8.22 | Run project tests/commands consistently | Use for validation commands referenced as evidence (`uv run pytest ...`). [VERIFIED: `uv --version`] [VERIFIED: .planning/phases/02-knowledge-extraction-rag/02-VALIDATION.md] |
| Node.js | v24.5.0 | Optional helper scripts for repo tooling | Use only if existing GSD scripts are needed locally. [VERIFIED: `node --version`] |
| grep/awk/sed | system tools | Deterministic evidence extraction from existing docs | Fast fallback because `rg` is unavailable in this environment. [VERIFIED: `rg: command not found`] |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Deterministic recompute from `*-VERIFICATION.md` | Manual status edits in each artifact | Faster initially but violates D-08 and creates drift risk. [VERIFIED: .planning/phases/07-verification-evidence-backfill/07-CONTEXT.md] |
| Single strict template for 01-04 verification files | Phase-specific free-form templates | More local flexibility but breaks D-01 and comparability. [VERIFIED: .planning/phases/07-verification-evidence-backfill/07-CONTEXT.md] |

**Installation:**
```bash
# No new runtime packages required for research-backed execution baseline.
# Use existing project toolchain and scripts.
```

**Version verification:**  
- Python 3.12.4 [VERIFIED: `python3 --version`]  
- Node v24.5.0 [VERIFIED: `node --version`]  
- uv 0.8.22 [VERIFIED: `uv --version`]  
- git 2.50.1 [VERIFIED: `git --version`]

## Architecture Patterns

### System Architecture Diagram

```text
Phase Summaries + Validation + Code/Test Artifacts
        |
        v
[Evidence Collector]
  - locate candidate evidence per requirement
  - bind to phase scope (1..4)
        |
        v
[3-Source Verifier]
  - requires SUMMARY + test/command + code/contract
  - marks row satisfied/orphaned
        |
        +------------------------------+
        |                              |
        v                              v
[Phase VERIFICATION Writer]      [Functional Gap Router]
  - write 01..04-VERIFICATION     - record gap (no code fixes in Phase 7)
        |                              |
        +--------------+---------------+
                       v
              [Deterministic Reconciler]
              - update REQUIREMENTS traceability
              - update v1-MILESTONE-AUDIT gate
              - update ROADMAP progress
                       |
                       v
                  [Gate Verdict]
```

### Recommended Project Structure
```text
.planning/
├── phases/
│   ├── 01-foundation-data-ingestion/
│   │   └── 01-VERIFICATION.md     # strict verification artifact
│   ├── 02-knowledge-extraction-rag/
│   │   └── 02-VERIFICATION.md
│   ├── 03-telegram-bot/
│   │   └── 03-VERIFICATION.md
│   └── 04-runtime-integration/
│       └── 04-VERIFICATION.md
├── REQUIREMENTS.md                 # reconciled statuses
├── v1-MILESTONE-AUDIT.md           # recomputed gate output
└── ROADMAP.md                      # progress consistency update
```

### Pattern 1: Strict Requirement-Evidence Row
**What:** Каждая requirement-строка в `VERIFICATION.md` должна содержать 3 обязательных источника доказательства и итог `verdict`. [VERIFIED: .planning/phases/07-verification-evidence-backfill/07-CONTEXT.md]  
**When to use:** Для всех ING/KNW/BOT(01-04) в фазах 1–4 без исключений. [VERIFIED: .planning/ROADMAP.md]  
**Example:**
```markdown
| Requirement | summary_evidence | test_or_command_evidence | code_or_contract_evidence | verdict |
|-------------|------------------|--------------------------|---------------------------|---------|
| KNW-03 | 02-03-SUMMARY.md#requirements-completed | tests/phase2/test_hybrid_retrieval.py + uv run pytest ... | src/api/routes/knowledge.py | satisfied |
```

### Pattern 2: Deterministic Gate Recompute
**What:** Статусы в `REQUIREMENTS.md` и `v1-MILESTONE-AUDIT.md` обновляются только после парсинга `*-VERIFICATION.md`, не «по памяти». [VERIFIED: .planning/phases/07-verification-evidence-backfill/07-CONTEXT.md]  
**When to use:** После завершения/изменения любого phase verification файла. [ASSUMED]  
**Example:**
```bash
# Source pattern: milestone gate treats missing VERIFICATION as orphaned
# .planning/v1-MILESTONE-AUDIT.md
python scripts/reconcile_verification.py \
  --phase 1 --phase 2 --phase 3 --phase 4 \
  --requirements .planning/REQUIREMENTS.md \
  --audit .planning/v1-MILESTONE-AUDIT.md \
  --roadmap .planning/ROADMAP.md
```

### Anti-Patterns to Avoid
- **SUMMARY-only satisfaction:** запрещено D-06; не засчитывать requirement без verification row. [VERIFIED: .planning/phases/07-verification-evidence-backfill/07-CONTEXT.md]
- **Manual status patching across files:** приводит к drift и нарушает D-08. [VERIFIED: .planning/phases/07-verification-evidence-backfill/07-CONTEXT.md]
- **Mixing evidence backfill with feature fixes:** нарушает D-09 и размывает ответственность Phase 7. [VERIFIED: .planning/phases/07-verification-evidence-backfill/07-CONTEXT.md]

## Implementation Strategy (Phase 7)

1. **Inventory evidence inputs (read-only pass):** собрать candidate evidence из `01..04-SUMMARY`, `01..04-VALIDATION`, тестов и ключевых code artifacts. [VERIFIED: required-read list + repository files]  
2. **Create strict 01..04 `*-VERIFICATION.md`:** единый шаблон, requirement rows only, 3-source columns mandatory. [VERIFIED: D-01..D-04 in 07-CONTEXT]  
3. **Run deterministic verdict pass:** для каждой requirement строки вычислить `satisfied|orphaned|unsatisfied` по completeness и quality evidence. [ASSUMED]  
4. **Reconcile traceability artifacts:** обновить `REQUIREMENTS.md`, `.planning/v1-MILESTONE-AUDIT.md`, `ROADMAP.md` только от новых verification rows. [VERIFIED: D-07..D-08 in 07-CONTEXT]  
5. **Functional gap routing:** любой code/runtime gap только логируется и отправляется в отдельную gap-phase backlog. [VERIFIED: D-09 in 07-CONTEXT]

## Sequencing (Deterministic)

1. Phase 1 verification backfill (highest risk: `01-VALIDATION.md` currently `nyquist_compliant: false`). [VERIFIED: .planning/phases/01-foundation-data-ingestion/01-VALIDATION.md]  
2. Phase 2 verification backfill. [VERIFIED: .planning/phases/02-knowledge-extraction-rag/02-VALIDATION.md]  
3. Phase 3 verification backfill. [VERIFIED: .planning/phases/03-telegram-bot/03-VALIDATION.md]  
4. Phase 4 verification backfill. [VERIFIED: .planning/phases/04-runtime-integration/04-VALIDATION.md]  
5. Global reconciliation: REQUIREMENTS -> MILESTONE-AUDIT -> ROADMAP progress. [VERIFIED: D-07 in 07-CONTEXT]

## Required Artifacts

| Artifact | Required | Purpose |
|----------|----------|---------|
| `.planning/phases/01-foundation-data-ingestion/01-VERIFICATION.md` | Yes | Close ING evidence orphaning at phase source. [VERIFIED: .planning/v1-MILESTONE-AUDIT.md] |
| `.planning/phases/02-knowledge-extraction-rag/02-VERIFICATION.md` | Yes | Provide KNW 3-source proof matrix. [VERIFIED: .planning/ROADMAP.md] |
| `.planning/phases/03-telegram-bot/03-VERIFICATION.md` | Yes | Provide BOT(01-04) phase-level proof rows. [VERIFIED: .planning/ROADMAP.md] |
| `.planning/phases/04-runtime-integration/04-VERIFICATION.md` | Yes | Capture runtime closure evidence for KNW/BOT links. [VERIFIED: .planning/ROADMAP.md] |
| `.planning/REQUIREMENTS.md` | Update | Traceability status sync from verification outcomes. [VERIFIED: D-07 in 07-CONTEXT] |
| `.planning/v1-MILESTONE-AUDIT.md` | Update | Deterministic gate recomputation from verification source. [VERIFIED: D-07 in 07-CONTEXT] |
| `.planning/ROADMAP.md` | Update | Progress reflection after reconciliation. [VERIFIED: D-07 in 07-CONTEXT] |

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Requirement status reconciliation | Manual spreadsheet/notebook tracking | Deterministic parser over `*-VERIFICATION.md` rows | Prevents subjective status drift and enforces D-08. [VERIFIED: .planning/phases/07-verification-evidence-backfill/07-CONTEXT.md] |
| Evidence completeness checks | Human eyeballing | Explicit 3-source completeness rule per row | D-03/D-04 requires objective pass/fail criteria. [VERIFIED: .planning/phases/07-verification-evidence-backfill/07-CONTEXT.md] |
| Gate status mutation | Direct text edits in multiple files first | Single-source-first update (`VERIFICATION` -> derived artifacts) | Keeps traceability deterministic and auditable. [ASSUMED] |

**Key insight:** In this phase, automation discipline matters more than implementation volume; deterministic evidence derivation is the product. [ASSUMED]

## Common Pitfalls

### Pitfall 1: Evidence Inflation
**What goes wrong:** requirement помечается `satisfied`, хотя одна из 3 обязательных ссылок отсутствует. [VERIFIED: D-03/D-04 in 07-CONTEXT]  
**Why it happens:** попытка «дотянуть» статус из SUMMARY-only. [VERIFIED: D-06 in 07-CONTEXT]  
**How to avoid:** blocking check: if any evidence column empty -> `orphaned/unsatisfied`. [ASSUMED]  
**Warning signs:** строки с `satisfied`, где нет test/command или code anchor. [ASSUMED]

### Pitfall 2: Cross-Artifact Drift
**What goes wrong:** `REQUIREMENTS.md` и `MILESTONE-AUDIT` показывают разные статусы одной requirement. [ASSUMED]  
**Why it happens:** файлы правятся вручную в разном порядке. [ASSUMED]  
**How to avoid:** фиксированный pipeline: `VERIFICATION` first, then deterministic reconcile in one run. [VERIFIED: D-08 in 07-CONTEXT]  
**Warning signs:** gate summary contradicts requirement traceability table. [ASSUMED]

### Pitfall 3: Scope Contamination
**What goes wrong:** в Phase 7 начинают чинить кодовые functional gaps. [VERIFIED: D-09 in 07-CONTEXT]  
**Why it happens:** evidence review находит реальные баги, и команда смешивает workstreams. [ASSUMED]  
**How to avoid:** отдельный gap register + explicit out-of-scope marker in VERIFICATION notes. [VERIFIED: D-09 in 07-CONTEXT]  
**Warning signs:** commits touching production code under Phase 7 without explicit re-scope decision. [ASSUMED]

## Risks and Guardrails

| Risk | Impact | Guardrail |
|------|--------|-----------|
| Missing third evidence source for many rows | Gate remains blocked | Enforce row-level completeness gate before status assignment. [VERIFIED: D-03/D-04 in 07-CONTEXT] |
| Ambiguous evidence linkage to requirement IDs | False positives/negatives | Require explicit requirement ID in every evidence note and command reference. [ASSUMED] |
| Hidden functional gaps discovered | Scope creep | Mark as `functional-gap` and route to separate phase only. [VERIFIED: D-09 in 07-CONTEXT] |
| Tooling mismatch (`gsd-sdk` unavailable locally) | Planned command cannot run | Use shell+python fallback scripts; keep outputs reproducible. [VERIFIED: `gsd-sdk: MISSING`] |

## Code Examples

Verified patterns from repository artifacts:

### Detect missing phase verification files
```bash
# Source: milestone currently reports missing *-VERIFICATION.md for phases 1-4
# .planning/v1-MILESTONE-AUDIT.md
find .planning/phases -maxdepth 2 -name '*-VERIFICATION.md' -print | sort
```

### Cross-check existing requirement declarations in summaries
```bash
# Source: frontmatter uses requirements-completed lists in phase summaries
grep -nE "^requirements-completed:|^  - [A-Z]+-[0-9]+" \
  .planning/phases/01-foundation-data-ingestion/*-SUMMARY.md \
  .planning/phases/02-knowledge-extraction-rag/*-SUMMARY.md \
  .planning/phases/03-telegram-bot/*-SUMMARY.md \
  .planning/phases/04-runtime-integration/*-SUMMARY.md
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| SUMMARY-driven implicit completion | Verification-driven strict 3-source completion | 2026-04-19 context decisions | Converts subjective completion into deterministic gate input. [VERIFIED: .planning/phases/07-verification-evidence-backfill/07-CONTEXT.md] |
| Missing VERIFICATION treated as documentation gap | Missing VERIFICATION treated as orphaned/unsatisfied gate failure | 2026-04-19 milestone audit policy | Forces explicit phase-level evidence artifacts before milestone close. [VERIFIED: .planning/v1-MILESTONE-AUDIT.md] |

**Deprecated/outdated:**
- `SUMMARY-only` completion as sufficient verification evidence. [VERIFIED: D-06 in 07-CONTEXT]

## Explicit Out-of-Scope Handling for Functional Gaps

- If backfill finds runtime/auth/business logic defects (e.g., BOT-05 hardcoded role currently noted in audit), Phase 7 must **not** modify functional code. [VERIFIED: .planning/v1-MILESTONE-AUDIT.md] [VERIFIED: D-09 in 07-CONTEXT]  
- Such findings must be logged as `functional-gap` with requirement ID, evidence link, and suggested target phase (`gap-phase`). [ASSUMED]  
- Verification row for affected requirement should remain `unsatisfied` until that gap-phase delivers and verifies code changes. [ASSUMED]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Capability-tier mapping should be treated as API/Backend + Storage for this docs reconciliation phase. | Architectural Responsibility Map | Planner may mis-assign tasks by subsystem. |
| A2 | A single scripted reconcile pass is available/should be created to update three artifacts atomically. | Pattern 2 / Implementation Strategy | Could require manual but controlled multi-step updates. |
| A3 | Requirement verdict vocabulary `satisfied/orphaned/unsatisfied` can be enforced row-level in verification files. | Implementation Strategy / Pitfalls | Status schema mismatch could break downstream parser assumptions. |
| A4 | Functional-gap logging format (`functional-gap`) should be introduced as marker taxonomy. | Out-of-Scope Handling | Inconsistent routing if taxonomy differs from project convention. |

## Open Questions (RESOLVED)

1. **Нужен ли единый machine-readable frontmatter schema для `*-VERIFICATION.md`?**  
   - Resolution: да, фиксируем единый schema: frontmatter (`phase`, `status`, `updated`, `requirements_total`, `requirements_satisfied`, `requirements_partial`, `requirements_unsatisfied`, `requirements_orphaned`) + обязательная requirements table. [VERIFIED: 07-CONTEXT D-01/D-02]  
   - Parser policy: `scripts/verify_backfill.py` валидирует и frontmatter, и requirements table; markdown-table only считается incomplete artifact.

2. **Где хранить functional-gap register, обнаруженный в backfill?**  
   - Resolution: canonical register file = `.planning/functional-gaps.md`. [VERIFIED: 07-CONTEXT D-09]  
   - Recording format: requirement_id, phase, evidence link, severity, suggested gap-phase.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| python3 | deterministic reconciliation scripts | ✓ | 3.12.4 | — |
| uv | running referenced verification tests | ✓ | 0.8.22 | `python -m pytest ...` |
| git | auditable artifact updates | ✓ | 2.50.1 | — |
| node | optional repo tooling helpers | ✓ | v24.5.0 | pure Python/bash scripts |
| gsd-sdk | optional init/commit helper commands from generic workflow | ✗ | — | direct shell + git workflow |

**Missing dependencies with no fallback:**
- None identified for Phase 7 backfill scope. [VERIFIED: command availability checks]

**Missing dependencies with fallback:**
- `gsd-sdk` missing; use repository-local deterministic scripts and direct git commits. [VERIFIED: `gsd-sdk: MISSING`]

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (project standard) + markdown consistency checks |
| Config file | `pyproject.toml` |
| Quick run command | `uv run pytest tests/ -q --maxfail=1` |
| Full suite command | `uv run pytest tests/ -v --tb=short` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ING-01..ING-06 | 3-source verification rows exist and pass completeness rules | integration (docs gate) | `python scripts/verify_backfill.py --phase 1` | ❌ Wave 0 |
| KNW-01..KNW-04 | verification rows linked to summary+test+code evidence | integration (docs gate) | `python scripts/verify_backfill.py --phase 2 --phase 4` | ❌ Wave 0 |
| BOT-01..BOT-04 | bot requirements have strict evidence rows and deterministic verdicts | integration (docs gate) | `python scripts/verify_backfill.py --phase 3 --phase 4` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `python scripts/verify_backfill.py --changed-only` [ASSUMED]
- **Per wave merge:** `python scripts/verify_backfill.py --phase 1 --phase 2 --phase 3 --phase 4` [ASSUMED]
- **Phase gate:** full suite + backfill verifier green before `/gsd-verify-work`. [ASSUMED]

### Wave 0 Gaps
- [ ] `scripts/verify_backfill.py` — deterministic 3-source completeness and status recompute engine
- [ ] `tests/planning/test_verification_backfill_rules.py` — parser/validator regression tests
- [ ] `tests/planning/test_traceability_reconcile.py` — REQUIREMENTS/AUDIT/ROADMAP sync checks

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | n/a (docs reconciliation scope) [ASSUMED] |
| V3 Session Management | no | n/a (docs reconciliation scope) [ASSUMED] |
| V4 Access Control | no | n/a in phase deliverable; handled by separate functional phases [VERIFIED: D-09 context scope] |
| V5 Input Validation | yes | strict schema validation for requirement IDs and evidence columns in `VERIFICATION.md` [ASSUMED] |
| V6 Cryptography | no | no cryptographic primitives introduced in Phase 7 [ASSUMED] |

### Known Threat Patterns for verification-backfill stack

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Evidence spoofing (fake satisfied row without real links) | Tampering | enforce 3-source completeness + resolvable file anchors [VERIFIED: D-03/D-04 in 07-CONTEXT] |
| Silent status drift across artifacts | Repudiation/Tampering | deterministic single-source reconcile from `*-VERIFICATION.md` [VERIFIED: D-08 in 07-CONTEXT] |
| Scope creep via hidden functional fixes | Elevation of Privilege (process) | explicit out-of-scope route for functional gaps (D-09) [VERIFIED: D-09 in 07-CONTEXT] |

## Sources

### Primary (HIGH confidence)
- `.planning/phases/07-verification-evidence-backfill/07-CONTEXT.md` — locked decisions D-01..D-09, scope, synchronization policy.
- `.planning/v1-MILESTONE-AUDIT.md` — current orphaned logic, fail-gate behavior, existing gaps.
- `.planning/ROADMAP.md` — Phase 7 requirements/success criteria and phase dependencies.
- `.planning/REQUIREMENTS.md` — requirement IDs, current traceability statuses.
- `.planning/STATE.md` — current execution position and phase completion state.
- `.planning/phases/01-foundation-data-ingestion/01-VALIDATION.md` — phase 1 nyquist status false.
- `.planning/phases/02-knowledge-extraction-rag/02-VALIDATION.md` — phase 2 validation baseline.
- `.planning/phases/03-telegram-bot/03-VALIDATION.md` — phase 3 validation baseline.
- `.planning/phases/04-runtime-integration/04-VALIDATION.md` — phase 4 validation baseline.
- Shell environment probes (`python3 --version`, `node --version`, `uv --version`, `git --version`, `command -v gsd-sdk`) — dependency availability.

### Secondary (MEDIUM confidence)
- None.

### Tertiary (LOW confidence)
- None.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - mostly repository-local tooling and directly verified local versions.
- Architecture: MEDIUM - policy and flow strongly constrained by context, but some tier mapping is process-level assumption.
- Pitfalls: HIGH - directly aligned with locked decisions and current milestone audit failures.

**Research date:** 2026-04-19  
**Valid until:** 2026-05-19
