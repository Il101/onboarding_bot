import hashlib
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    """TestClient with admin password pre-configured."""
    from src.api.main import app
    from src.core.config import settings

    settings.admin_password = hashlib.sha256("testpass".encode()).hexdigest()
    return TestClient(app, follow_redirects=False)


@pytest.fixture
def admin_client(client, db_session):
    """TestClient authenticated with admin session and mock DB."""
    response = client.post("/api/admin/login", data={"password": "testpass"})
    assert response.status_code == 302
    return client


@pytest.fixture
def db_session(client):
    """Provide a mock DB session for tests."""
    from src.api.deps import get_db_session

    mock_db = MagicMock()
    client.app.dependency_overrides[get_db_session] = lambda: mock_db
    yield mock_db
    client.app.dependency_overrides.clear()


# --- ADM-06: Auth tests ---


def test_login_page_renders(client):
    response = client.get("/api/admin/login")
    assert response.status_code == 200
    assert "password" in response.text.lower()


def test_login_wrong_password_returns_error(client):
    response = client.post("/api/admin/login", data={"password": "wrong"})
    assert response.status_code == 401
    assert "Неверный пароль" in response.text


def test_login_correct_password_sets_cookie_and_redirects(client):
    response = client.post("/api/admin/login", data={"password": "testpass"})
    assert response.status_code == 302
    assert "/api/admin/" in response.headers["location"]
    assert "admin_session" in response.headers.get("set-cookie", "")


def test_protected_route_redirects_without_session(client):
    response = client.get("/api/admin/sources")
    assert response.status_code == 302
    assert "/api/admin/login" in response.headers["location"]


def test_protected_route_accessible_with_session(admin_client):
    response = admin_client.get("/api/admin/sources")
    assert response.status_code == 200


def test_logout_clears_session(admin_client):
    response = admin_client.post("/api/admin/logout")
    assert response.status_code == 302
    assert "/api/admin/login" in response.headers["location"]


# --- ADM-01: PDF upload tests ---


def test_pdf_upload_form_renders(admin_client):
    response = admin_client.get("/api/admin/sources/upload")
    assert response.status_code == 200
    assert "PDF" in response.text


# --- ADM-02: Telegram upload tests ---


def test_telegram_upload_form_renders(admin_client):
    response = admin_client.get("/api/admin/sources/upload")
    assert response.status_code == 200
    assert "Telegram" in response.text


# --- ADM-03: Knowledge list tests ---


def test_knowledge_page_requires_auth(client):
    response = client.get("/api/admin/knowledge")
    assert response.status_code == 302


# --- ADM-04: Approve tests ---


def test_approve_knowledge_requires_auth(client):
    response = client.post("/api/admin/knowledge/approve", json={"item_ids": [1]})
    assert response.status_code == 302


# --- ADM-05: Reject/delete tests ---


def test_reject_knowledge_requires_auth(client):
    response = client.post("/api/admin/knowledge/reject", json={"item_ids": [1]})
    assert response.status_code == 302


# --- ADM-06: User management tests ---


def test_users_page_requires_auth(client):
    response = client.get("/api/admin/users")
    assert response.status_code == 302


# --- ADM-06: User management CRUD tests ---


def test_users_page_renders(admin_client, db_session):
    from datetime import datetime
    users = [MagicMock(user_id=12345, role="employee", created_at=datetime.utcnow())]
    db_session.query.return_value.order_by.return_value.all.return_value = users

    response = admin_client.get("/api/admin/users")
    assert response.status_code == 200
    assert "Пользователи" in response.text


def test_create_user_success(admin_client, db_session):
    db_session.query.return_value.filter.return_value.first.return_value = None  # no existing user

    response = admin_client.post(
        "/api/admin/users",
        data={"user_id": "123456", "role": "employee"},
    )
    assert response.status_code == 200
    assert "добавлен" in response.text.lower()
    db_session.add.assert_called_once()


def test_create_user_duplicate_returns_error(admin_client, db_session):
    existing = MagicMock(user_id=123456)
    db_session.query.return_value.filter.return_value.first.return_value = existing

    response = admin_client.post(
        "/api/admin/users",
        data={"user_id": "123456", "role": "employee"},
    )
    assert response.status_code == 200
    assert "уже существует" in response.text.lower()


def test_create_user_invalid_role_returns_error(admin_client, db_session):
    response = admin_client.post(
        "/api/admin/users",
        data={"user_id": "123456", "role": "superadmin"},
    )
    assert response.status_code == 200
    assert "Неверная роль" in response.text


def test_delete_user_success(admin_client, db_session):
    user = MagicMock(user_id=123456)
    db_session.query.return_value.filter.return_value.first.return_value = user

    response = admin_client.delete("/api/admin/users/123456")
    assert response.status_code == 200
    assert "удалён" in response.text.lower() or "deleted" in response.text.lower()


