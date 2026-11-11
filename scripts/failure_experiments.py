"""Run four isolated failure experiments; never edits the serving collection."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from dataclasses import replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "indexer"), str(ROOT / "api"), str(ROOT / "eval")]
from pipeline.chunk import chunk  # noqa: E402
from pipeline.config import IndexerSettings  # noqa: E402
from pipeline.embed import embed  # noqa: E402
from pipeline.models import Chunk, Document, Page  # noqa: E402
from pipeline.store import get_client  # noqa: E402
from app.config import Settings  # noqa: E402
from app.retrieval.chroma import ChromaRetriever  # noqa: E402
from run_eval import load_golden, recall_at_k  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--benchmark", type=Path,
                        default=ROOT / "docs/evidence/current/chunking-benchmark-versioned.json")
    parser.add_argument("--out", type=Path,
                        default=ROOT / "docs/evidence/current/failure-experiments-versioned.json")
    parser.add_argument("--fixed-collection", help="reuse an existing fixed-100 experiment collection")
    args = parser.parse_args()
    out = args.out
    benchmark = json.loads(args.benchmark.read_text())
    baseline = next(row for row in benchmark["configurations"] if row["size"] == 400)
    docs = []
    for path in (ROOT / ".cache/benchmark").glob("document-*.json"):
        value = json.loads(path.read_text())
        value["pages"] = [Page(**p) for p in value["pages"]]
        docs.append(Document(**value))
    scanned = next(d for d in docs if d.source.startswith("faculty-entrepreneurship"))
    before = len(chunk(scanned, 400, 50))
    broken = Document(scanned.source, scanned.doc_version, scanned.superseded,
                      pages=[Page(p.source, p.page, "" if p.ocr else p.text, p.ocr)
                             for p in scanned.pages])
    results = {"scope": "isolated collections and in-memory copies; serving index unchanged",
        "A_extraction": {"source": scanned.source, "intervention": "discard OCR text on image-only pages",
                         "ocr_pages": sum(p.ocr for p in scanned.pages),
                         "chunks_with_ocr": before, "chunks_without_ocr": len(chunk(broken, 400, 50))}}
    golden = load_golden(ROOT / "eval/golden.yaml")
    settings = Settings(retriever="chroma", chroma_host="127.0.0.1", chroma_port=8002,
                        collection=baseline["collection"], ollama_url="http://localhost:11434")
    retriever = ChromaRetriever(settings)
    rows = []
    source_rows = []
    for question in golden:
        passages = [p.model_dump() for p in retriever.retrieve(question["question"], 1)
                    if p.score >= 0.55]
        score = recall_at_k(question.get("relevant", []), passages, 5)
        if score is not None:
            rows.append(score)
        if not retriever._asks_for_old_version(question["question"]):
            raw = retriever.collection().query(query_embeddings=[retriever.embed(question["question"])],
                n_results=5, include=["metadatas", "distances"])
            old = [m for m, distance in zip(raw["metadatas"][0], raw["distances"][0])
                   if m.get("superseded") and 1 - distance >= 0.55]
            source_rows.append({"id": question["id"], "old_passages_without_filter": old})
    results["C_retrieval"] = {"intervention": "TOP_K=1", "baseline_recall_at_5": baseline["recall_at_5"],
                              "broken_recall_at_5": sum(rows) / len(rows)}
    results["E_source"] = {"intervention": "remove superseded=False filter on current-version questions",
                          "questions_retrieving_old_evidence": sum(bool(r["old_passages_without_filter"]) for r in source_rows),
                          "per_question": source_rows,
                          "interpretation": "Old evidence retrieval demonstrates exposure, not proof that an answer is factually wrong."}
    out.write_text(json.dumps(results, indent=2), encoding="utf-8")
    pieces = []
    for doc in docs:
        for page in doc.pages:
            words = page.text.split()
            for start in range(0, len(words), 100):
                text = " ".join(words[start:start + 100])
                digest = hashlib.sha256(f"{doc.source}:{page.page}:{start}".encode()).hexdigest()[:16]
                pieces.append(Chunk(digest, text, doc.source, "Document", page.page,
                                    doc.doc_version, doc.superseded))
    config = IndexerSettings("nomic-embed-text", "127.0.0.1", 8002,
        f"rahbar-failure-fixed100-{int(time.time())}", "corpus/raw", 100, 0, "http://localhost:11434")
    if args.fixed_collection:
        config = replace(config, collection=args.fixed_collection)
        collection = get_client(config).get_collection(config.collection)
        if collection.count() != len(pieces):
            raise ValueError("reused fixed-window collection has a different chunk count")
    else:
        vectors = []
        for start in range(0, len(pieces), 32):
            vectors.extend(embed([p.text for p in pieces[start:start + 32]], config))
            print(f"fixed-100 embedded {min(start + 32, len(pieces))}/{len(pieces)}", flush=True)
        collection = get_client(config).create_collection(config.collection,
                                                          metadata={"hnsw:space": "cosine"})
        for start in range(0, len(pieces), 500):
            batch = pieces[start:start + 500]
            collection.add(ids=[p.id for p in batch], documents=[p.text for p in batch],
                           embeddings=vectors[start:start + 500], metadatas=[p.metadata() for p in batch])
    retriever.settings = Settings(retriever="chroma", chroma_host="127.0.0.1", chroma_port=8002,
                                  collection=config.collection, ollama_url="http://localhost:11434")
    scores = []
    for q in golden:
        passages = [p.model_dump() for p in retriever.retrieve(q["question"], 5) if p.score >= 0.55]
        value = recall_at_k(q.get("relevant", []), passages, 5)
        if value is not None:
            scores.append(value)
    results["B_chunking"] = {"intervention": "fixed 100-word windows, no overlap or section headings",
        "collection": config.collection, "chunks": len(pieces),
        "baseline_recall_at_5": baseline["recall_at_5"], "broken_recall_at_5": sum(scores) / len(scores),
        "limitation": "Section loss contributes to this metric, which matches source and section."}
    out.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
