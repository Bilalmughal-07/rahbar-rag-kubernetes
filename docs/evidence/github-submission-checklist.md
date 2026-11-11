# GitHub submission evidence checklist

This checklist intentionally contains no fabricated external evidence. Fill in
the run-specific values only after an authenticated GitHub/Docker Hub run.

- Repository: `https://github.com/Bilalmughal-07/rahbar-rag-kubernetes`
- Branch submitted: `dev` -> `main` pull request: pending approval and push
- Successful CI workflow URL: pending actual GitHub run
- Successful CD workflow URL: pending actual GitHub run
- Docker Hub API image with exact commit SHA: pending actual publication
- Docker Hub indexer image with exact commit SHA: pending actual publication
- Docker Hub UI image with exact commit SHA: pending actual publication
- Failed-then-passing evaluation-gate evidence: pending an intentional, approved
  GitHub test change; no local result is represented as GitHub evidence
- Deployed SHA: pending actual CD deployment
- Branch protection verified: pending GitHub repository administration

Observed on 2026-11-11: repository visibility is private; remote main is unprotected;
no remote dev branch, Actions runs, repository Actions secrets or environments exist.
The authenticated collaborator can push but is not an administrator. No external
settings were changed. Confirm both instructors can access the private repository.
The local and remote roots differ; follow `docs/GIT-CONTRIBUTION-PLAN.md` before an
approved integration. Confirm real authors and verified emails before each commit.

Local evidence already available in this repository:

- `eval/baseline.json` and `eval/results.json`
- `eval/fixtures/baseline.fixture.json`
- `docs/INDEXING-REPORT.md`
- `docs/evidence/version-pair.md`
- `python scripts/check_submission.py` result: 164 passed, 3 warnings, 0 failures
- `docs/RECOVERY-REPORT.md`: current results, requirements and limitations
- `eval/results.json`: recall@3 0.684211, recall@5 0.894737,
  citation validity and abstention correctness 1.0 across 22 questions
- `docs/evidence/current/python312-checks.txt`: 28 tests, 74.41% API coverage,
  Ruff and mypy pass on the CI interpreter
- `docs/evidence/current/fixture-evaluation.json`: local ephemeral kind fixture gate
  passed; this is not a GitHub Actions run
- `docs/evidence/current/ui-grounded.png` and `ui-abstention.png`: genuine browser screenshots
- `docs/evidence/current/trivy-*-verified.json`: actual final image scans
