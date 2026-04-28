from __future__ import annotations

from typing import Any, Literal

from src.core.config import settings

LOCKED_FALLBACK_TEXT = "I don't know - please ask a colleague."


def _is_offtopic(query: str) -> bool:
    normalized = query.strip().lower()
    markers = {"joke", "weather", "movie", "recipe", "music", "horoscope"}
    return any(marker in normalized for marker in markers)


def _is_ambiguous(query: str) -> bool:
    normalized = query.strip().lower()
    return normalized.startswith("what should i do") or len(normalized.split()) <= 2


def _has_source_conflict(sources: list[dict[str, Any]]) -> bool:
    if len(sources) < 2:
        return False
    first, second = sources[0], sources[1]
    first_excerpt = str(first.get("excerpt", "")).strip().lower()
    second_excerpt = str(second.get("excerpt", "")).strip().lower()
    first_ts = str(first.get("timestamp", ""))
    second_ts = str(second.get("timestamp", ""))
    return bool(first_excerpt and second_excerpt and first_excerpt != second_excerpt and first_ts != second_ts)


def decide_next_action(
    state: dict[str, Any],
) -> Literal["deny", "offtopic", "fallback", "clarify", "conflict", "answer"]:
    if not bool(state.get("authorized", False)):
        return "deny"

    query = str(state.get("query", ""))
    if _is_offtopic(query):
        return "offtopic"

    rag_payload = state.get("rag_payload", {}) or {}
    confidence = float(rag_payload.get("confidence", 0.0))
    fallback_used = bool(rag_payload.get("fallback_used", False))
    if fallback_used or confidence < settings.rag_relevance_threshold:
        return "fallback"

    clarify_turns_used = int(state.get("clarify_turns_used", 0))
    if clarify_turns_used < settings.bot_clarify_max_turns and _is_ambiguous(query):
        return "clarify"

    sources = rag_payload.get("sources", [])
    if isinstance(sources, list) and _has_source_conflict(sources):
        return "conflict"

    return "answer"
