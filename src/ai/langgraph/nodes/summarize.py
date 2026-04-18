from __future__ import annotations

from typing import Any


def _message_token_len(message: dict[str, Any]) -> int:
    content = str(message.get("content", ""))
    return max(1, len(content.split()))


def _build_summary_text(summary: str, removed: list[dict[str, Any]]) -> str:
    snippets: list[str] = []
    if summary:
        snippets.append(summary)
    for item in removed:
        role = str(item.get("role", ""))
        content = str(item.get("content", "")).strip()
        if content:
            snippets.append(f"{role}: {content}")
    return " | ".join(snippets).strip()


def summarize_history_if_needed(
    state: dict[str, Any],
    *,
    max_messages: int,
    max_tokens: int,
) -> dict[str, Any]:
    messages = list(state.get("messages", []))
    if not messages:
        return {"summary": str(state.get("summary", "")), "messages": messages}

    latest_user_idx = -1
    for idx in range(len(messages) - 1, -1, -1):
        if str(messages[idx].get("role", "")) == "user":
            latest_user_idx = idx
            break

    trimmed = messages[:]
    removed: list[dict[str, Any]] = []
    while len(trimmed) > max_messages:
        if latest_user_idx == 0:
            break
        removed.append(trimmed.pop(0))
        latest_user_idx -= 1

    while sum(_message_token_len(item) for item in trimmed) > max_tokens and len(trimmed) > 1:
        if latest_user_idx == 0:
            break
        removed.append(trimmed.pop(0))
        latest_user_idx -= 1

    summary = _build_summary_text(str(state.get("summary", "")), removed)
    return {"summary": summary, "messages": trimmed}
