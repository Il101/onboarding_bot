# Phase 5: Bot Access Hardening - Pattern Map

**Mapped:** 2026-04-19  
**Files analyzed:** 7  
**Analogs found:** 7 / 7

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `src/core/config.py` | config | transform | `src/core/config.py` | exact |
| `src/bot/auth.py` | utility | request-response | `src/bot/auth.py` | exact |
| `src/bot/telegram_app.py` | controller | event-driven | `src/bot/telegram_app.py` | exact |
| `src/ai/langgraph/graph.py` | service | event-driven | `src/ai/langgraph/graph.py` | exact |
| `src/ai/langgraph/nodes/decide.py` | service | transform | `src/ai/langgraph/nodes/decide.py` | exact |
| `tests/phase3/test_auth_gate.py` | test | event-driven | `tests/phase3/test_auth_gate.py` | exact |
| `tests/phase5/test_access_policy.py` (new) | test | request-response | `tests/phase3/test_auth_gate.py` | role-match |

## Pattern Assignments

### `src/core/config.py` (config, transform)

**Analog:** `src/core/config.py`

**Imports + BaseSettings pattern** (lines 1-8):
```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )
```

**Typed policy fields pattern** (lines 40-43):
```python
telegram_bot_token: str = ""
telegram_allowed_roles: set[str] = {"employee", "mentor", "admin"}
telegram_feedback_enabled: bool = True
```

**Singleton settings export** (line 49):
```python
settings = Settings()
```

---

### `src/bot/auth.py` (utility, request-response)

**Analog:** `src/bot/auth.py`

**Imports + contract model pattern** (lines 3-12):
```python
from pydantic import BaseModel, Field

from src.ai.langgraph.state import BotAnswer, SourceRef
from src.core.config import settings


class AuthDecision(BaseModel):
    allowed: bool
    reason: str = Field(min_length=1)
```

**Authorization decision function pattern** (lines 14-20):
```python
def is_authorized_role(role: str | None) -> AuthDecision:
    normalized = (role or "").strip().lower()
    if not normalized:
        return AuthDecision(allowed=False, reason="missing_role")
    if normalized not in settings.telegram_allowed_roles:
        return AuthDecision(allowed=False, reason="role_not_allowed")
    return AuthDecision(allowed=True, reason="allowed")
```

**Deny-answer construction pattern** (lines 23-35):
```python
def build_access_denied_answer(reason: str) -> BotAnswer:
    return BotAnswer(
        answer="Доступ ограничен: бот доступен только сотрудникам компании.",
        confidence=1.0,
        fallback_used=True,
        sources=[
            SourceRef(
                source_id="policy:auth",
                excerpt=f"Access denied by auth policy: {reason}",
                timestamp="1970-01-01T00:00:00",
            )
        ],
    )
```

---

### `src/bot/telegram_app.py` (controller, event-driven)

**Analog:** `src/bot/telegram_app.py`

**Transport imports + handlers wiring pattern** (lines 8-16, 154-156):
```python
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
...
app.add_handler(CommandHandler("start", handle_start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(CallbackQueryHandler(handle_feedback_callback, pattern=r"^feedback:"))
```

**Current auth gate location to preserve (replace role source only)** (lines 67-75, 78-85):
```python
async def handle_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.message is None:
        return
    role = resolve_role_for_update(update)
    if not is_authorized_role(role).allowed:
        denied = build_access_denied_answer(reason="role_not_allowed")
        await update.message.reply_text(text=render_bot_message(denied))
        return
```

**Graph invocation envelope pattern** (lines 87-98):
```python
thread_id = build_thread_id(chat_id=update.effective_chat.id, user_id=update.effective_user.id)
graph = context.application.bot_data["graph"]
result = await graph.ainvoke(
    {
        "role": role,
        "query": update.message.text or "",
        "user_id": str(update.effective_user.id),
        "chat_id": str(update.effective_chat.id),
    },
    config={"configurable": {"thread_id": thread_id}},
)
```

**Error handling + safe fallback pattern** (lines 100-103):
```python
except Exception as exc:  # noqa: BLE001
    logger.error("telegram message handler failed: %s", exc)
    answer = _safe_error_answer()
```

---

### `src/ai/langgraph/graph.py` (service, event-driven)

**Analog:** `src/ai/langgraph/graph.py`

**Auth node + decision handoff pattern** (lines 98-101, 163-165):
```python
def auth_node(state: GraphState) -> dict[str, Any]:
    decision = is_authorized_role(state.get("role"))
    return {"authorized": decision.allowed}
...
workflow.add_edge(START, "auth")
workflow.add_conditional_edges("auth", route_after_auth, {"retrieve": "retrieve", "deny": "deny"})
```

