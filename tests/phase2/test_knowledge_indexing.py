from types import SimpleNamespace


class _FakeStore:
    COLLECTION_NAME = "knowledge"

    def __init__(self):
        self.calls = []

    def upsert_chunks(self, chunks):
        self.calls.append(chunks)
        return len(chunks)


def _publishable_units():
    from src.ai.extraction.schemas import KnowledgeUnit

    return [
        KnowledgeUnit.model_validate(
            {
                "fact": "Откройте CRM перед поиском клиента",
                "topic": "CRM",
                "confidence": 0.9,
                "source_refs": [
                    {
                        "source_id": "telegram:src1",
                        "excerpt": "Сначала CRM",
                        "timestamp": "2026-04-12T11:00:00",
                    }
                ],
            }
        )
    ]


def test_index_writer_maps_units_to_qdrant_points_payload_shape():
    from src.pipeline.indexer.knowledge_writer import index_knowledge_units

    store = _FakeStore()
    count = index_knowledge_units(_publishable_units(), store=store)
    assert count == 1
    payload = store.calls[0][0]["metadata"]
    assert payload["source_id"] == "telegram:src1"
    assert payload["topic"] == "CRM"
    assert payload["confidence"] == 0.9
    assert payload["timestamp"] == "2026-04-12T11:00:00"


def test_writer_uses_knowledge_collection_contract_and_locator_metadata():
    from src.pipeline.indexer.knowledge_writer import index_knowledge_units

    store = _FakeStore()
    index_knowledge_units(_publishable_units(), store=store)
    assert store.COLLECTION_NAME == "knowledge"
    assert "excerpt" in store.calls[0][0]["metadata"]


def test_extract_task_indexes_only_publishable_units():
    from src.tasks.knowledge import extract_knowledge_task

    chunks = [
        {"id": "x", "text": "x", "metadata": {"source_id": "src1", "timestamp": "2026-04-12T11:00:00"}},
        {"id": "y", "text": "y", "metadata": {"source_id": "src1", "timestamp": "2026-04-12T11:01:00"}},
    ]
    extraction_outputs = [
        [
            {
                "fact": "Публикуемое",
                "topic": "CRM",
                "confidence": 0.9,
                "source_refs": [{"source_id": "src1", "excerpt": "ok", "timestamp": "2026-04-12T11:00:00"}],
            }
        ],
        [
            {
                "fact": "На ревью",
                "topic": "CRM",
                "confidence": 0.1,
                "source_refs": [{"source_id": "src1", "excerpt": "low", "timestamp": "2026-04-12T11:01:00"}],
            }
        ],
    ]

    captured = {}

    def _writer(units, store=None):
        captured["count"] = len(units)
        return len(units)

    result = extract_knowledge_task.run(source_id="src1", chunks=chunks, extraction_outputs=extraction_outputs, index_writer=_writer)
    assert result["indexed_count"] == 1
    assert captured["count"] == 1


def test_empty_publishable_is_noop_indexed_count_zero():
    from src.pipeline.indexer.knowledge_writer import index_knowledge_units

    store = _FakeStore()
    count = index_knowledge_units([], store=store)
    assert count == 0
    assert store.calls == []
