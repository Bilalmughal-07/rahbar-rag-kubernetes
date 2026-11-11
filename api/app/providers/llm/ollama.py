"""Ollama provider: ollama-host or ollama-incluster (section 3.5). Yours to build."""

from __future__ import annotations

import httpx

from ...config import Settings
from ...schemas import Answer, Passage
from .common import answer_schema, build_messages, parse_answer


class OllamaProvider:
    name = "ollama"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings   # ollama_url, llm_model, temperature

    def generate(self, question: str, passages: list[Passage]) -> Answer:
        payload = {
            "model": self.settings.llm_model,
            "messages": build_messages(question, passages),
            "stream": False,
            # Qwen3 otherwise places its answer in the hidden thinking field;
            # grounded JSON must be returned in message.content for validation.
            "think": False,
            "format": answer_schema(passages),
            "options": {"temperature": self.settings.temperature},
        }
        try:
            response = httpx.post(
                f"{self.settings.ollama_url.rstrip('/')}/api/chat", json=payload, timeout=120.0
            )
            response.raise_for_status()
            message = response.json().get("message", {})
            return parse_answer(message.get("content", ""))
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Ollama generation failed: {exc}") from exc
