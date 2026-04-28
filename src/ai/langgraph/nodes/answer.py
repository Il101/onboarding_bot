from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from src.ai.langgraph.nodes.decide import LOCKED_FALLBACK_TEXT
from src.ai.langgraph.state import BotAnswer, SourceRef


def _coerce_sources(raw_sources: list[dict[str, Any]] | None, *, fallback_source_id: str) -> list[SourceRef]:
    output: list[SourceRef] = []
    for item in raw_sources or []:
        source_id = str(item.get("source_id", "")).strip()
        excerpt = str(item.get("excerpt", "")).strip()
        timestamp = item.get("timestamp")
        page = item.get("page")
        if source_id and excerpt and (timestamp is not None or page is not None):
            output.append(SourceRef(source_id=source_id, excerpt=excerpt, timestamp=timestamp, page=page))
    if output:
        return output
    return [
        SourceRef(
            source_id=fallback_source_id,
            excerpt="Source unavailable; response constrained by policy.",
            timestamp=datetime.now(UTC).isoformat(timespec="seconds"),
        )
    ]


def _render_sources_block(sources: list[SourceRef]) -> str:
    rows = "\n".join(f"- {item.source_id}: {item.excerpt}" for item in sources)
    return f"Sources:\n{rows}"


def _format_step_answer(base_text: str) -> str:
    base = base_text.strip() or "Follow the team playbook."
    return "\n".join(
        [
            "1. Clarify the request goal and expected outcome.",
            "2. Open the internal playbook and locate the relevant section.",
            "3. Execute the steps sequentially without skipping.",
            f"4. Validate the outcome against the guidance: {base}",
        ]
    )


def _sort_sources_freshest_first(sources: list[SourceRef]) -> list[SourceRef]:
    return sorted(sources, key=lambda item: item.timestamp or "", reverse=True)


def compose_grounded_answer(state: dict[str, Any]) -> BotAnswer:
    decision = str(state.get("decision", "answer"))
    rag_payload = state.get("rag_payload", {}) or {}
    confidence = float(rag_payload.get("confidence", 0.0))
    sources = _coerce_sources(rag_payload.get("sources"), fallback_source_id=f"policy:{decision or 'answer'}")

    if decision == "fallback":
        answer_core = LOCKED_FALLBACK_TEXT
        fallback_used = True
    elif decision == "deny":
        answer_core = "Access restricted: this bot is available only to company employees."
        fallback_used = True
    elif decision == "offtopic":
        answer_core = "I can help only with work-related questions. Please provide a work task."
        fallback_used = True
    elif decision == "clarify":
        answer_core = "Please clarify which process you need help with."
        fallback_used = False
    elif decision == "conflict":
        sources = _sort_sources_freshest_first(sources)
        answer_core = "Source conflict detected. Use the newest instruction and confirm with the process owner."
        fallback_used = False
    else:
        answer_core = _format_step_answer(str(rag_payload.get("answer", "")))
        fallback_used = False

    answer_text = f"{answer_core}\n\n{_render_sources_block(sources)}"
    return BotAnswer(
        answer=answer_text,
        confidence=confidence,
        fallback_used=fallback_used,
        needs_clarification=decision == "clarify",
        clarification_question="Please clarify which process you need help with."
        if decision == "clarify"
        else None,
        sources=sources,
    )
