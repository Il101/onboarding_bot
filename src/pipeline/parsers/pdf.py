from pathlib import Path

from docling.document_converter import DocumentConverter

from src.core.config import settings


def extract_pdf_text(filepath: str) -> str:
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(filepath)
    if path.suffix.lower() != ".pdf":
        raise ValueError("Only PDF files are supported")
    if path.stat().st_size > settings.max_file_size_mb * 1024 * 1024:
        raise ValueError("PDF file too large")
    if not path.read_bytes()[:5].startswith(b"%PDF-"):
        raise ValueError("Invalid PDF content")

    converter = DocumentConverter()
    result = converter.convert(str(path))
    return result.document.export_to_markdown()
