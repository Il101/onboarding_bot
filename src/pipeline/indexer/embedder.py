from fastembed import SparseTextEmbedding, TextEmbedding


class Embedder:
    def __init__(
        self,
        dense_model: str = "intfloat/multilingual-e5-large",
        sparse_model: str | None = None,
    ):
        self._dense = TextEmbedding(model_name=dense_model)
        self._sparse = SparseTextEmbedding(model_name=sparse_model) if sparse_model else None

    def embed_batch(self, texts: list[str]) -> tuple[list, list | None]:
        dense_vectors = list(self._dense.embed(texts, batch_size=32))
        sparse_vectors = list(self._sparse.embed(texts)) if self._sparse else None
        return dense_vectors, sparse_vectors
