from __future__ import annotations

from typing import Any, Literal

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from src.ai.langgraph.nodes.answer import compose_grounded_answer
from src.ai.langgraph.nodes.decide import LOCKED_FALLBACK_TEXT, decide_next_action
from src.ai.langgraph.nodes.retrieve_phase2 import retrieve_phase2_payload
from src.ai.langgraph.nodes.summarize import summarize_history_if_needed
from src.ai.langgraph.state import BotAnswer, SourceRef
from src.bot.auth import authorize_telegram_user, is_authorized_role
from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)


class GraphState(TypedDict, total=False):
    role: str
    query: str
    user_id: str
    chat_id: str
    thread_id: str
    messages: list[dict[str, Any]]
    summary: str
    rag_payload: dict[str, Any]
    authorized: bool
    clarify_turns_used: int
    decision: str
    error: bool
    result: BotAnswer


def route_after_auth(state: GraphState) -> Literal["retrieve", "deny"]:
    return "retrieve" if state.get("authorized", False) else "deny"


def route_after_decide(state: GraphState) -> Literal["fallback", "clarify", "answer", "offtopic", "conflict", "error"]:
    decision = str(state.get("decision", "answer"))
    if decision == "error":
        return "error"
    if decision == "fallback":
        return "fallback"
    if decision == "clarify":
        return "clarify"
    if decision == "offtopic":
        return "offtopic"
    if decision == "conflict":
        return "conflict"
    return "answer"


def _safe_error_answer() -> BotAnswer:
    sources = [
        SourceRef(
            source_id="policy:error",
            excerpt="Internal error handled by safe response policy.",
            timestamp="1970-01-01T00:00:00",
        )
    ]
    return BotAnswer(
        answer=(
            "Unable to process the request. Please try again or ask a colleague.\n\n"
            "Sources:\n- policy:error: Internal error handled by safe response policy."
        ),
        confidence=0.0,
        fallback_used=True,
        sources=sources,
    )


def _fallback_answer(state: dict[str, Any]) -> BotAnswer:
    rag_payload = state.get("rag_payload", {}) or {}
    source_items = rag_payload.get("sources", [])
    sources = []
    for item in source_items:
        if item.get("source_id") and item.get("excerpt") and (item.get("timestamp") or item.get("page")):
            sources.append(SourceRef(**item))
    if not sources:
        sources = [
            SourceRef(
                source_id="policy:fallback",
                excerpt="Insufficient relevant data for a reliable answer.",
                timestamp="1970-01-01T00:00:00",
            )
        ]
    return BotAnswer(
        answer=f"{LOCKED_FALLBACK_TEXT}\n\nSources:\n" + "\n".join(f"- {s.source_id}: {s.excerpt}" for s in sources),
        confidence=float(rag_payload.get("confidence", 0.0)),
        fallback_used=True,
        sources=sources,
    )


def build_graph():
    workflow = StateGraph(GraphState)

    def auth_node(state: GraphState) -> dict[str, Any]:
        if "authorized" in state:
            return {"authorized": bool(state.get("authorized")), "role": str(state.get("role", ""))}

        role_decision = is_authorized_role(str(state.get("role", "")))
        if role_decision.allowed:
            return {"authorized": True, "role": role_decision.role}

        decision = authorize_telegram_user(state.get("user_id", ""))
        return {"authorized": decision.allowed, "role": decision.role or role_decision.role}

    async def retrieve_node(state: GraphState) -> dict[str, Any]:
        try:
            return await retrieve_phase2_payload(state, top_k=settings.rag_hybrid_top_k)
        except Exception as exc:  # noqa: BLE001
            logger.error("langgraph retrieve failed for thread_id=%s: %s", state.get("thread_id"), exc)
            return {"decision": "error", "result": _safe_error_answer(), "error": True}

    def summarize_node(state: GraphState) -> dict[str, Any]:
        messages = list(state.get("messages", []))
        messages.append({"role": "user", "content": str(state.get("query", ""))})
        return summarize_history_if_needed(
            {**state, "messages": messages},
            max_messages=settings.bot_context_max_messages,
            max_tokens=settings.bot_context_max_tokens,
        )

    def decide_node(state: GraphState) -> dict[str, Any]:
        if state.get("error"):
            return {"decision": "error"}
        return {"decision": decide_next_action(state)}

    def deny_node(state: GraphState) -> dict[str, Any]:
        result = compose_grounded_answer({"decision": "deny", "rag_payload": {}})
        return {"decision": "deny", "result": result}

    def fallback_node(state: GraphState) -> dict[str, Any]:
        return {"decision": "fallback", "result": _fallback_answer(state)}

    def clarify_node(state: GraphState) -> dict[str, Any]:
        result = compose_grounded_answer({"decision": "clarify", "rag_payload": state.get("rag_payload", {})})
        return {
            "decision": "clarify",
            "result": result,
            "clarify_turns_used": int(state.get("clarify_turns_used", 0)) + 1,
        }

    def answer_node(state: GraphState) -> dict[str, Any]:
        result = compose_grounded_answer({"decision": "answer", "rag_payload": state.get("rag_payload", {})})
        return {"decision": "answer", "result": result}

    def offtopic_node(state: GraphState) -> dict[str, Any]:
        result = compose_grounded_answer({"decision": "offtopic", "rag_payload": state.get("rag_payload", {})})
        return {"decision": "offtopic", "result": result}

    def conflict_node(state: GraphState) -> dict[str, Any]:
        result = compose_grounded_answer({"decision": "conflict", "rag_payload": state.get("rag_payload", {})})
        return {"decision": "conflict", "result": result}

    def error_node(state: GraphState) -> dict[str, Any]:
        if state.get("result") is not None:
            return {"decision": "error", "result": state["result"]}
        return {"decision": "error", "result": _safe_error_answer()}

    workflow.add_node("auth", auth_node)
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("summarize", summarize_node)
    workflow.add_node("decide", decide_node)
    workflow.add_node("deny", deny_node)
    workflow.add_node("fallback", fallback_node)
    workflow.add_node("clarify", clarify_node)
    workflow.add_node("answer", answer_node)
    workflow.add_node("offtopic", offtopic_node)
    workflow.add_node("conflict", conflict_node)
    workflow.add_node("error", error_node)

    workflow.add_edge(START, "auth")
    workflow.add_conditional_edges("auth", route_after_auth, {"retrieve": "retrieve", "deny": "deny"})
    workflow.add_edge("retrieve", "summarize")
    workflow.add_edge("summarize", "decide")
    workflow.add_conditional_edges(
        "decide",
        route_after_decide,
        {
            "fallback": "fallback",
            "clarify": "clarify",
            "answer": "answer",
            "offtopic": "offtopic",
            "conflict": "conflict",
            "error": "error",
        },
    )
    workflow.add_edge("deny", END)
    workflow.add_edge("fallback", END)
    workflow.add_edge("clarify", END)
    workflow.add_edge("answer", END)
    workflow.add_edge("offtopic", END)
    workflow.add_edge("conflict", END)
    workflow.add_edge("error", END)

    return workflow.compile(checkpointer=InMemorySaver())
