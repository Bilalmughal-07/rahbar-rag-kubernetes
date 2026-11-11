# Verification evidence

Historical command records transferred from the previous machine remain local-only.
The exact publication allowlist and 48 exclusions are in
[the contribution plan](../GIT-CONTRIBUTION-PLAN.md). Fresh
2026-11-11 evidence is in [`current/`](current/), indexed by
[the recovery report](../RECOVERY-REPORT.md). It includes genuine browser screenshots,
raw API responses, Python 3.12 checks, image scans and local kind fixture results.

These files are command records from the local Docker Desktop Kubernetes cluster. GitHub
branch protection was not changed or claimed, because no push or GitHub administration was
authorized. Metrics Server was installed from the official release manifest and configured
with the Docker Desktop kubelet TLS workaround; the resulting `kubectl top` and HPA output
are retained in `current/cluster-final.txt` and `current/kubectl-top-final.txt`.
Raw execution logs, duplicate results and downloaded support manifests remain local-only;
the retained reports and structured evidence carry the submission results.

The following external evidence is intentionally not claimed yet: a GitHub CI run, a
failed-gate pull request, a passing-gate pull request, branch-protection settings, a CD
run, and Docker Hub image pages. They require an authenticated GitHub/Docker Hub account
and a reviewed push. No external run URLs or screenshots are fabricated; the new local
browser screenshots show the actually running UI and are not GitHub evidence.

The workflow design, required secrets, ephemeral-cluster behavior, and the checklist for
recording those real external results are documented in [CI-CD.md](../CI-CD.md) and
[github-submission-checklist.md](github-submission-checklist.md).
