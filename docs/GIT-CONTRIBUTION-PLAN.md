# Git audit and contribution plan

Verified 2026-11-11. No commits, pushes, pull requests, identity changes, or merges
were performed during this audit. Fetching added remote-tracking history only.

## Existing history

| Reference | Commit | Author | Subject |
| --- | --- | --- | --- |
| Local dev, local main | d4ac276 | Muhammad Bilal <muhammadbilalali774@gmail.com> | Initial RAHBAR starter kit |
| origin/main | 643415969cfc5618952ef9f5f0394c638b8dac16 | Muhammad Bilal <muhammadbilalali774@gmail.com> | Initial commit |

There are two distinct reachable commits, both authored by Bilal. Each is a root
commit; the remote root contains only README.md. There is no remote dev branch.
GitHub's commit API associates 6434159 with Bilalmughal-07. The local starter
commit has not been pushed, so its GitHub association cannot yet be verified.
No existing commit is attributed to Hanan. Do not invent earlier contributions.

The authenticated GitHub login is `ranahananshafique` and has repository push
permission. Repository-local user.name is `Bilalmughal-07` and user.email is
`muhammadbilalali774@gmail.com`. Authentication does not determine authorship.

## Confirmed identities; unconfirmed authorship

The partners supplied these GitHub-verified commit emails on 2026-11-11.
This is partner confirmation, not independent access to GitHub's private email settings.

| Partner | Confirmed GitHub account | Confirmed verified commit email |
| --- | --- | --- |
| Bilal | `Bilalmughal-07` | `muhammadbilalali774@gmail.com` |
| Hanan | `ranahananshafique` | `ranahananshafique.581@gmail.com` |

Both partners confirmed the package responsibilities below on 2026-11-11,
covering genuine contributions and work to be performed and verified. The commit
author records the confirmed responsible contributor submitting this AI-assisted
package; it does not assert that all included code was independently human-written
or retroactively assign original authorship of Codex edits. AI assistance remains
disclosed in [AI-USAGE.md](AI-USAGE.md). Historical human-only authorship is not claimed.

Git history integration is jointly authorized and jointly assigned. Hanan is the
authenticated operator responsible for executing the Codex-assisted integration;
no co-author trailer will be invented solely from joint responsibility.

## Proposed eight commit packages

These are the unchanged eight logical packages: **134 exact files**, with no
duplicates. The partners authorized local commits, history integration, pushing
only dev, running CI, and opening a PR. Main merge, registry publication and CD
remain subject to separate explicit approval. No equal-count allocation is implied.

Verification below refers to recorded full-tree recovery checks, not separately
tested intermediate commits. This cleanup rechecks documentation and inventory;
it does not rerun application, cluster or image tests.

### 1. `chore(build): pin runtime dependencies and container tooling` (12 files)

Purpose: Pin runtime dependencies and define reproducible image/check builds.

Verification: Recorded Python 3.12 checks and final image scans.

Confirmed responsible commit author: **Hanan** (AI assistance disclosed).

Exact files:

- `.gitignore`
- `api/requirements.txt`
- `api/requirements-dev.txt`
- `indexer/requirements.txt`
- `docs/AI-USAGE.md`
- `api/.dockerignore`
- `api/Dockerfile`
- `indexer/.dockerignore`
- `indexer/Dockerfile`
- `ui/Dockerfile`
- `mypy.ini`
- `scripts/Dockerfile.checks`

### 2. `feat(indexer): implement versioned corpus extraction and indexing` (14 files)

Purpose: Implement corpus provenance, extraction, chunking and versioned storage.

Verification: Recorded 10 indexer/evaluation tests, corpus hashes and 1,454-vector index metadata.

Confirmed responsible commit author: **Bilal** (AI assistance disclosed).

Exact files:

