# Phase 7: Verification Evidence Backfill - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-19
**Phase:** 07-verification-evidence-backfill
**Areas discussed:** VERIFICATION format, evidence policy, gate status policy, artifact sync, gap handling

---

## VERIFICATION format

| Option | Description | Selected |
|--------|-------------|----------|
| Единый строгий шаблон для всех фаз | Обязательные секции и единый формат | ✓ |
| Базовый шаблон + свободные секции по фазе | Частично унифицировано | |
| Минимальный формат | Только статус + таблица | |

**User's choice:** Единый строгий шаблон для всех фаз  
**Notes:** Фиксируем обязательные секции для фаз 1-4.

---

## Evidence policy

| Option | Description | Selected |
|--------|-------------|----------|
| 3-source обязательно | SUMMARY + test/command + code/contract | ✓ |
| 2-source | SUMMARY + test/command | |
| Только test/command | Упрощённая доказательная база | |

**User's choice:** 3-source обязательно  
**Notes:** Requirement без 3-source не считается satisfied.

---

## Gate status policy

| Option | Description | Selected |
|--------|-------------|----------|
| Строгая orphaned/unsatisfied | Нет VERIFICATION => fail gate | ✓ |
| Мягкая partial | Нет VERIFICATION => partial | |
| Auto-satisfied по SUMMARY | VERIFICATION не обязателен | |

**User's choice:** Строгая orphaned/unsatisfied  
**Notes:** SUMMARY-only подтверждение запрещено.

---

## Artifact synchronization

| Option | Description | Selected |
|--------|-------------|----------|
| REQUIREMENTS + MILESTONE-AUDIT + ROADMAP progress | Полная синхронизация в этом цикле | ✓ |
| Только MILESTONE-AUDIT | Частичная синхронизация | |
| Только REQUIREMENTS | Минимальная синхронизация | |

**User's choice:** REQUIREMENTS + MILESTONE-AUDIT + ROADMAP progress  
**Notes:** Изменения должны следовать verification evidence.

---

## Functional gaps discovered during backfill

| Option | Description | Selected |
|--------|-------------|----------|
| Не чинить в Phase 7 | Фиксировать и маршрутизировать в отдельную gap-phase | ✓ |
| Чинить сразу в Phase 7 | Смешивать evidence+implementation | |
| Ad-hoc | Без единого правила | |

**User's choice:** Не чинить в Phase 7  
**Notes:** Phase 7 = evidence backfill, не feature-fix phase.

---

## the agent's Discretion

- Детали табличной структуры внутри строгого шаблона.
- Последовательность обработки фаз 1-4 при backfill.

## Deferred Ideas

- Любые функциональные фиксы, найденные в процессе backfill — в отдельные gap phases.
