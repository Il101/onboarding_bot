from types import SimpleNamespace
from unittest.mock import patch

import numpy as np

from src.pipeline.indexer.embedder import Embedder
from src.pipeline.indexer.qdrant_store import QdrantStore


def test_embed_batch_returns_tuple():
    with patch("src.pipeline.indexer.embedder.TextEmbedding") as dense_cls:
        with patch("src.pipeline.indexer.embedder.SparseTextEmbedding") as sparse_cls:
            dense_cls.return_value.embed.return_value = [np.zeros(1024), np.ones(1024)]
            sparse_cls.return_value.embed.return_value = [
                SimpleNamespace(indices=[1], values=[0.1]),
                SimpleNamespace(indices=[2], values=[0.2]),
            ]
            embedder = Embedder()
            dense, sparse = embedder.embed_batch(["текст 1", "текст 2"])
            assert len(dense) == 2
            assert len(sparse) == 2


def test_dense_vector_dimensionality():
    with patch("src.pipeline.indexer.embedder.TextEmbedding") as dense_cls:
        with patch("src.pipeline.indexer.embedder.SparseTextEmbedding") as sparse_cls:
            dense_cls.return_value.embed.return_value = [np.zeros(1024)]
            sparse_cls.return_value.embed.return_value = [SimpleNamespace(indices=[1], values=[0.1])]
            embedder = Embedder()
            dense, _ = embedder.embed_batch(["текст"])
            assert dense[0].shape[0] == 1024


def test_ensure_collection_creates_with_config(mock_qdrant_client):
    store = QdrantStore(mock_qdrant_client)
    mock_qdrant_client.collection_exists.return_value = False
    store.ensure_collection()
    mock_qdrant_client.create_collection.assert_called_once()
    kwargs = mock_qdrant_client.create_collection.call_args.kwargs
    assert kwargs["vectors_config"]["dense"].size == 1024
    assert "sparse" in kwargs["sparse_vectors_config"]


def test_upsert_chunks_correct_format(mock_qdrant_client):
    store = QdrantStore(mock_qdrant_client)
    chunks = [
        {
            "id": "telegram:src1:0",
            "text": "текст",
            "dense_vector": [0.1] * 1024,
            "sparse_vector": SimpleNamespace(indices=[1, 2], values=[0.5, 0.3]),
            "metadata": {"source_type": "telegram", "source_id": "src1", "date_range": "..."},
        }
    ]
    count = store.upsert_chunks(chunks)
    assert count == 1
    mock_qdrant_client.upsert.assert_called_once()


def test_composite_ids(mock_qdrant_client):
    store = QdrantStore(mock_qdrant_client)
    chunks = [
        {
            "id": "telegram:source123:0",
            "text": "t",
            "dense_vector": [0.1] * 1024,
            "sparse_vector": SimpleNamespace(indices=[], values=[]),
            "metadata": {"source_id": "source123", "source_type": "telegram"},
        }
    ]
    store.upsert_chunks(chunks)
    points = mock_qdrant_client.upsert.call_args.kwargs["points"]
    assert points[0].id == "telegram:source123:0"


def test_delete_by_source(mock_qdrant_client):
    store = QdrantStore(mock_qdrant_client)
    store.delete_by_source("source123")
    mock_qdrant_client.delete.assert_called_once()


def test_payload_includes_text_and_metadata(mock_qdrant_client):
    store = QdrantStore(mock_qdrant_client)
    chunks = [
        {
            "id": "t:1:0",
            "text": "текст",
            "dense_vector": [0.1] * 1024,
            "sparse_vector": SimpleNamespace(indices=[], values=[]),
            "metadata": {"source_type": "pdf", "source_id": "1"},
        }
    ]
    store.upsert_chunks(chunks)
    points = mock_qdrant_client.upsert.call_args.kwargs["points"]
    assert points[0].payload["text"] == "текст"
    assert points[0].payload["source_type"] == "pdf"
