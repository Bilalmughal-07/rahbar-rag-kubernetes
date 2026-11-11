# Indexing and retrieval pipeline

## Extraction
`extract.py` handles PDF, Markdown, text, and simple HTML. PDF tables are rendered as
pipe-separated rows; pages without a text layer use the pinned RapidOCR ONNX OCR runtime
path and are marked `ocr=true`. The verified corpus run visited 400/400 PDF pages,
processed both HTML sources, and attempted OCR on 44 image-only pages. Thirty-three OCR
pages produced text; eleven blank/image-only pages remain explicitly recorded in the
indexing report.

## Cleaning
Cleaning normalizes line endings and whitespace, removes repeated page headers/footers, and
preserves headings. It deliberately does not remove clause numbers, numeric values, table
pipes, or section text needed for exact-term retrieval and citations.

## Chunking
Chunks are structure-aware: headings establish sections, then paragraphs and sentences are
packed into a word-count target. The default is 400 words with 50 words of same-section
overlap. IDs are deterministic SHA-1 prefixes. The complete run stored 1,454 chunks and
1,454 vectors; the production configuration was not silently changed for the CI fixture.

| Size (words) | Overlap (words) | Measured recall@5 | Chunks stored |
| --- | --- | --- | --- |
| 200 | 25 | 0.789474 | 1,636 |
| 400 | 50 | 0.894737 | 1,454 |
| 600 | 75 | 0.789474 | 1,397 |

These were measured on 2026-11-11 with the existing real golden questions, Ollama
embeddings, separate Chroma collections, the API's version filter and 0.55 relevance
floor. Generation is excluded from this retrieval-only comparison. The 400/50 choice
wins this comparison, rather than being justified by an unmeasured guess. Results and
per-question scores are in `docs/evidence/current/chunking-benchmark-versioned.json`;
reproduce with `python scripts/benchmark_retrieval.py --out docs/evidence/current/chunking-benchmark-versioned.json`
while Chroma is forwarded to localhost:8002. Before the version-filter repair, the
three recall@5 scores were 0.578947, 0.684211 and 0.578947; that initial comparison is
preserved as `chunking-benchmark.json`.
The script caches extracted text under `.cache/benchmark`; use `--cache-dir` with a new
directory for fresh extraction caches
when changing extraction code or dependencies. The recorded experiment used
pdfplumber 0.11.6 before its security update; the final index run verifies the updated
pipeline separately.

The final pdfplumber 0.11.10 run produced the identical content-derived index version
`6c5a18b1c31b580b` and 1,454 chunks as the preserved pre-update collection. This verifies
that chunk IDs and text remained identical across the dependency update for this corpus.

Actual text-token storage amplification is also recorded separately in
`docs/evidence/current/token-amplification.json`: using the explicit `cl100k_base`
measurement tokenizer, 180,067 cleaned input tokens become 163,645 stored text tokens
at 400/50, a ratio of **0.908801**. This tokenizer is not claimed to be nomic's tokenizer.
The ratio is below one because section headings move to metadata and are omitted from
chunk text; it does not prove lossless extraction. The word-count chunk targets are
not mislabeled as tokenizer token counts.

The historical previous-machine byte-footprint measurement was 126,984,992 bytes of Chroma data divided by
22,861,318 bytes of the downloaded raw corpus, or approximately **5.56x**. This includes
Chroma metadata and ANN index overhead as well as vectors; it is a footprint measurement,
not a claim that every byte is embedding payload.
That old byte-footprint figure was not remeasured during recovery; current Chroma
storage also contains preserved backups and isolated experiment collections.

## Embedding
The indexer calls Ollama `/api/embed` with `EMBED_MODEL`. Chroma records model, dimension,
and content-derived `index_version`; the API compares the model before readiness. Chunks
carry `source`, `section`, `page`, `doc_version`, and `superseded`.

The CI fixture job explicitly sets `EMBED_PROVIDER=hash` and `EMBED_MODEL=ci-hash-512`;
this deterministic 512-dimensional backend is test-only and avoids requiring a model
service in ordinary CI. The production ConfigMap remains on Ollama and
`nomic-embed-text`.

## Semantic cache
Redis stores an embedding and validated response under an index-version namespace. The
default threshold is 0.98; follow-ups, abstentions, invalid answers, and cache failures are
not stored. The live verification produced a cache miss followed by a cache hit for
the same grounded question under the current index version.

The 2026-11-11 threshold experiment used eight explicitly labeled pairs. Thresholds
0.85, 0.90, 0.92, 0.95, 0.98 and 1.00 produced 2, 1, 1, 1, 0 and 0 false hits respectively.
The 2023/2026 summer-rule pair had cosine similarity 0.951054 despite asking about
different versions. Thus 0.98 is the lowest tested zero-false-hit threshold. It also
accepted none of the three paraphrase pairs, a deliberate recall tradeoff; exact repeated
questions can still hit. This small test does not establish safety on unseen questions.
Reproduce with `python scripts/benchmark_cache.py`; see `cache-benchmark.json`.

Cache namespaces additionally fingerprint the retrieval/citation policy, provider,
generation model, temperature, top-k and relevance floor. A changed query policy must
not serve an older answer merely because the corpus bytes stayed identical. The
indexer's expiry function was verified through the real NetworkPolicy using sentinel
keys: old cache entries expired, the designated current prefix survived, and an
outside-prefix key survived. Narrow indexer-to-Redis access is required for that step.

## Evaluation method
Evaluation matches normalized `(source, section)` pairs against top-k retrieved references.
It reports recall@3, recall@5, citation validity, abstention correctness, and by-type recall.

The final uncached 22-question Ingress run measured recall@3=0.684211,
recall@5=0.894737, citation validity=1.0 and abstention correctness=1.0. Three questions
must abstain, leaving 19 questions in the recall denominator. Seventeen returned
grounded answers; two answerable questions declined. There was one safe provider
fallback across the whole run. These are pipeline metrics, not proof of factual
correctness: `expect` is retained for human review, and the automatic recall scorer
matches source/section rather than page. Broad `Document` sections are coarse labels.
Per-request responses are preserved in `evaluation-details.json` for review.

`eval/results.json` and `eval/baseline.json` now contain this measured improved run.
The identical previous-machine result and baseline are represented by
`docs/evidence/current/baseline-previous-machine.json`. This raises
the future regression floor; it was not a baseline reduction to hide a failure.
