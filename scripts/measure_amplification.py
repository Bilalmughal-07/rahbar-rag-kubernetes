"""Measure text-token amplification from benchmark extraction caches.

Install eval/requirements-benchmark.txt first. cl100k_base is an explicitly chosen
measurement tokenizer, not a claim about Ollama's embedding tokenizer.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import tiktoken

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "indexer"))
from pipeline.chunk import chunk  # noqa: E402
from pipeline.models import Document, Page  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cache-dir", type=Path, default=ROOT / ".cache/benchmark")
    parser.add_argument("--out", type=Path,
                        default=ROOT / "docs/evidence/current/token-amplification.json")
    args = parser.parse_args()
    documents = []
    for path in args.cache_dir.glob("document-*.json"):
        value = json.loads(path.read_text(encoding="utf-8"))
        value["pages"] = [Page(**page) for page in value["pages"]]
        documents.append(Document(**value))
    if not documents:
        parser.error("no extracted document caches; run benchmark_retrieval.py first")
    encoding = tiktoken.get_encoding("cl100k_base")
    original = sum(len(encoding.encode(page.text)) for doc in documents for page in doc.pages)
    rows = []
    for size, overlap in [(200, 25), (400, 50), (600, 75)]:
        stored = sum(len(encoding.encode(piece.text)) for doc in documents
                     for piece in chunk(doc, size, overlap))
        rows.append({"size_words": size, "overlap_words": overlap, "stored_tokens": stored,
                     "token_amplification": stored / original})
    result = {"tokenizer": "cl100k_base (measurement tokenizer; not the nomic embedding tokenizer)",
              "original_tokens": original, "configurations": rows}
    args.out.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
