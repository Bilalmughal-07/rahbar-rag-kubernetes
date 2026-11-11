# Submission status

Recorded 2026-11-11 during the authorized submission session.
This is a dated progress snapshot; the PR checks are authoritative for its latest
head. No main merge, Docker Hub publication or CD is claimed.

## History and verified GitHub authors

Repository: https://github.com/Bilalmughal-07/rahbar-rag-kubernetes

Pull request: https://github.com/Bilalmughal-07/rahbar-rag-kubernetes/pull/1

Development integration: `324add0d368a90d8015b69b3963f84bdea84492a`.
Remote main: `643415969cfc5618952ef9f5f0394c638b8dac16`.
Local main remains at `d4ac276`. Both roots are ancestors of integrated dev.
The separate integration branch/worktree is retained for review.

Commit authors record the partners' confirmed contribution responsibilities.
Codex assistance is disclosed in AI-USAGE.md and commit messages; no independently
human-written authorship of every line or invented historical work is claimed.
Hanan authenticated the push; GitHub author.login was checked separately.

| Commit | GitHub author | Contribution |
| --- | --- | --- |
| `d4ac27698eda` | `Bilalmughal-07` | Initial RAHBAR starter kit |
| `e388e48a2152` | `ranahananshafique` | chore(build): pin runtime dependencies and container tooling |
| `eb62ffd88305` | `Bilalmughal-07` | feat(indexer): implement versioned corpus extraction and indexing |
| `b152c1d4219c` | `ranahananshafique` | feat(api): implement grounded answers with version-aware retrieval and caching |
| `2178f9b6807c` | `Bilalmughal-07` | test(eval): add quality gates and reproducible retrieval experiments |
| `feadc6136f95` | `ranahananshafique` | fix(deploy): restore Kubernetes deployment and API routing |
| `620c5263d632` | `ranahananshafique` | ci: add gated build scan evaluation and deployment workflows |
| `9f2c7bc81ea4` | `Bilalmughal-07` | docs: document architecture recovery and submission requirements |
| `41d3126e7fc6` | `ranahananshafique` | docs(evidence): retain verified results and browser evidence |
| `324add0d368a` | `ranahananshafique` | chore(git): preserve local and remote history roots |

## Fresh local verification

- Python 3.13.14: 18 API tests and 10 indexer/evaluation tests pass;
  API coverage 74.41%, unchanged 60% threshold.
- Ruff passes including experiment scripts; mypy passes on 34 source files.
- Tests also pass in the integration worktree using the separately configured
  suites. A combined-folder invocation caused a collection import-path error;
  the documented separate invocations passed.
- All 11 corpus files match manifest hashes.
- Three application images rebuilt. Socket-free exported-image Trivy scans,
  using the existing cached vulnerability database, found zero fixable
  HIGH/CRITICAL vulnerabilities per image. Real CI scans separately.
- Exact publication file set passed Trivy secret scanning.
- Strict production manifest validation: 29 valid, zero invalid/errors.
- Ingress UI and cited POST /api/ask both return 200.
- Fresh 22-question live evaluation passed the unchanged golden set/baseline:
  recall@3 0.684211, recall@5 0.894737, citation validity 1.0,
  abstention correctness 1.0.
- Fresh evaluation cache hits: 0/22. Earlier retained recovery evaluation
  recorded zero hits; these runs are distinct.

- API three ready replicas; UI, Redis and Chroma ready; three PVCs Bound.
  HPA reports numeric CPU. Kubernetes data was preserved.
- Submission checker: 164 passed, three history warnings, zero failures.
- All 48 excluded local files were SHA-256 checked unchanged after commits.

Retained genuine browser screenshots, Python 3.12 checks, pod recovery/rollback,
network isolation and chunk/cache experiments are earlier recovery evidence;
they were not rerun or recaptured in this submission phase.
New raw local outputs are ignored scratch files. Original evidence is intact.
Original kubectl table padding is intentionally preserved in the evidence commit.

## Actual remote CI and remaining requirements

Actual CI run:
https://github.com/Bilalmughal-07/rahbar-rag-kubernetes/actions/runs/43058515362

The initial run passed lint, tests, manifests and image builds, then failed before
scanning because `aquasecurity/trivy-action@0.28.0` does not exist. The official
`v0.28.0` revision was verified and pinned to
`915b19bbe73b92a6cf82a1bc12b087c9a19a5fe2` without changing scan thresholds.
Fix commit `647e66dcd8c92a821ea36b46fc251589a7fecccf` maps to Hanan on GitHub.
The replacement PR run was started:
https://github.com/Bilalmughal-07/rahbar-rag-kubernetes/actions/runs/43059204957

Subsequent documentation commits trigger fresh checks; use the PR checks for
the exact latest head and result. Passing final scan/kind evaluation is not
claimed by this progress snapshot.
CI triggers on dev pushes and PRs to main; CD triggers only on main pushes.

- Hanan has collaborator push access, no admin access.
- Remote main is unprotected; no enforced branch protection is claimed.
- Rulesets API returned 403 requiring GitHub Pro or public visibility for this
  private repository. No visibility change was made. The owner can assess an
  eligible plan while retaining privacy. Manual review/approval is a procedural
  control, not equivalent to enforced protection.
- No repository Actions secrets or environments are configured.
  DOCKERHUB_USERNAME and DOCKERHUB_TOKEN must be securely configured before
  approved publication. Never place token values in chat, Git or logs.
- Repository secrets may be configured by an authorized collaborator;
  owner-only settings and protected environment controls depend on owner
  permissions and eligible features. No settings were changed.
- Instructor access to this private repository needs owner confirmation.
- Failed-then-passing evaluation-gate PR evidence is outstanding; no intentional
  failing change has been introduced and no baseline or golden set was weakened.
- CD deploys an ephemeral kind fixture target, not permanent production.

## Final approval boundary

Before main merge, show final dev SHA, verified authors, green CI/PR URLs,
protection status, secrets readiness, evaluation and remaining limitations.
Request separate explicit approval for main merge, SHA-tagged Docker Hub
publication and the configured CD deployment. None is authorized yet.
