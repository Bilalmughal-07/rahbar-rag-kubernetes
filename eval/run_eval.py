#!/usr/bin/env python3
"""Score a running RAHBAR against a golden set, and gate CI on the result (section 5).

    python eval/run_eval.py --api http://<ingress>                 # your corpus
    python eval/run_eval.py --api ... --golden eval/fixtures/golden.fixture.yaml
    python eval/run_eval.py --api ... --update-baseline            # after a deliberate improvement

Exit code 0 when every gate passes, 1 when any fails. CI relies on that exit code.

This script talks to the API, reads the golden set, writes results.json, and returns the
evaluation gate exit code.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import httpx
import yaml

HERE = Path(__file__).resolve().parent

# The gate from section 5.4. Change these only with a reason written in docs/PIPELINE.md.
MAX_RECALL5_DROP = 0.05        # recall@5 may fall at most 5 points below the baseline
MIN_CITATION_VALIDITY = 0.95   # at least 95% of citations must match retrieved passages
REQUIRED_ABSTENTION = 1.0      # every must-abstain question must be declined


def load_golden(path: Path) -> list[dict]:
    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    questions = data.get("questions") or []
    if not questions:
        sys.exit(f"no questions in {path}")
    return questions


def ask(client: httpx.Client, api: str, question: str) -> dict:
    """POST one question and return the AskResponse as a dict (see api/app/schemas.py)."""
    response = client.post(f"{api.rstrip('/')}/api/ask", json={"question": question})
    response.raise_for_status()
    return response.json()


def recall_at_k(relevant: list[dict], retrieved: list[dict], k: int) -> float | None:
    """Fraction of the relevant (source, section) pairs found in the top k retrieved.
    Return None when the question has no relevant passages (must-abstain questions)."""
    if not relevant:
        return None
    expected = {(str(item.get("source", "")).strip().casefold(),
                 str(item.get("section", "")).strip().casefold()) for item in relevant}
    found = {(str(item.get("source", "")).strip().casefold(),
              str(item.get("section", "")).strip().casefold())
             for item in retrieved[:k]}
    return len(expected & found) / len(expected)


def citation_validity(response: dict) -> float | None:
    """Fraction of the response's citations that match a passage in response['retrieved'].
    Return None when there are no citations."""
    citations = response.get("citations") or []
    if not citations:
        return None
    retrieved = {(p.get("source"), p.get("section"), p.get("page"))
                 for p in response.get("retrieved", [])}
    valid = sum((c.get("source"), c.get("section"), c.get("page")) in retrieved
                for c in citations)
    return valid / len(citations)


def summarise(rows: list[dict]) -> dict:
    """Overall recall@3, recall@5, citation validity and abstention correctness, plus
    recall@5 broken down by question type. This dict becomes results.json."""
    def average(values: list[float | None]) -> float | None:
        usable = [value for value in values if value is not None]
        return sum(usable) / len(usable) if usable else None

    scored = []
    for row in rows:
        response = row.get("response") or {}
        scored.append({
            "id": row.get("id"),
            "type": row.get("type", "ordinary"),
            "recall_at_3": recall_at_k(row.get("relevant") or [], response.get("retrieved") or [], 3),
            "recall_at_5": recall_at_k(row.get("relevant") or [], response.get("retrieved") or [], 5),
            "citation_validity": citation_validity(response),
            "abstention_correct": (not response.get("answered_from_context", True))
            if row.get("must_abstain", False) else None,
        })
    by_type: dict[str, list[float | None]] = {}
    for row in scored:
        by_type.setdefault(str(row["type"]), []).append(row["recall_at_5"])
    abstain_rows = [row for row in scored if row["abstention_correct"] is not None]
    return {
        "recall_at_3": average([row["recall_at_3"] for row in scored]),
        "recall_at_5": average([row["recall_at_5"] for row in scored]),
        "citation_validity": average([row["citation_validity"] for row in scored]),
        "abstention_correctness": (
            sum(bool(row["abstention_correct"]) for row in abstain_rows) / len(abstain_rows)
            if abstain_rows else 1.0
        ),
        "recall_at_5_by_type": {key: average(value) for key, value in sorted(by_type.items())},
        "per_question": scored,
    }


def gate(results: dict, baseline: dict | None) -> list[str]:
    """Return one message per failed gate (section 5.4); an empty list means pass."""
    failures: list[str] = []
    recall = results.get("recall_at_5")
    if baseline is not None and recall is not None and baseline.get("recall_at_5") is not None:
        if recall < float(baseline["recall_at_5"]) - MAX_RECALL5_DROP:
            failures.append("recall@5 dropped more than 5 percentage points below baseline")
    citation = results.get("citation_validity")
    if citation is not None and citation < MIN_CITATION_VALIDITY:
        failures.append(f"citation validity {citation:.3f} is below {MIN_CITATION_VALIDITY:.2f}")
    if float(results.get("abstention_correctness", 0.0)) < REQUIRED_ABSTENTION:
        failures.append("at least one must-abstain question was answered from context")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate RAHBAR against a golden set.")
    parser.add_argument("--api", required=True, help="base URL, e.g. http://192.168.49.2")
    parser.add_argument("--host", help="Host header, when your Ingress rule names a host")
    parser.add_argument("--golden", type=Path, default=HERE / "golden.yaml")
    parser.add_argument("--baseline", type=Path, default=HERE / "baseline.json")
    parser.add_argument("--out", type=Path, default=HERE / "results.json")
    parser.add_argument("--details-out", type=Path,
                        help="optional per-request responses and timings for evidence review")
    parser.add_argument("--update-baseline", action="store_true",
                        help="write these results as the new baseline")
    args = parser.parse_args()

    questions = load_golden(args.golden)
    rows = []
    headers = {"Host": args.host} if args.host else {}
    with httpx.Client(timeout=120.0, headers=headers) as client:
        for q in questions:
            started = time.perf_counter()
            response = ask(client, args.api, q["question"])
            rows.append({
                "id": q["id"], "type": q.get("type", "ordinary"),
                "must_abstain": bool(q.get("must_abstain", False)),
                "relevant": q.get("relevant") or [],
                "expect": q.get("expect"),
                "response": response,
                "seconds": round(time.perf_counter() - started, 2),
            })
            print(f"  {q['id']:<5} {rows[-1]['seconds']:>6.2f}s  {q['question'][:60]}")

    if args.details_out:
        args.details_out.write_text(json.dumps(rows, indent=2), encoding="utf-8")

    try:
        results = summarise(rows)
        baseline = json.loads(args.baseline.read_text()) if args.baseline.exists() else None
        failures = gate(results, baseline)
    except NotImplementedError as exc:
        print(f"\nnot implemented yet: {exc}")
        return 2

    results["golden"] = str(args.golden)
    results["questions"] = len(rows)
    args.out.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nresults written to {args.out}")
    if args.update_baseline:
        args.baseline.write_text(json.dumps(results, indent=2), encoding="utf-8")
        print(f"baseline updated: {args.baseline}")

    if failures:
        print("\nGATE FAILED")
        for message in failures:
            print(f"  - {message}")
        return 1
    print("\ngate passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
