#!/usr/bin/env python
"""
Add demo data for V-Brain admin panel.
Creates fake users, analytics, and feedback events for demo purposes.
"""

import random
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session

from src.api.deps import SessionLocal
from src.core.logging import get_logger
from src.models.feedback_event import FeedbackEvent
from src.models.telegram_user import TelegramUser, UserRole

logger = get_logger(__name__)


# Sample questions for demo
SAMPLE_QUESTIONS = [
    "How do I request vacation?",
    "Where is the Wi-Fi password?",
    "What's the onboarding schedule?",
    "How do I access the VPN?",
    "What benefits are available?",
    "How do I submit expenses?",
    "Who do I contact for IT support?",
    "What are the office hours?",
    "How do I book a meeting room?",
    "What's the dress code?",
    "How do I set up email?",
    "Where can I find company policies?",
    "How do I request time off?",
    "What's the procedure for sick leave?",
    "How do I access the knowledge base?",
    "What tools do I need installed?",
    "How do I join the team Slack?",
    "What's the GitHub org name?",
    "How do I get a badge?",
    "Where can I get office supplies?",
]


def create_demo_users(db: Session) -> int:
    """Create demo Telegram users."""
    # Sample user IDs and names
    demo_users = [
        (123456789, "admin"),
        (234567890, "employee"),
        (345678901, "employee"),
        (456789012, "employee"),
        (567890123, "employee"),
        (678901234, "employee"),
        (789012345, "employee"),
    ]

    created = 0
    for user_id, role_name in demo_users:
        existing = db.query(TelegramUser).filter(TelegramUser.user_id == user_id).first()
        if not existing:
            user = TelegramUser(
                user_id=user_id,
                role=UserRole(role_name),
                created_at=datetime.now(UTC) - timedelta(days=random.randint(1, 90)),
            )
            db.add(user)
            created += 1

    db.commit()
    return created


def create_demo_feedback(db: Session) -> int:
    """Create demo feedback events for analytics."""
    # Get existing users
    users = db.query(TelegramUser).all()
    if not users:
        logger.warning("No users found. Create users first.")
        return 0

    # Clean up existing demo feedback
    db.query(FeedbackEvent).delete()
    db.commit()

    # Create feedback for the last 30 days
    events_to_create = 150
    created = 0

    for _ in range(events_to_create):
        user = random.choice(users)
        question = random.choice(SAMPLE_QUESTIONS)
        # Use question as thread_id for display purposes
        thread_id = question

        # Weighted random: 80% positive, 20% negative
        vote = "up" if random.random() < 0.8 else "down"

        # Random date within last 30 days
        days_ago = random.randint(0, 29)
        created_at = datetime.now(UTC) - timedelta(days=days_ago, hours=random.randint(0, 23))

        # Generate unique message_id and chat_id for each event
        message_id = random.randint(100000, 999999)
        chat_id = user.user_id  # Simulate 1:1 chat

        event = FeedbackEvent(
            user_id=user.user_id,
            thread_id=thread_id,
            message_id=message_id,
            chat_id=chat_id,
            vote=vote,
            answer_confidence=round(random.uniform(0.7, 0.99), 2),
            created_at=created_at,
        )
        db.add(event)
        created += 1

    db.commit()
    return created


def main() -> int:
    print("Adding demo data for V-Brain Admin Panel\n")

    db = SessionLocal()
    try:
        print("1. Creating demo users...")
        users_created = create_demo_users(db)
        print(f"   ✓ Created {users_created} users")

        print("\n2. Creating demo feedback events...")
        feedback_created = create_demo_feedback(db)
        print(f"   ✓ Created {feedback_created} feedback events")

        # Verify
        total_users = db.query(TelegramUser).count()
        total_feedback = db.query(FeedbackEvent).count()
        positive_feedback = db.query(FeedbackEvent).filter(FeedbackEvent.vote == "up").count()

        # Calculate active users (last 7 days)
        week_ago = datetime.now(UTC) - timedelta(days=7)
        active_users = (
            db.query(FeedbackEvent.user_id).filter(FeedbackEvent.created_at >= week_ago).distinct().count()
        )

        # Calculate avg rating
        from sqlalchemy import case, func

        avg_rating_row = db.query(
            func.avg(
                case(
                    (FeedbackEvent.vote == "up", 1),
                    (FeedbackEvent.vote == "down", 0),
                    else_=0,
                )
            )
        ).scalar()
        avg_rating = round(float(avg_rating_row), 2) if avg_rating_row is not None else 0

        print(f"\n3. Demo statistics:")
        print(f"   Total users: {total_users}")
        print(f"   Total feedback: {total_feedback}")
        print(f"   Positive feedback: {positive_feedback} ({(positive_feedback/total_feedback*100):.1f}%)")
        print(f"   Active users (7 days): {active_users}")
        print(f"   Average rating: {avg_rating * 100:.0f}%")

        print(f"\n✓ Demo data added successfully!")
        print(f"\nNow visit the admin panel at:")
        print(f"   http://localhost:8000/admin")

        return 0

    except Exception as e:
        db.rollback()
        print(f"\n✗ Error: {e}")
        import traceback

        traceback.print_exc()
        return 1
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
