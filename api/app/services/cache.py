"""Redis-backed semantic cache with index-version namespacing."""

from __future__ import annotations

import hashlib
import json
import math
import re
from typing import Any, Callable

from ..config import Settings
from ..schemas import AskResponse


def cosine(a: list[float], b: list[float]) -> float:
    if len(a) != len(b) or not a or not b:
        return -1.0
    denominator = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(x * x for x in b))
    return sum(x * y for x, y in zip(a, b)) / denominator if denominator else -1.0


class SemanticCache:
    def __init__(self, settings: Settings, embedder: Callable[[str], list[float]] | None) -> None:
        self.settings = settings
        self.embedder = embedder
        self.client: Any = None
        if settings.cache_enabled and embedder is not None:
            try:
                import redis
                self.client = redis.Redis.from_url(settings.redis_url, decode_responses=True,
                                                  socket_timeout=1.5)
            except Exception:
                self.client = None

    @property
    def enabled(self) -> bool:
        return self.client is not None and self.embedder is not None

    def ping(self) -> bool:
        if self.client is None:
            return False
        try:
            return bool(self.client.ping())
        except Exception:
            return False

    def _version(self, value: str) -> str:
        return re.sub(r"[^A-Za-z0-9_.-]", "_", value or "unknown")

    def _prefix(self, index_version: str) -> str:
        return f"rahbar:cache:{self._version(index_version)}:"

    def get(self, question: str, index_version: str) -> AskResponse | None:
        if not self.enabled:
            return None
        try:
            query = self.embedder(question)  # type: ignore[misc]
            best: tuple[float, AskResponse] | None = None
            for key in self.client.scan_iter(match=f"{self._prefix(index_version)}*"):
                raw = self.client.get(key)
                if not raw:
                    continue
                entry = json.loads(raw)
                similarity = cosine(query, [float(v) for v in entry["vector"]])
                if similarity >= self.settings.cache_threshold and (best is None or similarity > best[0]):
                    best = (similarity, AskResponse.model_validate(entry["response"]))
            return best[1] if best else None
        except Exception:
            # Cache failure must never make a grounded request fail.
            return None

    def put(self, question: str, index_version: str, response: AskResponse) -> None:
        if not self.enabled:
            return
        try:
            vector = self.embedder(question)  # type: ignore[misc]
            digest = hashlib.sha256(question.strip().casefold().encode("utf-8")).hexdigest()
            key = f"{self._prefix(index_version)}{digest}"
            payload = {"vector": vector, "response": response.model_dump(mode="json")}
            self.client.setex(key, self.settings.cache_ttl_seconds, json.dumps(payload))
        except Exception:
            return

    def invalidate(self, index_version: str) -> None:
        """Expire entries for one index version; new versions are isolated by key."""
        if self.client is None:
            return
        try:
            keys = list(self.client.scan_iter(match=f"{self._prefix(index_version)}*"))
            if keys:
                self.client.delete(*keys)
        except Exception:
            return


def never_cache(answered_from_context: bool, follow_up: bool, validated: bool) -> bool:
    """Central never-cache rule for abstentions, follow-ups, and invalid answers."""
    return follow_up or not answered_from_context or not validated
