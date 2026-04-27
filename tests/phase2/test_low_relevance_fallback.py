from fastapi.testclient import TestClient


def test_synthesizer_returns_fallback_when_low_relevance():
    from src.ai.rag.synthesizer import synthesize_answer

    candidates = [{"score": 0.1, "text": "x", "metadata": {"source_id": "src1", "timestamp": "2026-04-12T11:00:00"}}]
    result = synthesize_answer("как оформить заказ", candidates=candidates)
    assert result.fallback_used is True
    assert "Недостаточно данных" in result.answer
    assert result.sources


def test_synthesizer_returns_grounded_answer_when_relevant():
    from src.ai.rag.synthesizer import synthesize_answer

    candidates = [
        {
            "score": 0.8,
            "text": "Откройте CRM и проверьте карточку клиента",
            "metadata": {"source_id": "src1", "timestamp": "2026-04-12T11:00:00"},
        }
    ]
    result = synthesize_answer("как оформить заказ", candidates=candidates)
    assert result.fallback_used is False
    assert result.answer
    assert result.sources


def test_api_query_returns_stable_envelope():
    from src.api.main import app

    client = TestClient(app)
    response = client.post("/api/knowledge/query", json={"query": "как оформить заказ"})
    assert response.status_code == 200
    data = response.json()
    assert set(data.keys()) == {"answer", "confidence", "sources", "fallback_used"}


def test_api_rejects_malformed_payload_without_internal_leakage():
    from src.api.main import app

    client = TestClient(app)
    response = client.post("/api/knowledge/query", json={})
    assert response.status_code in (400, 422)
    body = response.text.lower()
    assert "traceback" not in body
    assert "exception" not in body


def test_api_accepts_top_k_within_config_limit():
    from src.api.main import app

    client = TestClient(app)
    response = client.post("/api/knowledge/query", json={"query": "как оформить заказ", "top_k": 3})
    assert response.status_code == 200
    data = response.json()
    assert set(data.keys()) == {"answer", "confidence", "sources", "fallback_used"}


def test_api_rejects_top_k_above_config_limit():
    from src.api.main import app

    client = TestClient(app)
    response = client.post("/api/knowledge/query", json={"query": "как оформить заказ", "top_k": 999})
    assert response.status_code == 422
