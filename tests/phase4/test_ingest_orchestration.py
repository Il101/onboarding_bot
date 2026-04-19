from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest


class _Vec:
    def __init__(self, values: list[float]):
        self._values = values

    def tolist(self) -> list[float]:
        return self._values


def _raw_publishable():
    return [
        [
            {
                "fact": "Перед запуском отчета нужно выбрать филиал",
                "topic": "Отчетность",
                "confidence": 0.91,
                "source_refs": [
                    {
                        "source_id": "src1",
                        "excerpt": "нужно выбрать филиал",
                        "timestamp": "2026-04-12T11:00:00",
                    }
                ],
            }
        ]
    ]


def test_successful_telegram_ingest_dispatches_extraction_with_source_chunks():
    from src.tasks.ingest import ingest_telegram

    message = SimpleNamespace(text="Исходное сообщение")
    fake_store = MagicMock()
    fake_store.upsert_chunks.return_value = 1
    fake_extract_delay = MagicMock(return_value=SimpleNamespace(id="extract-job-1"))

    with (
        patch.object(ingest_telegram, "update_state", return_value=None),
        patch("src.tasks.ingest.parse_telegram_export", return_value=[message]),
        patch("src.tasks.ingest.transcribe_voice_messages", return_value=[message]),
        patch("src.tasks.ingest.create_analyzer", return_value=object()),
        patch("src.tasks.ingest.create_anonymizer", return_value=object()),
        patch("src.tasks.ingest.anonymize_text", side_effect=lambda text, *_: text),
        patch("src.tasks.ingest.filter_messages", return_value=[message]),
        patch(
            "src.tasks.ingest.chunk_telegram_messages",
            return_value=[{"text": "chunk-1", "metadata": {"source_type": "telegram"}}],
        ),
        patch("src.tasks.ingest.Embedder") as embedder_cls,
        patch("src.tasks.ingest.QdrantStore", return_value=fake_store),
        patch("src.tasks.ingest.extract_knowledge_task.delay", fake_extract_delay),
    ):
        embedder = embedder_cls.return_value
        embedder.embed_batch.return_value = ([_Vec([0.1, 0.2])], [SimpleNamespace(indices=[0], values=[1.0])])
        result = ingest_telegram.run(source_id="src1", json_path="/tmp/x.json", voice_dir="/tmp/voices")

    assert result == {"status": "completed", "messages_processed": 1, "chunks_indexed": 1}
    fake_extract_delay.assert_called_once()
    _, kwargs = fake_extract_delay.call_args
    assert kwargs["source_id"] == "src1"
    assert kwargs["chunks"][0]["text"] == "chunk-1"
    assert kwargs["chunks"][0]["metadata"]["source_id"] == "src1"


def test_extraction_completion_dispatches_sop_with_grouped_publishable_units():
    from src.tasks.knowledge import extract_knowledge_task

    sop_delay = MagicMock(return_value=SimpleNamespace(id="sop-job-1"))
    with (
        patch("src.tasks.knowledge.generate_sop_task.delay", sop_delay),
        patch.object(extract_knowledge_task, "update_state", return_value=None),
    ):
        result = extract_knowledge_task.run(
            source_id="src1",
            chunks=[{"text": "chunk-1", "metadata": {"source_id": "src1"}}],
            extraction_outputs=_raw_publishable(),
            index_writer=lambda units: len(units),
        )

    sop_delay.assert_called_once()
    _, kwargs = sop_delay.call_args
    assert kwargs["source_id"] == "src1"
    assert "Отчетность" in kwargs["grouped_units"]
    assert result["status"] == "completed"
    assert result["publishable_count"] == 1


def test_dispatch_failure_sets_controlled_failure_state_and_raises():
    from src.tasks.ingest import ingest_telegram

    states: list[str] = []

    def _capture_state(*, state, meta):
        states.append(state)

    message = SimpleNamespace(text="text")
    fake_store = MagicMock()
    fake_store.upsert_chunks.return_value = 1

    with (
        patch.object(ingest_telegram, "update_state", side_effect=_capture_state),
        patch("src.tasks.ingest.parse_telegram_export", return_value=[message]),
        patch("src.tasks.ingest.transcribe_voice_messages", return_value=[message]),
        patch("src.tasks.ingest.create_analyzer", return_value=object()),
        patch("src.tasks.ingest.create_anonymizer", return_value=object()),
        patch("src.tasks.ingest.anonymize_text", side_effect=lambda text, *_: text),
        patch("src.tasks.ingest.filter_messages", return_value=[message]),
        patch(
            "src.tasks.ingest.chunk_telegram_messages",
            return_value=[{"text": "chunk-1", "metadata": {"source_type": "telegram"}}],
        ),
        patch("src.tasks.ingest.Embedder") as embedder_cls,
        patch("src.tasks.ingest.QdrantStore", return_value=fake_store),
        patch("src.tasks.ingest.extract_knowledge_task.delay", side_effect=RuntimeError("dispatch failed")),
    ):
        embedder = embedder_cls.return_value
        embedder.embed_batch.return_value = ([_Vec([0.1, 0.2])], [SimpleNamespace(indices=[0], values=[1.0])])
        with pytest.raises(RuntimeError, match="dispatch failed"):
            ingest_telegram.run(source_id="src1", json_path="/tmp/x.json", voice_dir="/tmp/voices")

    assert "FAILURE" in states


def test_invalid_source_id_sets_failure_state_and_blocks_dispatch():
    from src.tasks.ingest import ingest_telegram

    states: list[str] = []

    def _capture_state(*, state, meta):
        states.append(state)

    with (
        patch.object(ingest_telegram, "update_state", side_effect=_capture_state),
        pytest.raises(ValueError, match="Invalid source_id"),
    ):
        ingest_telegram.run(source_id="   ", json_path="/tmp/x.json", voice_dir="/tmp/voices")

    assert "FAILURE" in states
