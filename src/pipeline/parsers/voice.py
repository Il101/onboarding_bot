import os

from groq import Groq

from src.core.config import settings
from src.core.logging import get_logger

logger = get_logger(__name__)

MAX_FILE_SIZE_BYTES = 25 * 1024 * 1024


def _load_audio_segment():
    from pydub import AudioSegment

    return AudioSegment


def _transcribe_single_file(client: Groq, file_path: str) -> str:
    with open(file_path, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            model="whisper-large-v3-turbo",
            file=audio_file,
            response_format="text",
            language="ru",
        )
    return getattr(transcription, "text", str(transcription))


def transcribe_audio(client: Groq, file_path: str) -> str:
    if os.path.getsize(file_path) <= MAX_FILE_SIZE_BYTES:
        return _transcribe_single_file(client, file_path)

    audio_segment = _load_audio_segment()
    audio = audio_segment.from_file(file_path)
    chunk_ms = 60_000
    texts: list[str] = []
    for start in range(0, len(audio), chunk_ms):
        part = audio[start : start + chunk_ms]
        temp_path = f"{file_path}.{start}.ogg"
        part.export(temp_path, format="ogg")
        try:
            texts.append(_transcribe_single_file(client, temp_path))
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    return " ".join(texts).strip()


def transcribe_voice_messages(messages: list, voice_dir: str, groq_client: Groq | None = None) -> list:
    client = groq_client or Groq(api_key=settings.groq_api_key)

    for message in messages:
        if message.media_type != "voice_message" or not message.voice_path:
            continue
        full_path = os.path.join(voice_dir, message.voice_path)
        if not os.path.exists(full_path):
            logger.warning("Voice file missing: %s", full_path)
            continue
        message.text = transcribe_audio(client, full_path)
    return messages