**Retrieve-node fail-safe pattern** (lines 102-108):
```python
async def retrieve_node(state: GraphState) -> dict[str, Any]:
    try:
        return await retrieve_phase2_payload(state, top_k=settings.rag_hybrid_top_k)
    except Exception as exc:  # noqa: BLE001
        logger.error("langgraph retrieve failed for thread_id=%s: %s", state.get("thread_id"), exc)
        return {"decision": "error", "result": _safe_error_answer(), "error": True}
```

**Terminal deny path pattern** (lines 123-126, 179):
```python
def deny_node(state: GraphState) -> dict[str, Any]:
    result = compose_grounded_answer({"decision": "deny", "rag_payload": {}})
    return {"decision": "deny", "result": result}
...
workflow.add_edge("deny", END)
```

---

### `src/ai/langgraph/nodes/decide.py` (service, transform)

**Analog:** `src/ai/langgraph/nodes/decide.py`

**Decision function structure pattern** (lines 33-56):
```python
def decide_next_action(state: dict[str, Any]) -> Literal["deny", "offtopic", "fallback", "clarify", "conflict", "answer"]:
    role = str(state.get("role", ""))
    if not is_authorized_role(role).allowed:
        return "deny"
    ...
    if fallback_used or confidence < settings.rag_relevance_threshold:
        return "fallback"
    ...
    return "answer"
```

---

### `tests/phase3/test_auth_gate.py` (test, event-driven)

**Analog:** `tests/phase3/test_auth_gate.py`

**Async handler test structure + monkeypatch pattern** (lines 30-45):
```python
@pytest.mark.asyncio
async def test_start_unauthorized_returns_deny_and_skips_graph(monkeypatch):
    from src.bot.telegram_app import handle_start
    ...
    monkeypatch.setattr("src.bot.telegram_app.resolve_role_for_update", lambda _u: "guest")

    await handle_start(upd, ctx)

    graph.ainvoke.assert_not_awaited()
    upd.message.reply_text.assert_awaited()
```

**Graph short-circuit assertion pattern** (lines 82-96):
```python
@pytest.mark.asyncio
async def test_unauthorized_role_short_circuits_before_retrieve(monkeypatch):
    from src.ai.langgraph.graph import build_graph
    ...
    monkeypatch.setattr("src.ai.langgraph.graph.retrieve_phase2_payload", _forbidden_retrieve)
    graph = build_graph()
    result = await graph.ainvoke(...)
    assert result["decision"] == "deny"
```

---

### `tests/phase5/test_access_policy.py` (new test, request-response)

**Analog:** `tests/phase3/test_auth_gate.py` (role-match)

**Use this style for deterministic auth-policy unit tests:**
- `pytest.mark.asyncio` only for coroutine handlers; pure policy tests should be synchronous.
- Keep `SimpleNamespace`/fixture-driven inputs.
- Assert both boolean outcome and reason code (`not_whitelisted`, `role_not_allowed`, `allowed` once implemented).

## Shared Patterns

### Authentication denial response envelope
**Source:** `src/bot/auth.py` lines 23-35  
**Apply to:** Telegram transport handlers + graph deny nodes
```python
return BotAnswer(
    answer="Доступ ограничен: бот доступен только сотрудникам компании.",
    confidence=1.0,
    fallback_used=True,
    sources=[SourceRef(source_id="policy:auth", excerpt=f"Access denied by auth policy: {reason}", ...)],
)
```

### Telegram transport deny-before-graph
**Source:** `src/bot/telegram_app.py` lines 81-85  
**Apply to:** `/start` and message handlers
```python
role = resolve_role_for_update(update)
if not is_authorized_role(role).allowed:
    denied = build_access_denied_answer(reason="role_not_allowed")
    await update.message.reply_text(text=render_bot_message(denied))
    return
```

### Defense-in-depth graph routing
**Source:** `src/ai/langgraph/graph.py` lines 37-39, 163-165  
**Apply to:** All auth-sensitive graph workflows
```python
def route_after_auth(state: GraphState) -> Literal["retrieve", "deny"]:
    return "retrieve" if state.get("authorized", False) else "deny"
```

### Safe error masking
**Source:** `src/bot/telegram_app.py` lines 100-103; `src/ai/langgraph/graph.py` lines 56-69  
**Apply to:** transport and graph nodes
```python
except Exception as exc:  # noqa: BLE001
    logger.error("...: %s", exc)
    answer = _safe_error_answer()
```

## No Analog Found

| File | Role | Data Flow | Reason |
|---|---|---|---|
| `tests/phase5/test_access_policy.py` (directory-level) | test | request-response | No existing `tests/phase5/` suite yet; use `tests/phase3/test_auth_gate.py` style. |

## Metadata

**Analog search scope:** `src/bot`, `src/core`, `src/ai/langgraph`, `tests/phase3`  
**Files scanned:** 11  
**Pattern extraction date:** 2026-04-19

