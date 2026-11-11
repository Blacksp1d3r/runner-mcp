# Isolated GitHub Actions CI runner admission (proposal)

Status: **NOT ADMITTED**. No existing runner is approved by this document. This is security/capacity groundwork, not approval to move production workloads. Related: #584, Runner-Fabric #1396, SAFETY #988.

## Billing and deployment decision (reconciled 2026-10-09)

- Runner-MCP is a **public** repository. Standard GitHub-hosted Actions runners for public repositories do not incur hosted-runner minute charges under GitHub's current plan policy; do not migrate this repository merely to avoid a nonexistent hosted-minute bill.
- Runner-Fabric, Fiscero and SAFETY! are **private** repositories with distinct CI constraints. Their hosted-minute and artifact/package-storage investigations belong in their existing issues (#1396, Fiscero #349/#350, SAFETY #988), not on this public-repo admission PR.
- Artifact and package storage accounting remains distinct from CI minutes. A self-hosted runner does not eliminate artifact retention charges; moving standard public-repo jobs to private infrastructure may increase security or maintenance risk without saving money.
- Current main already includes fixes #600 and #601 to local/remote registration integrity; this document requires those fixes and future tests but does not duplicate their code or relax branch protection.
- No host, registration token, disposable image or live runner admission evidence has been received. #387 and #388 remain separate open implementation PRs. Until each is verified and reviewed, retain hosted CI without disabling mandatory checks.

## Topology and separation

```text
GitHub protected/main PR checks
   |-- hosted job (fallback while admission incomplete)
   |-- isolated, ephemeral CI VM (future label: aifordable-ci-isolated)
       |-- validation: Python 3.12 / Ruff / pytest / pinned MCP registry validator
       |-- clean demo and release-artifact offline smoke
       |-- attribution: GitHub read-only API, no checkout required

Production VPS, staging/deploy-capable runners, DBs, home network and persistent
Runner-MCP/Fabric control-plane: NOT members of this CI trust boundary.
```

## Additional cache and workspace qualification (review of #387, 2026-10-09)

A job-local `HOME` and `.venv-ci` do not prove isolation when `RUNNER_TOOL_CACHE` persists across jobs or tenants. Before admitting PR-sourced work, prove at least one of these approaches:

- A fresh disposable runner/VM and fresh cache for each untrusted job, torn down after completion; **or**
- An independently security-reviewed, single-trust-domain cache with immutable, content-verified wheel files, pinned dependency resolution and protected ownership, plus an explicit prohibition on cross-trust reuse.

Qualification tests must exercise a deliberately poisoned cache entry, mismatched dependency resolution, unexpected writable cache path, interrupted `.complete` marker, cleanup after a failed job and a subsequent job on the same host. Every unsafe condition must fail closed, not silently use stale dependencies. A fingerprint of `pyproject.toml` plus source files is **not** a proof of complete dependency contents, versions or downloaded wheel integrity. This complements (not replaces) runner-group isolation, no production secrets/routes, and required-check preservation.

## Enrollment review gate (PR #388)

The current registration implementation passes a short-lived GitHub registration token via `config.sh --token` subprocess arguments. Do not equate sanitized stdout/stderr with protection from same-host process-list readers. Before admitting a runner, verify its transient registration process executes on a dedicated, isolated host with no unrelated local users/process-inspection privileges; bound registration duration and lifetime; verify script directory owner/mode and absence of other writable execution paths. Avoid publishing any real token or host-specific paths. If approved runner-registration architecture changes token delivery, add negative tests for output, argv/process visibility and timeout handling. This is a **review gate**, not a claim registration is compromised or already performed.

## Admission evidence required BEFORE changing runs-on

- [ ] Dedicated VM/runner configured and documented by operator; distinct runner group and label, no deployment/staging labels, no credentials or production network routes.
- [ ] Explicit handling for untrusted `pull_request` code: disposable VM/image **per job** or equivalent reset and credential/network isolation. Public PR forks must never run with privileged shared credentials. No `pull_request_target` for untrusted source.
- [ ] Runner registration is restricted to intended repositories; permissions least-privilege, short-lived and removed on teardown. Restrict outbound endpoints and artifact/cache poisoning paths as feasible.
- [ ] OS/toolchain validated: Python 3.12, Node only where needed, bash/curl/git, pinned GitHub Actions compatibility. Jobs operate in isolated working directories without persistent writable cross-job state.
- [ ] Validate ALL existing checks at exact head: `validate`, `demo-smoke`, `release-artifact`, `commit-attribution-policy`; branch protection and required check names stay unchanged. Keep hosted fallback until self-hosted evidence complete.
- [ ] Capacity and concurrency: maximum admission bounded by spare hardware/energy; no resource starvation of production or existing staging; safe offline/unavailable behavior is queued or explicit failure, not bypass.
- [ ] Provenance, immutable test/release evidence and re-run eligibility checked. Never elevate ordinary CI results to authority for production deploy.
- [ ] Security operator approves transition and rollback to previous workflow. GitHub billing after migration confirms reduced hosted minutes, without increased storage charges.

## Safe change plan

1. Prepare isolated VM and label **outside** production; verify exact registration and clean lifecycle.
2. Submit a small workflow PR changing runner selectors only for already-admitted jobs, not the whole matrix at once.
3. Run PR + main checks and adversarial isolation test (no secrets/production routing, intentional failed job, cleanup proof).
4. Only then merge; measure minutes, artifacts GB-hours, queue times and flake rate. Keep independent release approval and rollback.

## Failure museum / handover

- **CI-RUNNER-0001**: changing `runs-on` before runner exists causes indefinite queued checks; rollback selector, never disable branch protection.
- **CI-RUNNER-0002**: running untrusted PR on persistent privileged runner risks credential and lateral compromise; refuse admission, isolate/erase per job.
- **CI-RUNNER-0003**: self-hosted runner reduces GitHub-hosted **minutes** but upload-artifact retention still consumes GitHub **storage**.
- **CI-RUNNER-0004**: missing live runner evidence (Runner-MCP connector returned internal errors 2026-10-09) is not proof of healthy or enrolled capacity. No guessed enrollment.

Updated 2026-10-09. No infrastructure identifiers, secrets, or private network topology included.
