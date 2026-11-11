"""Stage 2: Clean. Remove artefacts without destroying structure."""

from __future__ import annotations

import re
from collections import Counter

from .models import Document


def clean(doc: Document) -> Document:
    """Strip headers and footers that repeat on every page; keep headings and
    section boundaries, because chunking and citations depend on them."""
    page_lines: list[list[str]] = []
    for page in doc.pages:
        lines = []
        for raw in page.text.replace("\r\n", "\n").replace("\r", "\n").splitlines():
            line = re.sub(r"[ \t]+", " ", raw).strip()
            if line:
                lines.append(line)
        page_lines.append(lines)

    # A line repeated on at least two pages at the top or bottom is treated as a
    # running header/footer. Numbered headings are deliberately never stripped.
    candidates: list[str] = []
    for lines in page_lines:
        candidates.extend(lines[:2] + lines[-2:])
    repeated = {line for line, count in Counter(candidates).items() if count >= 2}

    cleaned = []
    for page, lines in zip(doc.pages, page_lines):
        kept = [line for line in lines if line not in repeated or _looks_like_heading(line)]
        cleaned.append(type(page)(page.source, page.page, "\n".join(kept), page.ocr))
    return type(doc)(doc.source, doc.doc_version, doc.superseded, doc.title, cleaned)


def _looks_like_heading(line: str) -> bool:
    return bool(re.match(r"^(?:#+\s*|\d+(?:\.\d+)*[.)]?\s+)[A-Z0-9]", line))
