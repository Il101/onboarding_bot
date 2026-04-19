# Phase 3: Telegram Bot - Research

**Researched:** 2026-04-19  
**Domain:** Telegram bot orchestration (python-telegram-bot + LangGraph) over existing Phase 2 knowledge API  
**Confidence:** HIGH

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
### Bot Answer Policy (BOT-01, BOT-02)
- **D-01:** При низкой уверенности бот использует строгий fallback: **«Я не знаю — обратитесь к коллеге»**.
- **D-02:** Ответы всегда на русском языке.
- **D-03:** Формат ответа: кратко и по шагам (3-6 пунктов), без лишних пояснений.

### Source Attribution UX (BOT-01/BOT-02)
- **D-04:** Ответ пользователю: короткий основной ответ + отдельный блок **«Источники»** списком.
- **D-05:** Источники показываются в каждом ответе по умолчанию (не только по запросу).

### Multi-turn Context Handling (BOT-03)
- **D-06:** Логически хранится весь диалог пользователя с ботом в рамках сессии.
- **D-07:** Для вызова LLM используется динамическое контекстное окно с суммаризацией старых сообщений (оптимизация стоимости/латентности без потери смысла диалога).
- **D-08:** Если запрос двусмысленный/слишком общий, бот задаёт ровно 1 уточняющий вопрос перед финальным ответом.

### Conflict Resolution & Safety (BOT-02)
- **D-09:** При конфликте источников бот приоритизирует более свежую инструкцию и явно помечает, что есть конфликт.
- **D-10:** Для off-topic вопросов бот кратко отказывает и возвращает пользователя к рабочей теме.

### Access Control & Feedback (BOT-04, BOT-05)
- **D-11:** Доступ к боту только для авторизованных сотрудников; при `/start` обязательна проверка роли.
- **D-12:** Пользовательский feedback (thumbs up/down) сохраняется для последующей аналитики и улучшения качества ответов.

### the agent's Discretion
- Конкретный механизм хранения сессий и summaries (таблица БД/кэш/гибрид), при соблюдении D-06 и D-07.
- Формат UI-деталей у блока «Источники» (эмодзи, разделители, truncation), если не нарушает D-04/D-05.
- Точные пороги и триггеры для запуска уточняющего вопроса (при соблюдении D-08).

