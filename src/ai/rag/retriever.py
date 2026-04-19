from __future__ import annotations

from qdrant_client import QdrantClient

from src.ai.rag.reranker import rerank_candidates
from src.core.config import settings
from src.pipeline.indexer.embedder import Embedder
from src.pipeline.indexer.qdrant_store import QdrantStore


class HybridRetriever:
    def __init__(self, index=None, *, embedder: Embedder | None = None):
        self.index = index or QdrantStore(QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port))
        self.embedder = embedder or Embedder(
            dense_model=settings.dense_model_name,
            sparse_model=settings.sparse_model_name,
        )
        self.query_mode = "hybrid"

    def retrieve(self, query: str, *, candidates: list[dict] | None = None) -> list[dict]:
        if candidates is not None:
            return rerank_candidates(candidates, top_k=settings.rag_rerank_top_k)

        if not query.strip():
            return []

        try:
            dense_vectors, _ = self.embedder.embed_batch([query])
            query_vector = dense_vectors[0].tolist()
            result = self.index.client.query_points(
                collection_name=self.index.COLLECTION_NAME,
                using="dense",
                query=query_vector,
                limit=settings.rag_hybrid_top_k,
                with_payload=True,
            )
            points = list(getattr(result, "points", []))
            candidates_out = []
            for point in points:
                payload = point.payload or {}
                if not payload.get("source_id"):
                    continue
                if payload.get("timestamp") is None and payload.get("page") is None:
                    continue
                candidates_out.append(
                    {
                        "score": float(getattr(point, "score", 0.0)),
                        "text": payload.get("text", ""),
                        "metadata": {
                            "source_id": payload.get("source_id", ""),
                            "timestamp": payload.get("timestamp"),
                            "page": payload.get("page"),
                        },
                    }
                )
            return candidates_out
        except Exception:
            return []
