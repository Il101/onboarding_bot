from __future__ import annotations

from qdrant_client import QdrantClient

from src.ai.extraction.schemas import KnowledgeUnit
from src.core.config import settings
from src.pipeline.indexer.embedder import Embedder
from src.pipeline.indexer.qdrant_store import QdrantStore


def index_knowledge_units(
    units: list[KnowledgeUnit],
    store: QdrantStore | None = None,
    embedder: Embedder | None = None,
) -> int:
    if not units:
        return 0

    qdrant_store = store or QdrantStore(QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port))
    if hasattr(qdrant_store, "ensure_collection"):
        qdrant_store.ensure_collection()

    embedder_instance = embedder or Embedder(
        dense_model=settings.dense_model_name,
        sparse_model=settings.sparse_model_name,
    )
    texts = [unit.fact for unit in units]
    dense_vectors, sparse_vectors = embedder_instance.embed_batch(texts)

    chunks: list[dict] = []
    for idx, unit in enumerate(units):
        ref = unit.source_refs[0]
        chunks.append(
            {
                "id": f"knowledge:{ref.source_id}:{idx}",
                "text": unit.fact,
                "dense_vector": dense_vectors[idx].tolist(),
                "sparse_vector": sparse_vectors[idx],
                "metadata": {
                    "source_id": ref.source_id,
                    "excerpt": ref.excerpt,
                    "timestamp": ref.timestamp,
                    "page": ref.page,
                    "topic": unit.topic,
                    "confidence": unit.confidence,
                },
            }
        )

    return qdrant_store.upsert_chunks(chunks)
