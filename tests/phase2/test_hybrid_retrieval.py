
def test_retriever_defaults_to_hybrid_mode():
    from src.ai.rag.retriever import HybridRetriever

    retriever = HybridRetriever(index=object())
    assert retriever.query_mode == "hybrid"


def test_rerank_truncates_to_configured_top_k():
    from src.ai.rag.reranker import rerank_candidates

    candidates = [
        {"text": "A", "score": 0.2},
        {"text": "B", "score": 0.9},
        {"text": "C", "score": 0.7},
    ]
    ranked = rerank_candidates(candidates, top_k=2)
    assert len(ranked) == 2
    assert ranked[0]["text"] == "B"


def test_attribution_formatter_emits_required_fields():
    from src.ai.rag.attribution import format_attribution

    nodes = [
        {
            "score": 0.88,
            "text": "Откройте CRM и проверьте статус",
            "metadata": {"source_id": "src1", "timestamp": "2026-04-12T11:00:00"},
        }
    ]
    out = format_attribution(nodes)
    assert out[0].source_id == "src1"
    assert out[0].excerpt
    assert out[0].timestamp == "2026-04-12T11:00:00"


def test_attribution_preserves_score_for_auditability():
    from src.ai.rag.attribution import format_attribution

    nodes = [{"score": 0.42, "text": "x", "metadata": {"source_id": "src1", "page": 2}}]
    out = format_attribution(nodes)
    assert out[0].score == 0.42
