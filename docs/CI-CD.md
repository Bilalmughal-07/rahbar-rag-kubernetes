# CI/CD

RAHBAR has two GitHub Actions workflows. Neither workflow publishes or deploys
from a pull request.

## CI (`.github/workflows/ci.yml`)

CI runs on pushes to `dev`, pull requests targeting `main`, and as a reusable
workflow called by CD. The jobs form this dependency graph:

```text
lint ─┐
test ─┼─> build ─> scan ─┐
manifests ┘             ├─> e2e-eval
```

- `lint` runs Ruff and the Python 3.12 mypy configuration in `mypy.ini`.
- `test` runs the API coverage gate at 60%, then indexer and evaluation tests.
  Unit tests use stubs and do not need Ollama, a GPU, or live websites.
- `manifests` renders `k8s/overlays/prod` and validates it with strict
  kubeconform.
- `build` builds API, indexer, and UI images but never pushes them.
- `scan` rebuilds the three images in its own runner and runs Trivy against the
  actual images. Fixable HIGH or CRITICAL findings fail the job.
- `e2e-eval` creates a fresh kind cluster, installs a pinned ingress-nginx
  controller, loads the fixture corpus, indexes it with deterministic hash
  embeddings and the stub provider, and runs `eval/run_eval.py` through the
  Ingress. Failure diagnostics include pods, events, Job logs, API logs, and
  ingress-controller logs.

The fixture baseline is `eval/fixtures/baseline.fixture.json`; it is never
compared with the production baseline in `eval/baseline.json`.

Recovery fixed three executed/source-confirmed workflow setup problems: the kind action
defaults to `chart-testing`, so both workflows now explicitly name the cluster `kind`
to match image-load commands; the pinned kind Ingress manifest requires an
`ingress-ready=true` node label, now applied before installation; and fixture evaluation
starts its own port-forward because the earlier smoke step's EXIT trap stops that
step's forward. Mypy runs without its cache because cache serialization crashed during
the recovery checks; type checking remains enabled.

The final patched images were tested locally in a separate kind v1.31.4 cluster using
a workspace-only kubeconfig. The three-document fixture Job completed with 11 vectors,
the Ingress smoke test passed, and all four fixture metrics were 1.0. Evidence is in
`docs/evidence/current/fixture-evaluation.json` and `fixture-routing.txt`. This is local
end-to-end verification, not a claim that a GitHub Actions run passed.

GitHub inspection on 2026-11-11 found no Actions runs, no repository Actions secrets,
only the remote main branch, and `main.protected=false`. The current collaborator
has push permission but no administration permission. Publishing, protection settings,
PR evidence and the requested successful CD run remain pending approved repository
work and owner configuration. No secret values were requested or printed.

## CD (`.github/workflows/cd.yml`)

CD runs only on pushes to `main`:

```text
reusable CI -> build-push -> deploy
```

`build-push` authenticates to Docker Hub with Actions Secrets and publishes:

```text
<DOCKERHUB_USERNAME>/rahbar-api:<github.sha>
<DOCKERHUB_USERNAME>/rahbar-indexer:<github.sha>
<DOCKERHUB_USERNAME>/rahbar-ui:<github.sha>
```

`deploy` creates a new ephemeral kind cluster, pulls those exact SHA-tagged
images, loads them into kind, applies a temporary production-overlay copy with
the SHA substituted, indexes the fixture corpus, waits for rollouts, verifies
the image references, and sends a real `POST /api/ask` through the Ingress.
It does not use the Windows Docker Desktop kubeconfig. `KUBECONFIG_B64` is not
required because GitHub-hosted runners cannot reach the local cluster and the
assignment requires an ephemeral deployment target.

## Required GitHub configuration

Configure these repository or environment secrets without putting values in
Git:

- `DOCKERHUB_USERNAME`: Docker Hub namespace.
- `DOCKERHUB_TOKEN`: Docker Hub access token with permission to push the three
  repositories.

No GitHub secret is required for CI. `production` may be configured as a
protected environment so deployment requires an explicit environment approval.

Protect `main` with a ruleset requiring pull requests, at least one approval,
passing `lint`, `test`, `manifests`, `build`, `scan`, and `e2e-eval` checks, and
blocking force-pushes and direct pushes.

## Inspecting and reproducing

1. Open the repository's Actions tab and select `ci` or `cd`.
2. Inspect the job summary and uploaded manifest/coverage artifacts.
3. For local fixture evaluation, use the existing Docker Desktop or kind
   cluster and run the fixture commands documented in the workflow; production
   indexing remains a separate Kubernetes Job.
4. Record only actual run URLs, Docker Hub image links, measured evaluation
   results, and SHA values in the submission evidence checklist.

## Authorized submission progress

The earlier no-dev/no-Actions observations describe the initial audit.
See [submission status](SUBMISSION-STATUS.md) for subsequent authorized commits,
actual CI links, fresh verification and remaining approval/owner requirements.

Real CI also exposed a removed nested setup-trivy@v0.2.1 dependency in the
older v0.28.0 action. The workflow now pins official trivy-action v0.36.0 at
ed142fd0673e97e23eac54620cfb913e5ce36c25. Its pinned setup/cache dependencies
and default Trivy v0.70.0 release were verified through the official repositories.
All three HIGH/CRITICAL, ignore-unfixed and exit-code gates remain unchanged.
