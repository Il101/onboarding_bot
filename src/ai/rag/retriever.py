from __future__ import annotations

from qdrant_client import QdrantClient

from src.ai.rag.reranker import rerank_candidates
from src.core.config import settings
from src.pipeline.indexer.embedder import Embedder
from src.pipeline.indexer.qdrant_store import QdrantStore


class HybridRetriever:
    def __init__(self, index=None, *, embedder: Embedder | None = None):
        self.index = index or QdrantStore(QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port))
        self.embedder = embedder
        self.query_mode = "hybrid"

    def _get_embedder(self) -> Embedder:
        if self.embedder is None:
            # Disable sparse model if not supported to avoid errors
            self.embedder = Embedder(
                dense_model=settings.dense_model_name,
                sparse_model=None,
            )
        return self.embedder

    def retrieve(self, query: str, *, candidates: list[dict] | None = None) -> list[dict]:
        if candidates is not None:
            return rerank_candidates(candidates, top_k=settings.rag_rerank_top_k)

        if not query.strip():
            return []

        try:
            dense_vectors, _ = self._get_embedder().embed_batch([query])
            query_vector = dense_vectors[0].tolist()
            result = self.index.client.query_points(
                collection_name=self.index.COLLECTION_NAME,
                query=query_vector,
                limit=settings.rag_hybrid_top_k,
                with_payload=True,
            )
            points = list(getattr(result, "points", []))
            candidates_out = []
            for point in points:
                payload = point.payload or {}

                # Accept either format: old (text/source_id/timestamp/page) or new (topic/fact/confidence/source_refs)
                text = payload.get("text") or payload.get("fact", "")
                if not text:
                    continue

                candidates_out.append(
                    {
                        "score": float(getattr(point, "score", 0.0)),
                        "text": text,
                        "metadata": {
                            "topic": payload.get("topic"),
                            "fact": payload.get("fact"),
                            "confidence": payload.get("confidence"),
                            "source_id": payload.get("source_id") or (payload.get("source_refs", [None])[0] if payload.get("source_refs") else None),
                            "timestamp": payload.get("timestamp"),
                            "page": payload.get("page"),
                        },
                    }
                )
            return candidates_out
        except Exception:
            return []
