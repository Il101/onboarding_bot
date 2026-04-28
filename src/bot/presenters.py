from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from src.ai.langgraph.state import BotAnswer


def _parse_timestamp(value: str | None) -> datetime:
    if not value:
        return datetime(1970, 1, 1, tzinfo=UTC)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return datetime(1970, 1, 1, tzinfo=UTC)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed


def _truncate_excerpt(text: str, *, max_len: int) -> str:
    normalized = " ".join(str(text).split())
    if len(normalized) <= max_len:
        return normalized
    if max_len <= 1:
        return "…"
    return normalized[: max_len - 1].rstrip() + "…"


def render_sources_block(sources: list[Any], *, excerpt_max_len: int = 180) -> str:
    normalized: list[dict[str, Any]] = []
    for source in sources:
        item = source if isinstance(source, dict) else source.model_dump()
        normalized.append(
            {
                "source_id": str(item.get("source_id", "")).strip() or "policy:source-empty",
                "excerpt": _truncate_excerpt(
                    str(item.get("excerpt", "")).strip() or "Source not provided.",
                    max_len=excerpt_max_len,
                ),
                "score": float(item.get("score", 0.0) or 0.0),
                "timestamp": item.get("timestamp"),
            }
        )

    normalized.sort(key=lambda item: (item["score"], _parse_timestamp(item["timestamp"])), reverse=True)
    lines = [f"- {item['source_id']}: {item['excerpt']}" for item in normalized]
    if not lines:
        lines = ["- policy:source-empty: Source not provided."]
    return "Sources:\n" + "\n".join(lines)


def render_bot_message(answer: BotAnswer, *, excerpt_max_len: int = 180) -> str:
    body = str(answer.answer).strip()
    if "\n\nSources:" in body:
        body = body.split("\n\nSources:", 1)[0].strip()
    return f"{body}\n\n{render_sources_block(answer.sources, excerpt_max_len=excerpt_max_len)}"
