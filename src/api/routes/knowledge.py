from __future__ import annotations

from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

from src.ai.rag.synthesizer import synthesize_answer

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


class KnowledgeQueryRequest(BaseModel):
    query: str = Field(min_length=1)


@router.post("/query")
async def query_knowledge(payload: KnowledgeQueryRequest):
    try:
        result = synthesize_answer(
            payload.query,
            candidates=[
                {
                    "score": 0.2,
                    "text": "Ближайший найденный фрагмент по запросу",
                    "metadata": {"source_id": "seed:knowledge", "timestamp": "2026-04-01T00:00:00"},
                }
            ],
        )
        return {
            "answer": result.answer,
            "confidence": result.confidence,
            "sources": [item.model_dump() for item in result.sources],
            "fallback_used": result.fallback_used,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Knowledge query failed") from exc
