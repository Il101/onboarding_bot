# Phase 5: Bot Access Hardening - Research

**Researched:** 2026-04-19  
**Domain:** Telegram bot authorization hardening (whitelist `user_id` + non-hardcoded role source)  
**Confidence:** HIGH

## User Constraints

- No `05-CONTEXT.md` exists in `.planning/phases/05-bot-access-hardening`, so there are no additional locked discuss-phase decisions to copy verbatim. [VERIFIED: .planning/phases/05-bot-access-hardening directory listing]
- Phase scope is constrained to BOT-05 hardening only; BOT-01..BOT-04 are already implemented and verified in earlier phases. [VERIFIED: .planning/ROADMAP.md] [VERIFIED: .planning/REQUIREMENTS.md] [VERIFIED: .planning/v1-MILESTONE-AUDIT.md]

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| BOT-05 | Доступ к боту только для авторизованных сотрудников (проверка роли при /start) | Replaces hardcoded role resolution with `user_id -> role` whitelist source; enforces deny-before-graph and deny-in-graph invariants; adds deterministic tests proving no retrieval/LLM path for unauthorized users. [VERIFIED: .planning/REQUIREMENTS.md] [VERIFIED: src/bot/telegram_app.py] [VERIFIED: src/ai/langgraph/graph.py] |

## Summary

Current BOT-05 behavior is functionally incomplete: `resolve_role_for_update()` always returns `"employee"`, which means authorization is effectively hardcoded and independent of Telegram `user_id`. [VERIFIED: src/bot/telegram_app.py] Because `is_authorized_role("employee")` passes against `telegram_allowed_roles`, unauthorized Telegram accounts can pass the transport gate if role resolver is not monkeypatched in tests. [VERIFIED: src/bot/auth.py] [VERIFIED: src/core/config.py] This is the exact gap called out in milestone audit as “whitelist/role source integration pending.” [VERIFIED: .planning/v1-MILESTONE-AUDIT.md]

Phase 5 should implement a single, explicit authorization source for Telegram users: a whitelist mapping keyed by Telegram `user_id` with role values (`employee|mentor|admin`) loaded from configuration (env-backed settings) for now, with a clean repository seam for DB migration in Phase 6. [VERIFIED: .planning/ROADMAP.md] [VERIFIED: src/core/config.py] [VERIFIED: src/api/deps.py] This satisfies the success criteria without introducing migration infrastructure that does not exist yet in this repo. [VERIFIED: .planning/ROADMAP.md] [VERIFIED: repository scan: no alembic/migrations directory]

**Primary recommendation:** Implement `user_id`-based access map in `Settings`, resolve role from that map (not hardcoded), and enforce deny path at both Telegram transport edge and LangGraph auth node before retrieval invocation. [VERIFIED: src/bot/telegram_app.py] [VERIFIED: src/ai/langgraph/graph.py]

## Project Constraints (from copilot-instructions.md)

- `./copilot-instructions.md` is absent at repo root; no additional root-level project directives were found. [VERIFIED: path check for ./copilot-instructions.md]
- `.github/copilot-instructions.md` says to run GSD workflows only on explicit user request; this request is explicitly Phase research, so GSD workflow usage is in-scope. [VERIFIED: .github/copilot-instructions.md]

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Telegram identity extraction (`effective_user.id`) | Browser/Client (Telegram app provides identity) | API/Backend (bot receives update) | Telegram sends immutable `user_id` in update; backend must trust-but-verify against local policy. [VERIFIED: src/bot/telegram_app.py] [CITED: /python-telegram-bot/python-telegram-bot docs on Update handlers] |
| Authorization decision (allow/deny + reason) | API/Backend | — | Access control policy belongs server-side, not in Telegram client. [VERIFIED: src/bot/auth.py] |
| Whitelist + role source of truth | API/Backend config tier | Database/Storage (future admin-managed source) | Phase 5 can use settings-backed source; Phase 6 likely introduces managed users/roles. [VERIFIED: .planning/ROADMAP.md] [VERIFIED: src/core/config.py] |
| Deny-path short-circuit before retrieval/LLM | API/Backend | AI orchestration tier | Transport must deny before graph call; graph auth node must also deny for defense-in-depth. [VERIFIED: src/bot/telegram_app.py] [VERIFIED: src/ai/langgraph/graph.py] |

## Current-State Diagnosis (Exact Gap Cause)

