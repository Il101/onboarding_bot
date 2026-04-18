from __future__ import annotations

from pydantic import BaseModel, Field

from src.ai.extraction.schemas import KnowledgeUnit
from src.core.config import settings


class PublishDecision(BaseModel):
    publish: bool
    reason: str = Field(min_length=1)


def should_publish_knowledge(unit: KnowledgeUnit) -> PublishDecision:
    if unit.confidence < settings.knowledge_confidence_threshold:
        return PublishDecision(
            publish=False,
            reason=(
                f"low_confidence: {unit.confidence:.3f} < "
                f"{settings.knowledge_confidence_threshold:.3f}"
            ),
        )
    return PublishDecision(publish=True, reason="publishable")


def should_answer_for_relevance(score: float) -> bool:
    return score >= settings.rag_relevance_threshold
