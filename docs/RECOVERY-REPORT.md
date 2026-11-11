# RAHBAR recovery and submission report

Verified on 2026-11-11 on the transferred Windows 11 project. This report separates
executed local checks from GitHub publication that has not been authorized or run.

## Current outcome

RAHBAR is running in namespace `rahbar` on the existing Docker Desktop cluster:
API 3/3, UI 1/1, Redis 1/1 and Chroma 1/1. All three PVCs remain Bound. The final
index contains 1,454 vectors with complete required metadata. Health, readiness,
metrics, real browser submissions, cache behavior and API-pod recovery were checked.

The browser entry point currently exposed by port-forward is **http://localhost:8082/**.
Ingress is exposed on port 8080 and expects `Host: rahbar.local`; automated tests
sent that header. The Windows guide explains how to restart those forwards.

Read [architecture](ARCHITECTURE.md), [Windows setup/recovery](WINDOWS-RECOVERY.md),
[pipeline measurements](PIPELINE.md), [CI/CD](CI-CD.md), and
[the contribution plan](GIT-CONTRIBUTION-PLAN.md) for the supporting instructions.

## Repository and transfer audit

Project root: `C:\Hanan\University\Semester 5\Software Construction and Development\Assignments\rahbar`.
The original assignment PDF and STARTER.md were inspected as the requirements.
The ZIP preserved `.git`, source, corpus files and the substantial uncommitted
implementation; no `git init`, reset, history rewrite or source replacement was used.

| History location | Commit | Recorded author |
| --- | --- | --- |
| Local dev and local main | d4ac276, Initial RAHBAR starter kit | Muhammad Bilal <muhammadbilalali774@gmail.com> |
| Remote main | 643415969cfc5618952ef9f5f0394c638b8dac16, Initial commit | Muhammad Bilal <muhammadbilalali774@gmail.com> |

There are **two distinct reachable commits**, on separate history roots. Local dev
itself contains one commit. Remote main contains only README.md and there is no
remote dev branch. GitHub maps its existing commit to `Bilalmughal-07`; the local
starter has not been pushed, so its GitHub association is not yet independently
verified. No existing commit is attributed to Hanan.

GitHub authentication is `ranahananshafique`, with repository push permission and
no admin permission. Repository-local Git identity is still `Bilalmughal-07` with
Bilal's email. Authentication and authorship were checked separately and neither
was changed. The partners confirmed the GitHub identities and verified commit emails
listed in [the contribution plan](GIT-CONTRIBUTION-PLAN.md). This confirmation does
not establish authorship of any uncommitted change; both partners must confirm
their genuine contributions and the exact proposed author before each approved commit.

No commits, pushes, pull requests, merges, collaborator changes, global Git changes,
Docker resets or Kubernetes resets were performed. The safe future integration
plan preserves both roots on a separate branch/worktree after approved commits.

## Prerequisites and deployment

Docker Engine 29.7.2, Compose 5.5.1, kubectl, Docker Desktop Kubernetes v1.36.1,
Python 3.13.14 and Node 25.2.1 were available. Node is not needed to build this
starter's plain HTML/JavaScript UI. The Kubernetes node was Ready, with 16 CPUs
and approximately 7.6 GiB allocatable memory. The host had 16 GiB total memory.

Both `qwen3:1.7b` and `nomic-embed-text` were present. An API pod reached Ollama
through `host.docker.internal:11434`. No working prerequisite was reinstalled.
Missing support components were installed: ingress-nginx controller v1.12.1 and
Metrics Server v0.8.0. The local Metrics Server certificate exception is documented.

The API, indexer and UI images were built locally. Docker Desktop's image mirror
served the images to its kind node; `crictl pull` refreshed the RAHBAR dev tags
after rebuilding them. Final application image names match the manifests:
`rahbar-api:dev`, `rahbar-indexer:dev` and `rahbar-ui:dev`.

Chroma and Redis now run as UID/GID 10001 with read-only root filesystems. Their
data PVCs remain writable. Existing root-owned files needed one narrowly scoped
ownership migration; file contents and PVCs were preserved. The temporary loader
and permission pods were removed after verification, with their records retained.

## Corpus, indexing and quality

