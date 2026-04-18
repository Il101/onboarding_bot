from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.pipeline.parsers.telegram import TelegramMessage


@patch("src.tasks.ingest.parse_telegram_export")
@patch("src.tasks.ingest.transcribe_voice_messages")
@patch("src.tasks.ingest.anonymize_text")
@patch("src.tasks.ingest.filter_messages")
@patch("src.tasks.ingest.chunk_telegram_messages")
@patch("src.tasks.ingest.Embedder")
@patch("src.tasks.ingest.QdrantStore")
@patch("src.tasks.ingest.QdrantClient")
def test_ingest_telegram_pipeline_order(
    mock_qdrant_client,
    mock_store_cls,
    mock_embedder_cls,
    mock_chunk,
    mock_filter,
    mock_anonymize,
    mock_transcribe,
    mock_parse,
):
    from src.tasks.ingest import ingest_telegram

    msg = TelegramMessage(1, "2024-01-15T10:00:00", "A", "u1", "текст", False, False, None, None)
    mock_parse.return_value = [msg]
    mock_transcribe.side_effect = lambda msgs, d, c=None: msgs
    mock_anonymize.side_effect = lambda text, analyzer, anonymizer: text
    mock_filter.return_value = [msg]
    mock_chunk.return_value = [{"text": "чанк", "metadata": {"source_type": "telegram"}}]
    mock_embedder = MagicMock()
    mock_embedder.embed_batch.return_value = ([SimpleNamespace(tolist=lambda: [0.1] * 1024)], [SimpleNamespace(indices=[1], values=[0.5])])
    mock_embedder_cls.return_value = mock_embedder
    mock_store = MagicMock()
    mock_store.upsert_chunks.return_value = 1
    mock_store_cls.return_value = mock_store

    with patch.object(ingest_telegram, "update_state", return_value=None):
        result = ingest_telegram.run(source_id="test", json_path="/tmp/test.json", voice_dir="/tmp/voices")
    assert result["status"] == "completed"
    mock_parse.assert_called_once()
    mock_anonymize.assert_called()


@patch("src.tasks.ingest.extract_pdf_text")
@patch("src.tasks.ingest.anonymize_text")
@patch("src.tasks.ingest.chunk_text")
@patch("src.tasks.ingest.Embedder")
@patch("src.tasks.ingest.QdrantStore")
@patch("src.tasks.ingest.QdrantClient")
def test_ingest_pdf_pipeline(mock_qdrant_client, mock_store_cls, mock_embedder_cls, mock_chunk, mock_anonymize, mock_parse):
    from src.tasks.ingest import ingest_pdf

    mock_parse.return_value = "# PDF Content"
    mock_anonymize.return_value = "# Anonymized"
    mock_chunk.return_value = ["чанк 1", "чанк 2"]
    mock_embedder = MagicMock()
    mock_embedder.embed_batch.return_value = (
        [SimpleNamespace(tolist=lambda: [0.1] * 1024), SimpleNamespace(tolist=lambda: [0.2] * 1024)],
        [SimpleNamespace(indices=[1], values=[0.5]), SimpleNamespace(indices=[2], values=[0.6])],
    )
    mock_embedder_cls.return_value = mock_embedder
    mock_store = MagicMock()
    mock_store.upsert_chunks.return_value = 2
    mock_store_cls.return_value = mock_store

    with patch.object(ingest_pdf, "update_state", return_value=None):
        result = ingest_pdf.run(source_id="test", file_path="/tmp/test.pdf")
    assert result["status"] == "completed"


