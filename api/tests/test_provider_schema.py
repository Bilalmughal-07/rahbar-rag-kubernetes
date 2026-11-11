"""Regressions for model citation strings that caused valid evidence to fall back."""
from __future__ import annotations

import httpx
import pytest
from jsonschema import ValidationError, validate

from app.config import Settings
from app.providers.llm.common import answer_schema
from app.providers.llm.ollama import OllamaProvider
from app.schemas import Answer, Citation, Passage


def passages() -> list[Passage]:
    return [Passage(chunk_id="a", source="rules.pdf", section="6.1 A long exact heading",
                    page=20, text="The summer term lasts eight weeks.", score=0.9),
            Passage(chunk_id="b", source="handbook.pdf", section="Attendance", page=4,
                    text="Attendance is mandatory.", score=0.8)]


def test_schema_rejects_a_citation_assembled_from_different_passages() -> None:
    evidence = passages()
    answer = Answer(reasoning="", answer="Eight weeks.",
                    citations=[Citation(source="rules.pdf", section=evidence[0].section, page=20)],
                    answered_from_context=True, confidence="high").model_dump()
    schema = answer_schema(evidence)
    validate(answer, schema)
    answer["citations"][0]["section"] = evidence[1].section
    with pytest.raises(ValidationError):
        validate(answer, schema)


def test_ollama_receives_schema_with_exact_retrieved_citation_choices(monkeypatch) -> None:
    evidence = passages()
    expected = Answer(reasoning="", answer="Eight weeks.",
                      citations=[Citation(source="rules.pdf", section=evidence[0].section, page=20)],
                      answered_from_context=True, confidence="high")
    payloads = []

    def post(url, *, json, timeout):
        payloads.append(json)
        return httpx.Response(200, json={"message": {"content": expected.model_dump_json()}},
                              request=httpx.Request("POST", url))

    monkeypatch.setattr(httpx, "post", post)
    result = OllamaProvider(Settings()).generate("How long is summer?", evidence)
    assert result == expected
    choices = payloads[0]["format"]["$defs"]["Citation"]["enum"]
    assert choices == [{"source": p.source, "section": p.section, "page": p.page}
                       for p in evidence]
