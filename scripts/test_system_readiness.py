#!/usr/bin/env python
"""
System readiness check script.
Tests all major components of V-Brain system.
"""

import json
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

import qdrant_client as qc
from sqlalchemy import text
from sqlalchemy.orm import Session

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.api.deps import SessionLocal, engine
from src.ai.llm_client import llm_chat
from src.core.config import settings
from src.core.logging import get_logger
from src.models.knowledge_item import KnowledgeItem, KnowledgeStatus
from src.models.source import Source, SourceType
from src.models.telegram_user import TelegramUser, UserRole
from src.pipeline.filters.noise import filter_messages
from src.pipeline.parsers.telegram import parse_telegram_export
from src.pipeline.parsers.pdf import extract_pdf_text
from src.pipeline.anonymizer.engine import create_analyzer, create_anonymizer, anonymize_text
from src.pipeline.chunker.text_chunker import chunk_text

logger = get_logger(__name__)


class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


def print_header(text: str) -> None:
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'=' * 60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'=' * 60}{Colors.RESET}")


def print_success(text: str) -> None:
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")


def print_error(text: str) -> None:
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")


def print_warning(text: str) -> None:
    print(f"{Colors.YELLOW}⚠ {text}{Colors.RESET}")


def print_info(text: str) -> None:
    print(f"{Colors.BLUE}ℹ {text}{Colors.RESET}")


