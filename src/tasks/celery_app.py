from celery import Celery

from src.core.config import settings

celery_app = Celery("vbrain", broker=settings.redis_url, backend=settings.redis_url)

# Configuration for serializing complex objects like KnowledgeUnit (Pydantic models)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_always_eager=False,  # We use Docker Redis
)
