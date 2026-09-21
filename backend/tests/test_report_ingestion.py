"""Tests for report_ingestion service."""
from __future__ import annotations

from unittest.mock import patch

import pytest

try:
    import pymupdf as fitz
except ImportError:
    import fitz  # type: ignore

from services.ocr_service import OCRError
from services.report_ingestion import (
    IngestionError,
    extract_pdf_text_direct,
    ingest_report,
    validate_file_metadata,
)


@pytest.fixture(autouse=True)
def isolated_upload_dir(tmp_path, monkeypatch):
    """Keep service tests independent of persistent runtime uploads."""
    monkeypatch.setattr("services.report_ingestion.Config.UPLOAD_DIR", tmp_path / "uploads")


def create_synthetic_pdf(text_lines: list[str]) -> bytes:
    """Helper to generate a synthetic PDF in memory."""
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 50), "\n".join(text_lines))
    pdf_bytes = doc.write()
    doc.close()
    return pdf_bytes


def test_validate_file_metadata():
    ext, ftype = validate_file_metadata("sample_report.pdf", 100)
    assert ext == ".pdf"
    assert ftype == "pdf"

    ext, ftype = validate_file_metadata("scan.PNG", 500)
    assert ext == ".png"
    assert ftype == "png"

    with pytest.raises(IngestionError) as exc_info:
        validate_file_metadata("script.exe", 100)
    assert "Unsupported file type" in str(exc_info.value)

    with pytest.raises(IngestionError) as exc_info:
        validate_file_metadata("empty.pdf", 0)
    assert "file is empty" in str(exc_info.value)


def test_rejects_content_that_does_not_match_an_allowed_extension():
    with pytest.raises(IngestionError, match="not a valid PDF"):
        ingest_report(b"not a PDF", "masquerading.pdf")

    with pytest.raises(IngestionError, match="not a valid image"):
        ingest_report(b"not an image", "masquerading.png")


def test_direct_pdf_text_extraction():
    lines = [
        "Date: 2026-09-18",
        "Hemoglobin: 14.5 g/dL (13.5 - 17.5)",
    ]
    pdf_bytes = create_synthetic_pdf(lines)
    extracted_text, page_count = extract_pdf_text_direct(pdf_bytes)

    assert page_count == 1
    assert "--- Page 1 ---" in extracted_text
    assert "Hemoglobin: 14.5 g/dL" in extracted_text


def test_ingest_valid_pdf_report():
    lines = [
        "Date: 2026-09-18",
        "Fast Glucose: 95 mg/dL (70 - 99)",
    ]
    pdf_bytes = create_synthetic_pdf(lines)
    result = ingest_report(pdf_bytes, "test_lab_report.pdf")

    assert result["file_type"] == "pdf"
    assert result["extraction_method"] == "pdf_text"
    assert result["page_count"] == 1
    assert "Fast Glucose: 95 mg/dL" in result["extracted_text"]
    assert result["filename"].endswith(".pdf")
    # Verify local filename does not expose absolute directory paths
    assert "/" not in result["filename"] and "\\" not in result["filename"]


def test_ocr_fallback_for_scanned_pdf():
    # Create empty PDF page with no text layer
    doc = fitz.open()
    doc.new_page()
    scanned_pdf_bytes = doc.write()
    doc.close()

    with patch("services.report_ingestion.ocr_extract_from_pdf_bytes") as mock_ocr:
        mock_ocr.return_value = "--- Page 1 ---\nOCR Extracted Scanned Text"
        result = ingest_report(scanned_pdf_bytes, "scanned_doc.pdf")
        assert result["extraction_method"] == "pdf_ocr"
        assert "OCR Extracted Scanned Text" in result["extracted_text"]


def test_ocr_unavailable_error():
    lines = ["Date: 2026-09-18"]
    doc = fitz.open()
    doc.new_page()  # empty text page
    scanned_pdf_bytes = doc.write()
    doc.close()

    with patch("services.report_ingestion.ocr_extract_from_pdf_bytes") as mock_ocr:
        mock_ocr.side_effect = OCRError("Tesseract OCR engine is not installed")
        with pytest.raises(IngestionError) as exc_info:
            ingest_report(scanned_pdf_bytes, "scanned_doc.pdf")
        assert exc_info.value.status_code == 422
        assert "Tesseract OCR engine is not installed" in str(exc_info.value)
