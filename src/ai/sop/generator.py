from __future__ import annotations

from src.ai.extraction.schemas import KnowledgeUnit
from src.ai.rag.contracts import AttributionItem
from src.ai.sop.template import render_sop


def _attributions_from_units(units: list[KnowledgeUnit]) -> list[AttributionItem]:
    attributions: list[AttributionItem] = []
    for unit in units:
        for ref in unit.source_refs:
            attributions.append(
                AttributionItem(
                    source_id=ref.source_id,
                    excerpt=ref.excerpt,
                    score=unit.confidence,
                    timestamp=ref.timestamp,
                    page=ref.page,
                )
            )
    return attributions


def generate_sop_for_topic(topic: str, units: list[KnowledgeUnit]) -> dict:
    if not units:
        return {
            "topic": topic,
            "generated": False,
            "markdown": None,
            "sources": [],
            "reason": "insufficient_publishable_units",
        }

    goal = f"Выполнить процесс по теме '{topic}' на основе подтвержденных знаний."
    steps = [unit.fact for unit in units]
    exceptions = [f"Если confidence < 0.7, отправить на ревью ({unit.fact})" for unit in units if unit.confidence < 0.7]
    verification = ["Все шаги выполнены последовательно", "Результат подтвержден по источникам"]

    markdown = render_sop(
        topic=topic,
        goal=goal,
        steps=steps,
        exceptions=exceptions,
        verification=verification,
    )
    attributions = _attributions_from_units(units)

    return {
        "topic": topic,
        "generated": True,
        "markdown": markdown,
        "sources": attributions,
    }