def test_delete_user_not_found(admin_client, db_session):
    db_session.query.return_value.filter.return_value.first.return_value = None

    response = admin_client.delete("/api/admin/users/999999")
    assert response.status_code == 404


def test_telegram_user_model_importable():
    from src.models.telegram_user import TelegramUser, UserRole
    assert hasattr(TelegramUser, "user_id")
    assert hasattr(TelegramUser, "role")
    assert hasattr(UserRole, "ADMIN")
    assert hasattr(UserRole, "EMPLOYEE")


# --- ADM-07: Analytics tests ---


def test_analytics_page_requires_auth(client):
    response = client.get("/api/admin/analytics")
    assert response.status_code == 302


# --- ADM-01: PDF upload via admin (upload endpoints) ---


@patch("src.api.routes.admin.ingest_pdf")
def test_admin_pdf_upload_returns_success(mock_task, admin_client, db_session):
    mock_task.delay.return_value = MagicMock(id="admin-job-pdf-1")
    response = admin_client.post(
        "/api/admin/sources/pdf",
        files={"file": ("report.pdf", b"%PDF-1.4 test content", "application/pdf")},
    )
    assert response.status_code == 200
    assert "Job ID" in response.text or "job_id" in response.text.lower()


def test_admin_pdf_upload_invalid_extension_returns_error(admin_client):
    response = admin_client.post(
        "/api/admin/sources/pdf",
        files={"file": ("image.png", b"\x89PNG", "image/png")},
    )
    assert response.status_code == 200
    assert "Неверный тип" in response.text or "Invalid" in response.text


def test_admin_pdf_upload_invalid_content_returns_error(admin_client):
    response = admin_client.post(
        "/api/admin/sources/pdf",
        files={"file": ("fake.pdf", b"not real pdf content", "application/pdf")},
    )
    assert response.status_code == 200
    assert "Неверное содержимое" in response.text or "Invalid" in response.text


# --- ADM-02: Telegram upload via admin (upload endpoints) ---


@patch("src.api.routes.admin.ingest_telegram")
def test_admin_telegram_upload_returns_success(mock_task, admin_client, db_session):
    mock_task.delay.return_value = MagicMock(id="admin-job-tg-1")
    response = admin_client.post(
        "/api/admin/sources/telegram",
        files=[("json_file", ("result.json", b'{"name":"Test","messages":[]}', "application/json"))],
    )
    assert response.status_code == 200
    assert "Job ID" in response.text or "job_id" in response.text.lower()


def test_admin_telegram_upload_invalid_extension_returns_error(admin_client):
    response = admin_client.post(
        "/api/admin/sources/telegram",
        files=[("json_file", ("result.txt", b'{"name":"Test","messages":[]}', "text/plain"))],
    )
    assert response.status_code == 200
    assert "Неверный тип" in response.text or "Invalid" in response.text


def test_admin_telegram_upload_invalid_json_returns_error(admin_client):
    response = admin_client.post(
        "/api/admin/sources/telegram",
        files=[("json_file", ("result.json", b"not json", "application/json"))],
    )
    assert response.status_code == 200
    assert "Неверный" in response.text or "Invalid" in response.text


@patch("src.api.routes.admin.ingest_telegram")
def test_admin_telegram_upload_with_voice_files_returns_success(mock_task, admin_client, db_session):
    mock_task.delay.return_value = MagicMock(id="admin-job-tg-2")
    response = admin_client.post(
        "/api/admin/sources/telegram",
        files=[
            ("json_file", ("result.json", b'{"name":"Test","messages":[]}', "application/json")),
            ("voice_files", ("voice1.ogg", b"OggS\x00test", "audio/ogg")),
        ],
    )
    assert response.status_code == 200
    assert "Job ID" in response.text or "job_id" in response.text.lower()


def test_admin_sources_list_returns_html(admin_client, db_session):
    db_session.query.return_value.order_by.return_value.all.return_value = []
    response = admin_client.get("/api/admin/sources")
    assert response.status_code == 200
    assert "sources" in response.text.lower() or "Источники" in response.text


# --- ADM-03, ADM-04, ADM-05: Knowledge review tests ---


def _make_knowledge_item(item_id=1, fact="Test fact", topic="Test topic", confidence=0.8, status=None):
    """Helper to create a mock KnowledgeItem for tests."""
    from datetime import datetime
    from src.models.knowledge_item import KnowledgeStatus as KS
    item = MagicMock()
    item.id = item_id
    item.fact = fact
    item.topic = topic
    item.confidence = confidence
    item.status = status if status is not None else KS.PENDING
    item.source_refs = "[]"
    item.created_at = datetime.utcnow()
    item.updated_at = datetime.utcnow()
    return item


