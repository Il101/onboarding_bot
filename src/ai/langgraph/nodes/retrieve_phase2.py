from __future__ import annotations

import asyncio
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
        base_url=settings.knowledge_api_base_url,
        timeout=httpx.Timeout(15.0),
    )
    attempts = max(1, settings.bot_retrieve_max_attempts)
    backoff = max(0.0, settings.bot_retrieve_retry_backoff_seconds)
    try:
        last_error: Exception | None = None
        data: Any = None
        for attempt in range(1, attempts + 1):
            try:
                response = await local_client.post("/api/knowledge/query", json=payload)
                response.raise_for_status()
                data = response.json()
                break
            except (httpx.TimeoutException, httpx.TransportError, httpx.HTTPStatusError) as exc:
                last_error = exc
                if attempt >= attempts:
                    raise
                await asyncio.sleep(backoff * attempt)
        if last_error is not None and data is None:
            raise last_error
    finally:
        if owns_client:
            await local_client.aclose()

    if not isinstance(data, dict) or not _REQUIRED_KEYS.issubset(data.keys()):
        raise ValueError("invalid_phase2_envelope")
    strict_payload = {k: data[k] for k in ("answer", "confidence", "sources", "fallback_used")}
    return {"rag_payload": strict_payload}
