from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from src.pipeline.parsers.telegram import TelegramMessage
from src.pipeline.parsers.voice import transcribe_audio, transcribe_voice_messages


def test_transcribe_calls_groq(tmp_path):
    audio_path = tmp_path / "voice.ogg"
    audio_path.write_bytes(b"audio")
    client = MagicMock()
    client.audio.transcriptions.create.return_value = SimpleNamespace(text="ok")

    transcribe_audio(client, str(audio_path))
    kwargs = client.audio.transcriptions.create.call_args.kwargs
    assert kwargs["model"] == "whisper-large-v3-turbo"
    assert kwargs["language"] == "ru"


def test_transcribe_returns_text(tmp_path):
    audio_path = tmp_path / "voice.ogg"
    audio_path.write_bytes(b"audio")
    client = MagicMock()
    client.audio.transcriptions.create.return_value = SimpleNamespace(text="Transcribed text")
    assert transcribe_audio(client, str(audio_path)) == "Transcribed text"


def test_large_file_chunked(tmp_path):
    audio_path = tmp_path / "large.ogg"
    audio_path.write_bytes(b"audio")
    client = MagicMock()
    client.audio.transcriptions.create.return_value = SimpleNamespace(text="chunk")

    with patch("src.pipeline.parsers.voice.os.path.getsize", return_value=30 * 1024 * 1024):
        with patch("src.pipeline.parsers.voice._load_audio_segment") as load_audio:
            from_file = MagicMock()
            fake_seg = MagicMock()
            fake_seg.__len__.return_value = 120000
            fake_seg.__getitem__.return_value = fake_seg
            fake_seg.export.return_value = None
            from_file.return_value = fake_seg
            load_audio.return_value = SimpleNamespace(from_file=from_file)
            with patch("src.pipeline.parsers.voice._transcribe_single_file", return_value="chunk") as transcribe:
                transcribe_audio(client, str(audio_path))
                assert from_file.called
                assert transcribe.called


def test_transcribe_voice_messages(tmp_path):
    voice_dir = tmp_path / "voices"
    voice_dir.mkdir()
    (voice_dir / "1.ogg").write_bytes(b"audio")
    (voice_dir / "2.ogg").write_bytes(b"audio")

    messages = [
        TelegramMessage(1, "2024-01-15T10:00:00", "A", "user1", "", False, False, "voice_message", "1.ogg"),
        TelegramMessage(2, "2024-01-15T10:05:00", "B", "user2", "text", False, False, None, None),
        TelegramMessage(3, "2024-01-15T10:10:00", "A", "user1", "", False, False, "voice_message", "2.ogg"),
    ]
    client = MagicMock()
    client.audio.transcriptions.create.return_value = SimpleNamespace(text="voice text")
    result = transcribe_voice_messages(messages, str(voice_dir), client)
    assert result[0].text == "voice text"
    assert result[2].text == "voice text"


def test_messages_without_voice_unchanged():
    messages = [
        TelegramMessage(1, "2024-01-15T10:00:00", "A", "user1", "orig", False, False, None, None),
    ]
    result = transcribe_voice_messages(messages, ".", MagicMock())
    assert result[0].text == "orig"


def test_missing_voice_file_graceful():
    messages = [
        TelegramMessage(1, "2024-01-15T10:00:00", "A", "user1", "", False, False, "voice_message", "missing.ogg"),
    ]
    result = transcribe_voice_messages(messages, "/tmp/nonexistent", MagicMock())
    assert len(result) == 1