### Deferred Ideas (OUT OF SCOPE)
- Расширенные режимы ответа (кнопка "развернуть подробно") — потенциально в Phase 4 UX-полировке.
- Более сложная стратегия конфликтов (показывать оба варианта с explainability UI) — кандидат в отдельную future phase.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| BOT-01 | Новый сотрудник задаёт вопрос через Telegram бот и получает ответ на русском языке на основе RAG | Use `python-telegram-bot` async handlers + LangGraph node that calls existing `/api/knowledge/query` and enforces RU response format from locked D-02/D-03. [VERIFIED: .planning/REQUIREMENTS.md] [VERIFIED: src/api/routes/knowledge.py] [CITED: https://docs.python-telegram-bot.org/] [CITED: https://docs.langchain.com/oss/python/langgraph/use-graph-api] |
| BOT-02 | Бот возвращает "Я не знаю — обратитесь к коллеге" при confidence ниже порога | Reuse `fallback_used` + `confidence` from knowledge API envelope and hard branch to exact phrase; do not synthesize when low-confidence/low-relevance. [VERIFIED: src/api/routes/knowledge.py] [VERIFIED: src/ai/rag/synthesizer.py] [VERIFIED: .planning/phases/03-telegram-bot/03-CONTEXT.md] |
| BOT-03 | Бот учитывает контекст диалога | Persist LangGraph state with checkpointer + `thread_id`, trim/summarize history before LLM call, and allow exactly one clarify turn. [CITED: https://docs.langchain.com/oss/python/langgraph/add-memory] [CITED: https://docs.langchain.com/oss/python/langgraph/persistence] [CITED: https://docs.langchain.com/oss/python/langgraph/add-memory] |
| BOT-04 | Пользователь может оценить ответ (thumbs up/down) | Implement InlineKeyboard buttons + `CallbackQueryHandler`, store feedback event with message/thread linkage for analytics. [CITED: https://docs.python-telegram-bot.org/] [VERIFIED: .planning/phases/03-telegram-bot/03-CONTEXT.md] |
| BOT-05 | Доступ к боту только для авторизованных сотрудников | Enforce role check in `/start` path before retrieval/LLM node; deny unauthenticated roles with policy message. [VERIFIED: .planning/REQUIREMENTS.md] [VERIFIED: .planning/phases/03-telegram-bot/03-AI-SPEC.md] |
</phase_requirements>

## Summary

Phase 3 should be implemented as a **Telegram orchestration layer**, not a new RAG implementation. The backend already exposes `/api/knowledge/query` returning `answer`, `confidence`, `sources`, `fallback_used`; this must remain the single source for retrieval/fallback evidence used by the bot. [VERIFIED: src/api/routes/knowledge.py]

The AI-SPEC already locks LangGraph as runtime orchestration and python-telegram-bot as transport/UI contract. The most reliable architecture is: `/start` auth gate -> context-aware query node -> decision node (fallback / clarify / answer) -> formatter (always include “Источники”) -> feedback callback capture. [VERIFIED: .planning/phases/03-telegram-bot/03-AI-SPEC.md] [CITED: https://docs.langchain.com/oss/python/langgraph/use-graph-api] [CITED: https://docs.python-telegram-bot.org/]

Primary delivery risk is policy drift (wrong fallback phrase, missing source block, skipped auth gate) rather than model quality. Mitigation is contract-first response validation (Pydantic), deterministic branch conditions, and requirement-mapped tests for BOT-01..BOT-05. [VERIFIED: src/ai/rag/contracts.py] [VERIFIED: .planning/REQUIREMENTS.md]

**Primary recommendation:** Build a strict LangGraph state machine around the existing knowledge API contract, with auth-first execution and mandatory source/feedback UX in Telegram. [VERIFIED: .planning/phases/03-telegram-bot/03-CONTEXT.md] [VERIFIED: src/api/routes/knowledge.py]

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Telegram command/update intake | Browser / Client (Telegram app) | API / Backend | User updates originate in Telegram client; bot backend processes Update payloads. [CITED: https://docs.python-telegram-bot.org/] |
| Bot workflow orchestration (auth/retrieve/decide) | API / Backend | — | LangGraph state transitions and policy gates are backend responsibilities. [CITED: https://docs.langchain.com/oss/python/langgraph/use-graph-api] |
| Knowledge answering + fallback envelope | API / Backend | Database / Storage | Existing backend route computes answer/confidence/sources/fallback; storage holds indexed knowledge metadata. [VERIFIED: src/api/routes/knowledge.py] [VERIFIED: src/ai/rag/synthesizer.py] |
| Multi-turn memory/checkpoints | API / Backend | Database / Storage | Checkpointer persists thread state keyed by `thread_id` across messages. [CITED: https://docs.langchain.com/oss/python/langgraph/persistence] |
| Feedback persistence (thumbs up/down) | Database / Storage | API / Backend | Event records must be stored durably; backend callback handler writes records. [VERIFIED: .planning/phases/03-telegram-bot/03-CONTEXT.md] |
| Role-based access gate | API / Backend | Database / Storage | `/start` must verify authorization before any KB access, likely against role data store/service. [VERIFIED: .planning/REQUIREMENTS.md] [ASSUMED] |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| python-telegram-bot | 22.7 (2026-03-16) | Telegram bot transport, handlers, callback queries | Official async framework for Telegram Bot API, supports `CommandHandler`, `MessageHandler`, `CallbackQueryHandler`. [VERIFIED: PyPI JSON API query] [CITED: https://docs.python-telegram-bot.org/] |
| langgraph | 1.1.8 (2026-04-17) | Stateful branching graph (auth -> retrieval -> decision) | Native support for `StateGraph`, conditional edges, checkpointers, thread state. [VERIFIED: PyPI JSON API query] [CITED: https://docs.langchain.com/oss/python/langgraph/use-graph-api] |
| langchain + langchain-core | 1.2.15 / 1.3.0 | Model init, message utilities, structured output helpers | Needed for `trim_messages`, token-aware context windowing, and `with_structured_output`. [VERIFIED: PyPI JSON API query] [CITED: https://docs.langchain.com/oss/python/langgraph/add-memory] [CITED: https://docs.langchain.com/oss/python/integrations/chat/openai] |
| httpx | 0.28.1 | Async call from bot workflow to `/api/knowledge/query` | Aligns with current async Python stack and AI-SPEC integration examples. [VERIFIED: PyPI JSON API query] [VERIFIED: .planning/phases/03-telegram-bot/03-AI-SPEC.md] |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pydantic | 2.13.2 | Validate outgoing bot envelope (answer/sources/fallback flags) | Always validate before sending Telegram message to enforce BOT-02/BOT-01 contracts. [VERIFIED: PyPI JSON API query] [VERIFIED: src/ai/rag/contracts.py] |
| langgraph-checkpoint-postgres | 3.0.5 | Persistent LangGraph state store | Use in production for multi-turn memory durability across process restarts. [VERIFIED: PyPI JSON API query] [CITED: https://docs.langchain.com/oss/python/langgraph/persistence] |
| pytest | 9.0.3 latest (env has 8.3.4) | Policy regression tests | Use for BOT-01..BOT-05 contract tests; project already uses pytest test tree. [VERIFIED: PyPI JSON API query] [VERIFIED: tests/] |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| LangGraph orchestration | Plain async service functions | Less overhead, but weaker explicit branching/state persistence for BOT-03 policy. [CITED: https://docs.langchain.com/oss/python/langgraph/use-graph-api] [ASSUMED] |
| python-telegram-bot polling | Webhook mode | Webhook lowers polling lag but increases infra setup complexity (TLS/public endpoint). [CITED: https://docs.python-telegram-bot.org/] [ASSUMED] |
| Postgres checkpointer | In-memory saver | In-memory is faster for tests but loses production session continuity. [CITED: https://docs.langchain.com/oss/python/langgraph/add-memory] |

**Installation:**
```bash
uv add "python-telegram-bot>=22,<23" \
       "langgraph>=1.1,<2" \
       "langchain>=1.2,<2" \
       "langchain-core>=1.3,<2" \
       "langgraph-checkpoint-postgres>=3,<4" \
       "httpx>=0.28,<0.29"
```

**Version verification (latest on research date):**
- `python-telegram-bot 22.7` (2026-03-16) [VERIFIED: PyPI JSON API query]
- `langgraph 1.1.8` (2026-04-17) [VERIFIED: PyPI JSON API query]
- `langchain 1.2.15` (2026-04-03) [VERIFIED: PyPI JSON API query]
- `langchain-core 1.3.0` (2026-04-17) [VERIFIED: PyPI JSON API query]
- `langgraph-checkpoint-postgres 3.0.5` (2026-03-18) [VERIFIED: PyPI JSON API query]

## Architecture Patterns

### System Architecture Diagram

```text
[Telegram User Message]
        |
        v
[python-telegram-bot Handlers]
  /start       /message        callback_query
    |             |                  |
    |             v                  v
    |       [LangGraph START]   [Feedback Node]
    |             |
    +-----> [Auth Gate Node] --(unauthorized)--> [Deny Response]
                  |
           (authorized)
                  v
         [Retrieve Node: POST /api/knowledge/query]
                  |
                  v
             [Decision Node]
      +-----------+-------------+------------------+
      |                         |                  |
      v                         v                  v
[Fallback Node]         [Clarify Node]       [Answer Node]
 ("Я не знаю...")       (max 1 question)     (RU 3-6 steps)
      \_____________________|_____________________/
                            v
                 [Formatter: main + "Источники"]
                            |
                            v
                  [Telegram send/edit message]
                            |
                            v
        [Optional state checkpoint + feedback event storage]
```

### Recommended Project Structure
```text
src/
├── bot/
│   ├── telegram_app.py        # Application builder, handlers, startup/shutdown
│   ├── presenters.py          # RU response format + mandatory "Источники"
│   ├── auth.py                # /start role gate
│   └── feedback.py            # inline thumbs callback handling + persistence
├── ai/langgraph/
│   ├── state.py               # BotState + validated output contracts
│   ├── graph.py               # StateGraph compile + routes
│   └── nodes/
│       ├── retrieve.py        # call /api/knowledge/query
│       ├── decide.py          # fallback vs clarify vs answer
│       └── summarize.py       # trim/summarize old turns
└── api/routes/
    └── knowledge.py           # existing retrieval/fallback contract (reuse)
```

### Pattern 1: Auth-First Graph Routing
**What:** First node validates role; unauthorized users never hit retrieval/LLM branch. [VERIFIED: .planning/phases/03-telegram-bot/03-CONTEXT.md]  
**When to use:** Every `/start` and message handling path (BOT-05).  
**Example:**
```python
# Source: https://docs.langchain.com/oss/python/langgraph/use-graph-api
from langgraph.graph import StateGraph, START, END

def route_after_auth(state):
    return "__end__" if state.get("denied") else "retrieve"
```

### Pattern 2: Use Existing Knowledge API as Retrieval Tool
**What:** Bot invokes `POST /api/knowledge/query` and consumes response envelope (`answer`, `confidence`, `sources`, `fallback_used`). [VERIFIED: src/api/routes/knowledge.py]  
**When to use:** Every user question (BOT-01/BOT-02).  
**Example:**
```python
# Source: src/api/routes/knowledge.py
async with httpx.AsyncClient(base_url=base_url, timeout=12.0) as client:
    resp = await client.post("/api/knowledge/query", json={"query": query, "top_k": 6})
    payload = resp.json()  # answer/confidence/sources/fallback_used
```

### Pattern 3: Token-Bounded Multi-turn Context
**What:** Keep recent turns + summary using `trim_messages` and checkpoint by `thread_id`. [CITED: https://docs.langchain.com/oss/python/langgraph/add-memory]  
**When to use:** BOT-03 long conversations and follow-up questions.  
**Example:**
```python
# Source: https://docs.langchain.com/oss/python/langgraph/add-memory
from langchain_core.messages.utils import trim_messages, count_tokens_approximately

messages = trim_messages(
    state["messages"],
    strategy="last",
    token_counter=count_tokens_approximately,
    max_tokens=900,
    start_on="human",
    end_on=("human", "tool"),
)
```

### Pattern 4: Telegram Feedback via Inline Buttons
**What:** Add thumbs buttons in reply markup and process click via `CallbackQueryHandler`. [CITED: https://docs.python-telegram-bot.org/]  
**When to use:** BOT-04 per answer message.  
**Example:**
```python
# Source: https://docs.python-telegram-bot.org/
keyboard = [[
    InlineKeyboardButton("👍", callback_data="fb:up"),
    InlineKeyboardButton("👎", callback_data="fb:down"),
]]
```

### Anti-Patterns to Avoid
- **Calling LLM before auth check:** Violates BOT-05 and can leak internal knowledge. [VERIFIED: .planning/REQUIREMENTS.md]
- **Generating answer when `fallback_used=true` or confidence below threshold:** Violates D-01 strict refusal policy. [VERIFIED: .planning/phases/03-telegram-bot/03-CONTEXT.md] [VERIFIED: src/api/routes/knowledge.py]
- **Returning answer without source block:** Violates D-04/D-05. [VERIFIED: .planning/phases/03-telegram-bot/03-CONTEXT.md]
- **No `thread_id` in checkpointer config:** State won’t persist across turns. [CITED: https://docs.langchain.com/oss/python/langgraph/persistence]
- **Not answering callback queries (`query.answer()`):** Telegram clients keep spinner and UX breaks. [CITED: https://docs.python-telegram-bot.org/]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Telegram update loop | Custom long-polling HTTP plumbing | `python-telegram-bot` Application/handlers | Mature async handling and callback abstraction already solves update routing. [CITED: https://docs.python-telegram-bot.org/] |
| Stateful branching engine | Ad-hoc `if/else` chain with manual shared dicts | LangGraph `StateGraph` + conditional edges | Explicit graph routes reduce policy branch bugs for fallback/auth/clarify flows. [CITED: https://docs.langchain.com/oss/python/langgraph/use-graph-api] |
| Conversation context truncation | Manual token estimation heuristics | `trim_messages` + token counter utilities | Built-in utilities are deterministic and documented for context control. [CITED: https://docs.langchain.com/oss/python/langgraph/add-memory] |
| Feedback button protocol | Custom parsing from raw callback payloads without framework checks | `CallbackQueryHandler` patterns | Standard handler routing + callback answer lifecycle reduce UX and parsing errors. [CITED: https://docs.python-telegram-bot.org/] |

**Key insight:** Phase 3 complexity is workflow policy correctness; standard libraries reduce transport/state bugs so effort can focus on BOT policy enforcement. [VERIFIED: .planning/REQUIREMENTS.md] [ASSUMED]

## Common Pitfalls

### Pitfall 1: Fallback Phrase Drift (BOT-02)
**What goes wrong:** Bot emits alternative refusal wording instead of exact locked phrase. [VERIFIED: .planning/phases/03-telegram-bot/03-CONTEXT.md]  
**Why it happens:** Fallback generated by LLM prompt instead of deterministic branch response. [ASSUMED]  
**How to avoid:** Hardcode exact fallback constant in decision node and test exact match. [VERIFIED: .planning/phases/03-telegram-bot/03-CONTEXT.md]  
**Warning signs:** Snapshot tests pass on meaning but not exact phrase; inconsistent wording across sessions. [ASSUMED]

### Pitfall 2: Source Block Missing on Clarify/Fallback Paths (BOT-01/BOT-02)
**What goes wrong:** `Источники` shown only on successful answer path. [VERIFIED: .planning/phases/03-telegram-bot/03-CONTEXT.md]  
**Why it happens:** Formatter coupled to answer-only branch. [ASSUMED]  
**How to avoid:** Single presenter that always appends source section if any, with policy fallback source when empty. [VERIFIED: .planning/phases/03-telegram-bot/03-AI-SPEC.md] [ASSUMED]  
**Warning signs:** Contract test failures for fallback and off-topic responses missing source list. [ASSUMED]

### Pitfall 3: Lost Multi-turn Memory Due to Missing thread_id (BOT-03)
**What goes wrong:** Follow-up question treated as new dialog every time. [CITED: https://docs.langchain.com/oss/python/langgraph/persistence]  
**Why it happens:** `configurable.thread_id` not passed to graph invocation. [CITED: https://docs.langchain.com/oss/python/langgraph/add-memory]  
**How to avoid:** Build deterministic key (e.g., `tg:{chat_id}:{user_id}`) and pass on every `ainvoke`. [VERIFIED: .planning/phases/03-telegram-bot/03-AI-SPEC.md]  
**Warning signs:** User asks “а дальше?” and bot loses prior constraints/entities. [ASSUMED]

### Pitfall 4: Auth Gate After Retrieval (BOT-05)
**What goes wrong:** Unauthorized user can trigger KB/API load before deny message. [VERIFIED: .planning/REQUIREMENTS.md]  
**Why it happens:** Role check placed in handler tail instead of workflow head. [ASSUMED]  
**How to avoid:** Force `START -> auth node` and terminate early on denial. [VERIFIED: .planning/phases/03-telegram-bot/03-AI-SPEC.md]  
**Warning signs:** Logs show knowledge endpoint calls for denied users. [ASSUMED]

### Pitfall 5: Feedback Not Linked to Answer (BOT-04)
**What goes wrong:** Thumbs events stored without answer/message/thread IDs; analytics unusable. [VERIFIED: .planning/phases/03-telegram-bot/03-AI-SPEC.md]  
**Why it happens:** Callback payload stores only vote, no correlation keys. [ASSUMED]  
**How to avoid:** Encode or look up `thread_id`, `message_id`, `vote`, `answer_confidence`, timestamp. [VERIFIED: .planning/phases/03-telegram-bot/03-AI-SPEC.md]  
**Warning signs:** Feedback rows exist but cannot map to source answer for QA review. [ASSUMED]

## Code Examples

### Graph with persistent thread state
```python
# Source: https://docs.langchain.com/oss/python/langgraph/add-memory
config = {"configurable": {"thread_id": "tg:123:456"}}
await graph.ainvoke({"messages": [{"role": "user", "content": "..." }]}, config=config)
```

### Telegram callback feedback handler
```python
# Source: https://docs.python-telegram-bot.org/
async def on_feedback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    vote = query.data  # "fb:up" / "fb:down"
    # persist feedback event here
```

### Structured output validation before send
```python
# Source: https://docs.langchain.com/oss/python/integrations/chat/openai
structured_llm = llm.with_structured_output(TelegramAnswer, method="json_schema")
result = await structured_llm.ainvoke(prompt)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Stateless bot handlers only | Stateful graph + checkpoint persistence | LangGraph memory/persistence documentation era | Better multi-turn continuity and recovery on restarts. [CITED: https://docs.langchain.com/oss/python/langgraph/persistence] |
| Free-form LLM string outputs | Structured output contracts (Pydantic schema) | Modern provider/tooling support for JSON schema methods | Lower formatting/policy breakage for mandatory source blocks. [CITED: https://docs.langchain.com/oss/python/integrations/chat/openai] |
| UI-only feedback reactions | Callback events persisted as analytics records | Common bot analytics patterns in enterprise assistants | Enables quality loop by mapping thumbs to answer quality. [ASSUMED] |

**Deprecated/outdated:**
- “Always answer even when uncertain” is explicitly incompatible with BOT-02 + D-01. [VERIFIED: .planning/REQUIREMENTS.md] [VERIFIED: .planning/phases/03-telegram-bot/03-CONTEXT.md]

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Role verification will use existing or new role store not yet present in current codebase | Architectural Responsibility Map / Pitfalls | Additional schema/API work may be required in Wave 0 |
| A2 | Webhook mode is likely unnecessary for initial MVP versus polling | Standard Stack / Alternatives | Could miss latency/reliability requirements if deployment mandates webhooks |
| A3 | Feedback analytics schema should include confidence and message linkage fields | Pitfalls | Rework of feedback table and migration if analytics needs differ |
| A4 | Single presenter function can reliably enforce source block across all branches | Common Pitfalls | Might need stricter middleware-level enforcement |
| A5 | Persisted feedback patterns in enterprise assistants generalize to this project | State of the Art | Overfitting design to generic pattern instead of stakeholder-specific KPI needs |

## Open Questions (RESOLVED)

1. **Where does BOT-05 role membership come from at runtime?**
   - Resolution: for Phase 3, source of truth is configurable allowlist from settings (`telegram_allowed_roles`) plus user role resolved from app persistence layer when available; deny by default if role is missing/unknown. [VERIFIED: .planning/REQUIREMENTS.md] [ASSUMED]
   - Implementation directive: enforce auth gate at `/start` and before message handling; retrieval/LLM path is unreachable for denied roles.

2. **What exact clarify trigger threshold should be used for D-08?**
   - Resolution: deterministic rule for Phase 3: ask one clarification only when retrieval confidence is in gray zone `[rag_relevance_threshold, rag_relevance_threshold + 0.10)` OR query intent lacks actionable object/target; otherwise proceed with fallback/answer path. [VERIFIED: .planning/phases/03-telegram-bot/03-CONTEXT.md] [ASSUMED]
   - Implementation directive: enforce hard cap `max_clarifications_per_turn=1` in graph state and test it.

3. **Should feedback be stored in Postgres or Redis-first write-behind?**
   - Resolution: Phase 3 baseline is synchronous Postgres persistence for durability and analytics joins; Redis write-behind is deferred optimization triggered only by observed latency/SLA regressions. [VERIFIED: src/api/deps.py] [VERIFIED: src/core/config.py]
   - Implementation directive: persist `thread_id`, `message_id`, `vote`, `answer_confidence`, `created_at` in `feedback_events`.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python runtime | Bot + LangGraph | ✓ | 3.12.4 | — [VERIFIED: local command output] |
| uv | Dependency install / test runs | ✓ | 0.8.22 | pip [VERIFIED: local command output] |
| pytest | Validation architecture | ✓ | 8.3.4 installed (9.0.3 latest) | keep pinned current env initially [VERIFIED: local command output] [VERIFIED: PyPI JSON API query] |
| redis-cli | Redis diagnostics | ✓ | 8.2.1 | — [VERIFIED: local command output] |
| PostgreSQL client | DB access checks | ✓ | psql 14.19 | — [VERIFIED: local command output] |
| PostgreSQL server | LangGraph checkpoint + feedback persistence | ✗ (localhost:5432 down) | — | start via docker-compose / local service [VERIFIED: local command output] |
| Docker | Local infra startup | ✓ | 29.2.1 | external managed services [VERIFIED: local command output] |

**Missing dependencies with no fallback:**
- None identified; all missing runtime services are startable locally. [VERIFIED: docker-compose.yml]

**Missing dependencies with fallback:**
- Local Postgres currently unavailable; planner should include startup/health-check step before phase tests. [VERIFIED: local command output]

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (8.3.4 installed, pyproject configured) [VERIFIED: local command output] [VERIFIED: pyproject.toml] |
| Config file | `pyproject.toml` (`[tool.pytest.ini_options]`) [VERIFIED: pyproject.toml] |
| Quick run command | `uv run pytest tests/phase3/test_graph_fallback.py tests/phase3/test_auth_gate.py -q` [ASSUMED] |
| Full suite command | `uv run pytest tests/ -v --tb=short` [VERIFIED: tests/] |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| BOT-01 | RU answer + mandatory source block | integration | `uv run pytest tests/phase3/test_source_block_always_present.py -q` | ❌ Wave 0 |
| BOT-02 | Exact strict fallback phrase on low confidence | unit/integration | `uv run pytest tests/phase3/test_graph_fallback.py -q` | ❌ Wave 0 |
| BOT-03 | Multi-turn memory + 1 clarify max | integration | `uv run pytest tests/phase3/test_multiturn_context.py -q` | ❌ Wave 0 |
| BOT-04 | Thumbs callback captured and persisted | integration | `uv run pytest tests/phase3/test_feedback_capture.py -q` | ❌ Wave 0 |
| BOT-05 | Unauthorized user blocked before retrieval | integration | `uv run pytest tests/phase3/test_auth_gate.py -q` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `uv run pytest tests/phase3/test_graph_fallback.py tests/phase3/test_auth_gate.py -q` [ASSUMED]
- **Per wave merge:** `uv run pytest tests/phase3 -v` [ASSUMED]
- **Phase gate:** `uv run pytest tests/ -v --tb=short` full suite green before `/gsd-verify-work`. [VERIFIED: .planning/config.json]

### Wave 0 Gaps
- [ ] `tests/phase3/test_graph_fallback.py` — BOT-02 exact phrase + branch coverage
- [ ] `tests/phase3/test_source_block_always_present.py` — BOT-01/BOT-02 source block invariant
- [ ] `tests/phase3/test_auth_gate.py` — BOT-05 pre-retrieval denial
- [ ] `tests/phase3/test_multiturn_context.py` — BOT-03 thread state + clarify limit
- [ ] `tests/phase3/test_feedback_capture.py` — BOT-04 callback persistence contract

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | yes | Role check in `/start` before any retrieval/generation (BOT-05). [VERIFIED: .planning/REQUIREMENTS.md] |
| V3 Session Management | yes | `thread_id`-scoped conversation state and controlled persistence/checkpoint lifecycle. [CITED: https://docs.langchain.com/oss/python/langgraph/persistence] |
| V4 Access Control | yes | Deny unauthorized roles and prevent knowledge endpoint invocation on denied users. [VERIFIED: .planning/phases/03-telegram-bot/03-AI-SPEC.md] |
| V5 Input Validation | yes | Pydantic validation for bot output + request schema validation already present in knowledge API. [VERIFIED: src/ai/rag/contracts.py] [VERIFIED: src/api/routes/knowledge.py] |
| V6 Cryptography | no (new crypto primitives) | Reuse platform TLS/secrets; never hand-roll cryptography. [ASSUMED] |

### Known Threat Patterns for Telegram bot + RAG

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Unauthorized data access via `/start` bypass | Elevation of Privilege | Auth-first graph routing and deny-before-retrieve invariant tests. [VERIFIED: .planning/REQUIREMENTS.md] |
| Hallucinated operational guidance on weak evidence | Tampering | Strict fallback branch using confidence/fallback flags from knowledge API. [VERIFIED: src/api/routes/knowledge.py] [VERIFIED: .planning/phases/03-telegram-bot/03-CONTEXT.md] |
| Missing/invalid source citations | Repudiation | Mandatory source block formatter + contract tests. [VERIFIED: .planning/phases/03-telegram-bot/03-CONTEXT.md] |
| Feedback tampering/replay via callback payload | Tampering | Validate callback pattern, require message/thread linkage, ignore stale/unknown payloads. [CITED: https://docs.python-telegram-bot.org/] [ASSUMED] |
| Context leakage across users | Information Disclosure | Deterministic per-user/per-chat `thread_id`; never reuse graph config across users. [CITED: https://docs.langchain.com/oss/python/langgraph/persistence] [ASSUMED] |

## Sources

### Primary (HIGH confidence)
- `src/api/routes/knowledge.py` — existing answer/confidence/sources/fallback contract.  
- `src/ai/rag/synthesizer.py`, `src/ai/rag/contracts.py`, `src/ai/extraction/publish_policy.py` — current fallback and validation behavior.  
- `.planning/phases/03-telegram-bot/03-CONTEXT.md` — locked decisions D-01..D-12.  
- `.planning/phases/03-telegram-bot/03-AI-SPEC.md` — framework lock + integration contract details.  
- `.planning/REQUIREMENTS.md` — BOT-01..BOT-05 definitions.  
- `https://docs.langchain.com/oss/python/langgraph/use-graph-api`  
- `https://docs.langchain.com/oss/python/langgraph/add-memory`  
- `https://docs.langchain.com/oss/python/langgraph/persistence`  
- `https://docs.langchain.com/oss/python/integrations/chat/openai`  
- `https://docs.python-telegram-bot.org/`  
- PyPI JSON API responses for versions/publication dates (`python-telegram-bot`, `langgraph`, `langchain`, `langchain-core`, `langgraph-checkpoint-postgres`, `httpx`, `pydantic`, `fastapi`, `pytest`).

### Secondary (MEDIUM confidence)
- `.planning/PROJECT.md` — language/perimeter constraints informing security recommendations.

### Tertiary (LOW confidence)
- None beyond explicitly tagged `[ASSUMED]` implementation heuristics.

## Metadata

**Confidence breakdown:**
- Standard stack: **HIGH** — versions and capabilities verified via PyPI + official docs.
- Architecture: **HIGH** — constrained by locked phase decisions and existing API contracts.
- Pitfalls: **MEDIUM** — policy risks are clear, but some mitigations depend on yet-to-be-implemented role/feedback schema details.

**Research date:** 2026-04-19  
**Valid until:** 2026-05-19 (30 days; stack is active and versions move quickly)
