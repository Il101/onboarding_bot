from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from src.ai.extraction.publish_policy import should_publish_knowledge
from src.ai.extraction.schemas import KnowledgeUnit


def group_units_by_topic(units: Iterable[KnowledgeUnit]) -> dict[str, list[KnowledgeUnit]]:
    grouped: dict[str, list[KnowledgeUnit]] = defaultdict(list)
    for unit in units:
        grouped[unit.topic].append(unit)
    return {topic: grouped[topic] for topic in sorted(grouped)}


def extract_knowledge_units(
    chunks: list[dict],
    *,
    extraction_outputs: list[list[dict]] | None = None,
) -> dict[str, list[KnowledgeUnit]]:
    outputs = extraction_outputs or [[] for _ in chunks]
    all_units: list[KnowledgeUnit] = []
    publishable: list[KnowledgeUnit] = []
    review_needed: list[KnowledgeUnit] = []

    for chunk_output in outputs:
        for candidate in chunk_output:
            unit = KnowledgeUnit.model_validate(candidate)
            all_units.append(unit)

    for unit in all_units:
        decision = should_publish_knowledge(unit)
        if decision.publish:
            publishable.append(unit)
        else:
            review_needed.append(unit)

    return {
        "all_units": all_units,
        "publishable": publishable,
        "review_needed": review_needed,
    }