1. `resolve_role_for_update(update)` returns constant `"employee"` (hardcoded). [VERIFIED: src/bot/telegram_app.py]  
2. `is_authorized_role()` only checks role membership in `settings.telegram_allowed_roles`, not `user_id` whitelist. [VERIFIED: src/bot/auth.py] [VERIFIED: src/core/config.py]  
3. Therefore access control is role-string based and decoupled from actual Telegram identity, violating Phase 5 goal (“real authorization via whitelist user_id”). [VERIFIED: .planning/ROADMAP.md]  
4. Existing tests validate branch shape but primarily via monkeypatched role resolver (`guest`/`employee`), not real whitelist source integration. [VERIFIED: tests/phase3/test_auth_gate.py]  

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| python-telegram-bot | 22.5 locked (`pyproject`), 22.7 latest (2026-03-16) | Telegram transport handlers and update routing | Official async handler framework with `Application.builder()`, `CommandHandler`, `MessageHandler`, `CallbackQueryHandler`. [VERIFIED: pyproject.toml] [VERIFIED: PyPI JSON query] [CITED: /python-telegram-bot/python-telegram-bot docs] |
| pydantic-settings | 2.13.1 latest (2026-02-19) | Typed env-backed access policy config | Native `BaseSettings` + `SettingsConfigDict(env_file=...)` matches current config style. [VERIFIED: src/core/config.py] [VERIFIED: PyPI JSON query] [CITED: /pydantic/pydantic-settings docs] |
| LangGraph | 0.6.11 locked (uv.lock), 1.1.8 latest | Defense-in-depth graph auth routing and checkpointed thread execution | Existing graph already uses `StateGraph`, conditional edges, and checkpointer. [VERIFIED: uv.lock] [VERIFIED: src/ai/langgraph/graph.py] [CITED: /websites/langchain_oss_python_langgraph docs] |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| SQLAlchemy | 2.0.49 | Optional future DB-backed role store | Use when Phase 6 introduces admin-managed users/roles and persistence migrations. [VERIFIED: pyproject.toml] [VERIFIED: src/api/deps.py] |
| pytest + pytest-asyncio | 8.3.4 installed / 9.0.3 latest | Deterministic unit/integration policy tests | Use for auth gate invariants and retrieval short-circuit tests. [VERIFIED: pyproject.toml] [VERIFIED: tests/phase3/test_auth_gate.py] [VERIFIED: PyPI JSON query] |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Settings-based whitelist map (recommended now) | DB table (`telegram_users`) | DB source is better for runtime admin changes, but repo currently has no migration framework, increasing Phase 5 scope/risk. [VERIFIED: src/models/] [VERIFIED: repository scan: no alembic/migrations directory] |

**Installation:**
```bash
uv sync
```

## Architecture Patterns

### System Architecture Diagram

```text
Telegram Update (/start or message)
  -> telegram_app.handle_start/handle_message
    -> extract effective_user.id
      -> access_policy.resolve(user_id) from Settings map
        -> [DENY] build_access_denied_answer -> presenter -> reply_text
        -> [ALLOW] graph.ainvoke(state includes user_id + resolved role)
             -> graph.auth_node (re-check user_id/role via same policy)
               -> [DENY] deny node END
               -> [ALLOW] retrieve -> summarize -> decide -> answer/fallback
                    -> presenter + feedback keyboard -> reply_text
```

### Recommended Project Structure
```text
src/
├── bot/
│   ├── auth.py              # access policy models + authorize(user_id, role)
│   ├── telegram_app.py      # transport handlers; auth gate at entry
│   └── presenters.py        # deterministic user-visible formatting
├── core/
│   └── config.py            # whitelist and role mapping source
└── ai/langgraph/
    └── graph.py             # defense-in-depth auth route before retrieve
```

### Pattern 1: Policy Source Adapter (Config-first)
**What:** Add explicit typed settings such as `telegram_user_roles: dict[int, str]` and derive allow/role from this map. [VERIFIED: src/core/config.py]  
**When to use:** Phase 5 immediate hardening with no DB migrations. [VERIFIED: .planning/ROADMAP.md]  
**Example:**
```python
# Source: /pydantic/pydantic-settings docs + src/core/config.py pattern
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    telegram_user_roles: dict[int, str] = {}
```