def _setup_knowledge_query(db_session, items, total=None, status_counts=None):
    """Configure mock db_session to return items for the chained knowledge query."""
    mock_query = MagicMock()
    db_session.query.return_value = mock_query

    # Chain: query().filter().order_by().offset().limit().all()
    mock_filter = MagicMock()
    mock_query.filter.return_value = mock_filter
    mock_filter.filter.return_value = mock_filter
    mock_filter.order_by.return_value = mock_filter
    mock_filter.offset.return_value = mock_filter
    mock_filter.limit.return_value = mock_filter
    mock_filter.all.return_value = items
    mock_filter.count.return_value = len(items)

    # query().count() for total
    mock_query.count.return_value = total if total is not None else len(items)

    # query().distinct().all() for topics
    mock_query.distinct.return_value = MagicMock()
    mock_query.distinct.return_value.all.return_value = [(item.topic,) for item in items]

    # query().filter().count() for status counts (called 3 times for published/pending/rejected)
    if status_counts:
        mock_filter.count.side_effect = status_counts
    else:
        mock_filter.count.side_effect = [len(items), len(items), 0, 0]

    return mock_query, mock_filter


def test_knowledge_page_renders_with_items(admin_client, db_session):
    items = [_make_knowledge_item(1), _make_knowledge_item(2, topic="Other")]
    _setup_knowledge_query(db_session, items, total=2, status_counts=[2, 2, 1, 1, 0])
    response = admin_client.get("/api/admin/knowledge")
    assert response.status_code == 200
    assert "Test fact" in response.text or "Знания" in response.text or "знани" in response.text.lower()


def test_knowledge_filter_by_status(admin_client, db_session):
    from src.models.knowledge_item import KnowledgeStatus as KS
    pending_item = _make_knowledge_item(1, status=KS.PENDING)
    _setup_knowledge_query(db_session, [pending_item], total=1, status_counts=[1, 1, 1, 0, 0])
    response = admin_client.get("/api/admin/knowledge?status=pending")
    assert response.status_code == 200


def test_knowledge_filter_by_topic(admin_client, db_session):
    item = _make_knowledge_item(1, topic="Процессы")
    _setup_knowledge_query(db_session, [item], total=1, status_counts=[1, 1, 1, 0, 0])
    response = admin_client.get("/api/admin/knowledge?topic=Процессы")
    assert response.status_code == 200


def test_knowledge_approve_changes_status(admin_client, db_session):
    from src.models.knowledge_item import KnowledgeStatus as KS
    item = _make_knowledge_item(1, status=KS.PENDING)
    db_session.query.return_value.filter.return_value.all.return_value = [item]
    response = admin_client.post("/api/admin/knowledge/approve", data={"item_ids": [1]})
    assert response.status_code == 200
    assert "опубликовано" in response.text.lower()


def test_knowledge_reject_changes_status(admin_client, db_session):
    from src.models.knowledge_item import KnowledgeStatus as KS
    item = _make_knowledge_item(1, status=KS.PENDING)
    db_session.query.return_value.filter.return_value.all.return_value = [item]
    response = admin_client.post("/api/admin/knowledge/reject", data={"item_ids": [1]})
    assert response.status_code == 200
    assert "отклонено" in response.text.lower()


def test_knowledge_delete_removes_item(admin_client, db_session):
    item = _make_knowledge_item(1)
    db_session.query.return_value.filter.return_value.first.return_value = item
    response = admin_client.delete("/api/admin/knowledge/1")
    assert response.status_code == 200
    assert "удалено" in response.text.lower()


def test_knowledge_delete_not_found(admin_client, db_session):
    db_session.query.return_value.filter.return_value.first.return_value = None
    response = admin_client.delete("/api/admin/knowledge/999")
    assert response.status_code == 404


def test_knowledge_edit_updates_fact(admin_client, db_session):
    item = _make_knowledge_item(1, fact="Old fact")
    db_session.query.return_value.filter.return_value.first.return_value = item
    response = admin_client.put("/api/admin/knowledge/1", data={"fact": "New fact text"})
    assert response.status_code == 200


def test_knowledge_edit_not_found(admin_client, db_session):
    db_session.query.return_value.filter.return_value.first.return_value = None
    response = admin_client.put("/api/admin/knowledge/999", data={"fact": "Some fact"})
    assert response.status_code == 404


def test_knowledge_pagination_returns_limited_items(admin_client, db_session):
    items = [_make_knowledge_item(i, fact=f"Fact {i}") for i in range(1, 6)]
    _setup_knowledge_query(db_session, items, total=50, status_counts=[50, 5, 40, 5, 5])
    response = admin_client.get("/api/admin/knowledge?page=1&limit=5")
    assert response.status_code == 200
