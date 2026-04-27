import bcrypt
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, Response, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import case, desc, func
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import RedirectResponse as StarletteRedirectResponse

from src.api.deps import get_db_session
from src.api.routes.ingest import _ensure_upload_dirs, _validate_json_content, _validate_ogg_content, _validate_size
from src.core.config import settings
from src.core.logging import get_logger
from src.models.feedback_event import FeedbackEvent
from src.models.ingest_job import IngestJob
from src.models.knowledge_item import KnowledgeItem, KnowledgeStatus
from src.models.source import IngestStatus, Source, SourceType
from src.models.telegram_user import TelegramUser, UserRole
from src.tasks.ingest import ingest_pdf, ingest_telegram

logger = get_logger(__name__)

router = APIRouter(prefix="/api/admin", tags=["admin"])

templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))

# In-memory session store (sufficient for single-admin MVP)
_admin_sessions: dict[str, dict] = {}


def _verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), password_hash.encode())
    except Exception as e:
        logger.error("Password verification failed: %s", e)
        return False


class AdminAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        # Only protect /api/admin/* routes (except login and static)
        if path.startswith("/api/admin") and path not in ("/api/admin/login",):
            session_id = request.cookies.get("admin_session")
            if not session_id or session_id not in _admin_sessions:
                return StarletteRedirectResponse(url="/api/admin/login", status_code=302)
            session_data = _admin_sessions[session_id]
            if datetime.now(UTC) > session_data["expires"]:
                if session_id in _admin_sessions:
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
        "expires": datetime.now(UTC) + timedelta(seconds=settings.admin_session_timeout),
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