All 11 local downloads matched the SHA-256 values in the corpus index. The official
URLs and provenance remain in `corpus/MANIFEST.md`; this is local byte verification,
not a claim that the upstream website will always serve identical HTML bytes.

| Final index property | Observed result |
| --- | --- |
| Sources | 9 PDFs and 2 HTML pages |
| PDF coverage | 400 pages visited |
| OCR | 44 designated pages, 33 producing text, 11 empty pages recorded |
| Chunks/vectors | 1,454 / 1,454 |
| Embeddings | nomic-embed-text, 768 dimensions |
| Index version | 6c5a18b1c31b580b |
| Missing required chunk metadata | 0 |
| Superseded chunks | 149, including 76 from the 2023 rules |
| Final full Job duration | 382.3 seconds |

The security-updated extractor produced the identical chunk IDs/text and index
version as the preserved pre-update collection. A full backup collection,
`rahbar-before-pdf-update-20261111`, remains in Chroma. The completed original Job
and the final `indexer-security-verified` Job are retained as execution evidence.

The final real-corpus evaluation used 22 questions through Ingress, with **zero
cache hits** in that run. The 19 answerable questions are unchanged from the
earlier set; two absent-topic questions were added to its existing injection probe.

| Metric | Previous-machine baseline | Final measured run |
| --- | ---: | ---: |
| Recall@3 | 0.526316 | 0.684211 |
| Recall@5 | 0.684211 | 0.894737 |
| Citation validity | 1.0 | 1.0 |
| Must-abstain correctness | 1.0 | 1.0 |

The final run returned 17 grounded answers and declined both remaining answerable
questions plus all three must-abstain questions. One response used the safe provider
fallback. Full responses, citations and timings are in
[`evaluation-details.json`](evidence/current/evaluation-details.json).
The gate passed against the previous baseline before the new shipped baseline was
written. Both `eval/results.json` and `eval/baseline.json` now contain the improved
measured run; the identical previous-machine result and baseline are represented
by `evidence/current/baseline-previous-machine.json`.

The main quality repair was explicit version selection: a request for 2022–23 now
filters to that report period instead of permitting every year. Citation schemas
also restrict citation tuples to actual retrieved passages, reducing avoidable
formatting fallbacks. Cache namespaces include policy and generation settings so
older answers cannot bypass those changes on an unchanged corpus.

Three chunk configurations were measured before and after the version repair.
Final recall@5 was 0.789474 at 200/25 words, **0.894737 at 400/50**, and 0.789474
at 600/75. The existing 400/50 setting remains justified. Token amplification was
measured separately with a named tokenizer; words were not mislabeled as tokens.

Eight cache pairs ruled out thresholds through 0.95: the 2023/2026 summer-policy
pair had similarity 0.951054. The default is now 0.98, the lowest tested threshold
with no false hits. A live question produced a cache miss followed by a hit. A
separate indexer sentinel test verified scoped expiry and preservation of unrelated
keys after adding the required narrow indexer-to-Redis policy.

## Executed verification

| Check | Actual result / evidence |
| --- | --- |
| Linux Python 3.12.16, matching CI | 18 API tests + 10 indexer/evaluation tests pass; 74.41% API coverage; `python312-checks.txt` |
| Windows Python 3.13.14 | Same 28 tests pass; 74.41% API coverage |
| Ruff / mypy | Pass; mypy checks 34 source files with its crashing cache disabled |
| Strict production manifests | 29 valid, 0 invalid, 0 errors; `kubeconform-final.txt` |
| Final API/indexer/UI scans | 0 fixable HIGH/CRITICAL findings each; `trivy-*-verified.json` |
| Real Ingress and direct UI proxy | HTML 200 and cited POST 200 through both routes |
| Real browser JavaScript flow | Two form submissions used POST /api/ask and returned 200; `browser-evidence.json` |
| Health/readiness/metrics | All 200, Chroma count 1,454, Redis reachable; invalid short question 422 |
| NetworkPolicy | UI→API succeeds, UI→Chroma times out, API→Chroma returns 200 |
| Embedding pin | Isolated wrong-model pod stayed 0/1 Ready; readiness 503 named the conflict |
| Pod loss | One API pod replaced; cited request succeeded and three endpoints were restored |
| Rollout/rollback | Visible temporary UI marker served, then rollout undo restored the original UI |
| HPA | Three replicas, min 3/max 8, numeric CPU readings rather than unknown |
| Submission checker | 164 passed, 3 history warnings, 0 failures |
| Local ephemeral kind fixture stack | 11 vectors, six questions, all four metrics 1.0; final images tested |