- `corpus/fetch.py`
- `indexer/pipeline/chunk.py`
- `indexer/pipeline/clean.py`
- `indexer/pipeline/config.py`
- `indexer/pipeline/embed.py`
- `indexer/pipeline/extract.py`
- `indexer/pipeline/models.py`
- `indexer/pipeline/run.py`
- `indexer/pipeline/store.py`
- `docs/CORPUS.md`
- `corpus/sources.yaml`
- `corpus/MANIFEST.md`
- `indexer/tests/test_pipeline_stages.py`
- `docs/adr/0002-structure-aware-chunking.md`

### 3. `feat(api): implement grounded answers with version-aware retrieval and caching` (20 files)

Purpose: Implement grounded answers, explicit document versions and isolated semantic caching.

Verification: Recorded 18 API tests, 74.41% coverage, live citations and cache probes.

Confirmed responsible commit author: **Hanan** (AI assistance disclosed).

Exact files:

- `api/app/config.py`
- `api/app/main.py`
- `api/app/providers/llm/hosted.py`
- `api/app/providers/llm/ollama.py`
- `api/app/retrieval/base.py`
- `api/app/retrieval/chroma.py`
- `api/app/retrieval/stub.py`
- `api/app/routes/ask.py`
- `api/app/routes/health.py`
- `api/app/routes/metrics.py`
- `api/app/schemas.py`
- `api/app/services/answer.py`
- `api/tests/test_starter.py`
- `api/app/providers/llm/common.py`
- `api/app/services/cache.py`
- `api/app/services/embedding.py`
- `api/tests/test_answer_service.py`
- `api/tests/test_provider_schema.py`
- `docs/adr/0003-redis-semantic-cache.md`
- `docs/adr/0004-llm-provider-and-data-governance.md`

### 4. `test(eval): add quality gates and reproducible retrieval experiments` (14 files)

Purpose: Add quality gates and measured retrieval, cache and failure experiments.

Verification: Recorded uncached 22-question evaluation and chunk/cache/failure measurements.

Confirmed responsible commit author: **Bilal** (AI assistance disclosed).

Exact files:

- `eval/run_eval.py`
- `eval/fixtures/README.md`
- `docs/PIPELINE.md`
- `docs/FAILURE-ANALYSIS.md`
- `eval/test_run_eval.py`
- `eval/golden.yaml`
- `eval/baseline.json`
- `eval/results.json`
- `eval/fixtures/baseline.fixture.json`
- `eval/requirements-benchmark.txt`
- `scripts/benchmark_cache.py`
- `scripts/benchmark_retrieval.py`
- `scripts/failure_experiments.py`
- `scripts/measure_amplification.py`

### 5. `fix(deploy): restore Kubernetes deployment and API routing` (16 files)

Purpose: Restore deployment, persistent storage access, network policies and both API routes.

Verification: Recorded 29 valid manifests, routing/browser checks, pod replacement and rollback.

Confirmed responsible commit author: **Hanan** (AI assistance disclosed).

Exact files:

- `ui/nginx.conf`
- `k8s/base/hpa.yaml`
- `k8s/base/ingress.yaml`
- `k8s/base/kustomization.yaml`
- `k8s/base/namespace.yaml`
- `k8s/base/networkpolicy.yaml`
- `k8s/base/resources.yaml`
- `k8s/base/secret.placeholder.yaml`
- `k8s/base/services.yaml`
- `k8s/overlays/dev/kustomization.yaml`
- `k8s/overlays/dev/ollama-egress.yaml`
- `k8s/overlays/prod/kustomization.yaml`
- `k8s/corpus-loader.yaml`
- `k8s/volume-permissions.yaml`
- `scripts/routing_smoke.py`
- `docs/adr/0001-indexer-as-job.md`

### 6. `ci: add gated build scan evaluation and deployment workflows` (3 files)

Purpose: Prepare gated build, scan, fixture evaluation and publication workflows.

Verification: Recorded local Python 3.12 and kind fixture checks; remote Actions/CD remain unrun.

Confirmed responsible commit author: **Hanan** (AI assistance disclosed).

Exact files:

- `.github/workflows/ci.yml`
- `.github/workflows/cd.yml`
- `docs/CI-CD.md`

