from __future__ import annotations

from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient


def test_query_route_no_longer_uses_static_seed_candidates():
    from src.api.main import app

    client = TestClient(app)
    retriever = MagicMock()
    retriever.retrieve.return_value = [
        {
            "score": 0.8,
            "text": "Open CRM and check the client card",
            "metadata": {"source_id": "doc:crm", "timestamp": "2026-04-10T10:00:00"},
        }
    ]

    with (
        patch("src.api.routes.knowledge.HybridRetriever", return_value=retriever),
        patch("src.api.routes.knowledge.synthesize_answer") as synth,
    ):
        synth.return_value = MagicMock(
            answer="answer",
            confidence=0.8,
            sources=[],
            fallback_used=False,
        )
        response = client.post("/api/knowledge/query", json={"query": "how to submit a request"})

    assert response.status_code == 200
    retriever.retrieve.assert_called_once_with("how to submit a request")
    _, kwargs = synth.call_args
    assert kwargs["candidates"][0]["metadata"]["source_id"] == "doc:crm"


def test_query_route_passes_retrieval_candidates_to_synthesizer():
    from src.api.main import app

    client = TestClient(app)
    retriever = MagicMock()
    candidates = [
        {
            "score": 0.9,
            "text": "Real document",
            "metadata": {"source_id": "doc:1", "timestamp": "2026-04-11T10:00:00"},
        }
    ]
    retriever.retrieve.return_value = candidates

    with patch("src.api.routes.knowledge.HybridRetriever", return_value=retriever):
        response = client.post("/api/knowledge/query", json={"query": "where is the instruction", "top_k": 1})

    assert response.status_code == 200
    data = response.json()
    assert set(data.keys()) == {"answer", "confidence", "sources", "fallback_used"}


def test_low_relevance_fallback_stays_active_and_returns_sources():
    from src.api.main import app

    client = TestClient(app)
    retriever = MagicMock()
    retriever.retrieve.return_value = [
        {
            "score": 0.1,
            "text": "Weakly related fragment",
            "metadata": {"source_id": "doc:low", "timestamp": "2026-04-11T10:00:00"},
        }
    ]

    with patch("src.api.routes.knowledge.HybridRetriever", return_value=retriever):
        response = client.post("/api/knowledge/query", json={"query": "rare question"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["fallback_used"] is True
    assert payload["sources"]
