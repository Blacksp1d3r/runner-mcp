# Runner-MCP #341 — isolated exact old-source wheel evidence

## Goal
Construct a rebuildable, SHA-256-labelled **candidate historical wheel** from exact old commit `a0fd964c4a6fe7e0a1506a513e9b2b4059c5453a` on a disposable GitHub-hosted Ubuntu runner, without touching the installed service, shared volumes, A7 VM or other workers. This is not approval to recover/restore; do not call it a byte-identical installed artifact.

## Boundary
A single branch-local workflow `.github/workflows/341-historical-wheel-evidence.yml` triggers only on a pinned branch push changing itself; no secrets, runtime token, branch promotion, publication, ssh, SSH agent, production packaging, or service update. Uses immutable checkout/setup/upload Actions; checks exact detached source SHA; one output wheel; package metadata; emits SOURCE_COMMIT, SHA256SUMS, BUILD_INFO.json and short-lived GitHub artifact. The job may use GitHub-hosted build dependencies; this is an isolated reconstruction, not a reproducible proof.

## Acceptance
Workflow job green and artifact present, downloaded into independently preserved private Library; verify SHA256 locally and actual content; compare with independently witnessed active process modules and package bytes before any human-authorized recovery. Source review/security and A6/A7 are separate. Main checkout and no upload artifact means WAIT.

## Failure Museum
RMCP-F-0032 and -0034; preserve discrepancy between same v0.1.3 package label and 280-commit old source difference. If unsupported build or artifact unavailable: record WAIT and do not publish a guessed PyPI wheel.

## Handover
Owner: non-overlapping artifact evidence workstream. Parent #341, checkpoint draft/ready PR #659, handover; no claim over A6 #509 or Fabric #942/#943.
