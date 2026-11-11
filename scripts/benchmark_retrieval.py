"""Measure three chunk configurations in isolated Chroma collections.

Run from the repository root. Never modifies the serving collection or Redis.
Extraction and embeddings are cached locally by content hash for repeat runs.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from dataclasses import asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "indexer"), str(ROOT / "api"), str(ROOT / "eval")]

from pipeline.chunk import chunk  # noqa: E402
from pipeline.clean import clean  # noqa: E402
from pipeline.config import IndexerSettings  # noqa: E402
from pipeline.embed import embed  # noqa: E402
from pipeline.extract import extract  # noqa: E402
from pipeline.models import Document, Page  # noqa: E402
from pipeline.run import discover_entries  # noqa: E402
from pipeline.store import get_client  # noqa: E402
from app.config import Settings  # noqa: E402
from app.retrieval.chroma import ChromaRetriever  # noqa: E402
from run_eval import load_golden, recall_at_k  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", default="corpus/raw")
    parser.add_argument("--chroma-host", default="127.0.0.1")
    parser.add_argument("--chroma-port", type=int, default=8002)
    parser.add_argument("--ollama", default="http://localhost:11434")
    parser.add_argument("--out", default="docs/evidence/current/chunking-benchmark.json")
    parser.add_argument("--cache-dir", default=".cache/benchmark",
                        help="use a new directory after changing extraction dependencies")
    args = parser.parse_args()
    cache = ROOT / args.cache_dir
    cache.mkdir(parents=True, exist_ok=True)
    documents = []
    for entry in discover_entries(args.corpus):
        path = Path(args.corpus) / str(entry["file"])
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        saved = cache / f"document-{digest}.json"
        if saved.exists():
            value = json.loads(saved.read_text(encoding="utf-8"))
            value["pages"] = [Page(**page) for page in value["pages"]]
            document = Document(**value)
        else:
            document = clean(extract(str(path), str(entry["doc_version"]),
                                     bool(entry.get("superseded", False))))
            document.source_url = str(entry.get("url", ""))
            document.content_hash = digest
            saved.write_text(json.dumps(asdict(document)), encoding="utf-8")
        documents.append(document)
        print(f"extracted {path.name}: {len(document.pages)} pages", flush=True)
    golden = load_golden(ROOT / "eval/golden.yaml")
    original_words = sum(len(page.text.split()) for doc in documents for page in doc.pages)
    results = {"method": "Chroma cosine retrieval, same API version filter and relevance floor",
               "units": "whitespace-separated words (not tokenizer tokens)",
               "golden_sha256": hashlib.sha256((ROOT / "eval/golden.yaml").read_bytes()).hexdigest(),
               "original_words": original_words, "configurations": []}
    stamp = str(int(time.time()))
    for size, overlap in [(200, 25), (400, 50), (600, 75)]:
        pieces = [piece for doc in documents for piece in chunk(doc, size, overlap)]
        settings = IndexerSettings("nomic-embed-text", args.chroma_host, args.chroma_port,
                                   f"rahbar-benchmark-{stamp}-{size}", args.corpus,
                                   size, overlap, args.ollama)
        vectors = []
        for start in range(0, len(pieces), 32):
            batch = pieces[start:start + 32]
            missing = [p for p in batch if not (cache / f"vector-{hashlib.sha256(p.text.encode()).hexdigest()}.json").exists()]
            if missing:
                values = embed([p.text for p in missing], settings)
                for piece, vector in zip(missing, values):
                    saved = cache / f"vector-{hashlib.sha256(piece.text.encode()).hexdigest()}.json"
                    saved.write_text(json.dumps(vector), encoding="utf-8")
            for piece in batch:
                saved = cache / f"vector-{hashlib.sha256(piece.text.encode()).hexdigest()}.json"
                vectors.append(json.loads(saved.read_text(encoding="utf-8")))
            print(f"size={size}: embedded {min(start + 32, len(pieces))}/{len(pieces)}", flush=True)
        collection = get_client(settings).create_collection(settings.collection,
            metadata={"hnsw:space": "cosine", "embed_model": settings.embed_model,
                      "dimension": len(vectors[0])})
        for start in range(0, len(pieces), 500):
            batch = pieces[start:start + 500]
            collection.add(ids=[p.id for p in batch], documents=[p.text for p in batch],
                           embeddings=vectors[start:start + 500],
                           metadatas=[p.metadata() for p in batch])
        retriever = ChromaRetriever(Settings(retriever="chroma", chroma_host=args.chroma_host,
            chroma_port=args.chroma_port, collection=settings.collection, ollama_url=args.ollama))
        rows = []
        for question in golden:
            passages = [p.model_dump() for p in retriever.retrieve(question["question"], 5)
                        if p.score >= 0.55]
            rows.append({"id": question["id"], "type": question.get("type"),
                         "recall_at_3": recall_at_k(question.get("relevant", []), passages, 3),
                         "recall_at_5": recall_at_k(question.get("relevant", []), passages, 5)})
        stored_words = sum(len(p.text.split()) for p in pieces)
        row = {"size": size, "overlap": overlap, "chunks": len(pieces),
               "stored_words": stored_words,
               "word_amplification": stored_words / original_words,
               "collection": settings.collection, "per_question": rows}
        for metric in ["recall_at_3", "recall_at_5"]:
            values = [r[metric] for r in rows if r[metric] is not None]
            row[metric] = sum(values) / len(values)
        results["configurations"].append(row)
        Path(args.out).write_text(json.dumps(results, indent=2), encoding="utf-8")
        print(json.dumps({k: v for k, v in row.items() if k != "per_question"}), flush=True)


if __name__ == "__main__":
    main()
