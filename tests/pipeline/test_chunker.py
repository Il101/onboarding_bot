from src.pipeline.chunker.telegram_chunker import chunk_telegram_messages
from src.pipeline.chunker.text_chunker import chunk_text
from src.pipeline.parsers.telegram import TelegramMessage


def test_short_text_single_chunk():
    text = "Короткий текст."
    chunks = chunk_text(text)
    assert len(chunks) == 1
    assert chunks[0] == "Короткий текст."


def test_long_text_multiple_chunks():
    text = ("Предложение раз. " * 500).strip()
    chunks = chunk_text(text)
    assert len(chunks) >= 2


def test_overlap_between_chunks():
    text = (
        "Первое предложение. Второе. Третье. Четвёртое. Пятое. "
        "Шестое. Седьмое. Восьмое. Девятое. Десятое. "
    ) * 15
    chunks = chunk_text(text, overlap_sentences=1)
    if len(chunks) > 1:
        tail_sentence = chunks[0].split(".")[-2].strip()
        assert tail_sentence in chunks[1]


def test_markdown_heading_respected():
    text = "## Заголовок 1\nПараграф текста.\n\n## Заголовок 2\nДругой параграф."
    chunks = chunk_text(text)
    assert any("## Заголовок 1" in c for c in chunks)
    assert any("## Заголовок 2" in c for c in chunks)


def test_empty_text_returns_empty():
    assert chunk_text("") == []


def _msg(msg_id: int, date: str, author: str, text: str):
    return TelegramMessage(
        id=msg_id,
        date=date,
        author=author,
        author_id=f"user{msg_id}",
        text=text,
        is_service=False,
        is_bot=False,
        media_type=None,
        voice_path=None,
    )


def test_telegram_chunker_groups_and_chunks():
    messages = [
        _msg(1, "2024-01-15T10:00:00", "A", "Привет"),
        _msg(2, "2024-01-15T10:10:00", "B", "Ответ"),
        _msg(3, "2024-01-15T11:00:00", "A", "Новая тема"),
    ]
    chunks = chunk_telegram_messages(messages, window_minutes=30)
    assert all("source_type" in c["metadata"] for c in chunks)
    assert all(c["metadata"]["source_type"] == "telegram" for c in chunks)


def test_metadata_present():
    messages = [_msg(1, "2024-01-15T10:00:00", "A", "Текст")]
    chunks = chunk_telegram_messages(messages, window_minutes=30)
    md = chunks[0]["metadata"]
    assert "date_range" in md
    assert "authors" in md
    assert "chunk_index" in md


def test_author_prefixes():
    messages = [_msg(1, "2024-01-15T10:00:00", "AuthorName", "message text")]
    chunks = chunk_telegram_messages(messages, window_minutes=30)
    assert "[AuthorName]: message text" in chunks[0]["text"]


def test_single_message_group_metadata():
    messages = [_msg(1, "2024-01-15T10:00:00", "A", "single")]
    chunks = chunk_telegram_messages(messages, window_minutes=30)
    assert len(chunks) == 1
    assert chunks[0]["metadata"]["chunk_index"] == 0
