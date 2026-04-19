import hashlib
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import APIRouter, Depends, Form, HTTPException, Request, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse as StarletteRedirectResponse

from src.api.deps import get_db_session
from src.core.config import settings
from src.models.knowledge_item import KnowledgeItem, KnowledgeStatus

router = APIRouter(prefix="/api/admin", tags=["admin"])

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))

# In-memory session store (sufficient for single-admin MVP)
_admin_sessions: dict[str, dict] = {}


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def _verify_password(password: str, password_hash: str) -> bool:
    return _hash_password(password) == password_hash


class AdminAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        # Only protect /api/admin/* routes (except login and static)
        if path.startswith("/api/admin") and path not in ("/api/admin/login",):
            session_id = request.cookies.get("admin_session")
            if not session_id or session_id not in _admin_sessions:
                return StarletteRedirectResponse(url="/api/admin/login", status_code=302)
            session_data = _admin_sessions[session_id]
            if datetime.utcnow() > session_data["expires"]:
                del _admin_sessions[session_id]
                return StarletteRedirectResponse(url="/api/admin/login", status_code=302)
        response = await call_next(request)
        return response


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html")


@router.post("/login")
async def login_submit(request: Request, password: str = Form(...)):
    if not settings.admin_password:
        raise HTTPException(status_code=500, detail="Admin password not configured")
    if not _verify_password(password, settings.admin_password):
        return templates.TemplateResponse(
            request,
            "login.html",
            {"error": "Неверный пароль"},
            status_code=401,
        )
    session_id = str(uuid.uuid4())
    _admin_sessions[session_id] = {
        "expires": datetime.utcnow() + timedelta(seconds=settings.admin_session_timeout),
    }
    response = RedirectResponse(url="/api/admin/", status_code=302)
    response.set_cookie(
        key="admin_session",
        value=session_id,
        httponly=True,
        max_age=settings.admin_session_timeout,
        samesite="lax",
    )
    return response


@router.post("/logout")
async def logout(request: Request):
    session_id = request.cookies.get("admin_session")
    if session_id and session_id in _admin_sessions:
        del _admin_sessions[session_id]
    response = RedirectResponse(url="/api/admin/login", status_code=302)
    response.delete_cookie("admin_session")
    return response


@router.get("/", response_class=HTMLResponse)
async def admin_index(request: Request):
    return templates.TemplateResponse(request, "sources/list.html")


@router.get("/sources", response_class=HTMLResponse)
async def sources_page(request: Request, db: Session = Depends(get_db_session)):
    from src.models.source import Source

    sources = db.query(Source).order_by(Source.created_at.desc()).all()
    return templates.TemplateResponse(
        request,
        "sources/list.html",
        {"sources": sources},
    )


@router.get("/sources/upload", response_class=HTMLResponse)
async def sources_upload_page(request: Request):
    return templates.TemplateResponse(request, "sources/upload_form.html")
