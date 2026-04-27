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
            excerpt="Источник недоступен, ответ ограничен политикой.",
            timestamp=datetime.now(UTC).isoformat(timespec="seconds"),
        )
    ]


def _render_sources_block(sources: list[SourceRef]) -> str:
    rows = "\n".join(f"- {item.source_id}: {item.excerpt}" for item in sources)
    return f"Источники:\n{rows}"


def _format_step_answer(base_text: str) -> str:
    base = base_text.strip() or "Действуйте по регламенту команды."
    return "\n".join(
        [
            "1. Уточните цель обращения и ожидаемый результат.",
            "2. Откройте внутренний регламент и найдите нужный раздел.",
            "3. Выполните шаги регламента последовательно без пропусков.",
            f"4. Сверьте результат с инструкцией: {base}",
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
        answer_core = "Доступ ограничен: бот доступен только сотрудникам компании."
        fallback_used = True
    elif decision == "offtopic":
        answer_core = "Я помогаю только по рабочим вопросам. Сформулируйте рабочую задачу, и я помогу по шагам."
        fallback_used = True
    elif decision == "clarify":
        answer_core = "Уточните, пожалуйста, по какому процессу нужен ответ?"
        fallback_used = False
    elif decision == "conflict":
        sources = _sort_sources_freshest_first(sources)
        answer_core = (
            "Обнаружен конфликт источников. Используйте более свежую инструкцию и согласуйте шаги с ответственным."
        )
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
        clarification_question="Уточните, пожалуйста, по какому процессу нужен ответ?"
        if decision == "clarify"
        else None,
        sources=sources,
    )
