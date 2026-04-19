from pathlib import Path
from uuid import uuid4

from celery.result import AsyncResult
from fastapi import APIRouter, File, HTTPException, UploadFile

from src.core.config import settings
from src.models.source import SourceType
from src.tasks.ingest import ingest_pdf, ingest_telegram

router = APIRouter(prefix="/api/ingest", tags=["ingestion"])


def _ensure_upload_dirs() -> Path:
    base = Path(settings.upload_dir)
    base.mkdir(parents=True, exist_ok=True)
    return base


def _validate_size(content: bytes):
    max_bytes = settings.max_file_size_mb * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(status_code=413, detail="File too large")


def _validate_json_content(content: bytes):
    try:
        import json

        payload = json.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HTTPException(status_code=400, detail="Invalid JSON content") from exc
    if not isinstance(payload, dict) or "messages" not in payload:
        raise HTTPException(status_code=400, detail="Invalid JSON content")


def _validate_ogg_content(content: bytes):
    if not (content.startswith(b"OggS") or content.startswith(b"ID3")):
        raise HTTPException(status_code=400, detail="Invalid voice file content")


@router.post("/telegram")
async def upload_telegram(
    json_file: UploadFile = File(...),
    voice_files: list[UploadFile] = File(default=[]),
):
    if not (json_file.filename or "").lower().endswith(".json"):
        raise HTTPException(status_code=400, detail="Invalid JSON file type")

    base = _ensure_upload_dirs()
    source_id = str(uuid4())
    json_name = f"{uuid4()}.json"
    json_path = base / json_name
    json_content = await json_file.read()
    _validate_size(json_content)
    _validate_json_content(json_content)
    json_path.write_bytes(json_content)

    voice_dir = base / f"{source_id}_voices"
    voice_dir.mkdir(parents=True, exist_ok=True)
    for file in voice_files:
        if not (file.filename or "").lower().endswith(".ogg"):
            raise HTTPException(status_code=400, detail="Invalid voice file type")
        content = await file.read()
        _validate_size(content)
        _validate_ogg_content(content)
        safe_name = f"{uuid4()}.ogg"
        (voice_dir / safe_name).write_bytes(content)

    task = ingest_telegram.delay(source_id, str(json_path), str(voice_dir))
    return {"job_id": task.id, "status": "started", "source_type": SourceType.TELEGRAM.value}


@router.post("/pdf")
async def upload_pdf(file: UploadFile = File(...)):
    filename = (file.filename or "").lower()
    if not filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Invalid PDF file type")

    base = _ensure_upload_dirs()
    source_id = str(uuid4())
    safe_name = f"{uuid4()}.pdf"
    file_path = base / safe_name

    content = await file.read()
    _validate_size(content)
    if not content.startswith(b"%PDF-"):
        raise HTTPException(status_code=400, detail="Invalid PDF content")
    file_path.write_bytes(content)

    task = ingest_pdf.delay(source_id, str(file_path))
    return {"job_id": task.id, "status": "started", "source_type": SourceType.PDF.value}


@router.get("/status/{job_id}")
async def get_status(job_id: str):
    result = AsyncResult(job_id)
    if result.state == "PROGRESS":
        return {"status": "processing", **(result.info or {})}
    if result.state == "SUCCESS":
        return {"status": "completed", **(result.result or {})}
    if result.state == "FAILURE":
        return {"status": "failed", "error": "Task failed"}
    if result.state == "PENDING":
        return {"status": "pending"}
    return {"status": result.state.lower()}
