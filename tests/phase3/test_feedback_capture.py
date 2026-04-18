from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
import pytest


def test_callback_vote_normalization_and_rejection():
    from src.bot.feedback import normalize_vote_from_callback

    assert normalize_vote_from_callback("feedback:up") == "up"
    assert normalize_vote_from_callback("feedback:down") == "down"
    with pytest.raises(ValueError):
        normalize_vote_from_callback("feedback:sideways")
    with pytest.raises(ValueError):
        normalize_vote_from_callback("invalid")


def test_save_feedback_persists_required_fields():
    from src.bot.feedback import save_feedback_event
    from src.models.base import Base
    from src.models.feedback_event import FeedbackEvent

    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, class_=Session, autoflush=False, autocommit=False)

    with SessionLocal() as db:
        event = save_feedback_event(
            db,
            callback_data="feedback:up",
            thread_id="tg:100:200",
            message_id=300,
            user_id=200,
            chat_id=100,
            answer_confidence=0.84,
        )
        db.commit()
        db.refresh(event)
        assert event.thread_id == "tg:100:200"
        assert event.message_id == 300
        assert event.vote == "up"
        assert event.answer_confidence == 0.84
        assert event.created_at is not None

        row = db.scalar(select(FeedbackEvent).where(FeedbackEvent.id == event.id))
        assert row is not None


def test_feedback_event_does_not_store_raw_answer_text():
    from src.models.feedback_event import FeedbackEvent

    columns = FeedbackEvent.__table__.columns.keys()
    assert "answer_text" not in columns
    assert "raw_answer" not in columns
    assert "thread_id" in columns
    assert "message_id" in columns
    assert "user_id" in columns
    assert "chat_id" in columns


def test_save_feedback_rejects_malformed_callback_data():
    from src.bot.feedback import save_feedback_event
    from src.models.base import Base

    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine, class_=Session, autoflush=False, autocommit=False)

    with SessionLocal() as db:
        with pytest.raises(ValueError):
            save_feedback_event(
                db,
                callback_data="feedback:unknown",
                thread_id="tg:100:200",
                message_id=300,
                user_id=200,
                chat_id=100,
                answer_confidence=0.84,
            )
