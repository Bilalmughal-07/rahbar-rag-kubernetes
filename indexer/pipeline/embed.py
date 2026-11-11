"""Stage 4: Embed. One vector per chunk, from the pinned model only."""

from __future__ import annotations

import os
import hashlib
import math
import re

import httpx

from .config import IndexerSettings


def _hash_embedding(text: str, dimensions: int = 512) -> list[float]:
    """Return a deterministic test-only vector without network/model dependencies.

    This backend is used only by the offline CI fixture job. Production indexing keeps
    the pinned Ollama embedding model as the default provider.
    """
    vector = [0.0] * dimensions
    tokens = re.findall(r"\w+", text.casefold())
    features = tokens + [" ".join(tokens[i:i + 2]) for i in range(len(tokens) - 1)]
    for token in features:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % dimensions
        vector[index] += 1.0
    norm = math.sqrt(sum(value * value for value in vector))
    return [value / norm for value in vector] if norm else vector


def embed(texts: list[str], settings: IndexerSettings) -> list[list[float]]:
    """Embed with settings.embed_model and nothing else.

    With Ollama: POST {ollama_url}/api/embed with {"model": ..., "input": [texts]}
    returns {"embeddings": [[...], ...]}. Batch the calls; one request per chunk is slow.
    """
    if not texts:
        return []
    if settings.embed_provider == "hash":
        return [_hash_embedding(text) for text in texts]
    if settings.embed_provider != "ollama":
        raise ValueError(f"unknown EMBED_PROVIDER {settings.embed_provider!r}")
    batch_size = max(1, int(os.environ.get("EMBED_BATCH_SIZE", "32")))
    vectors: list[list[float]] = []
    endpoint = f"{settings.ollama_url.rstrip('/')}/api/embed"
    for start in range(0, len(texts), batch_size):
        batch = texts[start:start + batch_size]
        try:
            response = httpx.post(
                endpoint,
                json={"model": settings.embed_model, "input": batch},
                timeout=180.0,
            )
            response.raise_for_status()
            payload = response.json()
        except httpx.HTTPError as exc:
            raise RuntimeError(
                f"embedding request failed for model {settings.embed_model} "
                f"(batch {start // batch_size + 1}): {exc}"
            ) from exc
        batch_vectors = payload.get("embeddings")
        if batch_vectors is None and len(batch) == 1:
            batch_vectors = [payload.get("embedding")]
        if (not isinstance(batch_vectors, list) or len(batch_vectors) != len(batch)
                or any(not vector for vector in batch_vectors)):
            raise RuntimeError(
                f"Ollama returned an invalid embedding response for batch "
                f"{start // batch_size + 1}"
            )
        vectors.extend([[float(value) for value in vector] for vector in batch_vectors])
    return vectors
