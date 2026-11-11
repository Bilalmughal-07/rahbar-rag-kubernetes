"""The indexer Job's entry point. It runs once and exits (section 4.2).

    python -m pipeline.run --dummy    # week 1: three fake chunks, no model needed
    python -m pipeline.run            # the real pipeline: extract, clean, chunk, embed, store

Exit code 0 means the index was written; anything else fails the Job, and
Kubernetes retries it up to the Job's backoffLimit.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

from .config import IndexerSettings, get_settings
from .models import Chunk


def log(msg: str, **fields: object) -> None:
    print(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                      "logger": "rahbar.indexer", "msg": msg, **fields}), flush=True)


def _front_matter(path: Path) -> dict[str, str]:
    """Read `key: value` lines between leading '---' markers (used by eval/fixtures)."""
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    meta: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip()
    return meta


def discover(corpus_dir: str, active_only: bool = False) -> list[tuple[Path, str, bool]]:
    """List (path, doc_version, superseded) for every document to index.

    corpus/fetch.py writes _index.json next to the files it downloads; use it when
    present. Otherwise read Markdown front matter (the CI fixtures work this way).
    """
    root = Path(corpus_dir)
    index = root / "_index.json"
    if index.exists():
        entries = json.loads(index.read_text(encoding="utf-8"))
        if active_only:
            entries = [entry for entry in entries if entry.get("active", True)]
        return [(root / e["file"], str(e.get("doc_version", "unknown")),
                 bool(e.get("superseded", False))) for e in entries]
    found = []
    for path in sorted(root.glob("*")):
        if path.suffix.lower() not in {".pdf", ".md", ".html", ".txt"}:
            continue
        if path.name.lower().startswith("readme"):
            continue
        meta = _front_matter(path) if path.suffix.lower() == ".md" else {}
        found.append((path, meta.get("doc_version", "unknown"),
                      meta.get("superseded", "false").lower() == "true"))
    return found


def discover_entries(corpus_dir: str, active_only: bool = False) -> list[dict[str, object]]:
    """Return full fetch metadata while retaining the legacy discover() contract."""
    root = Path(corpus_dir)
    index = root / "_index.json"
    if index.exists():
        entries = json.loads(index.read_text(encoding="utf-8"))
        return [entry for entry in entries if not active_only or entry.get("active", True)]
    return [{"file": str(path.relative_to(root)), "doc_version": version,
             "superseded": old, "name": path.name}
            for path, version, old in discover(corpus_dir, active_only)]


def run_pipeline(settings: IndexerSettings) -> int:
    from .chunk import chunk
    from .clean import clean
    from .embed import embed
    from .extract import extract
    from .store import store

    entries = discover_entries(settings.corpus_dir, settings.active_only)
    documents = [(Path(settings.corpus_dir) / str(entry["file"]),
                  str(entry.get("doc_version", "unknown")),
                  bool(entry.get("superseded", False)), entry) for entry in entries]
    if not documents:
        raise SystemExit(f"no documents found in {settings.corpus_dir}")
    all_chunks: list[Chunk] = []
    coverage: list[dict[str, object]] = []
    for path, doc_version, superseded, entry in documents:
        doc = clean(extract(str(path), doc_version, superseded))
        source_url = str(entry.get("url", ""))
        doc.document_id = hashlib.sha256(
            f"{source_url}\0{doc_version}\0{path.name}".encode("utf-8")
        ).hexdigest()[:16]
        doc.source_url = source_url
        doc.content_hash = str(entry.get("sha256", ""))
        pieces = chunk(doc, settings.chunk_size, settings.chunk_overlap)
        empty_pages = [page.page for page in doc.pages if not page.text.strip()]
        ocr_pages = [page.page for page in doc.pages if page.ocr]
        coverage.append({"source": path.name, "url": source_url, "document_id": doc.document_id,
                         "content_hash": doc.content_hash, "pages": len(doc.pages),
                         "ocr_pages": len(ocr_pages), "empty_pages": empty_pages,
                         "chunks": len(pieces)})
        log("chunked", source=path.name, pages=len(doc.pages), ocr_pages=len(ocr_pages),
            empty_pages=empty_pages, chunks=len(pieces), document_id=doc.document_id)
        all_chunks.extend(pieces)
    log("coverage", document_count=len(coverage), pdf_pages=sum(int(str(row["pages"])) for row in coverage
        if str(row["source"]).lower().endswith(".pdf")),
        html_documents=sum(1 for row in coverage if str(row["source"]).lower().endswith(".html")),
        ocr_pages=sum(int(str(row["ocr_pages"])) for row in coverage), chunks=len(all_chunks),
        documents=coverage)
    vectors = embed([c.text for c in all_chunks], settings)
    return store(all_chunks, vectors, settings)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the RAHBAR index, then exit.")
    parser.add_argument("--dummy", action="store_true", help="write three fake chunks")
    args = parser.parse_args()
    settings = get_settings()
    log("indexer starting", dummy=args.dummy, embed_model=settings.embed_model,
        collection=settings.collection, chroma=f"{settings.chroma_host}:{settings.chroma_port}",
        pod=os.environ.get("HOSTNAME", "-"))
    started = time.perf_counter()
    try:
        if args.dummy:
            from .dummy import write_dummy_index
            from .store import get_client

            count = write_dummy_index(settings, get_client(settings))
        else:
            count = run_pipeline(settings)
    except NotImplementedError as exc:
        log("indexer stage not implemented yet", error=str(exc))
        return 2
    log("indexer finished", chunks=count, seconds=round(time.perf_counter() - started, 1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
