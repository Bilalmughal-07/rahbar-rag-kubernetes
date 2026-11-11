"""Stage 5: Store. The only code in the whole system that writes to Chroma."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from .config import IndexerSettings
from .models import Chunk


def get_client(settings: IndexerSettings) -> Any:
    import chromadb  # the thin client, from chromadb-client in requirements.txt
    from chromadb.config import Settings as ChromaSettings

    return chromadb.HttpClient(host=settings.chroma_host, port=settings.chroma_port,
                               settings=ChromaSettings(anonymized_telemetry=False))


def store(chunks: list[Chunk], vectors: list[list[float]], settings: IndexerSettings) -> int:
    """Write every chunk with its vector and metadata, and record the embedding model
    and vector dimension in the collection metadata (section 4.4). Return the count."""
    if not chunks:
        raise ValueError("refusing to write an empty index")
    if len(chunks) != len(vectors):
        raise ValueError(f"chunk/vector count mismatch: {len(chunks)} != {len(vectors)}")
    dimensions = {len(vector) for vector in vectors}
    if len(dimensions) != 1 or not next(iter(dimensions), 0):
        raise ValueError("all embeddings must have the same non-zero dimension")

    client = get_client(settings)
    try:
        client.delete_collection(settings.collection)
    except Exception:
        pass
    index_version = hashlib.sha256(
        json.dumps([(c.id, c.text) for c in chunks], sort_keys=True).encode("utf-8")
    ).hexdigest()[:16]
    collection = client.create_collection(
        name=settings.collection,
        metadata={"hnsw:space": "cosine", "embed_model": settings.embed_model,
                  "dimension": next(iter(dimensions)), "index_version": index_version},
    )
    ids = [chunk.id for chunk in chunks]
    documents = [chunk.text for chunk in chunks]
    metadatas = [chunk.metadata() for chunk in chunks]
    if hasattr(collection, "upsert"):
        collection.upsert(ids=ids, documents=documents, embeddings=vectors, metadatas=metadatas)
    else:  # small fakes used by unit tests and older Chroma clients
        collection.add(ids=ids, documents=documents, embeddings=vectors, metadatas=metadatas)
    _invalidate_old_cache(settings, index_version)
    return int(collection.count())


def _invalidate_old_cache(settings: IndexerSettings, index_version: str) -> None:
    """Remove cache entries from previous indexes without making Redis mandatory."""
    try:
        import redis
        client = redis.Redis.from_url(settings.redis_url, decode_responses=True,
                                      socket_timeout=1.5)
        prefix = f"rahbar:cache:{index_version}:"
        keys = [key for key in client.scan_iter(match="rahbar:cache:*")
                if not str(key).startswith(prefix)]
        if keys:
            client.delete(*keys)
    except Exception:
        # An unavailable cache must not make a successful index write fail.
        return
