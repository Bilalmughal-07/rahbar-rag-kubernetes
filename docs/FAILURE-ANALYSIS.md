# Failure analysis

These are controlled failure experiments to run against fixtures or the real stack. The
diagnostic signals are recorded without inventing results.

## Executed experiments (2026-11-11)

The final version-filter configuration was checked again in
`failure-experiments-versioned.json`: the baseline recall@5 is 0.894737, while both
fixed-100 chunking and top-k=1 produce 0.526316. The OCR result remains 29 to zero
chunks, and removing the version filter still exposes old evidence in five current
questions. The earlier table below records the first configuration, before the
explicit-year repair; it is preserved rather than silently relabeled as the final run.

Run `python scripts/failure_experiments.py` after the versioned retrieval benchmark, with Chroma
forwarded to localhost:8002. It changes isolated collections and in-memory documents,
never the serving index. Current results go to
`docs/evidence/current/failure-experiments-versioned.json`; initial results remain in
`failure-experiments.json`. `--fixed-collection` can reuse the unchanged isolated
fixed-window vectors to repeat retrieval comparisons without regenerating embeddings.

| Stage | Intervention | Observed result | Diagnosis without knowing the cause |
| --- | --- | --- | --- |
| A | Discard OCR text from the eight-page image-only entrepreneurship policy | 29 chunks became zero | Compare page OCR flags, empty-page counts and per-source chunk logs |
| B | Fixed 100-word windows, no overlap, section headings discarded | recall@5 0.684211 to 0.473684 | Inspect chunk boundaries and by-question relevant-section matches |
| C | Retrieve one passage instead of five | recall@5 0.684211 to 0.368421 | Check configured top-k and the logged retrieved IDs/scores |
| E | Remove the superseded filter on current-version questions | Five questions retrieved old evidence | Inspect retrieved version metadata and the query's missing filter |

Experiment B measures both boundary and section-metadata damage: the scorer matches
source/section, so the result is not a pure measurement of window length. Experiment E
demonstrates exposure to old passages, not proof of an incorrect generated answer.
Restore the original structural chunker, top-k=5, OCR and version filter as the remedies.

The embedding-pin diagnostic was also executed in the separate fixture cluster: the
test pod stayed 0/1 Ready and `/readyz` returned HTTP 503 naming indexed `ci-hash-512`
versus configured `deliberately-wrong-model`. Its log and response are in
`docs/evidence/current/pin-mismatch.txt`. The serving deployment's pin was not changed.

## Stage A - extraction
- **What we broke:** Index the image-only PDF without OCR.
- **Symptom:** Empty pages or no useful chunks.
- **Diagnosis:** Compare page `ocr` flags, chunk counts, and indexer JSON logs.
- **Remedy:** Use the pinned RapidOCR ONNX runtime with pdfplumber/pypdfium2 rendering; it avoids system Tesseract, Poppler, and X11 dependencies. Rerun the Job and verify nonempty OCR pages.

## Stage B - chunking
- **What we broke:** Use fixed 100-word chunks with no overlap.
- **Symptom:** Definitions and clauses split; recall@5 falls.
- **Diagnosis:** Compare recall@5 by type and retrieved section/page metadata.
- **Remedy:** Restore structure-aware chunking with measured overlap.

## Stage C - retrieval
- **What we broke:** Set `TOP_K=1` or change `EMBED_MODEL` only on the API.
- **Symptom:** Fewer relevant passages or readiness failure due to pin conflict.
- **Diagnosis:** `/readyz`, conflict logs, retrieval latency, and chunk scores.
- **Remedy:** Restore the shared model pin and measured top-k.

## Stage E - source version
- **What we broke:** Remove the superseded filter and ask a version-sensitive question.
- **Symptom:** An older clause is returned as current.
- **Diagnosis:** Retrieved source/doc_version metadata and request chunk IDs.
- **Remedy:** Restore the default metadata filter.