### Pattern 2: Auth-at-Edge + Auth-in-Graph
**What:** Enforce deny at transport handler before graph call, and keep graph auth node as backup guard. [VERIFIED: src/bot/telegram_app.py] [VERIFIED: src/ai/langgraph/graph.py]  
**When to use:** Always for sensitive internal knowledge bot access. [VERIFIED: .planning/REQUIREMENTS.md]  
**Example:**
```python
# Source: src/bot/telegram_app.py + src/ai/langgraph/graph.py
if not decision.allowed:
    await update.message.reply_text(text=render_bot_message(denied))
    return
# only then call graph.ainvoke(...)
```

### Anti-Patterns to Avoid
- **Hardcoded default role (`"employee"`)**: bypasses real identity binding and violates BOT-05 intent. [VERIFIED: src/bot/telegram_app.py] [VERIFIED: .planning/ROADMAP.md]
- **Role-only check without `user_id` source**: allows any user represented as allowed role. [VERIFIED: src/bot/auth.py]
- **Single-layer gate only in decide-node**: increases risk of accidental retrieval call if transport logic regresses; keep dual-layer checks. [VERIFIED: src/ai/langgraph/graph.py]

## Recommended Data Source for Whitelist + Role Mapping

**Phase 5 default:** `Settings`-backed whitelist role map (`telegram_user_roles`) loaded from env/.env (JSON string or structured env parser), keyed by Telegram numeric `user_id`, value in `telegram_allowed_roles`. [VERIFIED: src/core/config.py] [CITED: /pydantic/pydantic-settings docs]  

**Default authorization rule:**  
- `user_id` missing from map -> deny (`reason=not_whitelisted`) [ASSUMED]  
- `user_id` present but role not in allowed roles -> deny (`reason=role_not_allowed`) [VERIFIED: src/bot/auth.py] [ASSUMED]  
- `user_id` present + role allowed -> allow [VERIFIED: src/bot/auth.py] [ASSUMED]  

## Implementation Steps (Mapped to Code Files)

1. **`src/core/config.py`**  
   - Add typed policy source fields: `telegram_user_roles` (dict) and optional `telegram_access_policy_version` for observability. [VERIFIED: existing settings pattern in src/core/config.py]  
   - Keep `telegram_allowed_roles` as role vocabulary guardrail. [VERIFIED: src/core/config.py]

2. **`src/bot/auth.py`**  
   - Introduce `resolve_role_for_user_id(user_id: int) -> str | None` from settings map. [ASSUMED]  
   - Replace role-only decision entrypoint with `authorize_telegram_user(user_id: int) -> AuthDecision` returning `allowed`, `reason`, `role`. [ASSUMED]  
   - Preserve `build_access_denied_answer` behavior for consistent UX. [VERIFIED: src/bot/auth.py]

3. **`src/bot/telegram_app.py`**  
   - Replace hardcoded `resolve_role_for_update` with `user_id` lookup via auth module. [VERIFIED: src/bot/telegram_app.py]  
   - `/start` and message handlers: deny immediately on unauthorized `user_id` before graph invocation. [VERIFIED: src/bot/telegram_app.py]  
   - Pass resolved role from policy into graph state for downstream policy branches. [VERIFIED: src/bot/telegram_app.py]

4. **`src/ai/langgraph/graph.py` (+ optionally `nodes/decide.py`)**  
   - Auth node should validate user authorization with same shared policy API (not independent logic). [VERIFIED: src/ai/langgraph/graph.py]  
   - Keep conditional edge `auth -> deny/retrieve`; retrieval must stay unreachable for unauthorized users. [VERIFIED: src/ai/langgraph/graph.py]  
   - Optional cleanup: remove duplicate auth check from `decide_next_action` once auth node is authoritative. [VERIFIED: src/ai/langgraph/nodes/decide.py]

5. **Tests (`tests/phase3/test_auth_gate.py` or `tests/phase5/*`)**  
   - Replace monkeypatch-only role simulation with settings-backed whitelist fixtures. [VERIFIED: tests/phase3/test_auth_gate.py]  
   - Add negative tests for unknown `user_id` and stale role map entry.

## Deterministic Test Strategy (Unit + Integration)

### Unit Tests

1. `test_authorize_user_not_in_whitelist_denied`  
   - Input: `user_id` absent in map  
   - Assert: `allowed=False`, reason=`not_whitelisted` [ASSUMED]

2. `test_authorize_user_role_not_allowed_denied`  
   - Input: mapped role=`guest`  
   - Assert: `allowed=False`, reason=`role_not_allowed` [VERIFIED: src/bot/auth.py]

