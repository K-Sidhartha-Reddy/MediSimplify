import io
import shutil
from pathlib import Path

import fitz
import pytesseract
from PIL import Image
from app.core.config import get_settings

settings = get_settings()


class OCRUnavailableError(RuntimeError):
    pass


def _resolve_tesseract_cmd() -> str | None:
    configured = (settings.tesseract_cmd or "").strip()
    if configured:
        if Path(configured).exists():
            return configured
        resolved = shutil.which(configured)
        if resolved:
            return resolved

    return shutil.which("tesseract")


TESSERACT_CMD = _resolve_tesseract_cmd()
if TESSERACT_CMD:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD


def _require_tesseract() -> None:
    if not TESSERACT_CMD:
        raise OCRUnavailableError(
            "OCR engine is not available. Install Tesseract or upload a text-based PDF."
        )


def extract_text_from_file(file_name: str, file_bytes: bytes) -> str:
    lower_name = file_name.lower()

    if lower_name.endswith(".pdf"):
        return _extract_text_from_pdf(file_bytes)

    return _extract_text_from_image(file_bytes)


def _extract_text_from_image(file_bytes: bytes) -> str:
    _require_tesseract()
    image = Image.open(io.BytesIO(file_bytes)).convert("RGB")
    try:
        text = pytesseract.image_to_string(image)
    except pytesseract.TesseractNotFoundError as exc:
        raise OCRUnavailableError(
            "OCR engine is not available. Install Tesseract and retry."
        ) from exc
    return " ".join(text.split())


def _extract_text_from_pdf(file_bytes: bytes) -> str:
    doc = fitz.open(stream=file_bytes, filetype="pdf")

    # Prefer embedded/selectable text when available.
    embedded_text_pages: list[str] = []
    for page in doc:
        page_text = page.get_text("text")
        if page_text and page_text.strip():
            embedded_text_pages.append(" ".join(page_text.split()))

    if embedded_text_pages:
        return "\n".join(embedded_text_pages)

    _require_tesseract()

    pages: list[str] = []

    try:
        for page in doc:
            pix = page.get_pixmap(dpi=220)
            image = Image.open(io.BytesIO(pix.tobytes("png"))).convert("RGB")
            page_text = pytesseract.image_to_string(image)
            pages.append(page_text)
    except pytesseract.TesseractNotFoundError as exc:
        raise OCRUnavailableError(
            "OCR engine is not available. Install Tesseract and retry."
        ) from exc

    return "\n".join(" ".join(page.split()) for page in pages if page.strip())
