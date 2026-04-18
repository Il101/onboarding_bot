from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest


class _FakeChat:
    def __init__(self, chat_id: int):
        self.id = chat_id


class _FakeUser:
    def __init__(self, user_id: int):
        self.id = user_id


class _FakeMessage:
    def __init__(self):
        self.reply_text = AsyncMock()


def _update(*, user_id: int = 200, chat_id: int = 100):
    return SimpleNamespace(
        effective_user=_FakeUser(user_id),
        effective_chat=_FakeChat(chat_id),
        message=_FakeMessage(),
    )


@pytest.mark.asyncio
async def test_start_unauthorized_returns_deny_and_skips_graph(monkeypatch):
    from src.bot.telegram_app import handle_start

    graph = SimpleNamespace(ainvoke=AsyncMock())
    ctx = SimpleNamespace(application=SimpleNamespace(bot_data={"graph": graph}))
    upd = _update()
    monkeypatch.setattr("src.bot.telegram_app.resolve_role_for_update", lambda _u: "guest")

    await handle_start(upd, ctx)

    graph.ainvoke.assert_not_awaited()
    upd.message.reply_text.assert_awaited()
    sent_text = upd.message.reply_text.await_args.kwargs["text"]
    assert "Доступ ограничен" in sent_text
    assert "Источники" in sent_text


@pytest.mark.asyncio
async def test_authorized_message_invokes_graph_with_thread_id_and_sends_formatted_answer(monkeypatch):
    from src.ai.langgraph.state import BotAnswer, SourceRef
    from src.bot.telegram_app import handle_message

    graph_result = {
        "result": BotAnswer(
            answer="1. Откройте CRM",
            confidence=0.84,
            fallback_used=False,
            sources=[SourceRef(source_id="doc:crm", excerpt="CRM инструкция", timestamp="2026-04-10T00:00:00")],
        )
    }
    graph = SimpleNamespace(ainvoke=AsyncMock(return_value=graph_result))
    ctx = SimpleNamespace(application=SimpleNamespace(bot_data={"graph": graph}))
    upd = _update()
    upd.message.text = "Как оформить доступ?"
    monkeypatch.setattr("src.bot.telegram_app.resolve_role_for_update", lambda _u: "employee")

    await handle_message(upd, ctx)

    graph.ainvoke.assert_awaited_once()
    kwargs = graph.ainvoke.await_args.kwargs
    assert kwargs["config"]["configurable"]["thread_id"] == "tg:100:200"
    sent_text = upd.message.reply_text.await_args.kwargs["text"]
    assert "Источники" in sent_text


@pytest.mark.asyncio
async def test_handler_error_path_returns_safe_russian_message(monkeypatch):
    from src.bot.telegram_app import handle_message

    graph = SimpleNamespace(ainvoke=AsyncMock(side_effect=RuntimeError("traceback internal secret")))
    ctx = SimpleNamespace(application=SimpleNamespace(bot_data={"graph": graph}))
    upd = _update()
    upd.message.text = "Как оформить доступ?"
    monkeypatch.setattr("src.bot.telegram_app.resolve_role_for_update", lambda _u: "employee")

    await handle_message(upd, ctx)

    sent_text = upd.message.reply_text.await_args.kwargs["text"]
    assert "Не удалось обработать запрос" in sent_text
    assert "traceback" not in sent_text.lower()
