"""Measure cache-threshold false hits on explicit equivalent/different pairs."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "api"))
from app.services.cache import cosine  # noqa: E402

PAIRS = [
    ("What attendance is required to sit the final exam?",
     "What minimum class attendance is needed for the final examination?", True),
    ("What does grade A mean?", "What is the meaning of an A grade?", True),
    ("How many credit hours are required in the PhD roadmap?",
     "What is the total credit requirement for the PhD roadmap?", True),
    ("What does grade A mean?", "What does grade B mean?", False),
    ("What does grade A mean?", "What does grade F mean?", False),
    ("What is the fee refund rule after one week?",
     "What is the fee refund rule after four weeks?", False),
    ("What is the summer attendance rule in the 2023 policy?",
     "What is the summer attendance rule in the 2026 policy?", False),
    ("What is the CGPA for readmission?", "What is the CGPA for graduation?", False),
]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ollama", default="http://localhost:11434")
    parser.add_argument("--out", default="docs/evidence/current/cache-benchmark.json")
    args = parser.parse_args()
    texts = [text for left, right, _ in PAIRS for text in (left, right)]
    response = httpx.post(f"{args.ollama}/api/embed",
        json={"model": "nomic-embed-text", "input": texts}, timeout=180)
    response.raise_for_status()
    vectors = response.json()["embeddings"]
    rows = [{"left": a, "right": b, "equivalent": expected,
             "similarity": cosine(vectors[2 * i], vectors[2 * i + 1])}
            for i, (a, b, expected) in enumerate(PAIRS)]
    thresholds = [{"threshold": threshold,
                   "false_hits": sum(not r["equivalent"] and r["similarity"] >= threshold
                                     for r in rows),
                   "true_hits": sum(r["equivalent"] and r["similarity"] >= threshold
                                    for r in rows)}
                  for threshold in (0.85, 0.90, 0.92, 0.95, 0.98, 1.0)]
    selected = next(row["threshold"] for row in thresholds if row["false_hits"] == 0)
    result = {"model": "nomic-embed-text", "pairs": rows, "thresholds": thresholds,
              "lowest_tested_zero_false_hit_threshold": selected,
              "limitation": "Eight labeled pairs; no claim of zero false hits on unseen questions."}
    Path(args.out).write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
