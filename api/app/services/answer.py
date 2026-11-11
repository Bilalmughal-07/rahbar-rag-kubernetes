"""Turns a question into an AskResponse. This is where the query pipeline lives.

The version below is the bare minimum that works with the stubs: retrieve,
generate, return. Section 3.2 lists eight steps; this file does two of them.
"""

from __future__ import annotations

import logging
import hashlib
import time
from typing import Any

from ..config import Settings
from ..logjson import request_id_var
from ..providers.llm.base import LLMProvider
from ..retrieval.base import Retriever
from ..routes.metrics import (ABSTENTIONS, CACHE_HITS, CACHE_MISSES, FALLBACKS,
                              GENERATION_LATENCY, RETRIEVAL_LATENCY, TOKENS_IN, TOKENS_OUT)
from ..schemas import Answer, AskResponse, RetrievedRef
from .cache import SemanticCache, never_cache

log = logging.getLogger("rahbar.answer")


def answer_question(
    question: str, retriever: Retriever, provider: LLMProvider, settings: Settings,
    cache: SemanticCache | None = None,
) -> AskResponse:
    follow_up = _is_follow_up(question)
    # A corpus version alone cannot distinguish changed retrieval/generation policy.
    profile = (f"citations-v2/versions-v2/{settings.llm_provider}/{settings.llm_model}/"
               f"{settings.temperature}/{settings.top_k}/{settings.relevance_floor}")
    fingerprint = hashlib.sha256(profile.encode()).hexdigest()[:12]
    index_version = f"{_index_version(retriever)}-{fingerprint}"
    if cache is not None and not follow_up:
        cached = cache.get(question, index_version)
        if cached is not None:
            CACHE_HITS.inc()
            return cached.model_copy(update={"request_id": request_id_var.get(), "cached": True})
        CACHE_MISSES.inc()

    started = time.perf_counter()
    passages = retriever.retrieve(question, k=settings.top_k)
    RETRIEVAL_LATENCY.observe(time.perf_counter() - started)
    passages = [p for p in passages if p.score >= settings.relevance_floor]

    if not passages:
        return _response(question, retriever.name, [], _abstention(), False)

    started = time.perf_counter()
    answer: Answer | None = None
    # Retry exactly once after provider/schema/citation validation failure.
    retry_attempts = 2
    for _attempt in range(retry_attempts):
        try:
            candidate = provider.generate(question, passages)
            answer = _validated(candidate, passages)
            break
        except Exception as exc:
            log.warning("retrying provider validation", extra={"attempt": _attempt + 1})
            log.warning("provider validation failed", extra={"attempt": _attempt + 1,
                                                               "error": str(exc)})
    GENERATION_LATENCY.observe(time.perf_counter() - started)
    TOKENS_IN.inc(max(1, len(question.split()) + sum(len(p.text.split()) for p in passages)))

    if answer is None:
        FALLBACKS.inc()
        answer = _fallback()
    TOKENS_OUT.inc(max(1, len(answer.answer.split())))

    response = _response(question, provider.name, passages, answer, answer.answered_from_context)
    if cache is not None and not never_cache(answer.answered_from_context, follow_up, True):
        cache.put(question, index_version, response)

    log.info(
        "answered",
        extra={
            "retriever": retriever.name,
            "provider": provider.name,
            "top_k": settings.top_k,
            "chunk_ids": [p.chunk_id for p in passages],
            "scores": [round(p.score, 4) for p in passages],
            "answered_from_context": answer.answered_from_context,
        },
    )
    return response


def _is_follow_up(question: str) -> bool:
    return question.strip().casefold().startswith(("and ", "also ", "what about ", "how about "))


def _index_version(retriever: Retriever) -> str:
    metadata: object = getattr(retriever, "metadata", lambda: {})()
    return str(metadata.get("index_version", "unknown")) if isinstance(metadata, dict) else "unknown"


def _validated(value: Any, passages: list[Any]) -> Answer:
    answer = Answer.model_validate(value)
    if answer.answered_from_context and _looks_like_abstention(answer.answer):
        return answer.model_copy(update={
            "answered_from_context": False,
            "citations": [],
            "confidence": "low",
        })
    allowed = {(p.source, p.section, p.page) for p in passages}
    if answer.answered_from_context:
        if not answer.citations or any((c.source, c.section, c.page) not in allowed for c in answer.citations):
            raise ValueError("answer citation does not match retrieved context")
    elif answer.citations:
        raise ValueError("abstention must not contain citations")
    return answer


def _looks_like_abstention(text: str) -> bool:
    normalized = " ".join(text.casefold().split())
    return any(phrase in normalized for phrase in (
        "the corpus does not cover",
        "does not cover it",
        "the evidence does not answer",
        "cannot answer it reliably",
        "not enough information",
        "insufficient evidence",
    ))


def _abstention() -> Answer:
    return Answer(reasoning="No passage cleared the relevance floor.",
                  answer="The corpus does not cover that question, so I cannot answer it reliably.",
                  citations=[], answered_from_context=False, confidence="low")


def _fallback() -> Answer:
    return Answer(reasoning="Provider output failed schema or citation validation.",
                  answer="I could not produce a validated grounded answer from the retrieved evidence.",
                  citations=[], answered_from_context=False, confidence="low")


def _response(question: str, provider: str, passages: list[Any], answer: Answer,
              answered_from_context: bool) -> AskResponse:
    if not answered_from_context:
        ABSTENTIONS.inc()
    return AskResponse(
        request_id=request_id_var.get(), answer=answer.answer, citations=answer.citations,
        answered_from_context=answer.answered_from_context, confidence=answer.confidence,
        retrieved=[RetrievedRef(chunk_id=p.chunk_id, source=p.source, section=p.section,
                                 page=p.page, score=p.score) for p in passages],
        provider=provider,
    )
