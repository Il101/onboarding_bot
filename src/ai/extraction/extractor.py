from __future__ import annotations

import json
from collections import defaultdict
from typing import Iterable

from src.ai.extraction.publish_policy import should_publish_knowledge
from src.ai.extraction.schemas import KnowledgeUnit
from src.ai.llm_client import llm_chat
from src.core.logging import get_logger

logger = get_logger(__name__)

_EXTRACTION_SYSTEM_PROMPT = """\
Ты — аналитик знаний. Твоя задача — извлечь структурированные бизнес-знания из текста.

Для каждого явного знания, инструкции или процедуры создай объект:
{
  "fact": "конкретный факт или пошаговая инструкция (1-3 предложения)",
  "topic": "тема на русском (Продажи | Поддержка | CRM | Онбординг | Процессы | Финансы | Техника | Другое)",
  "confidence": 0.0-1.0
}

Правила:
- Включай только конкретные, повторно применимые знания
- НЕ включай обычную переписку, приветствия, мнения
- Если знаний нет — верни пустой массив []
- Отвечай строго JSON-массивом, без пояснений
"""


def _extract_from_chunk(chunk: dict) -> list[dict]:
    """Call LLM to extract knowledge units from a single chunk."""
    text = chunk.get("text", "").strip()
    if not text or len(text) < 50:  # Skip very short chunks
        return []

    source_id = chunk.get("metadata", {}).get("source_id", "unknown")
    timestamp = chunk.get("metadata", {}).get("date_range") or chunk.get("metadata", {}).get("timestamp")
    page = chunk.get("metadata", {}).get("chunk_index")

    try:
        response = llm_chat(
            messages=[
                {"role": "system", "content": _EXTRACTION_SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            temperature=0.1,
            max_tokens=1000,
        )
        # Strip markdown code fences if present
        cleaned = response.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
        raw_units: list[dict] = json.loads(cleaned)
    except (json.JSONDecodeError, Exception) as exc:
        logger.warning("LLM extraction failed for source %s: %s", source_id, exc)
        return []

    if not isinstance(raw_units, list):
        return []

    # Attach source attribution to each extracted unit
    enriched: list[dict] = []
    for unit in raw_units:
        if not isinstance(unit, dict):
            continue
        source_ref: dict = {"source_id": source_id, "excerpt": text[:200]}
        if timestamp:
            source_ref["timestamp"] = str(timestamp)
        elif page is not None:
            source_ref["page"] = int(page)
        else:
            source_ref["timestamp"] = "1970-01-01T00:00:00"
        unit["source_refs"] = [source_ref]
        enriched.append(unit)

    return enriched


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
    # If extraction_outputs not provided — run real LLM extraction
    if extraction_outputs is None:
        logger.info("Running LLM knowledge extraction on %d chunks", len(chunks))
        extraction_outputs = [_extract_from_chunk(chunk) for chunk in chunks]

    all_units: list[KnowledgeUnit] = []
    publishable: list[KnowledgeUnit] = []
    review_needed: list[KnowledgeUnit] = []

    for chunk_output in extraction_outputs:
        for candidate in chunk_output:
            try:
                unit = KnowledgeUnit.model_validate(candidate)
                all_units.append(unit)
            except Exception as exc:
                logger.warning("Skipping invalid knowledge unit: %s — %s", candidate, exc)

    for unit in all_units:
        decision = should_publish_knowledge(unit)
        if decision.publish:
            publishable.append(unit)
        else:
            review_needed.append(unit)

    logger.info(
        "Extraction complete: total=%d publishable=%d review_needed=%d",
        len(all_units), len(publishable), len(review_needed),
    )

    return {
        "all_units": all_units,
        "publishable": publishable,
        "review_needed": review_needed,
    }
