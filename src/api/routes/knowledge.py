from __future__ import annotations

from pydantic import BaseModel, Field
from fastapi import APIRouter

from src.ai.rag.retriever import HybridRetriever
from src.ai.rag.synthesizer import synthesize_answer
from src.core.config import settings

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


class KnowledgeQueryRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int | None = Field(default=None, ge=1, le=settings.rag_hybrid_top_k)


@router.post("/query")
async def query_knowledge(payload: KnowledgeQueryRequest):
    try:
        effective_top_k = payload.top_k or settings.rag_hybrid_top_k
        retriever = HybridRetriever()
        candidates = retriever.retrieve(payload.query)
        result = synthesize_answer(
            payload.query,
            candidates=candidates[:effective_top_k],
        )
        return {
            "answer": result.answer,
            "confidence": result.confidence,
            "sources": [item.model_dump() for item in result.sources],
            "fallback_used": result.fallback_used,
        }
    except Exception:
        return {
            "answer": "Недостаточно данных для уверенного ответа. Проверьте ближайшие источники.",
            "confidence": 0.0,
            "sources": [
                {
                    "source_id": "policy:error",
                    "excerpt": "Временная ошибка retrieval path, возвращен безопасный fallback.",
                    "score": 0.0,
                    "timestamp": "1970-01-01T00:00:00",
                    "page": None,
                }
            ],
            "fallback_used": True,
        }