@router.get("/knowledge", response_class=HTMLResponse)
async def knowledge_page(
    request: Request,
    db: Session = Depends(get_db_session),
    status: str | None = None,
    topic: str | None = None,
    page: int = 1,
    limit: int = 20,
):
    query = db.query(KnowledgeItem)
    total = query.count()

    if status and status in ("published", "pending", "rejected"):
        query = query.filter(KnowledgeItem.status == status)
    if topic:
        query = query.filter(KnowledgeItem.topic.contains(topic))

    filtered_total = query.count()
    items = query.order_by(KnowledgeItem.created_at.desc()).offset((page - 1) * limit).limit(limit).all()

    topics = db.query(KnowledgeItem.topic).distinct().all()

    status_counts = {
        "total": total,
        "published": db.query(KnowledgeItem).filter(KnowledgeItem.status == KnowledgeStatus.PUBLISHED).count(),
        "pending": db.query(KnowledgeItem).filter(KnowledgeItem.status == KnowledgeStatus.PENDING).count(),
        "rejected": db.query(KnowledgeItem).filter(KnowledgeItem.status == KnowledgeStatus.REJECTED).count(),
    }

    total_pages = max(1, (filtered_total + limit - 1) // limit)

    return templates.TemplateResponse(
        request,
        "knowledge/review.html",
        {
            "items": items,
            "topics": [t[0] for t in topics],
            "current_status": status,
            "current_topic": topic,
            "current_page": page,
            "total_pages": total_pages,
            "filtered_total": filtered_total,
            "status_counts": status_counts,
        },
    )


@router.post("/knowledge/approve", response_class=HTMLResponse)
async def approve_knowledge(
    item_ids: list[int] = Form(...),
    db: Session = Depends(get_db_session),
):
    try:
        items = db.query(KnowledgeItem).filter(KnowledgeItem.id.in_(item_ids)).all()
        count = 0
        for item in items:
            item.status = KnowledgeStatus.PUBLISHED
            item.updated_at = datetime.utcnow()
            count += 1
        db.commit()
        return HTMLResponse(
            content=f'<div class="bg-green-50 text-green-700 px-4 py-3 rounded-lg text-sm">'
                    f'<i class="ti ti-check mr-1"></i> {count} знаний опубликовано</div>',
        )
    except Exception:
        db.rollback()
        return HTMLResponse(
            content='<div class="bg-red-50 text-red-700 px-4 py-3 rounded-lg text-sm">'
                    '<i class="ti ti-alert-circle mr-1"></i> Ошибка при публикации</div>',
            status_code=500,
        )


@router.post("/knowledge/reject", response_class=HTMLResponse)
async def reject_knowledge(
    item_ids: list[int] = Form(...),
    db: Session = Depends(get_db_session),
):
    try:
        items = db.query(KnowledgeItem).filter(KnowledgeItem.id.in_(item_ids)).all()
        count = 0
        for item in items:
            item.status = KnowledgeStatus.REJECTED
            item.updated_at = datetime.utcnow()
            count += 1
        db.commit()
        return HTMLResponse(
            content=f'<div class="bg-yellow-50 text-yellow-700 px-4 py-3 rounded-lg text-sm">'
                    f'<i class="ti ti-x mr-1"></i> {count} знаний отклонено</div>',
        )
    except Exception:
        db.rollback()
        return HTMLResponse(
            content='<div class="bg-red-50 text-red-700 px-4 py-3 rounded-lg text-sm">'
                    '<i class="ti ti-alert-circle mr-1"></i> Ошибка при отклонении</div>',
            status_code=500,
        )


@router.delete("/knowledge/{item_id}", response_class=HTMLResponse)
async def delete_knowledge(item_id: int, db: Session = Depends(get_db_session)):
    item = db.query(KnowledgeItem).filter(KnowledgeItem.id == item_id).first()
    if not item:
        return HTMLResponse(
            content='<div class="bg-red-50 text-red-700 p-3 rounded">Знание не найдено</div>',
            status_code=404,
        )
    db.delete(item)
    db.commit()
    return HTMLResponse(content='<div class="bg-green-50 text-green-700 p-3 rounded">Знание удалено</div>')


@router.put("/knowledge/{item_id}", response_class=HTMLResponse)
async def edit_knowledge(
    request: Request,
    item_id: int,
    fact: str = Form(...),
    db: Session = Depends(get_db_session),
):
    item = db.query(KnowledgeItem).filter(KnowledgeItem.id == item_id).first()
    if not item:
        return HTMLResponse(
            content='<div class="bg-red-50 text-red-700 p-3 rounded">Знание не найдено</div>',
            status_code=404,
        )
    item.fact = fact
    item.updated_at = datetime.utcnow()
    db.commit()
    return templates.TemplateResponse(
        request,
        "knowledge/_row.html",
        {"item": item},
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


# --- User management endpoints (ADM-06) ---


@router.get("/users", response_class=HTMLResponse)
async def users_page(request: Request, db: Session = Depends(get_db_session)):
    users = db.query(TelegramUser).order_by(TelegramUser.created_at.desc()).all()
    return templates.TemplateResponse(
        request,
        "users/manage.html",
        {"users": users},
    )


@router.post("/users", response_class=HTMLResponse)
async def create_user(
    request: Request,
    user_id: int = Form(...),
    role: str = Form(...),
    db: Session = Depends(get_db_session),
):
    # Validate role
    try:
        user_role = UserRole(role)
    except ValueError:
        return templates.TemplateResponse(
            request,
            "users/_add_result.html",
            {"success": False, "message": "Неверная роль. Допустимые: admin, employee"},
        )

    # Check if user already exists
    existing = db.query(TelegramUser).filter(TelegramUser.user_id == user_id).first()
    if existing:
        return templates.TemplateResponse(
            request,
            "users/_add_result.html",
            {"success": False, "message": "Пользователь с таким ID уже существует"},
        )

    user = TelegramUser(user_id=user_id, role=user_role)
    db.add(user)
    db.commit()

    # Also update runtime config so bot auth sees the new user immediately
    settings.telegram_user_roles[user_id] = role

    return templates.TemplateResponse(
        request,
        "users/_add_result.html",
        {"success": True, "message": f"Пользователь {user_id} добавлен"},
    )


@router.delete("/users/{user_id}", response_class=HTMLResponse)
async def delete_user(user_id: int, db: Session = Depends(get_db_session)):
    user = db.query(TelegramUser).filter(TelegramUser.user_id == user_id).first()
    if not user:
        return HTMLResponse(
            content='<div class="bg-red-50 text-red-700 p-3 rounded">Пользователь не найден</div>',
            status_code=404,
        )
    db.delete(user)
    db.commit()

    # Remove from runtime config
    settings.telegram_user_roles.pop(user_id, None)

    return HTMLResponse(content='<div class="bg-green-50 text-green-700 p-3 rounded">Пользователь удалён</div>')


# --- Analytics dashboard (ADM-07) ---


@router.get("/analytics", response_class=HTMLResponse)
async def analytics_page(request: Request, db: Session = Depends(get_db_session)):
    # Knowledge stats by status
    knowledge_total = db.query(func.count(KnowledgeItem.id)).scalar() or 0
    knowledge_published = db.query(func.count(KnowledgeItem.id)).filter(
        KnowledgeItem.status == KnowledgeStatus.PUBLISHED
    ).scalar() or 0
    knowledge_pending = db.query(func.count(KnowledgeItem.id)).filter(
        KnowledgeItem.status == KnowledgeStatus.PENDING
    ).scalar() or 0
    knowledge_rejected = db.query(func.count(KnowledgeItem.id)).filter(
        KnowledgeItem.status == KnowledgeStatus.REJECTED
    ).scalar() or 0

    # Average answer rating from feedback (vote="up" => 1, vote="down" => 0)
    avg_rating_row = db.query(
        func.avg(
            case(
                (FeedbackEvent.vote == "up", 1),
                (FeedbackEvent.vote == "down", 0),
                else_=0,
            )
        )
    ).scalar()
    avg_rating = round(float(avg_rating_row), 2) if avg_rating_row is not None else None

    total_feedback = db.query(func.count(FeedbackEvent.id)).scalar() or 0

    # Active users (unique user_ids with feedback in last 7 days)
    week_ago = datetime.utcnow() - timedelta(days=7)
    active_users = db.query(
        func.count(func.distinct(FeedbackEvent.user_id))
    ).filter(FeedbackEvent.created_at >= week_ago).scalar() or 0

    # Popular questions (top 10 thread_ids by frequency)
    popular_questions = db.query(
        FeedbackEvent.thread_id,
        func.count(FeedbackEvent.id).label("count"),
    ).group_by(FeedbackEvent.thread_id).order_by(desc("count")).limit(10).all()

    # Ingest job stats
    ingest_completed = db.query(func.count(IngestJob.id)).filter(
        IngestJob.status == "SUCCESS"
    ).scalar() or 0
    ingest_failed = db.query(func.count(IngestJob.id)).filter(
        IngestJob.status == "FAILURE"
    ).scalar() or 0
    ingest_total = db.query(func.count(IngestJob.id)).scalar() or 0

    # Source counts by type
    pdf_count = db.query(func.count(Source.id)).filter(
        Source.type == SourceType.PDF
    ).scalar() or 0
    telegram_count = db.query(func.count(Source.id)).filter(
        Source.type == SourceType.TELEGRAM
    ).scalar() or 0

    return templates.TemplateResponse(
        request,
        "analytics/dashboard.html",
        {
            "knowledge_total": knowledge_total,
            "knowledge_published": knowledge_published,
            "knowledge_pending": knowledge_pending,
            "knowledge_rejected": knowledge_rejected,
            "avg_rating": avg_rating,
            "total_feedback": total_feedback,
            "active_users": active_users,
            "popular_questions": popular_questions,
            "ingest_completed": ingest_completed,
            "ingest_failed": ingest_failed,
            "ingest_total": ingest_total,
            "pdf_count": pdf_count,
            "telegram_count": telegram_count,
        },
    )
