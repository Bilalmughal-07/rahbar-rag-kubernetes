"""Stage 1: Extract. PDF (or HTML, or Markdown) to text, page by page."""

from __future__ import annotations

import html
import re
from functools import lru_cache
from pathlib import Path
from typing import Any

from .models import Document
from .models import Page


def _front_matter_title(text: str) -> str:
    if not text.startswith("---"):
        return ""
    for line in text.splitlines()[1:]:
        if line.strip() == "---":
            break
        key, _, value = line.partition(":")
        if key.strip().lower() in {"title", "name"}:
            return value.strip().strip("\"'")
    return ""


def _without_front_matter(text: str) -> str:
    if not text.startswith("---"):
        return text
    lines = text.splitlines()
    for index, line in enumerate(lines[1:], 1):
        if line.strip() == "---":
            return "\n".join(lines[index + 1:])
    return text


def _html_text(raw: str) -> str:
    """Extract readable HTML while retaining heading boundaries."""
    raw = re.sub(r"<\s*(br|/p|/div|/li|/tr|/h[1-6])\s*/?>", "\n", raw, flags=re.I)
    raw = re.sub(r"<\s*h[1-6][^>]*>", "\n", raw, flags=re.I)
    raw = re.sub(r"<[^>]+>", " ", raw)
    return html.unescape(re.sub(r"[ \t]+", " ", raw)).strip()


def _tables_for_page(page: Any) -> str:
    """Render detected PDF tables as pipe-separated rows instead of losing columns."""
    try:
        tables = page.extract_tables() or []
    except Exception:
        return ""
    rendered: list[str] = []
    for table in tables:
        rows = []
        for row in table:
            cells = [re.sub(r"\s+", " ", (cell or "")).strip() for cell in row]
            if any(cells):
                rows.append(" | ".join(cells))
        if rows:
            rendered.append("TABLE\n" + "\n".join(rows))
    return "\n\n".join(rendered)


@lru_cache(maxsize=1)
def _rapid_ocr() -> Any:
    """Load the bundled ONNX OCR engine once per indexer process."""
    from rapidocr_onnxruntime import RapidOCR

    return RapidOCR()


def _ocr_page(path: str, page_number: int) -> str:
    """OCR one image-only page using the pip-distributed ONNX runtime.

    pdfplumber's bundled pypdfium2 renderer produces the page image, so this
    path has no Poppler or system Tesseract dependency. The old pytesseract
    path remains a best-effort fallback when an environment provides binaries.
    """
    try:
        import numpy as np
        import pdfplumber

        with pdfplumber.open(path) as pdf:
            image = np.asarray(pdf.pages[page_number - 1].to_image(resolution=200).original)
        result, _elapsed = _rapid_ocr()(image)
        if not result:
            return ""
        return "\n".join(str(line[1]).strip() for line in result if len(line) > 1).strip()
    except Exception:
        try:
            from pdf2image import convert_from_path
            import pytesseract

            image = convert_from_path(path, first_page=page_number, last_page=page_number,
                                      dpi=200, fmt="png")[0]
            return pytesseract.image_to_string(image).strip()
        except Exception:
            # Preserve the page in coverage and report it as empty; never invent OCR text.
            return ""


def extract(path: str, doc_version: str, superseded: bool) -> Document:
    """Return the document's text page by page.

    Detect pages with no text layer and OCR them; mark those pages ocr=True.
    The primary OCR runtime is the pinned RapidOCR ONNX wheel; pdfplumber's
    pypdfium2 renderer handles scanned pages without system Poppler/Tesseract.
    """
    file_path = Path(path)
    suffix = file_path.suffix.lower()
    title = file_path.stem.replace("_", " ").replace("-", " ").strip()

    if suffix in {".md", ".txt"}:
        raw = file_path.read_text(encoding="utf-8", errors="replace")
        title = _front_matter_title(raw) or title
        return Document(file_path.name, doc_version, superseded, title,
                        [Page(file_path.name, 1, _without_front_matter(raw), False)])

    if suffix in {".html", ".htm"}:
        raw = file_path.read_text(encoding="utf-8", errors="replace")
        return Document(file_path.name, doc_version, superseded, title,
                        [Page(file_path.name, 1, _html_text(raw), False)])

    if suffix != ".pdf":
        raise ValueError(f"unsupported document type: {file_path.suffix}")

    try:
        import pdfplumber
        with pdfplumber.open(str(file_path)) as pdf:
            pages: list[Page] = []
            for number, pdf_page in enumerate(pdf.pages, 1):
                text = (pdf_page.extract_text() or "").strip()
                table_text = _tables_for_page(pdf_page)
                if table_text and table_text not in text:
                    text = f"{text}\n\n{table_text}".strip()
                ocr = not bool(text)
                if ocr:
                    text = _ocr_page(str(file_path), number)
                pages.append(Page(file_path.name, number, text, ocr))
    except Exception as exc:
        raise RuntimeError(f"could not extract PDF {file_path}: {exc}") from exc

    return Document(file_path.name, doc_version, superseded, title, pages)