3. `test_authorize_user_allowed`  
   - Input: mapped role=`employee` with allowed set containing employee  
   - Assert: `allowed=True`

### Integration Tests

1. `test_start_unknown_user_denies_and_skips_graph`  
   - Assert `graph.ainvoke` not awaited; deny message returned. [VERIFIED: tests/phase3/test_auth_gate.py pattern]

2. `test_message_unknown_user_denies_and_skips_graph`  
   - Assert no retrieval/LLM path for unauthorized user_id. [VERIFIED: tests/phase3/test_auth_gate.py]

3. `test_message_whitelisted_user_invokes_graph_with_role`  
   - Assert graph called once with resolved role and thread_id. [VERIFIED: tests/phase3/test_auth_gate.py]

4. `test_graph_auth_node_unauthorized_short_circuits_retrieve`  
   - Monkeypatch retrieve node to raise if called; unauthorized input must end at deny. [VERIFIED: tests/phase3/test_auth_gate.py]

### Commands

- Quick: `uv run pytest tests/phase3/test_auth_gate.py -q` [VERIFIED: local run output]  
- Phase auth suite (recommended): `uv run pytest tests/phase3/test_auth_gate.py tests/phase3/test_graph_fallback.py -q` [VERIFIED: tests/phase3 files exist]

## Don’t Hand-Roll

| Problem | Don’t Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Telegram update router | Custom polling/event loop | `python-telegram-bot` handlers (`Application`, `CommandHandler`, `MessageHandler`, `CallbackQueryHandler`) | Official framework already provides async-safe handler orchestration. [CITED: /python-telegram-bot/python-telegram-bot docs] |
| Env parsing for structured policy | Manual `.env` string parsing | `pydantic-settings` typed settings | Prevents parsing bugs and keeps configuration validated. [CITED: /pydantic/pydantic-settings docs] |
| Graph state branching engine | Custom if/else orchestration state machine | LangGraph conditional edges + checkpointer | Existing architecture already uses this reliably. [VERIFIED: src/ai/langgraph/graph.py] [CITED: /websites/langchain_oss_python_langgraph docs] |

**Key insight:** authorization should be a small deterministic policy module plus framework primitives, not ad-hoc branching spread across handlers. [VERIFIED: src/bot/auth.py] [VERIFIED: src/bot/telegram_app.py]

## Common Pitfalls

### Pitfall 1: “Role Exists” ≠ “User Authorized”
**What goes wrong:** allowing by role string only lets non-whitelisted users in. [VERIFIED: src/bot/auth.py]  
**Why it happens:** missing identity-to-role binding source. [VERIFIED: src/bot/telegram_app.py]  
**How to avoid:** always derive role from whitelist map by `user_id`. [ASSUMED]  
**Warning signs:** tests need monkeypatches to fake unauthorized paths. [VERIFIED: tests/phase3/test_auth_gate.py]

### Pitfall 2: Auth Check Happens Too Late
**What goes wrong:** retrieval/LLM executes before deny. [VERIFIED: BOT-05 intent in .planning/ROADMAP.md]  
**Why it happens:** gate implemented only in downstream graph decision node. [VERIFIED: src/ai/langgraph/nodes/decide.py]  
**How to avoid:** enforce deny in transport and graph auth node. [VERIFIED: src/bot/telegram_app.py] [VERIFIED: src/ai/langgraph/graph.py]  
**Warning signs:** `graph.ainvoke` called in unauthorized tests.

### Pitfall 3: Non-Deterministic Auth Tests
**What goes wrong:** tests pass with monkeypatched roles but fail in real config. [VERIFIED: tests/phase3/test_auth_gate.py]  
**Why it happens:** tests don’t exercise settings-based source.  
**How to avoid:** use fixture-driven access map in settings and assert branch/no-branch behavior.

## Code Examples

### Telegram Handler Registration
```python
# Source: /python-telegram-bot/python-telegram-bot docs
application = Application.builder().token("TOKEN").build()
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_message))
application.add_handler(CallbackQueryHandler(on_callback, pattern=r"^feedback:"))
```

### LangGraph Compile with Checkpointer
```python
# Source: /websites/langchain_oss_python_langgraph docs
workflow = StateGraph(GraphState)
workflow.add_edge(START, "auth")
workflow.add_conditional_edges("auth", route_after_auth, {"retrieve": "retrieve", "deny": "deny"})
graph = workflow.compile(checkpointer=InMemorySaver())
```