All evidence paths in the table are under `docs/evidence/current/`. The disposable
`rahbar-ci` cluster was removed after saving its results. Docker Desktop remains
Ready on its original context, with RAHBAR and all three PVCs intact. Tests and
scans are local verification, not fabricated GitHub Actions runs.

The original scans found 5 API, 24 indexer and 67 UI fixable HIGH findings. Fixed
versions of FastAPI/Starlette, PDF libraries, zlib and the digest-pinned nginx base
were built and rescanned. No Docker control socket was given to the scanner;
it scanned exported image archives. One automatic approval review rejected the
initial socket-mount method, and the safer archive method completed successfully.

## Screenshots and evidence checklist

- [x] [Actual grounded answer screenshot](evidence/current/ui-grounded.png)
- [x] [Actual absent-topic screenshot](evidence/current/ui-abstention.png)
- [x] Browser POST method/status record
- [x] Index metadata, corpus hashes and backup record; raw index logs remain local-only
- [x] Current metrics, ready endpoints, PVCs and HPA readings
- [x] Real evaluation, raw responses, chunk/cache experiments and failure experiments
- [x] Python 3.12 coverage, lint/type checks, manifest validation and image scans
- [x] API pod recovery and UI rollout/rollback
- [x] Isolated kind fixture evaluation and cleanup record
- [ ] GitHub CI/CD run URLs, Docker Hub SHA image pages and branch-protection screenshots
- [ ] Actual failed-then-passing PR gate/blocked-merge screenshots

No unchecked external evidence has been invented. Use
[the external submission checklist](evidence/github-submission-checklist.md) after
the approved repository work.

## Remaining owner decisions and genuine contributions

The GitHub repository is private. It has no repository Actions secrets, no
environments, no Actions runs, no remote dev branch, and unprotected main. The
assignment's successful CD link and SHA-tagged Docker Hub image links do not exist
yet. The current collaborator cannot configure protection without owner/admin
access. Instructor access to the private repository needs owner confirmation.

Before any commit, confirm who actually performed each contribution and the
correct verified email. Proposed responsibilities are Bilal for corpus/indexing
and evaluation, Hanan for API/Kubernetes/CI, and each person's actual documentation
contributions. This is a proposed work/review split, not a retroactive authorship
claim. See the focused Conventional Commit plan, including safe integration of
both roots, in `GIT-CONTRIBUTION-PLAN.md`. Do not invent authors or commits to
remove the checker's history warnings.

Owner-approved remaining work is to review the prepared changes, confirm authors,
approve focused commits/pushing dev, configure Docker Hub secrets and main
protection, run CI, open/review the PR, approve main integration/CD, and collect
the real remote evidence. None of those external mutations was attempted.
The partners must also confirm their own personal engineering retrospective
and time spent; an individual greater-than-one-hour failure story was not invented.

## Practical limits

The automatic citation metric checks that a citation was retrieved, not that every
claim is correct. Recall matches source/section and ignores page, so broad Document
sections are coarse. Manual review still found an annual-report answer describing
an admissions table in response to a graduation question. Two answerable questions
declined; exact-term and HTML-table recall@5 remain 0.5. These limitations are not
hidden by the passing gate, and the original questions were not rewritten to inflate
their scores. Hybrid retrieval, better HTML extraction and generation review are
reasonable future improvements.

The store operation replaces a collection when reindexing, so a brief readiness
gap is possible; atomic publication is not implemented. This is a single-node
local deployment, not distributed database availability. The true memory peak was
not captured before container exit; sampled usage is reported honestly. The CPU
HPA measures API overhead while inference runs on the host. Cache threshold testing
covered only eight pairs. Package pins and saved image identities help reproduce
the run, but transitive packages, security repositories and upstream documents can
change over time. Registry publication by commit SHA remains an approved next step.

## Authorized submission progress

The earlier no-dev/no-Actions observations describe the initial audit.
See [submission status](SUBMISSION-STATUS.md) for subsequent authorized commits,
actual CI links, fresh verification and remaining approval/owner requirements.
