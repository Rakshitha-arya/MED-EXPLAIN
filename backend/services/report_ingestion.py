"""Report ingestion service for validating, storing, and extracting text from reports."""
from __future__ import annotations

import uuid
import io
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

try:
    import pymupdf as fitz
except ImportError:
    import fitz  # type: ignore

try:
    from PIL import Image
except ImportError:
    Image = None  # type: ignore

from config import Config
from services.ocr_service import (
    OCRError,
    ocr_extract_from_image,
    ocr_extract_from_pdf_bytes,
)

ALLOWED_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png"}


class IngestionError(Exception):
    """Raised when file validation or text extraction fails."""

    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


def validate_file_metadata(filename: Optional[str], file_size: int) -> Tuple[str, str]:
    """Validate filename extension and file size."""
    if not filename:
        raise IngestionError("Filename missing or empty.", status_code=400)

    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise IngestionError(
            f"Unsupported file type '{ext}'. Allowed types: PDF, JPG, PNG.",
            status_code=400,
        )

    if file_size <= 0:
        raise IngestionError("Uploaded file is empty.", status_code=400)

    max_bytes = getattr(Config, "MAX_CONTENT_LENGTH", 16 * 1024 * 1024)
    if file_size > max_bytes:
        max_mb = max_bytes / (1024 * 1024)
        raise IngestionError(
            f"File size exceeds maximum allowed limit of {max_mb:.1f}MB.",
            status_code=400,
        )

    file_type = (
        "pdf" if ext == ".pdf" else ("jpg" if ext in (".jpg", ".jpeg") else "png")
    )
    return ext, file_type


def validate_file_content(file_bytes: bytes, file_type: str) -> None:
    """Reject content that does not match the claimed, allow-listed file type."""
    if file_type == "pdf":
        if not file_bytes.startswith(b"%PDF-"):
            raise IngestionError("Uploaded content is not a valid PDF file.", status_code=400)
        return

    if Image is None:
        raise IngestionError("Image processing support is unavailable.", status_code=422)
    try:
        with Image.open(io.BytesIO(file_bytes)) as image:
            image.verify()
    except Exception as exc:
        raise IngestionError("Uploaded content is not a valid image file.", status_code=400) from exc


def extract_pdf_text_direct(pdf_bytes: bytes) -> Tuple[str, int]:
    """Extract text from a PDF page-by-page using PyMuPDF (fitz).

    Returns (extracted_text, page_count).
    Preserves page boundaries.
    """
    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        page_count = len(doc)
        if page_count == 0:
            doc.close()
            raise IngestionError("PDF file contains no pages.", status_code=400)

        page_texts = []
        for i, page in enumerate(doc):
            text = page.get_text("text").strip()
            if text:
                page_texts.append(f"--- Page {i + 1} ---\n{text}")
            else:
                page_texts.append(f"--- Page {i + 1} ---")
        doc.close()

        full_text = "\n\n".join(page_texts).strip()
        return full_text, page_count
    except IngestionError:
        raise
    except Exception as exc:
        raise IngestionError(
            f"Failed to read PDF structure: {exc}", status_code=400
        ) from exc


def ingest_report(file_bytes: bytes, original_filename: Optional[str]) -> Dict[str, Any]:
    """Validate, save, and extract text from an uploaded medical report.

    Saves file to Config.UPLOAD_DIR using a secure generated filename (UUID).
    Never exposes internal filesystem paths to the caller.
    """
    ext, file_type = validate_file_metadata(original_filename, len(file_bytes))
    validate_file_content(file_bytes, file_type)

    Config.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    safe_filename = f"{uuid.uuid4().hex}{ext}"
    saved_path = Config.UPLOAD_DIR / safe_filename

    try:
        saved_path.write_bytes(file_bytes)
    except Exception as exc:
        raise IngestionError(
            "Failed to save uploaded file locally.", status_code=500
        ) from exc

    extracted_text = ""
    extraction_method = ""
    page_count = 1

    if file_type == "pdf":
        text_direct, page_count = extract_pdf_text_direct(file_bytes)

        # Check if direct text extraction yields non-empty content
        cleaned_text = "\n".join(
            line
            for line in text_direct.splitlines()
            if not line.startswith("--- Page")
        ).strip()

        if len(cleaned_text) >= 15:
            extracted_text = text_direct
            extraction_method = "pdf_text"
        else:
            # Fall back to OCR for scanned PDFs
            try:
                extracted_text = ocr_extract_from_pdf_bytes(file_bytes)
                extraction_method = "pdf_ocr"
            except OCRError as ocr_err:
                raise IngestionError(str(ocr_err), status_code=422) from ocr_err
    else:
        # JPG / PNG image processing through OCR
        try:
            extracted_text = ocr_extract_from_image(file_bytes)
            extraction_method = "image_ocr"
            page_count = 1
        except OCRError as ocr_err:
            raise IngestionError(str(ocr_err), status_code=422) from ocr_err

    if not extracted_text.strip():
        raise IngestionError(
            "No extractable text found in the report.",
            status_code=400,
        )

    return {
        "filename": safe_filename,
        "original_filename": original_filename,
        "file_type": file_type,
        "extraction_method": extraction_method,
        "page_count": page_count,
        "extracted_text": extracted_text,
    }
