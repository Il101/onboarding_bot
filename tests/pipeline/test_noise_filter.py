from src.pipeline.filters.grouping import group_messages_chronologically
from src.pipeline.filters.noise import filter_messages, is_noise
from src.pipeline.parsers.telegram import TelegramMessage


def _msg(
    text: str,
    *,
    date: str = "2024-01-15T10:00:00",
    is_service: bool = False,
    is_bot: bool = False,
    author: str = "user",
) -> TelegramMessage:
    return TelegramMessage(
        id=1,
        date=date,
        author=author,
        author_id="bot" if is_bot else "user",
        text=text,
        is_service=is_service,
        is_bot=is_bot,
        media_type=None,
        voice_path=None,
    )


def test_service_is_noise():
    assert is_noise("привет", is_service=True, is_bot=False, author="user")


def test_bot_is_noise():
    assert is_noise("hello", is_service=False, is_bot=True, author="bot")


def test_exact_noise_words():
    assert is_noise("ок", is_service=False, is_bot=False, author="user")
    assert is_noise("спасибо", is_service=False, is_bot=False, author="user")
    assert is_noise("+", is_service=False, is_bot=False, author="user")


def test_short_valuable_not_noise():
    assert not is_noise("звони Ивану", is_service=False, is_bot=False, author="user")
    assert not is_noise("проверь накладную", is_service=False, is_bot=False, author="user")


def test_empty_is_noise():
    assert is_noise("   ", is_service=False, is_bot=False, author="user")


def test_filter_messages_removes_noise():
    messages = [
        _msg("спасибо"),
        _msg("звони Ивану"),
        _msg("ok"),
        _msg("важное сообщение"),
        _msg("x", is_bot=True),
    ]
    filtered = filter_messages(messages)
    assert [m.text for m in filtered] == ["звони Ивану", "важное сообщение"]


def test_grouping_within_window():
    messages = [
        _msg("a", date="2024-01-15T10:00:00"),
        _msg("b", date="2024-01-15T10:10:00"),
        _msg("c", date="2024-01-15T10:25:00"),
    ]
    groups = group_messages_chronologically(messages, window_minutes=30)
    assert len(groups) == 1
    assert len(groups[0]) == 3


def test_grouping_across_gap():
    messages = [
        _msg("a", date="2024-01-15T10:00:00"),
        _msg("b", date="2024-01-15T10:45:00"),
    ]
    groups = group_messages_chronologically(messages, window_minutes=30)
    assert len(groups) == 2


def test_grouping_empty():
    assert group_messages_chronologically([], window_minutes=30) == []


def test_grouping_single():
    msg = _msg("single", date="2024-01-15T10:00:00")
    assert group_messages_chronologically([msg], window_minutes=30) == [[msg]]
