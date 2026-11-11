# RAHBAR

[![CI](https://github.com/Bilalmughal-07/rahbar-rag-kubernetes/actions/workflows/ci.yml/badge.svg)](https://github.com/Bilalmughal-07/rahbar-rag-kubernetes/actions/workflows/ci.yml)

RAHBAR is a grounded question-answering service for a versioned university document corpus.
The indexer runs as a one-shot process and writes chunks and embedding metadata to Chroma;
the API retrieves evidence, validates model output, cites only retrieved passages, and
abstains when evidence is below the relevance floor.

## Architecture

```text
corpus -> indexer Job -> Chroma StatefulSet <- API Deployment (3 replicas) <- Ingress
                                                    |                    \
                                                    v                     v
                                                  Redis                 UI nginx
```

The API never indexes on startup. `EMBED_MODEL` is read from the same ConfigMap by the API
and indexer, and the API refuses readiness when collection metadata disagrees.

See [architecture](docs/ARCHITECTURE.md), [Windows recovery](docs/WINDOWS-RECOVERY.md),
and the [Git history and contribution plan](docs/GIT-CONTRIBUTION-PLAN.md).
The [recovery report](docs/RECOVERY-REPORT.md) is the current verification and submission checklist.
Fresh recovery evidence is under `docs/evidence/current/`; older evidence is historical.
The UI is the starter's plain HTML/JavaScript chat page, not a React build.

## Local validation

The repository targets Python 3.12. The Windows implementation work was verified with
the Docker Desktop Kubernetes cluster, including the real Chroma/Ollama/OCR pipeline;
the unit suites also run locally with the installed compatible Python packages.

```powershell
python -m pytest -q api
python -m pytest -q indexer
python -m pytest -q eval
python scripts/check_submission.py
```

The API and indexer have separate pinned requirement files because the API only needs the
thin Chroma HTTP client while the indexer additionally needs extraction and OCR libraries.
Both use `chromadb-client==1.0.12`, matching the `chromadb/chroma:1.0.12` server required by
the assignment.

## Kubernetes apply order

For Docker Desktop, enable its built-in Kubernetes cluster, install the official Metrics
Server if `kubectl top` is unavailable, and ensure an nginx Ingress controller exists. Build/load
the three images, run `kubectl apply -k k8s/overlays/dev`,
wait for Chroma and Redis, copy the verified corpus into the `corpus-data` PVC, then run the
indexer Job. No secret value belongs in Git. A Minikube cluster can use the same manifests
with the equivalent cluster start and image-load commands.

The initial dev Job is suspended until the corpus is copied; explicitly resume it as
documented in the Windows guide. Ollama host mode needs no API-key Secret. Create the
Secret only when using a hosted provider. The Makefile requires bash/WSL and is not a
native PowerShell entry point.

### Windows access through Ingress

The browser entry point is the Ingress, not a direct port-forward to `svc/ui`. A direct UI
port-forward bypasses the `/api` Ingress route; if the running UI image has no internal API
proxy, `POST /api/ask` reaches static nginx and returns HTTP 405. Use these PowerShell
commands instead:

```powershell
# Verify the controller, Ingress, and backend endpoints.
kubectl get pods -n ingress-nginx
kubectl get ingressclass nginx
kubectl get ingress rahbar -n rahbar
kubectl get endpoints api ui -n rahbar

# If ingress-nginx is not installed, install the pinned controller once.
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.12.1/deploy/static/provider/cloud/deploy.yaml
kubectl wait --namespace ingress-nginx --for=condition=Ready pod `
  --selector=app.kubernetes.io/component=controller --timeout=300s

# Keep this terminal open. The controller's port 80 is exposed locally as 8080.
kubectl -n ingress-nginx port-forward service/ingress-nginx-controller 8080:80
```

In an Administrator PowerShell, map the Ingress host for browser access:

```powershell
Add-Content -Path "$env:SystemRoot\System32\drivers\etc\hosts" -Value "127.0.0.1 rahbar.local"
```

Open `http://rahbar.local:8080/` in the browser. The UI's same-origin request to
`/api/ask` is then routed by the `rahbar` Ingress to the FastAPI `api` Service. To verify
the exact browser path from another terminal without opening the UI, run:

```powershell
python scripts/routing_smoke.py --base-url http://127.0.0.1:8080 --host rahbar.local
```

This test requires both a successful UI response and a successful cited `POST /api/ask`.
The rebuilt UI also proxies `/api/` internally, with an explicit egress policy and
120-second read timeout. Direct UI access is an additional tested option:

```powershell
kubectl -n rahbar port-forward service/ui 8082:8080
# Open http://localhost:8082/ while the command stays running.
```

Ingress remains the assignment's primary evaluation route.

## API contract

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/healthz` | Process liveness only |
| GET | `/readyz` | Chroma, collection, Redis, and embedding-pin readiness |
| GET | `/metrics` | Prometheus metrics |
| POST | `/api/ask` | `{"question": "..."}` to grounded `AskResponse` |

`POST /api/ask` validates a 3–500 character question, retrieves top-k passages, applies
the relevance floor, uses a schema-constrained provider, retries invalid output once, and
returns a safe abstention/fallback rather than a 500. Cache entries are namespaced by the
indexed content version and never store abstentions or invalid answers.

## Status

Implemented and locally verified: the complete 11-source corpus (400 PDF pages plus two
HTML sources), authentic 2023/2026 policy versions, RapidOCR fallback, 1,454 idempotent
vectors, Chroma retrieval, provider adapters, grounding safeguards, readiness checks,
metrics, semantic cache, 22-question real-corpus evaluation, Kubernetes manifests, CI/CD
workflows, and unit tests. See [CI/CD documentation](docs/CI-CD.md) for workflow
dependencies, fixture evaluation, SHA-tagged Docker images, secrets, and the external
evidence checklist. The current run measured recall@3=0.684, recall@5=0.895,
citation validity=1.0 and abstention correctness=1.0. Python 3.12 checks passed 28 tests
with 74.41% API coverage. Genuine browser screenshots are in `docs/evidence/current/`.
GitHub-hosted CI/CD and Docker Hub publication remain pending approved commits/pushes,
registry secrets and owner configuration. Remote `main` is currently unprotected.
