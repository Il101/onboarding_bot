from unittest.mock import MagicMock, patch

from src.pipeline.parsers.pdf import extract_pdf_text


def test_extract_text_from_pdf(sample_pdf_path):
    with patch("src.pipeline.parsers.pdf.DocumentConverter") as mock_converter:
        mock_doc = MagicMock()
        mock_doc.export_to_markdown.return_value = "# Extracted content"
        mock_result = MagicMock()
        mock_result.document = mock_doc
        mock_converter.return_value.convert.return_value = mock_result

        result = extract_pdf_text(sample_pdf_path)
    assert isinstance(result, str)
    assert result.strip() != ""


def test_missing_file_raises():
    import pytest

    with pytest.raises(FileNotFoundError):
        extract_pdf_text("/nonexistent/file.pdf")


def test_non_pdf_raises(tmp_path):
    import pytest

    txt_path = tmp_path / "not_a_pdf.txt"
    txt_path.write_text("hello", encoding="utf-8")
    with pytest.raises(ValueError):
        extract_pdf_text(str(txt_path))


def test_cyrillic_preserved(sample_pdf_path):
    with patch("src.pipeline.parsers.pdf.DocumentConverter") as mock_converter:
        mock_doc = MagicMock()
        mock_doc.export_to_markdown.return_value = "Тестовый документ с кириллицей"
        mock_result = MagicMock()
        mock_result.document = mock_doc
        mock_converter.return_value.convert.return_value = mock_result

        result = extract_pdf_text(sample_pdf_path)
    assert "Тестовый" in result
