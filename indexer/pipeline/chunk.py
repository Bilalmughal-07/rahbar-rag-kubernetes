"""Stage 3: Chunk. Structure-aware, with overlap."""

from __future__ import annotations

import hashlib
import re

from .models import Chunk, Document


def _heading(line: str) -> bool:
    value = line.strip()
    if value.startswith("#"):
        return True
    return bool(re.match(r"^\d+(?:\.\d+)*[.)]?\s+[A-Z][^.!?]{0,100}$", value)) or (
        len(value) <= 120 and value.isupper() and len(value.split()) > 1
    )


def _units(text: str, current_section: str) -> list[tuple[str, str]]:
    section = current_section or "Document"
    units: list[tuple[str, str]] = []
    paragraphs: list[str] = []
    for line in text.splitlines() + [""]:
        line = line.strip()
        if _heading(line):
            if paragraphs:
                units.append((section, " ".join(paragraphs)))
                paragraphs = []
            section = re.sub(r"^#+\s*", "", line).strip()
        elif line:
            paragraphs.append(line)
        elif paragraphs:
            units.append((section, " ".join(paragraphs)))
            paragraphs = []
    return units


def _sentences(text: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]


def _word_count(text: str) -> int:
    return len(text.split())


def _window_text(parts: list[str], limit: int) -> list[str]:
    result: list[str] = []
    current: list[str] = []
    count = 0
    for part in parts:
        words = part.split()
        if current and count + len(words) > limit:
            result.append(" ".join(current))
            current, count = [], 0
        if len(words) > limit:
            for start in range(0, len(words), limit):
                result.append(" ".join(words[start:start + limit]))
            continue
        current.append(part)
        count += len(words)
    if current:
        result.append(" ".join(current))
    return result


def chunk(doc: Document, size: int, overlap: int) -> list[Chunk]:
    """Split on sections, then paragraphs, then sentences, keeping each chunk under
    `size` tokens, with `overlap` tokens shared between neighbours. Every chunk keeps
    the section heading it sits under, its page, doc_version and superseded."""
    if size <= 0 or overlap < 0 or overlap >= size:
        raise ValueError("chunk size must be positive and overlap must be between 0 and size")
    chunks: list[Chunk] = []
    position = 0
    for page in doc.pages:
        units = _units(page.text, "Document")
        for section, value in units:
            parts = _sentences(value) or [value]
            for text in _window_text(parts, size):
                words = text.split()
                if not words:
                    continue
                chunk_id = hashlib.sha1(
                    f"{doc.source}\0{doc.doc_version}\0{position}\0{text}".encode("utf-8")
                ).hexdigest()[:16]
                chunks.append(Chunk(chunk_id, text, doc.source, section, page.page,
                                    doc.doc_version, doc.superseded, doc.title,
                                    doc.source_url, doc.document_id, doc.content_hash))
                position += 1
    if overlap and len(chunks) > 1:
        # Add a deterministic tail of the preceding chunk to each next chunk. This is
        # performed after structural splitting so section/page metadata stays truthful.
        for index in range(1, len(chunks)):
            previous_words = chunks[index - 1].text.split()
            if chunks[index].section != chunks[index - 1].section:
                continue
            tail = previous_words[-overlap:]
            if tail and not chunks[index].text.startswith(" ".join(tail)):
                chunks[index].text = " ".join(tail + chunks[index].text.split())
    return chunks
