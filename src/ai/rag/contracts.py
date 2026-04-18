from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class AttributionItem(BaseModel):
    source_id: str = Field(min_length=1)
    excerpt: str = Field(min_length=1)
    score: float = Field(ge=0.0, le=1.0)
    timestamp: str | None = None
    page: int | None = None

    @model_validator(mode="after")
    def validate_locator(self) -> "AttributionItem":
        if self.timestamp is None and self.page is None:
            raise ValueError("attribution requires timestamp or page for manual verification")
        return self


class RagAnswer(BaseModel):
    answer: str = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)
    sources: list[AttributionItem] = Field(default_factory=list)
    fallback_used: bool = False
