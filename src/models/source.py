import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class SourceType(str, enum.Enum):
    TELEGRAM = "telegram"
    PDF = "pdf"


class IngestStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    type: Mapped[SourceType] = mapped_column(Enum(SourceType))
    filename: Mapped[str] = mapped_column(String)
    file_path: Mapped[str] = mapped_column(String)
    status: Mapped[IngestStatus] = mapped_column(Enum(IngestStatus), default=IngestStatus.PENDING)
    messages_count: Mapped[int | None] = mapped_column(default=None)
    chunks_indexed: Mapped[int | None] = mapped_column(default=None)
    error_message: Mapped[str | None] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
