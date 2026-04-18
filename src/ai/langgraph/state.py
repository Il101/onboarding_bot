from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, model_validator


def build_thread_id(*, chat_id: int | str, user_id: int | str) -> str:
    return f"tg:{chat_id}:{user_id}"


class SourceRef(BaseModel):
    source_id: str = Field(min_length=1)
    excerpt: str = Field(min_length=1)
    timestamp: str | None = None
    page: int | None = None

    @model_validator(mode="after")
    def validate_locator(self) -> "SourceRef":
        if self.timestamp is None and self.page is None:
            raise ValueError("source requires timestamp or page for manual verification")
        return self


class BotAnswer(BaseModel):
    answer: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    fallback_used: bool
    needs_clarification: bool = False
    clarification_question: str | None = None
    sources: list[SourceRef] = Field(min_length=1)


class BotState(BaseModel):
    thread_id: str = Field(min_length=1)
    user_id: str = Field(min_length=1)
    chat_id: str = Field(min_length=1)
    role: str = "employee"
    query: str = Field(min_length=1)
    summary: str = ""
    clarify_turns_used: int = Field(default=0, ge=0, le=1)
    rag_payload: dict[str, Any] = Field(default_factory=dict)
    result: BotAnswer | None = None
