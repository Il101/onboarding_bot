from pydantic import ValidationError
import pytest


def test_build_thread_id_is_deterministic_for_same_chat_and_user():
    from src.ai.langgraph.state import build_thread_id

    first = build_thread_id(chat_id=12345, user_id=777)
    second = build_thread_id(chat_id=12345, user_id=777)
    assert first == second
    assert first == "tg:12345:777"


def test_build_thread_id_changes_when_chat_or_user_changes():
    from src.ai.langgraph.state import build_thread_id

    base = build_thread_id(chat_id=12345, user_id=777)
    other_chat = build_thread_id(chat_id=54321, user_id=777)
    other_user = build_thread_id(chat_id=12345, user_id=888)
    assert base != other_chat
    assert base != other_user


def test_bot_answer_requires_non_empty_sources_and_text():
    from src.ai.langgraph.state import BotAnswer, SourceRef

    with pytest.raises(ValidationError):
        BotAnswer(answer="", confidence=0.5, fallback_used=False, sources=[])

    valid = BotAnswer(
        answer="1. Откройте базу знаний\n2. Найдите раздел\n3. Повторите шаги",
        confidence=0.78,
        fallback_used=False,
        sources=[
            SourceRef(
                source_id="pdf:onboarding",
                excerpt="Шаг 1. Откройте базу знаний",
                page=2,
            )
        ],
    )
    assert valid.sources


def test_one_clarify_turn_limit_in_state():
    from src.ai.langgraph.state import BotState

    state = BotState(
        thread_id="tg:12345:777",
        user_id="777",
        chat_id="12345",
        query="Где смотреть отчет?",
        clarify_turns_used=0,
    )
    assert state.clarify_turns_used == 0
    state.clarify_turns_used += 1
    assert state.clarify_turns_used == 1


def test_settings_load_telegram_and_context_fields(monkeypatch):
    from src.core.config import Settings

    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setenv("TELEGRAM_ALLOWED_ROLES", '["employee","admin"]')
    monkeypatch.setenv("BOT_CONTEXT_MAX_MESSAGES", "14")
    monkeypatch.setenv("BOT_CONTEXT_MAX_TOKENS", "900")
    monkeypatch.setenv("BOT_CLARIFY_MAX_TURNS", "1")

    overridden = Settings()
    assert overridden.telegram_bot_token == "test-token"
    assert overridden.telegram_allowed_roles == {"employee", "admin"}
    assert overridden.bot_context_max_messages == 14
    assert overridden.bot_context_max_tokens == 900
    assert overridden.bot_clarify_max_turns == 1
