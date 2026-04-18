from __future__ import annotations


def rerank_candidates(candidates: list[dict], top_k: int) -> list[dict]:
    if not candidates or top_k <= 0:
        return []
    ranked = sorted(candidates, key=lambda item: item.get("score", 0.0), reverse=True)
    return ranked[:top_k]
