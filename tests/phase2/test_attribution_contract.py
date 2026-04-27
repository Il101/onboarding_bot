def test_attribution_contract_structure_and_locator_presence():
    from src.ai.rag.attribution import format_attribution

    nodes = [
        {
            "score": 0.78,
            "text": "Шаг 1",
            "metadata": {"source_id": "pdf:guide", "page": 3},
        }
    ]
    items = format_attribution(nodes)
    assert len(items) == 1
    item = items[0]
    assert item.source_id == "pdf:guide"
    assert item.excerpt
    assert item.page == 3


def test_attribution_handles_timestamp_locator():
    from src.ai.rag.attribution import format_attribution

    nodes = [
        {"score": 0.61, "text": "Шаг 2", "metadata": {"source_id": "telegram:ops", "timestamp": "2026-04-12T11:00:00"}}
    ]
    items = format_attribution(nodes)
    assert items[0].timestamp == "2026-04-12T11:00:00"
