import json
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def sample_telegram_messages():
    return [
        {
            "id": 1,
            "type": "message",
            "date": "2024-01-15T10:00:00",
            "from": "John Doe",
            "from_id": "user123",
            "text": "Call Alex at +7(903)123-45-67",
        },
        {
            "id": 2,
            "type": "service",
            "date": "2024-01-15T10:01:00",
            "from": "John Doe",
            "from_id": "user123",
            "text": "John Doe joined the group",
        },
        {
            "id": 3,
            "type": "message",
            "date": "2024-01-15T10:05:00",
            "from": "SomeBot",
            "from_id": "bot456",
            "text": "Reminder: meeting at 15:00",
        },
    ]


@pytest.fixture
def sample_telegram_json(tmp_path, sample_telegram_messages):
    data = {"name": "Test Chat", "messages": sample_telegram_messages}
    path = tmp_path / "result.json"
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return str(path)


@pytest.fixture
def sample_pii_text():
    return "Call John Doe at +7(903)123-45-67, email ivan@company.ru. Tax ID: 7707083893."


@pytest.fixture
def mock_qdrant_client():
    client = MagicMock()
    client.collection_exists.return_value = True
    return client


@pytest.fixture
def mock_groq_client():
    client = MagicMock()
    mock_result = MagicMock()
    mock_result.text = "Transcribed voice message text"
    client.audio.transcriptions.create.return_value = mock_result
    return client


@pytest.fixture
def sample_pdf_path(tmp_path):
    from fpdf import FPDF

    pdf_path = tmp_path / "sample.pdf"
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    pdf.cell(text="Test PDF content")
    pdf.output(str(pdf_path))
    return str(pdf_path)