### 7. `docs: document architecture recovery and submission requirements` (9 files)

Purpose: Document architecture, recovery, contribution constraints and submission requirements.

Verification: Documentation references and file inventory rechecked during this cleanup.

Confirmed responsible commit author: **Bilal** (AI assistance disclosed).

Exact files:

- `README.md`
- `docs/ENGINEERING-NOTES.md`
- `docs/ARCHITECTURE.md`
- `docs/GIT-CONTRIBUTION-PLAN.md`
- `docs/INDEXING-REPORT.md`
- `docs/RECOVERY-REPORT.md`
- `docs/WINDOWS-RECOVERY.md`
- `docs/evidence/README.md`
- `docs/evidence/github-submission-checklist.md`

### 8. `docs(evidence): retain verified results and browser evidence` (46 files)

Purpose: Retain selected measured results and genuine browser evidence.

Verification: Recorded recovery evidence reviewed; these are local results, not remote CI/CD evidence.

Confirmed responsible commit author: **Hanan** (AI assistance disclosed).

Exact files:

- `docs/evidence/current/api-endpointslices.yaml`
- `docs/evidence/current/baseline-previous-machine.json`
- `docs/evidence/current/browser-evidence.json`
- `docs/evidence/current/cache-benchmark.json`
- `docs/evidence/current/cache-invalidation.txt`
- `docs/evidence/current/cache-live.json`
- `docs/evidence/current/chunking-benchmark-versioned.json`
- `docs/evidence/current/chunking-benchmark.json`
- `docs/evidence/current/cluster-final.txt`
- `docs/evidence/current/corpus-pvc-index-hash.txt`
- `docs/evidence/current/endpoint-probes.json`
- `docs/evidence/current/evaluation-details.json`
- `docs/evidence/current/evaluation-final.txt`
- `docs/evidence/current/failure-experiments-versioned.json`
- `docs/evidence/current/failure-experiments.json`
- `docs/evidence/current/fixture-cleanup.txt`
- `docs/evidence/current/fixture-cluster.txt`
- `docs/evidence/current/fixture-evaluation.json`
- `docs/evidence/current/fixture-evaluation.txt`
- `docs/evidence/current/fixture-node-final.txt`
- `docs/evidence/current/fixture-routing.txt`
- `docs/evidence/current/image-identities.txt`
- `docs/evidence/current/index-backup.json`
- `docs/evidence/current/index-metadata.json`
- `docs/evidence/current/kubeconform-final.txt`
- `docs/evidence/current/kubectl-top-final.txt`
- `docs/evidence/current/metrics-final.txt`
- `docs/evidence/current/network-policy-final.txt`
- `docs/evidence/current/pin-mismatch-pod.yaml`
- `docs/evidence/current/pin-mismatch.txt`
- `docs/evidence/current/pod-recovery.txt`
- `docs/evidence/current/python312-checks.txt`
- `docs/evidence/current/resource-samples.txt`
- `docs/evidence/current/rollout-rollback.txt`
- `docs/evidence/current/routing-ingress-final.txt`
- `docs/evidence/current/routing-ui-proxy-final.txt`
- `docs/evidence/current/submission-check.txt`
- `docs/evidence/current/tests-api.txt`
- `docs/evidence/current/tests-indexer-eval.txt`
- `docs/evidence/current/token-amplification.json`
- `docs/evidence/current/trivy-api-verified.json`
- `docs/evidence/current/trivy-indexer-verified.json`
- `docs/evidence/current/trivy-ui-verified.json`
- `docs/evidence/current/ui-abstention.png`
- `docs/evidence/current/ui-grounded.png`
- `docs/evidence/version-pair.md`

## Local-only exclusions (48 files; preserve on disk)

These files are excluded from all eight proposed commits. Do not delete them.
They include duplicate/intermediate results, temporary support downloads, raw
build records, historical command records and the assignment handout.