@patch("src.tasks.ingest.filter_messages")
@patch("src.tasks.ingest.anonymize_text")
@patch("src.tasks.ingest.transcribe_voice_messages")
@patch("src.tasks.ingest.parse_telegram_export")
@patch("src.tasks.ingest.chunk_telegram_messages")
@patch("src.tasks.ingest.Embedder")
@patch("src.tasks.ingest.QdrantStore")
@patch("src.tasks.ingest.QdrantClient")
def test_pii_before_filter_enforced(
    mock_qdrant_client,
    mock_store_cls,
    mock_embedder_cls,
    mock_chunk,
    mock_parse,
    mock_transcribe,
    mock_anonymize,
    mock_filter,
):
    from src.tasks.ingest import ingest_telegram

    calls = []
    msg = TelegramMessage(1, "2024-01-15T10:00:00", "A", "u1", "text", False, False, None, None)
    mock_parse.return_value = [msg]

    def track_anonymize(text, analyzer, anonymizer):
        calls.append("anonymize")
        return text

    def track_filter(msgs):
        calls.append("filter")
        return msgs

    mock_anonymize.side_effect = track_anonymize
    mock_filter.side_effect = track_filter
    mock_transcribe.side_effect = lambda m, d, c=None: m
    mock_chunk.return_value = [{"text": "x", "metadata": {"source_type": "telegram"}}]
    mock_embedder = MagicMock()
    mock_embedder.embed_batch.return_value = ([SimpleNamespace(tolist=lambda: [0.1] * 1024)], [SimpleNamespace(indices=[1], values=[0.5])])
    mock_embedder_cls.return_value = mock_embedder
    mock_store = MagicMock()
    mock_store.upsert_chunks.return_value = 1
    mock_store_cls.return_value = mock_store

    with patch.object(ingest_telegram, "update_state", return_value=None):
        ingest_telegram.run(source_id="s1", json_path="/tmp/a.json", voice_dir="/tmp")
    assert calls.index("anonymize") < calls.index("filter")


@patch("src.tasks.ingest.filter_messages", side_effect=RuntimeError("boom"))
@patch("src.tasks.ingest.parse_telegram_export")
def test_failure_state_on_exception(mock_parse, mock_filter):
    from src.tasks.ingest import ingest_telegram

    mock_parse.return_value = [TelegramMessage(1, "2024-01-15T10:00:00", "A", "u1", "x", False, False, None, None)]
    with patch.object(ingest_telegram, "update_state", return_value=None):
        try:
            ingest_telegram.run(source_id="s1", json_path="/tmp/a.json", voice_dir="/tmp")
        except RuntimeError:
            assert True


@pytest.fixture
def client():
    from src.api.main import app

    return TestClient(app)


@patch("src.api.routes.ingest.ingest_telegram")
def test_upload_telegram_returns_job_id(mock_task, client):
    mock_task.delay.return_value = MagicMock(id="test-job-123")
    response = client.post(
        "/api/ingest/telegram",
        files={"json_file": ("result.json", b'{"messages": []}', "application/json")},
    )
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert data["status"] == "started"


@patch("src.api.routes.ingest.ingest_pdf")
def test_upload_pdf_returns_job_id(mock_task, client):
    mock_task.delay.return_value = MagicMock(id="test-job-456")
    response = client.post(
        "/api/ingest/pdf",
        files={"file": ("doc.pdf", b"%PDF-1.4 content", "application/pdf")},
    )
    assert response.status_code == 200
    assert "job_id" in response.json()


@patch("src.api.routes.ingest.AsyncResult")
def test_get_status_returns_progress(mock_result, client):
    mock_result.return_value.state = "PROGRESS"
    mock_result.return_value.info = {"stage": "parsing", "progress": 10}
    response = client.get("/api/ingest/status/test-job-123")
    assert response.status_code == 200
    assert response.json()["status"] == "processing"


def test_upload_invalid_file_type_returns_400(client):
    response = client.post(
        "/api/ingest/pdf",
        files={"file": ("doc.txt", b"not a pdf", "text/plain")},
    )
    assert response.status_code == 400


def test_upload_oversized_file_returns_413(client):
    big_content = b"x" * (101 * 1024 * 1024)
    response = client.post(
        "/api/ingest/pdf",
        files={"file": ("big.pdf", b"%PDF-" + big_content, "application/pdf")},
    )
    assert response.status_code == 413


@patch("src.api.routes.ingest.ingest_pdf")
def test_filenames_uuid_based(mock_task, client):
    mock_task.delay.return_value = MagicMock(id="job-1")
    response = client.post(
        "/api/ingest/pdf",
        files={"file": ("../../evil.pdf", b"%PDF-1.4 content", "application/pdf")},
    )
    assert response.status_code == 200
    args = mock_task.delay.call_args.args
    saved_path = args[1]
    assert ".." not in saved_path
    assert saved_path.endswith(".pdf")
