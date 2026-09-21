"""OCR service module for extracting text from scanned documents and images."""
from __future__ import annotations

import io
from pathlib import Path
from typing import Union

try:
    import pymupdf as fitz
except ImportError:
    import fitz  # type: ignore

try:
    from PIL import Image
except ImportError:
    Image = None  # type: ignore

try:
    import pytesseract
except ImportError:
    pytesseract = None  # type: ignore


class OCRError(Exception):
    """Raised when OCR processing fails or Tesseract is unavailable."""

    pass


def is_ocr_available() -> bool:
    """Check if pytesseract and Tesseract OCR engine are available."""
    if pytesseract is None:
        return False
    try:
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False


def ocr_extract_from_image(image_input: Union[Image.Image, bytes, Path, str]) -> str:
    """Extract text from an image (PIL Image object, bytes, or file path)."""
    if not is_ocr_available():
        raise OCRError(
            "Tesseract OCR engine is not installed or available in the system PATH. "
            "Please install Tesseract OCR to process image-based reports."
        )

    try:
        if isinstance(image_input, (bytes, bytearray)):
            if Image is None:
                raise OCRError("Pillow library is required for image processing.")
            img = Image.open(io.BytesIO(image_input))
        elif isinstance(image_input, (str, Path)):
            if Image is None:
                raise OCRError("Pillow library is required for image processing.")
            img = Image.open(image_input)
        elif hasattr(Image, "Image") and isinstance(image_input, Image.Image):
            img = image_input
        else:
            raise OCRError("Invalid image input type.")

        text = pytesseract.image_to_string(img)
        return text.strip()
    except OCRError:
        raise
    except Exception as exc:
        raise OCRError(f"OCR image extraction failed: {exc}") from exc


def ocr_extract_from_pdf_bytes(pdf_bytes: bytes) -> str:
    """Extract text from a scanned PDF by rendering pages to images and running OCR."""
    if not is_ocr_available():
        raise OCRError(
            "Tesseract OCR engine is not installed or available in the system PATH. "
            "Please install Tesseract OCR to process image-based PDFs."
        )

    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        page_texts = []
        for i, page in enumerate(doc):
            pix = page.get_pixmap(dpi=150)
            img_bytes = pix.tobytes("png")
            if Image is None:
                raise OCRError("Pillow library is required for OCR operations.")
            img = Image.open(io.BytesIO(img_bytes))
            text = pytesseract.image_to_string(img).strip()
            if text:
                page_texts.append(f"--- Page {i + 1} ---\n{text}")
            else:
                page_texts.append(f"--- Page {i + 1} ---")
        doc.close()
        return "\n\n".join(page_texts)
    except OCRError:
        raise
    except Exception as exc:
        raise OCRError(f"OCR PDF extraction failed: {exc}") from exc
