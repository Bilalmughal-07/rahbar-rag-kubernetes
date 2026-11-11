"""Smoke-test the real browser entry point, including the routed API POST.

This intentionally targets the Ingress URL, not a direct UI or API Service
port-forward. A successful HTML response alone cannot prove that the UI can
submit a question, so the test also validates POST /api/ask and its citations.
"""

from __future__ import annotations

import argparse
import json
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


def request(url: str, method: str = "GET", body: bytes | None = None,
            host: str | None = None) -> tuple[int, str]:
    headers = {"Accept": "application/json, text/html"}
    if host:
        headers["Host"] = host
    if body is not None:
        headers["Content-Type"] = "application/json"
    req = Request(url, data=body, headers=headers, method=method)
    try:
        with urlopen(req, timeout=120) as response:
            return response.status, response.read().decode("utf-8", errors="replace")
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        return exc.code, detail
    except URLError as exc:
        raise RuntimeError(f"could not reach {url}: {exc.reason}") from exc


def run(base_url: str, host: str | None, question: str) -> None:
    base = base_url.rstrip("/")
    page_status, page_body = request(f"{base}/", host=host)
    if page_status != 200 or "rahbar" not in page_body.casefold():
        raise AssertionError(f"Ingress UI check failed: HTTP {page_status}: {page_body[:300]}")

    payload = json.dumps({"question": question}).encode("utf-8")
    api_status, api_body = request(f"{base}/api/ask", "POST", payload, host)
    if api_status != 200:
        raise AssertionError(f"Ingress API check failed: HTTP {api_status}: {api_body[:500]}")
    try:
        answer = json.loads(api_body)
    except json.JSONDecodeError as exc:
        raise AssertionError(f"/api/ask did not return JSON: {api_body[:500]}") from exc

    required = {"answer", "citations", "answered_from_context", "retrieved"}
    missing = required.difference(answer)
    if missing:
        raise AssertionError(f"/api/ask response is missing fields: {sorted(missing)}")
    if not answer["answered_from_context"]:
        raise AssertionError(f"real routing question abstained unexpectedly: {api_body[:500]}")
    if not answer["citations"]:
        raise AssertionError("/api/ask answered without citations")

    print(json.dumps({
        "ui_status": page_status,
        "api_status": api_status,
        "answered_from_context": answer["answered_from_context"],
        "citations": answer["citations"],
        "retrieved_count": len(answer["retrieved"]),
    }, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", required=True, help="Ingress base URL")
    parser.add_argument("--host", help="Host header for a named Ingress rule")
    parser.add_argument(
        "--question",
        default="What attendance is required to sit the final exam?",
    )
    args = parser.parse_args()
    try:
        run(args.base_url, args.host, args.question)
    except (AssertionError, RuntimeError, TimeoutError) as exc:
        print(f"routing smoke failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
