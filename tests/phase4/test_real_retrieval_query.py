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
            "text": "Откройте CRM и проверьте карточку клиента",
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
        response = client.post("/api/knowledge/query", json={"query": "как оформить заявку"})

    assert response.status_code == 200
    retriever.retrieve.assert_called_once_with("как оформить заявку")
    _, kwargs = synth.call_args
    assert kwargs["candidates"][0]["metadata"]["source_id"] == "doc:crm"


def test_query_route_passes_retrieval_candidates_to_synthesizer():
    from src.api.main import app

    client = TestClient(app)
    retriever = MagicMock()
    candidates = [
        {
            "score": 0.9,
            "text": "Реальный документ",
            "metadata": {"source_id": "doc:1", "timestamp": "2026-04-11T10:00:00"},
        }
    ]
    retriever.retrieve.return_value = candidates

    with patch("src.api.routes.knowledge.HybridRetriever", return_value=retriever):
        response = client.post("/api/knowledge/query", json={"query": "где инструкция", "top_k": 1})

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
            "text": "Слабосвязанный фрагмент",
            "metadata": {"source_id": "doc:low", "timestamp": "2026-04-11T10:00:00"},
        }
    ]

    with patch("src.api.routes.knowledge.HybridRetriever", return_value=retriever):
        response = client.post("/api/knowledge/query", json={"query": "редкий вопрос"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["fallback_used"] is True
    assert payload["sources"]