- `Assignment 02, RAHBAR Grounded RAG on Kubernetes.pdf`
- `docs/evidence/branch-protection.md`
- `docs/evidence/current/api-build-final.txt`
- `docs/evidence/current/api-build-verified.txt`
- `docs/evidence/current/assignment-extracted.txt`
- `docs/evidence/current/citation-schema-probe.json`
- `docs/evidence/current/cluster-initial.txt`
- `docs/evidence/current/coverage-api-python312.xml`
- `docs/evidence/current/coverage-api.xml`
- `docs/evidence/current/dependencies-update.txt`
- `docs/evidence/current/evaluation-after-citation-schema-details.json`
- `docs/evidence/current/evaluation-after-citation-schema.json`
- `docs/evidence/current/evaluation-after-schema.txt`
- `docs/evidence/current/evaluation-before-schema-details.json`
- `docs/evidence/current/evaluation-before-schema.json`
- `docs/evidence/current/evaluation.json`
- `docs/evidence/current/evaluation.txt`
- `docs/evidence/current/git-status.txt`
- `docs/evidence/current/indexer-build-verified.txt`
- `docs/evidence/current/indexer-build.txt`
- `docs/evidence/current/indexer-cgroup.txt`
- `docs/evidence/current/ingress-controller.yaml`
- `docs/evidence/current/kubeconform.txt`
- `docs/evidence/current/maintenance-pods.json`
- `docs/evidence/current/metrics-patch.json`
- `docs/evidence/current/metrics-server.yaml`
- `docs/evidence/current/mypy-fresh.txt`
- `docs/evidence/current/mypy.txt`
- `docs/evidence/current/network-policy-probe.txt`
- `docs/evidence/current/node-metrics.json`
- `docs/evidence/current/production-rendered.yaml`
- `docs/evidence/current/python312-checks-build.txt`
- `docs/evidence/current/results-previous-machine.json`
- `docs/evidence/current/resume-indexer.json`
- `docs/evidence/current/rollout-build.txt`
- `docs/evidence/current/routing-initial.txt`
- `docs/evidence/current/routing-warm.txt`
- `docs/evidence/current/ruff.txt`
- `docs/evidence/current/trivy-api.json`
- `docs/evidence/current/trivy-indexer.json`
- `docs/evidence/current/trivy-ui.json`
- `docs/evidence/current/ui-build-final.txt`
- `docs/evidence/current/ui-build-verified.txt`
- `docs/evidence/endpoints.txt`
- `docs/evidence/hpa.txt`
- `docs/evidence/indexing.md`
- `docs/evidence/kubectl-top.md`
- `docs/evidence/routing.md`

## Before any approved commit

1. Obtain both partners' confirmation of genuine contributions and responsibility.
   Reviewing AI output alone is not original authorship. Confirm the actual author's
   exact name and GitHub-verified email for the approved package.
2. Inspect `git diff` and `git diff --cached`; stage only that contribution.
3. Check `git config --local user.name`, `git config --local user.email`, and
   `git var GIT_AUTHOR_IDENT` separately from `gh api user --jq .login`.
4. Set repository-local identity only when authorized and needed. Never change
   global identity, disconnect accounts, rewrite history, or force-push.
5. After an approved push, inspect the commit API's `author.login` and commit URL.
   A missing/wrong mapping must be reported, not silently rewritten.

## Preserving the two history roots

Keep development on local dev and leave local/remote main untouched. After the
working changes have been reviewed and committed with approval, use a separate
integration branch or worktree to merge origin/main with
`--allow-unrelated-histories`, resolving README.md while preserving both roots.
Review that merge before any approved push or PR. Do not run that merge in this
dirty working tree and do not replace remote main with the local root.

Git's default HTTPS helper could not authenticate noninteractively even though
GitHub CLI could. Fetch succeeded with a command-scoped helper:

```powershell
git -c credential.helper= -c 'credential.helper=!gh auth git-credential' fetch origin
```

This changes no persistent credential configuration. A successful local audit
is not evidence of a successful Actions run or Docker Hub publication.