### Pydantic Settings with .env
```python
# Source: /pydantic/pydantic-settings docs
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Hardcoded transport role (`"employee"`) | Identity-bound whitelist mapping (`user_id -> role`) | Phase 5 target | Real access control boundary for BOT-05. [VERIFIED: src/bot/telegram_app.py] [VERIFIED: .planning/ROADMAP.md] |
| Single-point policy checks | Defense-in-depth checks (transport + graph auth node) | Already partly present in Phase 3 graph | Reduces accidental bypass risk. [VERIFIED: src/ai/langgraph/graph.py] |

**Deprecated/outdated:**
- Hardcoded role resolver for production authorization. [VERIFIED: src/bot/telegram_app.py]

## Threat Model and Failure Modes

| Threat / Failure Mode | STRIDE | Impact | Mitigation |
|-----------------------|--------|--------|------------|
| Unauthorized Telegram user gets KB answer | Elevation of Privilege | Internal data leakage | `user_id` whitelist decision before graph call + graph auth recheck. [VERIFIED: src/bot/telegram_app.py] [VERIFIED: src/ai/langgraph/graph.py] |
| Policy config missing/empty in production | Denial of Service (auth) | Legit users denied | Fail-closed by default; document bootstrap whitelist process. [ASSUMED] |
| Stale/incorrect role mapping | Tampering / Misconfiguration | Wrong access grants/denials | Validate roles against `telegram_allowed_roles`; log deny reasons. [VERIFIED: src/core/config.py] [VERIFIED: src/bot/auth.py] |
| Accidental regression invokes retrieve for denied user | Information Disclosure | Policy bypass | Integration test asserting `graph.ainvoke` not awaited and retrieve never called. [VERIFIED: tests/phase3/test_auth_gate.py] |

## Open Questions (RESOLVED)

None. Resolved defaults for planning:  
1) Source of truth in Phase 5 is config-backed `user_id -> role` map. [VERIFIED: success criteria in .planning/ROADMAP.md] [ASSUMED: exact field name]  
2) Policy is fail-closed on missing users. [ASSUMED]  
3) DB-backed role store is deferred to Phase 6 user-management scope. [VERIFIED: .planning/ROADMAP.md]

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | Bot/runtime | ✓ | 3.12.4 | — [VERIFIED: local command output] |
| uv | Install/test execution | ✓ | 0.8.22 | pip [VERIFIED: local command output] |
| pytest | Deterministic tests | ✓ | 8.3.4 | `uv run pytest` in managed env [VERIFIED: local command output] |
| Docker | Optional local infra startup | ✓ | 29.2.1 | existing external services [VERIFIED: local command output] |
| PostgreSQL server (localhost) | DB-backed tests / feedback table path | ✗ | — | Start via docker-compose if needed [VERIFIED: `pg_isready` output] [VERIFIED: docker-compose.yml exists] |
| Redis server (localhost) | Ancillary runtime paths | ✗ | — | Start via docker-compose if needed [VERIFIED: `redis-cli ping` output] |

**Missing dependencies with no fallback:** None. [VERIFIED: local tooling + docker available]  
**Missing dependencies with fallback:** Local Postgres/Redis services are down; plan should include bring-up/health-check step before full integration run. [VERIFIED: `pg_isready` and `redis-cli ping` outputs]

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest + pytest-asyncio [VERIFIED: pyproject.toml] |
| Config file | `pyproject.toml` (`[tool.pytest.ini_options]`) [VERIFIED: pyproject.toml] |
| Quick run command | `uv run pytest tests/phase3/test_auth_gate.py -q` [VERIFIED: local run output] |
| Full suite command | `uv run pytest tests/ -v --tb=short` [VERIFIED: tests/ directory + existing pattern] |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| BOT-05 | Unauthorized `user_id` denied before retrieval/LLM | integration | `uv run pytest tests/phase3/test_auth_gate.py::test_start_unknown_user_denies_and_skips_graph -q` | ❌ (new case required) |
| BOT-05 | Authorized whitelisted `user_id` enters normal workflow | integration | `uv run pytest tests/phase3/test_auth_gate.py::test_message_whitelisted_user_invokes_graph_with_role -q` | ❌ (new case required) |
| BOT-05 | Graph unauthorized path never executes retrieve | integration | `uv run pytest tests/phase3/test_auth_gate.py::test_graph_auth_node_unauthorized_short_circuits_retrieve -q` | ⚠️ Similar case exists; update to `user_id` source |
| BOT-05 | Auth policy function enforces whitelist+role semantics | unit | `uv run pytest tests/phase5/test_access_policy.py -q` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/phase3/test_auth_gate.py -q`  
- **Per wave merge:** `uv run pytest tests/phase3 -q`  
- **Phase gate:** `uv run pytest tests/ -v --tb=short`

