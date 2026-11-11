from __future__ import annotations

from pathlib import Path

from pipeline.chunk import chunk
from pipeline.clean import clean
from pipeline.extract import extract
from pipeline.embed import embed
from pipeline.models import Chunk
from pipeline.store import store


def test_markdown_front_matter_is_metadata_not_chunk_text() -> None:
    path = Path(__file__).resolve().parents[2] / "eval" / "fixtures" / "academic-rules-2026.md"
    doc = clean(extract(str(path), "2026", False))
    pieces = chunk(doc, 40, 5)
    assert pieces
    assert all("doc_version:" not in piece.text for piece in pieces)
    assert any(piece.section == "1. Attendance" for piece in pieces)
    assert all(piece.doc_version == "2026" and not piece.superseded for piece in pieces)
    assert all(piece.title for piece in pieces)


def test_chunk_ids_are_deterministic_and_overlap_is_present() -> None:
    path = Path(__file__).resolve().parents[2] / "eval" / "fixtures" / "academic-rules-2026.md"
    doc = clean(extract(str(path), "2026", False))
    first = chunk(doc, 12, 3)
    second = chunk(doc, 12, 3)
    assert [piece.id for piece in first] == [piece.id for piece in second]
    same_section = [piece for piece in first if piece.section == "1. Attendance"]
    assert len(same_section) >= 2
    assert set(same_section[0].text.split()[-3:]) & set(same_section[1].text.split()[:5])


def test_store_records_model_dimension_and_upserts(monkeypatch) -> None:
    class Collection:
        def __init__(self, metadata):
            self.metadata = metadata
            self.rows = {}

        def upsert(self, **kwargs):
            self.rows.update(dict(zip(kwargs["ids"], kwargs["documents"])))

        def count(self):
            return len(self.rows)

    class Client:
        def __init__(self):
            self.collection = None

        def delete_collection(self, name):
            self.collection = None

        def create_collection(self, name, metadata):
            self.collection = Collection(metadata)
            return self.collection

    client = Client()
    monkeypatch.setattr("pipeline.store.get_client", lambda settings: client)
    chunks = [Chunk("c1", "text", "a.md", "1", 1, "2026", False)]
    from pipeline.config import IndexerSettings
    settings = IndexerSettings("test-model", "chroma", 8000, "rahbar", "/tmp", 400, 50,
                               "http://ollama")
    assert store(chunks, [[0.1, 0.2]], settings) == 1
    assert client.collection.metadata["embed_model"] == "test-model"
    assert client.collection.metadata["dimension"] == 2


def test_hash_embedding_is_deterministic_for_offline_fixture_runs() -> None:
    from pipeline.config import IndexerSettings

    settings = IndexerSettings("ci-hash-512", "chroma", 8000, "rahbar", "/tmp", 400, 50,
                               "http://unused", embed_provider="hash")
    first = embed(["academic warning"], settings)[0]
    second = embed(["academic warning"], settings)[0]
    assert len(first) == 512
    assert first == second