class ReadinessChecker:
    def __init__(self) -> None:
        self.results: dict[str, dict[str, Any]] = {}
        self.total_checks = 0
        self.passed_checks = 0
        self.failed_checks = 0

    def record_result(self, component: str, check: str, passed: bool, details: str = "", error: str = "") -> None:
        self.total_checks += 1
        if passed:
            self.passed_checks += 1
            print_success(f"{component}: {check}")
        else:
            self.failed_checks += 1
            print_error(f"{component}: {check}")
            if error:
                print(f"  Error: {error}")
        if details:
            print(f"  {details}")

        if component not in self.results:
            self.results[component] = {}
        self.results[component][check] = {
            "passed": passed,
            "details": details,
            "error": error,
        }

    def check_database(self) -> None:
        print_header("DATABASE CHECK")
        try:
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1"))
                result.scalar()
                self.record_result("Database", "Connectivity", True, "PostgreSQL connection successful")

                tables = conn.execute(text("""
                    SELECT table_name FROM information_schema.tables
                    WHERE table_schema = 'public'
                """)).fetchall()
                table_names = [t[0] for t in tables]

                required_tables = ["sources", "ingest_jobs", "knowledge_items", "telegram_users", "feedback_events"]
                missing = [t for t in required_tables if t not in table_names]

                if not missing:
                    self.record_result("Database", "Schema", True, f"All {len(required_tables)} required tables present")
                else:
                    self.record_result("Database", "Schema", False, error=f"Missing tables: {missing}")

                if "sources" in table_names:
                    count = conn.execute(text("SELECT COUNT(*) FROM sources")).scalar()
                    self.record_result("Database", "Data", True, f"{count} sources in database")

        except Exception as e:
            self.record_result("Database", "Connectivity", False, error=str(e))

    def check_qdrant(self) -> None:
        print_header("QDRANT CHECK")
        try:
            client = qc.QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)
            collections = client.get_collections()
            self.record_result("Qdrant", "Connectivity", True, "Qdrant connection successful")

            collection_names = [c.name for c in collections.collections]
            expected_collections = ["knowledge"]

            for col in expected_collections:
                if col in collection_names:
                    info = client.get_collection(col)
                    points = client.count(collection_name=col)
                    self.record_result(
                        "Qdrant",
                        f"Collection '{col}'",
                        True,
                        f"{points.count} points, vector_dim={info.config.params.vectors.size}",
                    )
                else:
                    self.record_result("Qdrant", f"Collection '{col}'", False, error="Collection does not exist")

        except Exception as e:
            self.record_result("Qdrant", "Connectivity", False, error=str(e))

    def check_redis(self) -> None:
        print_header("REDIS CHECK")
        try:
            import redis
            client = redis.from_url(settings.redis_url)
            client.ping()
            self.record_result("Redis", "Connectivity", True, "Redis connection successful")

            info = client.info("memory")
            self.record_result("Redis", "Memory", True, f"{info['used_memory_human']} used")

        except Exception as e:
            self.record_result("Redis", "Connectivity", False, error=str(e))

    def check_llm(self) -> None:
        print_header("LLM CHECK")
        try:
            result = llm_chat([{"role": "user", "content": "Say 'OK'"}], temperature=0)
            if result and "ok" in result.lower():
                self.record_result(
                    "LLM",
                    "API Response",
                    True,
                    f"Provider: {settings.llm_provider}, Model: {settings.llm_model}",
                )
            else:
                self.record_result("LLM", "API Response", False, error="Unexpected response")

        except Exception as e:
            self.record_result("LLM", "API Connectivity", False, error=str(e))

    def check_pipeline_components(self) -> None:
        print_header("PIPELINE COMPONENTS CHECK")

        try:
            analyzer = create_analyzer()
            anonymizer = create_anonymizer()
            test_text = "Call Ivan Ivanov at +7 999 123 45 67 or email ivan@example.com"
            anonymized = anonymize_text(test_text, analyzer, anonymizer)

            if "Ivan" not in anonymized and "+7" not in anonymized:
                self.record_result("Pipeline", "PII Anonymizer", True, "PII properly anonymized")
            else:
                self.record_result("Pipeline", "PII Anonymizer", False, error="PII not properly anonymized")

        except Exception as e:
            self.record_result("Pipeline", "PII Anonymizer", False, error=str(e))

        try:
            long_text = " ".join(["This is a test sentence. "] * 20)
            chunks = chunk_text(long_text)

            if len(chunks) > 1:
                self.record_result("Pipeline", "Text Chunker", True, f"Created {len(chunks)} chunks")
            else:
                self.record_result("Pipeline", "Text Chunker", False, error="Chunking not working")

        except Exception as e:
            self.record_result("Pipeline", "Text Chunker", False, error=str(e))

        try:
            messages = [
                {"text": "Photo", "type": "service_message"},
                {"text": "User joined", "type": "service_message"},
                {"text": "This is important information", "type": "message"},
            ]
            filtered = filter_messages(messages)

            if len(filtered) == 1:
                self.record_result("Pipeline", "Noise Filter", True, f"Filtered {len(messages)-len(filtered)} noise messages")
            else:
                self.record_result("Pipeline", "Noise Filter", False, error=f"Expected 1 message, got {len(filtered)}")

        except Exception as e:
            self.record_result("Pipeline", "Noise Filter", False, error=str(e))

    def check_qdrant_indexer(self) -> None:
        print_header("QDRANT INDEXER CHECK")
        try:
            from src.pipeline.indexer.embedder import Embedder
            embedder = Embedder()
            test_texts = ["Test document for embedding"]
            dense_vectors, sparse_vectors = embedder.embed_batch(test_texts)

            if dense_vectors and len(dense_vectors) == len(test_texts):
                dim = len(dense_vectors[0])
                self.record_result("Indexer", "Embedding Generation", True, f"Generated {dim}-dimensional dense vectors")
            else:
                self.record_result("Indexer", "Embedding Generation", False, error="Vector generation failed")

        except Exception as e:
            self.record_result("Indexer", "Embedding Generation", False, error=str(e))

    def run_test_workflow(self) -> None:
        print_header("E2E WORKFLOW TEST")

        try:
            sample_telegram = {
                "messages": [
                    {
                        "id": 1,
                        "type": "message",
                        "date": "2024-01-15T10:00:00",
                        "from": "John Doe",
                        "from_id": 123456789,
                        "text": "Important: Project deadline is March 15th. All deliverables must be submitted.",
                    },
                    {
                        "id": 2,
                        "type": "message",
                        "date": "2024-01-15T10:05:00",
                        "from": "Jane Smith",
                        "from_id": 987654321,
                        "text": "Got it. I'll ensure the team is aware.",
                    },
                ]
            }

            # Create temp file and parse
            import tempfile
            import json
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(sample_telegram, f)
                temp_file = f.name
            
            try:
                parsed = parse_telegram_export(temp_file)
                if len(parsed) >= 2:
                    self.record_result("E2E", "Telegram Parser", True, f"Parsed {len(parsed)} messages")
                else:
                    self.record_result("E2E", "Telegram Parser", False, error=f"Expected 2 messages, got {len(parsed)}")
            finally:
                import os
                os.unlink(temp_file)

        except Exception as e:
            self.record_result("E2E", "Telegram Parser", False, error=str(e))

        try:
            import reportlab.pdfgen.canvas as canvas
            import reportlab.lib.pagesizes as pagesizes

            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
                c = canvas.Canvas(f.name, pagesize=pagesizes.A4)
                c.drawString(100, 800, "V-Brain Company Handbook")
                c.drawString(100, 750, "Chapter 1: Onboarding Process")
                c.drawString(100, 700, "New employees must complete orientation within first week.")
                c.drawString(100, 650, "Contact HR at ext. 100 for any questions.")
                c.save()
                pdf_path = f.name

            parsed = extract_pdf_text(pdf_path)
            os.unlink(pdf_path)

            if parsed and "orientation" in parsed.lower():
                self.record_result("E2E", "PDF Parser", True, f"Extracted {len(parsed)} characters")
            else:
                self.record_result("E2E", "PDF Parser", False, error="PDF parsing incomplete")

        except Exception as e:
            self.record_result("E2E", "PDF Parser", False, error=str(e))

    def create_test_data(self) -> None:
        print_header("TEST DATA CREATION")

        db = SessionLocal()
        try:
            existing_user = db.query(TelegramUser).filter_by(user_id=999999).first()
            if not existing_user:
                user = TelegramUser(
                    user_id=999999,
                    username="test_user",
                    role=UserRole.EMPLOYEE,
                )
                db.add(user)
                db.commit()
                self.record_result("Test Data", "Test User", True, "Created test_user (999999)")
            else:
                self.record_result("Test Data", "Test User", True, "Test user already exists")

            existing_source = db.query(Source).filter_by(name="Test Telegram Export").first()
            if not existing_source:
                source = Source(
                    name="Test Telegram Export",
                    source_type=SourceType.TELEGRAM,
                    file_path="test_telegram.json",
                    status="completed",
                )
                db.add(source)
                db.commit()
                source_id = source.id
                self.record_result("Test Data", "Test Source", True, f"Created source with ID {source_id}")
            else:
                source_id = existing_source.id
                self.record_result("Test Data", "Test Source", True, f"Source already exists (ID {source_id})")

            test_facts = [
                {
                    "topic": "Onboarding",
                    "fact": "New employees must complete orientation within first week",
                    "confidence": 0.9,
                },
                {
                    "topic": "Contacts",
                    "fact": "HR can be reached at extension 100",
                    "confidence": 0.95,
                },
                {
                    "topic": "Project Management",
                    "fact": "Project deadline is March 15th for all deliverables",
                    "confidence": 0.85,
                },
            ]

            created_count = 0
            for fact in test_facts:
                existing = db.query(KnowledgeItem).filter_by(source_id=source_id, fact=fact["fact"]).first()
                if not existing:
                    item = KnowledgeItem(
                        source_id=source_id,
                        topic=fact["topic"],
                        fact=fact["fact"],
                        confidence=fact["confidence"],
                        status=KnowledgeStatus.PUBLISHED,
                        published_at=datetime.utcnow(),
                    )
                    db.add(item)
                    created_count += 1

            if created_count > 0:
                db.commit()
                self.record_result("Test Data", "Knowledge Items", True, f"Created {created_count} test knowledge items")
            else:
                self.record_result("Test Data", "Knowledge Items", True, "Test knowledge items already exist")

        except Exception as e:
            db.rollback()
            self.record_result("Test Data", "Creation", False, error=str(e))
        finally:
            db.close()

    def test_knowledge_query(self) -> None:
        print_header("KNOWLEDGE QUERY TEST")

        try:
            db = SessionLocal()
            published_count = db.query(KnowledgeItem).filter_by(status=KnowledgeStatus.PUBLISHED).count()

            if published_count > 0:
                self.record_result("Query", "Published Knowledge", True, f"Found {published_count} published items")

                items = db.query(KnowledgeItem).filter_by(status=KnowledgeStatus.PUBLISHED).limit(3).all()
                topics = set(item.topic for item in items)
                self.record_result("Query", "Topic Diversity", True, f"Topics: {', '.join(topics)}")

                try:
                    client = qc.QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)
                    if client.collection_exists("knowledge"):
                        results = client.search(
                            collection_name="knowledge",
                            query_vector=[0] * 1024,
                            limit=3
                        )
                        self.record_result("Query", "Qdrant Search", True, f"Collection exists, {len(results)} points returned")
                    else:
                        self.record_result("Query", "Qdrant Search", False, error="Knowledge collection does not exist")
                except Exception as e:
                    self.record_result("Query", "Qdrant Search", False, error=str(e))
            else:
                self.record_result("Query", "Published Knowledge", False, error="No published knowledge items")

            db.close()
        except Exception as e:
            self.record_result("Query", "Database Query", False, error=str(e))

    def print_summary(self) -> None:
        print_header("READINESS SUMMARY")

        print(f"\n{Colors.BOLD}Total Checks: {self.total_checks}{Colors.RESET}")
        print(f"{Colors.GREEN}Passed: {self.passed_checks}{Colors.RESET}")
        print(f"{Colors.RED}Failed: {self.failed_checks}{Colors.RESET}")

        pass_rate = (self.passed_checks / self.total_checks * 100) if self.total_checks > 0 else 0
        print(f"\n{Colors.BOLD}Pass Rate: {pass_rate:.1f}%{Colors.RESET}")

        if pass_rate >= 90:
            status = f"{Colors.GREEN}READY{Colors.RESET}"
        elif pass_rate >= 70:
            status = f"{Colors.YELLOW}MOSTLY READY{Colors.RESET}"
        else:
            status = f"{Colors.RED}NOT READY{Colors.RESET}"

        print(f"\n{Colors.BOLD}System Status: {status}{Colors.RESET}")

        print(f"\n{Colors.BOLD}Component Status:{Colors.RESET}")
        for component, checks in self.results.items():
            comp_passed = sum(1 for c in checks.values() if c["passed"])
            comp_total = len(checks)
            comp_rate = comp_passed / comp_total * 100 if comp_total > 0 else 0

            if comp_rate == 100:
                status_icon = f"{Colors.GREEN}✓{Colors.RESET}"
            elif comp_rate >= 50:
                status_icon = f"{Colors.YELLOW}~{Colors.RESET}"
            else:
                status_icon = f"{Colors.RED}✗{Colors.RESET}"

            print(f"  {status_icon} {component}: {comp_passed}/{comp_total} ({comp_rate:.0f}%)")

        print(f"\n{Colors.BOLD}Recommendations:{Colors.RESET}")
        if pass_rate == 100:
            print(f"  {Colors.GREEN}• System is fully operational!{Colors.RESET}")
            print(f"  {Colors.GREEN}• Start API: uvicorn src.api.main:app --reload{Colors.RESET}")
            print(f"  {Colors.GREEN}• Start Bot: python -m src.bot.telegram_app{Colors.RESET}")
        elif pass_rate >= 70:
            print(f"  {Colors.YELLOW}• Fix the failing components above{Colors.RESET}")
        else:
            print(f"  {Colors.RED}• Start containers: docker-compose up -d{Colors.RESET}")
            print(f"  {Colors.RED}• Check .env configuration{Colors.RESET}")
            print(f"  {Colors.RED}• Run migrations: alembic upgrade head{Colors.RESET}")

    def run_all_checks(self) -> None:
        print(f"\n{Colors.BOLD}{Colors.MAGENTA}V-Brain System Readiness Check{Colors.RESET}")
        print(f"{Colors.CYAN}Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.RESET}")

        self.check_database()
        self.check_qdrant()
        self.check_redis()
        self.check_llm()
        self.check_pipeline_components()
        self.check_qdrant_indexer()
        self.run_test_workflow()
        self.create_test_data()
        self.test_knowledge_query()
        self.print_summary()


def main() -> int:
    checker = ReadinessChecker()
    checker.run_all_checks()
    return 0 if checker.failed_checks == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
