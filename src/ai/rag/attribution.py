from __future__ import annotations

from src.ai.rag.contracts import AttributionItem


def format_attribution(nodes: list[dict]) -> list[AttributionItem]:
    output: list[AttributionItem] = []
    for node in nodes:
        metadata = node.get("metadata", {})
        output.append(
            AttributionItem(
                source_id=metadata.get("source_id", ""),
                excerpt=node.get("text", "")[:240],
                score=float(node.get("score", 0.0)),
                timestamp=metadata.get("timestamp"),
                page=metadata.get("page"),
            )
        )
    return output
