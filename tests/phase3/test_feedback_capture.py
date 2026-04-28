from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker


@pytest.fixture
def db_session():
    from src.models.base import Base

    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, class_=Session, autoflush=False, autocommit=False)
    with SessionLocal() as db:
        yield db


@pytest.mark.asyncio
async def test_callback_handler_acknowledges_and_persists_vote(db_session):
    from src.bot.telegram_app import handle_feedback_callback
    from src.models.feedback_event import FeedbackEvent

    query = SimpleNamespace(
        data="feedback:up",
        answer=AsyncMock(),
        message=SimpleNamespace(message_id=300, chat=SimpleNamespace(id=100)),
        from_user=SimpleNamespace(id=200),
    )
    update = SimpleNamespace(callback_query=query)
    ctx = SimpleNamespace(application=SimpleNamespace(bot_data={"db_session_factory": lambda: db_session}))

    await handle_feedback_callback(update, ctx)
    db_session.commit()

    query.answer.assert_awaited_once()
    row = db_session.scalar(select(FeedbackEvent).where(FeedbackEvent.message_id == 300))
    assert row is not None
    assert row.thread_id == "tg:100:200"
    assert row.vote == "up"


@pytest.mark.asyncio
async def test_callback_handler_rejects_invalid_vote_with_safe_ack(db_session):
    from src.bot.telegram_app import handle_feedback_callback

    query = SimpleNamespace(
        data="feedback:sideways",
        answer=AsyncMock(),
        message=SimpleNamespace(message_id=300, chat=SimpleNamespace(id=100)),
        from_user=SimpleNamespace(id=200),
    )
    update = SimpleNamespace(callback_query=query)
    ctx = SimpleNamespace(application=SimpleNamespace(bot_data={"db_session_factory": lambda: db_session}))

    await handle_feedback_callback(update, ctx)

    query.answer.assert_awaited_once()


@pytest.mark.asyncio
async def test_callback_handler_replay_is_idempotent_and_not_duplicated(db_session):
    from src.bot.telegram_app import handle_feedback_callback
    from src.models.feedback_event import FeedbackEvent

    query = SimpleNamespace(
        data="feedback:up",
        answer=AsyncMock(),
        message=SimpleNamespace(message_id=300, chat=SimpleNamespace(id=100)),
        from_user=SimpleNamespace(id=200),
    )
    update = SimpleNamespace(callback_query=query)
    ctx = SimpleNamespace(application=SimpleNamespace(bot_data={"db_session_factory": lambda: db_session}))

    await handle_feedback_callback(update, ctx)
    await handle_feedback_callback(update, ctx)
    db_session.commit()

    assert query.answer.await_count == 2
    second_call = query.answer.await_args_list[1]
    assert second_call.kwargs.get("text") == "Feedback already recorded."
    count = db_session.scalar(select(func.count()).select_from(FeedbackEvent))
    assert count == 1
