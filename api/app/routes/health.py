"""Liveness and readiness (section 4.3). They answer different questions."""

from __future__ import annotations

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get("/healthz")
def healthz() -> dict[str, str]:
    """Is the process alive? Must never touch Chroma, Redis or the LLM."""
    return {"status": "alive"}


@router.get("/readyz")
def readyz(request: Request, response: Response) -> dict[str, object]:
    settings = request.app.state.settings
    checks: dict[str, object] = {}
    failures: list[str] = []
    retriever = request.app.state.retriever

    if settings.retriever == "stub":
        checks["retriever"] = "stub"
    else:
        try:
            metadata = retriever.metadata()
            count = int(retriever.collection().count())
            checks["chroma"] = {"reachable": True, "count": count}
            if count == 0:
                failures.append("chroma collection is empty")
            indexed_model = str(metadata.get("embed_model", ""))
            checks["embedding_model"] = {"indexed": indexed_model, "configured": settings.embed_model}
            if indexed_model != settings.embed_model:
                failures.append(
                    f"embedding model conflict: index={indexed_model!r}, api={settings.embed_model!r}"
                )
        except Exception as exc:
            failures.append(f"chroma unavailable: {exc}")
            checks["chroma"] = {"reachable": False, "error": str(exc)}

    cache = getattr(request.app.state, "cache", None)
    if settings.retriever == "stub" or cache is None or not settings.cache_enabled:
        checks["redis"] = "stub" if settings.retriever == "stub" else "disabled"
    elif cache.ping():
        checks["redis"] = "reachable"
    else:
        failures.append("redis unavailable")
        checks["redis"] = "unreachable"

    if failures:
        return JSONResponse(status_code=503, content={"status": "not_ready", "checks": checks,
                                                       "failures": failures})
    return {"status": "ready", "checks": checks}
