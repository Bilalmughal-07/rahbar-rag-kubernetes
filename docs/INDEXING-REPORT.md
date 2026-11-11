# Full-corpus indexing report

This is the transferred previous-machine report. For the fresh 2026-11-11 verification,
see [RECOVERY-REPORT.md](RECOVERY-REPORT.md) and `docs/evidence/current/`. The current
run independently reproduced all counts and index version below; its final duration
was 382.3 seconds and its final recall@5 improved to 0.894737 after version-filter fixes.
The older timings and evaluation numbers below remain explicitly historical.

This report records the real Kubernetes verification performed on 2026-11-09.
The verified corpus contains all 11 configured sources: the original ten-source
corpus plus the official 2023 undergraduate academic-rules edition used as the
same-policy version pair for the 2026 edition.

## Corpus coverage

| Metric | Measured value |
|---|---:|
| Sources discovered from `corpus/raw/_index.json` | 11 |
| PDF pages extracted | 400 / 400 |
| HTML documents processed | 2 / 2 |
| OCR-designated PDF pages | 44 |
| OCR pages with text produced | 33 / 44 |
| Empty pages reported | 11 (blank/image-only pages; listed below) |
| Chunks generated | 1,454 |
| Chroma vectors stored | 1,454 |
| Embedding model | `nomic-embed-text` |
| Vector dimension | 768 |
| Index version | `6c5a18b1c31b580b` |
| Kubernetes pipeline duration | 751.2 seconds first run; 749.5 seconds idempotency rerun |

The vector count exactly matches the generated chunk count. Chroma is persistent
on the existing PVC. The second complete Job run against the same 11-source PVC
also left the collection at exactly 1,454 vectors, with the same index version
`6c5a18b1c31b580b`; no duplicate accumulation occurred.

## Per-document result

| Source | Pages | OCR-designated | Empty pages | Chunks/vectors |
|---|---:|---:|---|---:|
| Student Handbook 2026 | 64 | 4 | pages 2, 63 | 286 |
| Faculty Handbook 2026 | 60 | 4 | pages 1, 2, 58, 59 | 190 |
| Undergraduate Academic Rules Handbook 2026 | 58 | 4 | pages 1, 2, 56, 57 | 282 |
| Prospectus Academic Rules | 5 | 0 | none | 25 |
| Annual Report 2023-24 | 85 | 0 | none | 217 |
| Annual Report 2022-23 | 36 | 0 | none | 73 |
| PhD Handbook 2026 | 58 | 0 | none | 265 |
| Fee Structure HTML | 1 logical page | 0 | none | 6 |
| Grading HTML | 1 logical page | 0 | none | 5 |
| Faculty Entrepreneurship and Technical Start-ups Policy | 8 | 8 | none | 29 |
| Undergraduate Academic Rules and Regulations 2023-08 | 26 | 24 | page 3 | 76 |

The scanned entrepreneurship policy produced nonempty OCR text on all 8 pages.
The 2023 rules edition is also image-heavy: two pages had native text and
RapidOCR produced nonempty text on 23 of its 24 OCR-designated pages. Page 3
remained empty and is recorded as an extraction gap rather than silently
omitted. Its remaining 25 pages are represented by 76 chunks. The other ten
empty pages are blank/image-only pages in the three 2026 handbooks and are
listed in the per-document table.

## Runtime and idempotency verification

- Chroma `1/1 Running`; the collection reported 1,454 vectors after both runs.
- The 2026 rules source contributed 282 chunks with `doc_version: 2026-06` and
  `superseded: false`.
- The 2023 rules source contributed 76 chunks with `doc_version: 2023-08` and
  `superseded: true`.
- API, Redis, and UI remained deployed from the existing manifests; no corpus,
  Chroma, or Redis PVC was replaced.
- The indexer uses deterministic chunk IDs and rebuilds the named collection
  from the full manifest. The second Job completed in 749.5 seconds and was the
  required real idempotency check.

## API/evaluation result

The golden set contains 20 real questions, including three version-sensitive
questions grounded in the verified 2023/2026 rules differences. The final live
API run passed the unchanged evaluation gate:

| Metric | Measured value |
|---|---:|
| Questions | 20 |
| Recall@3 | 0.526 |
| Recall@5 | 0.684 |
| Citation validity | 1.000 |
| Abstention correctness | 1.000 |
| Evaluation gate | passed |

The identical historical result and baseline are represented by the retained
`docs/evidence/current/baseline-previous-machine.json`; the main `eval/` files now contain the fresh run. Direct API
checks also verified grounded citations for the 2023 failed-course policy, the
2023 Rule 6.1 summer duration, the 2026 summer attendance rule, and the scanned
entrepreneurship policy. A repeated question returned `cached: true`; `/readyz`
reported Chroma count 1,454 and Redis reachable.

## Remaining extraction note

Eleven PDF pages yielded no text after native extraction and OCR: pages 2 and
63 of Student Handbook 2026; pages 1, 2, 58, and 59 of Faculty Handbook 2026;
pages 1, 2, 56, and 57 of Undergraduate Academic Rules Handbook 2026; and page
3 of the 2023 official rules PDF. They were retained in coverage accounting and
not silently replaced with fabricated text. The remaining 389 PDF pages and
both HTML sources produced content, and all configured sources have nonzero
chunks.
