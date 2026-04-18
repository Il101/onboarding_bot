from qdrant_client import QdrantClient, models
from qdrant_client.models import SparseVectorParams


class QdrantStore:
    COLLECTION_NAME = "knowledge"

    def __init__(self, client: QdrantClient):
        self.client = client

    def ensure_collection(self, dense_size: int = 1024):
        if not self.client.collection_exists(self.COLLECTION_NAME):
            self.client.create_collection(
                collection_name=self.COLLECTION_NAME,
                vectors_config={
                    "dense": models.VectorParams(
                        size=dense_size,
                        distance=models.Distance.COSINE,
                        hnsw_config=models.HnswConfigDiff(m=16, ef_construct=100),
                    )
                },
                sparse_vectors_config={
                    "sparse": SparseVectorParams(
                        index=models.SparseIndexParams(),
                    )
                },
            )

    def upsert_chunks(self, chunks: list[dict]) -> int:
        points = []
        for chunk in chunks:
            points.append(
                models.PointStruct(
                    id=chunk["id"],
                    vector={
                        "dense": chunk["dense_vector"],
                        "sparse": models.SparseVector(
                            indices=chunk["sparse_vector"].indices,
                            values=chunk["sparse_vector"].values,
                        ),
                    },
                    payload={"text": chunk["text"], **chunk["metadata"]},
                )
            )
        self.client.upsert(self.COLLECTION_NAME, points=points)
        return len(points)

    def delete_by_source(self, source_id: str):
        self.client.delete(
            self.COLLECTION_NAME,
            models.Filter(
                must=[
                    models.FieldCondition(
                        key="source_id",
                        match=models.MatchValue(value=source_id),
                    )
                ]
            ),
        )
