from pathlib import Path

from docling.document_converter import DocumentConverter


def extract_pdf_text(filepath: str) -> str:
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(filepath)
    if path.suffix.lower() != ".pdf":
        raise ValueError("Only PDF files are supported")

    converter = DocumentConverter()
    result = converter.convert(str(path))
    return result.document.export_to_markdown()
