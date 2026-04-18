from __future__ import annotations

from src.ai.rag.attribution import format_attribution
from src.ai.rag.contracts import RagAnswer
from src.ai.rag.reranker import rerank_candidates
from src.ai.extraction.publish_policy import should_answer_for_relevance
from src.core.config import settings


FALLBACK_MESSAGE = "Недостаточно данных для уверенного ответа. Проверьте ближайшие источники."


def synthesize_answer(query: str, candidates: list[dict]) -> RagAnswer:
    reranked = rerank_candidates(candidates, top_k=settings.rag_rerank_top_k)
    sources = format_attribution(reranked)
    top_score = reranked[0].get("score", 0.0) if reranked else 0.0

    if not should_answer_for_relevance(float(top_score)):
        return RagAnswer(
            answer=FALLBACK_MESSAGE,
            confidence=float(top_score),
            sources=sources,
            fallback_used=True,
        )

    grounded_text = reranked[0].get("text", "") if reranked else FALLBACK_MESSAGE
    return RagAnswer(
        answer=grounded_text,
        confidence=float(top_score),
        sources=sources,
        fallback_used=False,
    )
