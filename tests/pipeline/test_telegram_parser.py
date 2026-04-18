import json

from src.pipeline.parsers.telegram import parse_telegram_export


def test_parse_regular_messages(tmp_path):
    data = {
        "messages": [
            {
                "id": 1,
                "type": "message",
                "date": "2024-01-15T10:00:00",
                "from": "Иван Иванов",
                "from_id": "user123",
                "text": "Привет",
            }
        ]
    }
    path = tmp_path / "result.json"
    path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")

    parsed = parse_telegram_export(str(path))
    assert len(parsed) == 1
    assert parsed[0].id == 1
    assert parsed[0].author == "Иван Иванов"
    assert parsed[0].author_id == "user123"


def test_service_messages_excluded(sample_telegram_json):
    parsed = parse_telegram_export(sample_telegram_json)
    assert all(msg.is_service is False for msg in parsed)
    assert len(parsed) == 2


def test_rich_text_array(tmp_path):
    data = {
        "messages": [
            {
                "id": 1,
                "type": "message",
                "date": "2024-01-15T10:00:00",
                "from": "A",
                "from_id": "user1",
                "text": [{"type": "plain", "text": "Hello "}, {"type": "bold", "text": "world"}],
            }
        ]
    }
    path = tmp_path / "result.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    parsed = parse_telegram_export(str(path))
    assert parsed[0].text == "Hello world"


def test_voice_message_linked(tmp_path):
    data = {
        "messages": [
            {
                "id": 1,
                "type": "message",
                "date": "2024-01-15T10:00:00",
                "from": "A",
                "from_id": "user1",
                "text": "",
                "media_type": "voice_message",
                "file_name": "voice.ogg",
            }
        ]
    }
    path = tmp_path / "result.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    parsed = parse_telegram_export(str(path))
    assert parsed[0].voice_path == "voice.ogg"


def test_html_stripped(tmp_path):
    data = {
        "messages": [
            {
                "id": 1,
                "type": "message",
                "date": "2024-01-15T10:00:00",
                "from": "A",
                "from_id": "user1",
                "text": "<b>bold</b> text",
            }
        ]
    }
    path = tmp_path / "result.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    parsed = parse_telegram_export(str(path))
    assert parsed[0].text == "bold text"


def test_empty_text_non_voice_skipped(tmp_path):
    data = {"messages": [{"id": 1, "type": "message", "date": "2024-01-15T10:00:00", "from": "A", "from_id": "user1"}]}
    path = tmp_path / "result.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    parsed = parse_telegram_export(str(path))
    assert parsed == []


def test_edited_message(tmp_path):
    data = {
        "messages": [
            {
                "id": 1,
                "type": "message",
                "date": "2024-01-15T10:00:00",
                "edit_date": "2024-01-15T10:01:00",
                "from": "A",
                "from_id": "user1",
                "text": "updated",
            }
        ]
    }
    path = tmp_path / "result.json"
    path.write_text(json.dumps(data), encoding="utf-8")
    parsed = parse_telegram_export(str(path))
    assert parsed[0].edit_date == "2024-01-15T10:01:00"
