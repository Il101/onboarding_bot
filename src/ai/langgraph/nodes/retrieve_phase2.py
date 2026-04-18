from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import httpx

from src.core.config import settings

_REQUIRED_KEYS = {"answer", "confidence", "sources", "fallback_used"}


async def retrieve_phase2_payload(
    state: Mapping[str, Any],
    *,
    top_k: int | None = None,
    client: httpx.AsyncClient | None = None,
) -> dict[str, Any]:
    bounded_top_k = min(top_k or settings.rag_hybrid_top_k, settings.rag_hybrid_top_k)
    payload = {"query": str(state.get("query", "")), "top_k": bounded_top_k}
    owns_client = client is None
    local_client = client or httpx.AsyncClient(
        base_url="http://localhost:8000",
        timeout=httpx.Timeout(15.0),
    )
    try:
        response = await local_client.post("/api/knowledge/query", json=payload)
        response.raise_for_status()
        data = response.json()
    finally:
        if owns_client:
            await local_client.aclose()

    if not isinstance(data, dict) or not _REQUIRED_KEYS.issubset(data.keys()):
        raise ValueError("invalid_phase2_envelope")
    strict_payload = {k: data[k] for k in ("answer", "confidence", "sources", "fallback_used")}
    return {"rag_payload": strict_payload}
