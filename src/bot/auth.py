from __future__ import annotations

from pydantic import BaseModel, Field

from src.ai.langgraph.state import BotAnswer, SourceRef
from src.core.config import settings


class AuthDecision(BaseModel):
    allowed: bool
    reason: str = Field(min_length=1)
    role: str = Field(default="")


def is_authorized_role(role: str | None) -> AuthDecision:
    normalized = (role or "").strip().lower()
    if not normalized:
        return AuthDecision(allowed=False, reason="missing_role", role="")
    if normalized not in settings.telegram_allowed_roles:
        return AuthDecision(allowed=False, reason="role_not_allowed", role=normalized)
    return AuthDecision(allowed=True, reason="allowed", role=normalized)


def authorize_telegram_user(user_id: int | str) -> AuthDecision:
    try:
        normalized_user_id = int(user_id)
    except (TypeError, ValueError):
        return AuthDecision(allowed=False, reason="not_whitelisted", role="")

    role = settings.telegram_user_roles.get(normalized_user_id)
    if role is None:
        return AuthDecision(allowed=False, reason="not_whitelisted", role="")
    return is_authorized_role(role)


def build_access_denied_answer(reason: str) -> BotAnswer:
    return BotAnswer(
        answer="Доступ ограничен: бот доступен только сотрудникам компании.",
        confidence=1.0,
        fallback_used=True,
        sources=[
            SourceRef(
                source_id="policy:auth",
                excerpt=f"Access denied by auth policy: {reason}",
                timestamp="1970-01-01T00:00:00",
            )
        ],
    )