### Wave 0 Gaps
- [ ] Add unit auth policy tests for settings-backed whitelist (`tests/phase5/test_access_policy.py`)  
- [ ] Refactor auth gate integration tests to real `user_id` map instead of monkeypatched hardcoded role  
- [ ] Add explicit regression asserting unauthorized user does not call graph/retrieve nodes

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | yes | Verify Telegram `user_id` against allowlist source before any business logic. [VERIFIED: BOT-05 in .planning/REQUIREMENTS.md] |
| V3 Session Management | yes | Keep per-thread state via `thread_id` after successful auth only. [VERIFIED: src/ai/langgraph/state.py] [VERIFIED: src/bot/telegram_app.py] |
| V4 Access Control | yes | Deny-by-default for non-whitelisted users and role mismatches. [VERIFIED: src/bot/auth.py] [ASSUMED: deny-by-default unchanged] |
| V5 Input Validation | yes | Typed settings + Pydantic models for policy and bot answer contracts. [VERIFIED: src/core/config.py] [VERIFIED: src/ai/langgraph/state.py] |
| V6 Cryptography | no | Reuse platform TLS/secrets handling; no custom crypto in this phase. [ASSUMED] |

### Known Threat Patterns for Telegram Bot Access Hardening

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Spoofed authorization via hardcoded role | Elevation of Privilege | Resolve role from `user_id` whitelist source, not constants. [VERIFIED: src/bot/telegram_app.py] |
| Auth bypass by late checks | Information Disclosure | Auth gate at transport + graph auth node before retrieve. [VERIFIED: src/bot/telegram_app.py] [VERIFIED: src/ai/langgraph/graph.py] |
| Misconfigured role map grants excess access | Tampering | Validate mapped role against `telegram_allowed_roles` and fail closed. [VERIFIED: src/core/config.py] [VERIFIED: src/bot/auth.py] |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Exact new settings field name/shape for whitelist map can be chosen by implementation (`telegram_user_roles` suggested) | Recommended Data Source | Minor refactor cost if naming differs |
| A2 | Missing whitelist entries should deny access by default | Recommended Data Source / Security Domain | Could block legitimate users if onboarding process is missing |
| A3 | DB-backed auth source is deferred to Phase 6 | Open Questions | If required now, Phase 5 scope expands with schema/migration work |

## Sources

### Primary (HIGH confidence)
- `.planning/ROADMAP.md` — Phase 5 goal and success criteria  
- `.planning/REQUIREMENTS.md` — BOT-05 requirement text  
- `.planning/v1-MILESTONE-AUDIT.md` — identified BOT-05 authorization gap  
- `src/bot/telegram_app.py` — hardcoded role resolver and transport auth flow  
- `src/bot/auth.py` — role-only authorization logic  
- `src/ai/langgraph/graph.py` — auth node + deny/retrieve conditional routing  
- `src/ai/langgraph/nodes/decide.py` — duplicate role check in decision node  
- `tests/phase3/test_auth_gate.py` — current auth test shape  
- `pyproject.toml`, `uv.lock` — locked dependency versions in project

### Secondary (MEDIUM confidence)
- Context7 docs `/python-telegram-bot/python-telegram-bot` — builder/handlers/callback patterns  
- Context7 docs `/websites/langchain_oss_python_langgraph` — checkpointer and conditional routing patterns  
- Context7 docs `/pydantic/pydantic-settings` — `BaseSettings` + `.env` config patterns  
- PyPI JSON API responses for latest version/publish dates (`python-telegram-bot`, `langgraph`, `pydantic-settings`, `sqlalchemy`, `pytest`)

### Tertiary (LOW confidence)
- None beyond explicitly tagged `[ASSUMED]` items.

## Metadata

**Confidence breakdown:**  
- Standard stack: HIGH — versions and APIs verified via lockfiles + docs + PyPI.  
- Architecture: HIGH — directly constrained by current code and Phase 5 success criteria.  
- Pitfalls: MEDIUM — implementation-safe, but final config schema details are still planner/executor choices.

**Research date:** 2026-04-19  
**Valid until:** 2026-05-19

## RESEARCH COMPLETE
