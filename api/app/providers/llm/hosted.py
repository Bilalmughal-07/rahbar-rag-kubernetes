"""Hosted free-tier provider (Groq, Google AI Studio, OpenRouter). Yours to build.

The key arrives as LLM_API_KEY from a Kubernetes Secret created on the command
line. It never appears in a file you commit, and never in a log line.
"""

from __future__ import annotations

import httpx

from ...config import Settings
from ...schemas import Answer, Passage
from .common import build_messages, parse_answer


class HostedProvider:
    name = "hosted"

    def __init__(self, settings: Settings) -> None:
        self.settings = settings   # hosted_base_url, llm_model, llm_api_key, temperature

    def generate(self, question: str, passages: list[Passage]) -> Answer:
        if not self.settings.hosted_base_url or not self.settings.llm_api_key:
            raise RuntimeError("HOSTED_BASE_URL and LLM_API_KEY are required for hosted mode")
        payload = {
            "model": self.settings.llm_model,
            "messages": build_messages(question, passages),
            "temperature": self.settings.temperature,
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": "rahbar_answer", "schema": Answer.model_json_schema()},
            },
        }
        headers = {"Authorization": f"Bearer {self.settings.llm_api_key}"}
        url = f"{self.settings.hosted_base_url.rstrip('/')}/chat/completions"
        try:
            response = httpx.post(url, json=payload, headers=headers, timeout=120.0)
            response.raise_for_status()
            choices = response.json().get("choices") or []
            content = choices[0].get("message", {}).get("content", "") if choices else ""
            return parse_answer(content)
        except httpx.HTTPError as exc:
            raise RuntimeError(f"hosted generation failed: {exc}") from exc
