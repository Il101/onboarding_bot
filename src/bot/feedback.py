from __future__ import annotations

from sqlalchemy.orm import Session

from src.models.feedback_event import FeedbackEvent


def normalize_vote_from_callback(callback_data: str) -> str:
    if not callback_data.startswith("feedback:"):
        raise ValueError("invalid_callback_prefix")
    vote = callback_data.split(":", 1)[1].strip().lower()
    if vote not in {"up", "down"}:
        raise ValueError("invalid_vote")
    return vote


def save_feedback_event(
    db: Session,
    *,
    callback_data: str,
    thread_id: str,
    message_id: int,
    user_id: int,
    chat_id: int,
    answer_confidence: float,
) -> FeedbackEvent:
    vote = normalize_vote_from_callback(callback_data)
    event = FeedbackEvent(
        thread_id=thread_id,
        message_id=message_id,
        user_id=user_id,
        chat_id=chat_id,
        vote=vote,
        answer_confidence=answer_confidence,
    )
    db.add(event)
    db.flush()
    return event
