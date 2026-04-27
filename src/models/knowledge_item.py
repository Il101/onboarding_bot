import enum
from datetime import UTC, datetime

from sqlalchemy import DateTime, Enum, Float, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class KnowledgeStatus(str, enum.Enum):
    PUBLISHED = "published"
    PENDING = "pending"
    REJECTED = "rejected"


class KnowledgeItem(Base):
    __tablename__ = "knowledge_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    fact: Mapped[str] = mapped_column(Text)
    topic: Mapped[str] = mapped_column(String(256))
    confidence: Mapped[float] = mapped_column(Float)
    source_refs: Mapped[str] = mapped_column(Text, default="[]")  # JSON string of SourceRef[]
    status: Mapped[KnowledgeStatus] = mapped_column(Enum(KnowledgeStatus), default=KnowledgeStatus.PENDING)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC)
    )
