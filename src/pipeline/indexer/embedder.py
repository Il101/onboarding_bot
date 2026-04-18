from fastembed import SparseTextEmbedding, TextEmbedding


class Embedder:
    def __init__(
        self,
        dense_model: str = "intfloat/multilingual-e5-large",
        sparse_model: str = "Qdrant/bm42-all-MiniLM-L6-v2-quantized",
    ):
        self._dense = TextEmbedding(model_name=dense_model)
        self._sparse = SparseTextEmbedding(model_name=sparse_model)

    def embed_batch(self, texts: list[str]) -> tuple[list, list]:
        dense_vectors = list(self._dense.embed(texts, batch_size=32))
        sparse_vectors = list(self._sparse.embed(texts))
        return dense_vectors, sparse_vectors
