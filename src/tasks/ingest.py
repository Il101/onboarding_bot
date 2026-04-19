from celery import Celery
from qdrant_client import QdrantClient

from src.core.config import settings
from src.core.logging import get_logger
from src.pipeline.anonymizer.engine import anonymize_text, create_analyzer, create_anonymizer
from src.pipeline.chunker.telegram_chunker import chunk_telegram_messages
from src.pipeline.chunker.text_chunker import chunk_text
from src.pipeline.filters.noise import filter_messages
from src.pipeline.indexer.embedder import Embedder
from src.pipeline.indexer.qdrant_store import QdrantStore
from src.pipeline.parsers.pdf import extract_pdf_text
from src.pipeline.parsers.telegram import parse_telegram_export
from src.pipeline.parsers.voice import transcribe_voice_messages
from src.tasks.knowledge import extract_knowledge_task

logger = get_logger(__name__)

celery_app = Celery("vbrain", broker=settings.redis_url, backend=settings.redis_url)


def _validate_source_id(source_id: str) -> str:
    if not isinstance(source_id, str) or not source_id.strip():
        raise ValueError("Invalid source_id for dispatch payload")
    return source_id.strip()


def _validate_chunks_for_dispatch(chunks: list[dict]) -> None:
    for idx, chunk in enumerate(chunks):
        if not isinstance(chunk, dict):
            raise ValueError(f"Invalid chunk payload at index {idx}: expected dict")
        if not isinstance(chunk.get("text"), str):
            raise ValueError(f"Invalid chunk payload at index {idx}: missing text")
        if not isinstance(chunk.get("metadata"), dict):
            raise ValueError(f"Invalid chunk payload at index {idx}: missing metadata")


@celery_app.task(bind=True, autoretry_for=(Exception,), max_retries=3)
def ingest_telegram(self, source_id: str, json_path: str, voice_dir: str):
    try:
        source_id = _validate_source_id(source_id)
        self.update_state(state="PROGRESS", meta={"stage": "parsing", "progress": 10})
        messages = parse_telegram_export(json_path)

        self.update_state(state="PROGRESS", meta={"stage": "transcribing", "progress": 20})
        messages = transcribe_voice_messages(messages, voice_dir)

        self.update_state(state="PROGRESS", meta={"stage": "anonymizing", "progress": 35})
        analyzer = create_analyzer()
        anonymizer = create_anonymizer()
        for msg in messages:
            msg.text = anonymize_text(msg.text, analyzer, anonymizer)

        self.update_state(state="PROGRESS", meta={"stage": "filtering", "progress": 50})
        messages = filter_messages(messages)

        self.update_state(state="PROGRESS", meta={"stage": "chunking", "progress": 65})
        chunks = chunk_telegram_messages(messages)

        self.update_state(state="PROGRESS", meta={"stage": "indexing", "progress": 80})
        embedder = Embedder()
        store = QdrantStore(QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port))
        store.ensure_collection()

        for chunk in chunks:
            if not isinstance(chunk.get("metadata"), dict):
                raise ValueError("Invalid chunk payload: missing metadata")
            chunk["metadata"]["source_id"] = source_id

        texts = [c["text"] for c in chunks]
        dense_vectors, sparse_vectors = embedder.embed_batch(texts)

        for i, chunk in enumerate(chunks):
            chunk["dense_vector"] = dense_vectors[i].tolist()
            chunk["sparse_vector"] = sparse_vectors[i]
            chunk["id"] = f"telegram:{source_id}:{i}"

        count = store.upsert_chunks(chunks)
        _validate_chunks_for_dispatch(chunks)
        extract_knowledge_task.delay(source_id=source_id, chunks=chunks)
        return {"status": "completed", "messages_processed": len(messages), "chunks_indexed": count}
    except Exception as exc:
        logger.error("Ingestion failed for source %s: %s", source_id, exc)
        self.update_state(state="FAILURE", meta={"error": str(exc)})
        raise


@celery_app.task(bind=True, autoretry_for=(Exception,), max_retries=3)
def ingest_pdf(self, source_id: str, file_path: str):
    try:
        source_id = _validate_source_id(source_id)
        self.update_state(state="PROGRESS", meta={"stage": "parsing", "progress": 15})
        markdown = extract_pdf_text(file_path)

        self.update_state(state="PROGRESS", meta={"stage": "anonymizing", "progress": 30})
        analyzer = create_analyzer()
        anonymizer = create_anonymizer()
        markdown = anonymize_text(markdown, analyzer, anonymizer)

        self.update_state(state="PROGRESS", meta={"stage": "chunking", "progress": 50})
        text_chunks = chunk_text(markdown)
        chunks = []
        for idx, chunk in enumerate(text_chunks):
            chunks.append({"text": chunk, "metadata": {"source_type": "pdf", "source_id": source_id, "chunk_index": idx}})

        self.update_state(state="PROGRESS", meta={"stage": "indexing", "progress": 75})
        embedder = Embedder()
        store = QdrantStore(QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port))
        store.ensure_collection()

        texts = [c["text"] for c in chunks]
        dense_vectors, sparse_vectors = embedder.embed_batch(texts)
        for i, chunk in enumerate(chunks):
            chunk["dense_vector"] = dense_vectors[i].tolist()
            chunk["sparse_vector"] = sparse_vectors[i]
            chunk["id"] = f"pdf:{source_id}:{i}"

        count = store.upsert_chunks(chunks)
        _validate_chunks_for_dispatch(chunks)
        extract_knowledge_task.delay(source_id=source_id, chunks=chunks)
        return {"status": "completed", "chunks_indexed": count}
    except Exception as exc:
        logger.error("PDF ingestion failed for source %s: %s", source_id, exc)
        self.update_state(state="FAILURE", meta={"error": str(exc)})
        raise
