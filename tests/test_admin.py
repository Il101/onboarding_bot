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
