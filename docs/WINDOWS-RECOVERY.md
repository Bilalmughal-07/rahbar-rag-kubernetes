# Windows 11 recovery

Run from the existing `rahbar` repository in PowerShell. These steps target the
Docker Desktop `docker-desktop` context and preserve other projects. The Makefile
uses bash/Minikube and is not the PowerShell recovery entry point.

## Verify prerequisites

```powershell
docker version
docker compose version
kubectl config current-context
kubectl get nodes
kubectl get storageclass
Invoke-RestMethod http://localhost:11434/api/tags
```

Use an already installed Python interpreter. This laptop has Python 3.13; the
application Dockerfiles and CI use Python 3.12. Local checks must report their
actual interpreter rather than claim version parity.

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r api/requirements-dev.txt -r indexer/requirements-dev.txt pytest-cov
.\.venv\Scripts\python.exe corpus/fetch.py --verify
```

Existing `corpus/raw` contains the 11 verified downloads. On a clean clone,
run the fetcher without `--verify` first. Never replace a good local corpus merely
because it is gitignored.

## Build and apply

```powershell
docker build -t rahbar-api:dev api
docker build -t rahbar-indexer:dev indexer
docker build -t rahbar-ui:dev ui
kubectl apply -k k8s/overlays/dev
kubectl apply -f k8s/corpus-loader.yaml
kubectl wait -n rahbar --for=condition=Ready pod/corpus-loader --timeout=180s
kubectl cp corpus/raw/. rahbar/corpus-loader:/corpus
kubectl exec -n rahbar corpus-loader -- sh -c 'ls -lh /corpus; sha256sum /corpus/*'
```

Docker Desktop's image mirror made these built images available to its kind
node on this machine. Verify the actual image IDs and pod events. Other kind
installations may require `kind load docker-image` for each tag; do not assume
a successful build means every cluster has the image.

The dev overlay suspends the initial indexing Job to allow the corpus to be
copied first. Resume explicitly using a patch file, which avoids Windows native
argument quoting problems:

```powershell
New-Item -ItemType Directory -Force .cache | Out-Null
'{"spec":{"suspend":false}}' | Set-Content -Encoding ascii .cache/resume-indexer.json
kubectl patch job indexer -n rahbar --type=merge --patch-file .cache/resume-indexer.json
kubectl logs -n rahbar job/indexer -f
kubectl wait -n rahbar --for=condition=complete job/indexer --timeout=7200s
kubectl rollout status statefulset/chroma -n rahbar --timeout=180s
kubectl rollout status deployment/redis -n rahbar --timeout=180s
kubectl rollout status deployment/api -n rahbar --timeout=180s
kubectl rollout status deployment/ui -n rahbar --timeout=180s
```

Create `.cache` first if it does not exist. Reapplying the dev overlay suspends
the initial Job again; use unique Jobs from `cronjob/reindex` for later deliberate
reindex runs. The current store operation replaces the collection, so do not
promise zero-downtime reindexing.

For an existing completed Job, changes to its pod template are immutable: do not
delete it merely to update Deployments. Render the overlay, omit the completed Job
from that runtime update, and create a new uniquely named Job from the CronJob.
The actual second verification Job is `indexer-security-verified`. Its predecessor
and a full backup collection (`rahbar-before-pdf-update-20261111`) were preserved.

Chroma and Redis now run as UID/GID 10001. If migrating an existing root-written
RAHBAR volume, `kubectl apply -f k8s/volume-permissions.yaml` performs the one-time
ownership change on those two PVCs only. Inspect its completion and database logs;
do not delete or recreate a volume to solve ownership errors. This maintenance
pod is not part of the normal overlay.

## Supporting components

Check for an existing nginx Ingress controller and Metrics Server first. The
recovery used ingress-nginx controller v1.12.1 and Metrics Server v0.8.0.
The downloaded manifests remain local-only and are not required submission files.
Obtain those pinned releases from the official
[ingress-nginx release](https://github.com/kubernetes/ingress-nginx/releases/tag/controller-v1.12.1)
and [Metrics Server release](https://github.com/kubernetes-sigs/metrics-server/releases/tag/v0.8.0). The local Metrics Server patch adds
`--kubelet-insecure-tls` for the kind kubelet certificate; it is a development
exception, not production guidance. Do not reset Kubernetes or replace its CNI.

```powershell
kubectl get pods -n ingress-nginx
kubectl get ingressclass
kubectl top nodes
kubectl get pods,pvc,services,ingress,hpa,jobs -n rahbar
```

## Access and verification

Keep this command running in a separate terminal:

```powershell
kubectl -n ingress-nginx port-forward service/ingress-nginx-controller 8080:80
```

Create `.cache` if needed and keep new evaluation outputs there so the retained
`eval/results.json` and recovery evidence are preserved.

The named Ingress expects `Host: rahbar.local`. Test without editing the system
hosts file:

```powershell
.\.venv\Scripts\python.exe scripts/routing_smoke.py --base-url http://127.0.0.1:8080 --host rahbar.local
.\.venv\Scripts\python.exe eval/run_eval.py --api http://127.0.0.1:8080 --host rahbar.local --out .cache/evaluation-recheck.json
```

For browser access, use an existing `rahbar.local` hosts entry if present, or a
local browser endpoint that supplies the same host. A hosts-file change is not
required for automated evaluation. Direct UI port-forwarding exercises the UI's
internal API proxy and is a useful additional routing check.

```powershell
.\.venv\Scripts\python.exe -m pytest -q api --cov=api/app --cov-fail-under=60
.\.venv\Scripts\python.exe -m pytest -q indexer eval
.\.venv\Scripts\ruff.exe check api indexer eval corpus scripts/benchmark_retrieval.py
.\.venv\Scripts\python.exe -m mypy --cache-dir=nul --config-file mypy.ini api/app indexer/pipeline
.\.venv\Scripts\python.exe scripts/check_submission.py
```

`--cache-dir=nul` avoids a reproduced mypy 1.15 cache-serialization crash on the
Windows Python 3.13 installation; it does not disable type checks. Store current
outputs separately from previous-machine evidence. Do not update a quality
baseline just to make a regression pass.

The checks also passed inside Linux Python 3.12.16, matching CI, with 18 API tests,
10 indexer/evaluation tests and 74.41% API coverage. To reproduce that environment:

```powershell
docker build -f scripts/Dockerfile.checks -t rahbar-checks:local .
docker run --rm --mount "type=bind,source=$((Get-Location).Path),target=/work,readonly" `
  --tmpfs /tmp:rw -e PYTHONDONTWRITEBYTECODE=1 -e COVERAGE_FILE=/tmp/coverage `
  --entrypoint /bin/sh rahbar-checks:local -c 'python -m pytest -q api --cov=api/app --cov-fail-under=60 -o cache_dir=/tmp/pytest-api && python -m pytest -q indexer eval -o cache_dir=/tmp/pytest-other && ruff check --cache-dir=/tmp/ruff api indexer eval corpus && mypy --cache-dir=/dev/null --config-file mypy.ini api/app indexer/pipeline'
```

If container downloads stall, the recovery run used official PyPI Linux wheels
downloaded to `.cache/wheels`, checked against PyPI's SHA-256 values, and mounted
into a temporary equivalent check Dockerfile. This changed the download transport,
not dependency versions. No tool was installed globally.
