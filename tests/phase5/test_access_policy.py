from types import SimpleNamespace

from src.bot import auth as auth_module


def test_authorize_user_not_whitelisted_denied(monkeypatch):
    monkeypatch.setattr(
        auth_module,
        "settings",
        SimpleNamespace(
            telegram_user_roles={},
            telegram_allowed_roles={"employee", "mentor", "admin"},
        ),
    )

    authorize = getattr(auth_module, "authorize_telegram_user", None)
    assert authorize is not None, "authorize_telegram_user must be implemented for BOT-05"
    decision = authorize(user_id=999_001)

    assert decision.allowed is False
    assert decision.reason == "not_whitelisted"


def test_authorize_user_disallowed_role_denied(monkeypatch):
    monkeypatch.setattr(
        auth_module,
        "settings",
        SimpleNamespace(
            telegram_user_roles={999_002: "guest"},
            telegram_allowed_roles={"employee", "mentor", "admin"},
        ),
    )

    authorize = getattr(auth_module, "authorize_telegram_user", None)
    assert authorize is not None, "authorize_telegram_user must be implemented for BOT-05"
    decision = authorize(user_id=999_002)

    assert decision.allowed is False
    assert decision.reason == "role_not_allowed"


def test_authorize_user_allowed_role_allowed(monkeypatch):
    monkeypatch.setattr(
        auth_module,
        "settings",
        SimpleNamespace(
            telegram_user_roles={999_003: "employee"},
            telegram_allowed_roles={"employee", "mentor", "admin"},
        ),
    )

    authorize = getattr(auth_module, "authorize_telegram_user", None)
    assert authorize is not None, "authorize_telegram_user must be implemented for BOT-05"
    decision = authorize(user_id=999_003)

    assert decision.allowed is True
    assert decision.reason == "allowed"
