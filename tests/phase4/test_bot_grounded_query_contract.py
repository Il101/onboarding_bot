from __future__ import annotations

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient


def test_route_returns_bot_adapter_envelope_keys_unchanged():
    from src.api.main import app

    client = TestClient(app)
    with patch("src.api.routes.knowledge.HybridRetriever.retrieve", return_value=[]):
        response = client.post("/api/knowledge/query", json={"query": "how to request access"})

    assert response.status_code == 200
    payload = response.json()
    assert set(payload.keys()) == {"answer", "confidence", "sources", "fallback_used"}


def test_route_sources_include_required_attribution_fields():
    from src.api.main import app

    client = TestClient(app)
    candidates = [
        {
            "score": 0.9,
            "text": "Open the access portal",
            "metadata": {"source_id": "doc:portal", "timestamp": "2026-04-12T11:00:00"},
        }
    ]
    with patch("src.api.routes.knowledge.HybridRetriever.retrieve", return_value=candidates):
        response = client.post("/api/knowledge/query", json={"query": "where is the portal"})

    assert response.status_code == 200
    source = response.json()["sources"][0]
    assert source["source_id"]
    assert source["excerpt"]
    assert source.get("timestamp") or source.get("page")


@pytest.mark.asyncio
async def test_phase3_retrieve_adapter_consumes_migrated_query_output():
    import httpx

    from src.ai.langgraph.nodes.retrieve_phase2 import retrieve_phase2_payload

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "answer": "Open the access portal",
                "confidence": 0.86,
                "sources": [
                    {
                        "source_id": "doc:portal",
                        "excerpt": "Access instructions",
                        "timestamp": "2026-04-12T11:00:00",
                    }
                ],
                "fallback_used": False,
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(base_url="http://test", transport=transport) as client:
        result = await retrieve_phase2_payload({"query": "how to request access"}, client=client)

    assert set(result["rag_payload"].keys()) == {"answer", "confidence", "sources", "fallback_used"}
