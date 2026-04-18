from dataclasses import dataclass


@dataclass
class _FakeUser:
    role: str


def _run_start_flow(user_role: str, retrieve_callable):
    from src.bot.auth import is_authorized_role

    decision = is_authorized_role(_FakeUser(role=user_role).role)
    if not decision.allowed:
        return {"status": "denied", "decision": decision}

    payload = retrieve_callable()
    return {"status": "ok", "payload": payload}


def test_denied_role_never_reaches_retrieval():
    calls = {"count": 0}

    def _retrieve():
        calls["count"] += 1
        return {"answer": "should never happen"}

    result = _run_start_flow("guest", _retrieve)
    assert result["status"] == "denied"
    assert calls["count"] == 0


def test_allowed_role_reaches_retrieval():
    calls = {"count": 0}

    def _retrieve():
        calls["count"] += 1
        return {"answer": "ok"}

    result = _run_start_flow("employee", _retrieve)
    assert result["status"] == "ok"
    assert result["payload"]["answer"] == "ok"
    assert calls["count"] == 1


def test_build_access_denied_answer_is_deterministic():
    from src.bot.auth import build_access_denied_answer

    denied = build_access_denied_answer(reason="role_not_allowed")
    assert denied.answer == "Доступ ограничен: бот доступен только сотрудникам компании."
    assert denied.fallback_used is True
    assert denied.confidence == 1.0
    assert len(denied.sources) == 1
    assert denied.sources[0].source_id == "policy:auth"
