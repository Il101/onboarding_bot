from __future__ import annotations

from celery import Celery

from src.ai.extraction.extractor import extract_knowledge_units, group_units_by_topic
from src.ai.sop.generator import generate_sop_for_topic
from src.core.config import settings
from src.core.logging import get_logger
from src.pipeline.indexer.knowledge_writer import index_knowledge_units

logger = get_logger(__name__)
celery_app = Celery("vbrain", broker=settings.redis_url, backend=settings.redis_url)


@celery_app.task(bind=True, autoretry_for=(Exception,), max_retries=3)
def extract_knowledge_task(
    self,
    source_id: str,
    chunks: list[dict],
    extraction_outputs: list[list[dict]] | None = None,
    index_writer=index_knowledge_units,
):
    try:
        self.update_state(state="PROGRESS", meta={"stage": "extracting", "progress": 20})
        result = extract_knowledge_units(chunks, extraction_outputs=extraction_outputs)

        self.update_state(state="PROGRESS", meta={"stage": "validating", "progress": 40})
        all_units = result["all_units"]

        self.update_state(state="PROGRESS", meta={"stage": "gating", "progress": 60})
        publishable = result["publishable"]
        review_needed = result["review_needed"]

        self.update_state(state="PROGRESS", meta={"stage": "grouping", "progress": 80})
        grouped = group_units_by_topic(publishable)

        indexed_count = index_writer(publishable)

        self.update_state(state="PROGRESS", meta={"stage": "completed", "progress": 100})
        return {
            "status": "completed",
            "source_id": source_id,
            "all_units_count": len(all_units),
            "publishable_count": len(publishable),
            "review_needed_count": len(review_needed),
            "indexed_count": indexed_count,
            "grouped_topics": list(grouped.keys()),
            "grouped": grouped,
            "publishable": publishable,
            "review_needed": review_needed,
        }
    except Exception as exc:
        logger.error("Knowledge extraction failed for source %s: %s", source_id, exc)
        self.update_state(state="FAILURE", meta={"error": str(exc)})
        raise


@celery_app.task(bind=True, autoretry_for=(Exception,), max_retries=3)
def generate_sop_task(self, source_id: str, grouped_units: dict[str, list]):
    try:
        self.update_state(state="PROGRESS", meta={"stage": "generating", "progress": 50})
        topic_results = [generate_sop_for_topic(topic, units) for topic, units in grouped_units.items()]
        self.update_state(state="PROGRESS", meta={"stage": "completed", "progress": 100})
        return {
            "status": "completed",
            "source_id": source_id,
            "topics": topic_results,
        }
    except Exception as exc:
        logger.error("SOP generation failed for source %s: %s", source_id, exc)
        self.update_state(state="FAILURE", meta={"error": str(exc)})
        raise
