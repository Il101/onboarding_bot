#!/usr/bin/env python
"""
Index published knowledge items into Qdrant vector database.
Creates embeddings and stores them for RAG retrieval.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, PointStruct, VectorParams
from sqlalchemy.orm import Session

from src.api.deps import SessionLocal
from src.core.config import settings
from src.core.logging import get_logger
from src.models.knowledge_item import KnowledgeItem, KnowledgeStatus
from src.pipeline.indexer.embedder import Embedder

logger = get_logger(__name__)


def create_qdrant_collection(client: QdrantClient, collection_name: str = "knowledge") -> None:
    """Create Qdrant collection with proper configuration."""
    if client.collection_exists(collection_name):
        logger.info(f"Collection '{collection_name}' already exists")
        return

    logger.info(f"Creating collection '{collection_name}'...")
    client.create_collection(
        collection_name=collection_name,
        vectors_config=VectorParams(size=1024, distance=Distance.COSINE),
    )
    logger.info(f"Collection '{collection_name}' created successfully")


def index_knowledge_items(db: Session, client: QdrantClient, collection_name: str = "knowledge") -> int:
    """Index published knowledge items into Qdrant."""
    embedder = Embedder()

    # Get all published items
    items = db.query(KnowledgeItem).filter_by(status=KnowledgeStatus.PUBLISHED).all()

    if not items:
        logger.warning("No published knowledge items to index")
        return 0

    logger.info(f"Indexing {len(items)} knowledge items...")

    # Prepare texts for embedding
    texts = [f"{item.topic}: {item.fact}" for item in items]

    # Generate embeddings
    logger.info("Generating embeddings...")
    dense_vectors, _ = embedder.embed_batch(texts)

    # Prepare points for Qdrant
    points = []
    for item, vec in zip(items, dense_vectors):
        point = PointStruct(
            id=item.id,
            vector=vec,
            payload={
                "topic": item.topic,
                "fact": item.fact,
                "confidence": item.confidence,
                "source_refs": json.loads(item.source_refs) if item.source_refs else [],
            },
        )
        points.append(point)

    # Upsert to Qdrant
    logger.info(f"Upserting {len(points)} points to Qdrant...")
    client.upsert(collection_name=collection_name, points=points)

    return len(points)


def verify_indexing(db: Session, client: QdrantClient, collection_name: str = "knowledge") -> None:
    """Verify indexing was successful."""
    # Check collection info
    if not client.collection_exists(collection_name):
        logger.error(f"Collection '{collection_name}' does not exist!")
        return

    info = client.get_collection(collection_name)
    count = client.count(collection_name=collection_name)

    logger.info(f"Collection '{collection_name}':")
    logger.info(f"  Points: {count.count}")
    logger.info(f"  Vector size: {info.config.params.vectors.size}")
    logger.info(f"  Distance: {info.config.params.vectors.distance}")

    # Test search
    logger.info("\nTesting search with sample query...")
    embedder = Embedder()
    query_vec = embedder.embed_batch(["онбординг"])[0][0]

    results = client.query_points(
        collection_name=collection_name,
        query=query_vec,
        limit=3,
    )

    logger.info(f"Found {len(results.points)} results for query 'онбординг':")
    for i, result in enumerate(results.points, 1):
        logger.info(f"  {i}. [{result.score:.3f}] {result.payload.get('topic', 'N/A')}: {result.payload.get('fact', 'N/A')[:60]}...")


def main() -> int:
    print("Indexing knowledge to Qdrant\n")

    # Initialize Qdrant client
    client = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)

    try:
        # Create collection
        print("1. Creating Qdrant collection...")
        create_qdrant_collection(client, "knowledge")

        # Index items
        print("\n2. Indexing knowledge items...")
        db = SessionLocal()
        try:
            indexed = index_knowledge_items(db, client, "knowledge")
            print(f"   ✓ Indexed {indexed} items")

            # Verify
            print("\n3. Verifying indexing...")
            verify_indexing(db, client, "knowledge")

            print("\n✓ Indexing completed successfully!")
            return 0

        finally:
            db.close()

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
