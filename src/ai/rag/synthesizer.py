from __future__ import annotations

from src.ai.extraction.publish_policy import should_answer_for_relevance
from src.ai.llm_client import llm_chat
from src.ai.rag.attribution import format_attribution
from src.ai.rag.contracts import RagAnswer
from src.ai.rag.reranker import rerank_candidates
from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)

FALLBACK_MESSAGE = "Недостаточно данных для уверенного ответа. Проверьте ближайшие источники."

_SYSTEM_PROMPT = (
    "Ты — AI-ментор компании. Твоя задача — отвечать на вопросы новых сотрудников.\n"
    "Правила:\n"
    "1. Отвечай ТОЛЬКО на основе предоставленного контекста из внутренней базы знаний.\n"
    "2. Если в контексте нет ответа — честно скажи 'Я не знаю — обратитесь к коллеге'.\n"
    "3. Отвечай на русском языке, чётко и по шагам.\n"
    "4. Не придумывай информацию, которой нет в контексте."
)


def _build_context(candidates: list[dict]) -> str:
    """Format retrieved chunks into a readable context block for the LLM."""
    parts: list[str] = []
    for i, c in enumerate(candidates, start=1):
        source_id = c.get("metadata", {}).get("source_id", "unknown")
        text = c.get("text", "").strip()
        if text:
            parts.append(f"[{i}] Источник: {source_id}\n{text}")
    return "\n\n---\n\n".join(parts) if parts else ""


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

    context = _build_context(reranked)
    if not context:
        return RagAnswer(
            answer=FALLBACK_MESSAGE,
            confidence=float(top_score),
            sources=sources,
            fallback_used=True,
        )

    try:
        answer = llm_chat(
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": f"Контекст из базы знаний:\n\n{context}\n\n---\n\nВопрос сотрудника: {query}",
                },
            ],
            temperature=0.2,
            max_tokens=1500,
        )
    except Exception as exc:
        logger.error("synthesize_answer LLM call failed: %s", exc)
        return RagAnswer(
            answer=FALLBACK_MESSAGE,
            confidence=float(top_score),
            sources=sources,
            fallback_used=True,
        )

    return RagAnswer(
        answer=answer,
        confidence=float(top_score),
        sources=sources,
        fallback_used=False,
    )
