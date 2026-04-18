from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class SourceRef(BaseModel):
    source_id: str = Field(min_length=1)
    excerpt: str = Field(min_length=1)
    timestamp: str | None = None
    page: int | None = None

    @model_validator(mode="after")
    def validate_locator(self) -> "SourceRef":
        if self.timestamp is None and self.page is None:
            raise ValueError("source reference requires at least one locator: timestamp or page")
        return self


class KnowledgeUnit(BaseModel):
    fact: str = Field(min_length=1)
    topic: str = Field(min_length=1)
    source_refs: list[SourceRef] = Field(min_length=1)
    confidence: float = Field(ge=0.0, le=1.0)


class KnowledgeBatch(BaseModel):
    units: list[KnowledgeUnit] = Field(default_factory=list)
