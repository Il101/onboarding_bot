from __future__ import annotations

from src.ai.rag.reranker import rerank_candidates
from src.core.config import settings


class HybridRetriever:
    def __init__(self, index):
        self.index = index
        self.query_mode = "hybrid"

    def retrieve(self, query: str, *, candidates: list[dict] | None = None) -> list[dict]:
        if candidates is not None:
            return rerank_candidates(candidates, top_k=settings.rag_rerank_top_k)
        return []
