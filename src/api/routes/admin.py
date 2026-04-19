import hashlib
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, Response, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse as StarletteRedirectResponse

from src.api.deps import get_db_session
from src.api.routes.ingest import _ensure_upload_dirs, _validate_json_content, _validate_ogg_content, _validate_size
from src.core.config import settings
from src.models.ingest_job import IngestJob
from src.models.knowledge_item import KnowledgeItem, KnowledgeStatus
from src.models.source import IngestStatus, Source, SourceType
from src.tasks.ingest import ingest_pdf, ingest_telegram

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


@router.post("/sources/pdf", response_class=HTMLResponse)
async def admin_upload_pdf(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db_session),
):
    filename = (file.filename or "").lower()
    if not filename.endswith(".pdf"):
        return templates.TemplateResponse(
            request,
            "sources/_upload_status.html",
            {"success": False, "message": "Неверный тип файла. Ожидается .pdf"},
        )

    try:
        content = await file.read()
        _validate_size(content)
        if not content.startswith(b"%PDF-"):
            return templates.TemplateResponse(
                request,
                "sources/_upload_status.html",
                {"success": False, "message": "Неверное содержимое PDF файла"},
            )

        base = _ensure_upload_dirs()
        source_id = str(uuid.uuid4())
        safe_name = f"{source_id}.pdf"
        file_path = base / safe_name
        file_path.write_bytes(content)

        source = Source(
            id=source_id,
            type=SourceType.PDF,
            filename=file.filename or "unknown.pdf",
            file_path=str(file_path),
            status=IngestStatus.PENDING,
        )
        db.add(source)
        db.commit()

        task = ingest_pdf.delay(source_id, str(file_path))
        job = IngestJob(
            id=str(uuid.uuid4()),
            source_id=source_id,
            celery_task_id=task.id,
            status="PENDING",
            progress=0,
        )
        db.add(job)
        db.commit()

        return templates.TemplateResponse(
            request,
            "sources/_upload_status.html",
            {"success": True, "message": f"PDF загружен. Job ID: {task.id}", "job_id": task.id},
        )
    except HTTPException as exc:
        return templates.TemplateResponse(
            request,
            "sources/_upload_status.html",
            {"success": False, "message": exc.detail},
        )
    except Exception as e:
        return templates.TemplateResponse(
            request,
            "sources/_upload_status.html",
            {"success": False, "message": f"Ошибка загрузки: {str(e)}"},
        )


@router.post("/sources/telegram", response_class=HTMLResponse)
async def admin_upload_telegram(
    request: Request,
    json_file: UploadFile = File(...),
    voice_files: list[UploadFile] = File(default=[]),
    db: Session = Depends(get_db_session),
):
    if not (json_file.filename or "").lower().endswith(".json"):
        return templates.TemplateResponse(
            request,
            "sources/_upload_status.html",
            {"success": False, "message": "Неверный тип файла. Ожидается .json"},
        )

    try:
        base = _ensure_upload_dirs()
        source_id = str(uuid.uuid4())
        json_name = f"{source_id}.json"
        json_path = base / json_name
        json_content = await json_file.read()
        _validate_size(json_content)
        _validate_json_content(json_content)
        json_path.write_bytes(json_content)

        voice_dir = base / f"{source_id}_voices"
        voice_dir.mkdir(parents=True, exist_ok=True)
        for vf in voice_files:
            if not (vf.filename or "").lower().endswith(".ogg"):
                return templates.TemplateResponse(
                    request,
                    "sources/_upload_status.html",
                    {"success": False, "message": "Неверный тип голосового файла. Ожидается .ogg"},
                )
            content = await vf.read()
            _validate_size(content)
            _validate_ogg_content(content)
            safe_name = f"{uuid.uuid4()}.ogg"
            (voice_dir / safe_name).write_bytes(content)

        source = Source(
            id=source_id,
            type=SourceType.TELEGRAM,
            filename=json_file.filename or "result.json",
            file_path=str(json_path),
            status=IngestStatus.PENDING,
        )
        db.add(source)
        db.commit()

        task = ingest_telegram.delay(source_id, str(json_path), str(voice_dir))
        job = IngestJob(
            id=str(uuid.uuid4()),
            source_id=source_id,
            celery_task_id=task.id,
            status="PENDING",
            progress=0,
        )
        db.add(job)
        db.commit()

        return templates.TemplateResponse(
            request,
            "sources/_upload_status.html",
            {"success": True, "message": f"Telegram логи загружены. Job ID: {task.id}", "job_id": task.id},
        )
    except HTTPException as exc:
        return templates.TemplateResponse(
            request,
            "sources/_upload_status.html",
            {"success": False, "message": exc.detail},
        )
    except Exception as e:
        return templates.TemplateResponse(
            request,
            "sources/_upload_status.html",
            {"success": False, "message": f"Ошибка загрузки: {str(e)}"},
        )


@router.delete("/sources/{source_id}", response_class=HTMLResponse)
async def delete_source(source_id: str, db: Session = Depends(get_db_session)):
    source = db.query(Source).filter(Source.id == source_id).first()
    if not source:
        return HTMLResponse(
            content='<div class="bg-red-50 text-red-700 p-3 rounded">Источник не найден</div>',
            status_code=404,
        )
    db.delete(source)
    db.commit()
    return HTMLResponse(content='<div class="bg-green-50 text-green-700 p-3 rounded">Источник удалён</div>')
