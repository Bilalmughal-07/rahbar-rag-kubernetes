"""Small Ollama embedding client shared by Chroma retrieval and the cache."""

from __future__ import annotations

import hashlib
import httpx
import math
import re

from ..config import Settings


def _hash_embedding(text: str, dimensions: int = 512) -> list[float]:
    """Match the indexer's deterministic backend for offline CI fixture evaluation."""
    vector = [0.0] * dimensions
    tokens = re.findall(r"\w+", text.casefold())
    features = tokens + [" ".join(tokens[i:i + 2]) for i in range(len(tokens) - 1)]
    for token in features:
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % dimensions
        vector[index] += 1.0
    norm = math.sqrt(sum(value * value for value in vector))
    return [value / norm for value in vector] if norm else vector


def embed_text(text: str, settings: Settings) -> list[float]:
    if settings.embed_provider == "hash":
        return _hash_embedding(text)
    if settings.embed_provider != "ollama":
        raise ValueError(f"unknown EMBED_PROVIDER {settings.embed_provider!r}")
    try:
        response = httpx.post(
            f"{settings.ollama_url.rstrip('/')}/api/embed",
            json={"model": settings.embed_model, "input": [text]},
            timeout=60.0,
        )
        response.raise_for_status()
        payload = response.json()
    except httpx.HTTPError as exc:
        raise RuntimeError(f"embedding request failed for model {settings.embed_model}: {exc}") from exc
    vectors = payload.get("embeddings")
    if vectors is None and payload.get("embedding") is not None:
        vectors = [payload["embedding"]]
    if not vectors or not vectors[0]:
        raise RuntimeError("embedding provider returned no vector")
    return [float(value) for value in vectors[0]]
