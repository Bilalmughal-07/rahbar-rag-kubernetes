"""The shapes passed between stages. Metadata fields are required (section 3.1)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Page:
    """Text of one page, as extraction produced it."""

    source: str              # file name, e.g. Academic_Rules_Handbook_2026.pdf
    page: int                # 1-based
    text: str
    ocr: bool = False        # True when this page had no text layer and was OCR'd


@dataclass
class Document:
    source: str
    doc_version: str         # e.g. "2026-06"; from corpus/sources.yaml
    superseded: bool         # True for an older version of a policy
    title: str = ""
    pages: list[Page] = field(default_factory=list)
    source_url: str = ""
    document_id: str = ""
    content_hash: str = ""


@dataclass
class Chunk:
    id: str                  # stable: same document + same position gives the same id
    text: str
    source: str
    section: str             # the heading this chunk sits under, e.g. "5.4 Academic Warning"
    page: int
    doc_version: str
    superseded: bool
    title: str = ""
    source_url: str = ""
    document_id: str = ""
    content_hash: str = ""

    def metadata(self) -> dict[str, str | int | bool]:
        """Chroma metadata values must be str, int, float or bool."""
        metadata: dict[str, str | int | bool] = {
            "source": self.source,
            "section": self.section,
            "page": self.page,
            "doc_version": self.doc_version,
            "superseded": self.superseded,
        }
        if self.title:
            metadata["title"] = self.title
        if self.source_url:
            metadata["source_url"] = self.source_url
        if self.document_id:
            metadata["document_id"] = self.document_id
        if self.content_hash:
            metadata["content_hash"] = self.content_hash
        return metadata
