"""The real retriever. Yours to build (sections 3.2 and 4.4).

Connection details are already here; the query is not.
"""

from __future__ import annotations

import re

from ..config import Settings
from ..schemas import Passage
from ..services.embedding import embed_text


class ChromaRetriever:
    name = "chroma"

    def __init__(self, settings: Settings) -> None:
        import chromadb  # the thin client, from chromadb-client in requirements.txt
        from chromadb.config import Settings as ChromaSettings

        self.settings = settings
        self.client = chromadb.HttpClient(host=settings.chroma_host, port=settings.chroma_port,
                                          settings=ChromaSettings(anonymized_telemetry=False))

    def collection(self):
        return self.client.get_collection(self.settings.collection)

    def metadata(self) -> dict[str, object]:
        return dict(self.collection().metadata or {})

    def embed(self, text: str) -> list[float]:
        return embed_text(text, self.settings)

    @staticmethod
    def _asks_for_old_version(question: str) -> bool:
        return bool(re.search(
            r"\b(?:19|20)\d{2}\b|older|old version|previous version|superseded|repealed",
            question,
            flags=re.I,
        ))

    @staticmethod
    def _version_filter(question: str) -> dict[str, object] | None:
        """Select explicitly requested versions instead of merely allowing all years."""
        periods = re.findall(r"\b((?:19|20)\d{2})[-\u2013]((?:19|20)?\d{2})\b", question)
        if periods:
            versions = list(dict.fromkeys(f"{start}-{end[-2:]}" for start, end in periods))
            return {"doc_version": {"$in": versions}}
        years = list(dict.fromkeys(re.findall(r"\b(?:19|20)\d{2}\b", question)))
        if years:
            versions = []
            for year in years:
                versions.extend([year, *(f"{year}-{month:02d}" for month in range(1, 13)),
                                 f"{year}-{(int(year) + 1) % 100:02d}"])
            return {"doc_version": {"$in": versions}}
        if ChromaRetriever._asks_for_old_version(question):
            return {"superseded": True}
        return {"superseded": False}

    def retrieve(self, question: str, k: int) -> list[Passage]:
        if k <= 0:
            return []
        collection = self.collection()
        query: dict[str, object] = {
            "query_embeddings": [self.embed(question)],
            "n_results": k,
            "include": ["documents", "metadatas", "distances"],
        }
        version_filter = self._version_filter(question)
        if version_filter is not None:
            query["where"] = version_filter
        result = collection.query(**query)
        documents = (result.get("documents") or [[]])[0]
        metadatas = (result.get("metadatas") or [[]])[0]
        distances = (result.get("distances") or [[]])[0]
        ids = (result.get("ids") or [[]])[0]
        passages: list[Passage] = []
        for chunk_id, text, metadata, distance in zip(ids, documents, metadatas, distances):
            metadata = metadata or {}
            passages.append(Passage(
                chunk_id=str(chunk_id),
                text=str(text or ""),
                source=str(metadata.get("source", "unknown")),
                section=str(metadata.get("section", "Document")),
                page=int(metadata["page"]) if metadata.get("page") is not None else None,
                score=max(-1.0, min(1.0, 1.0 - float(distance))),
            ))
        return passages
