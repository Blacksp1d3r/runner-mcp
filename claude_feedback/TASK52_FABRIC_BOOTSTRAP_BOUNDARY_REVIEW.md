# Task 52 — Runner Fabric first-install bootstrap boundary review

Date: 2026-09-30

## Scope

Review only. Reconcile issue #144 against the already integrated bootstrap implementation from PR #150 / merge `00ce316124ebc13c65e8a26762f7ea1f69404f50`.

No new bootstrap authority is added in this review.

## What is already proven by PR #150

The integrated `FabricBootstrapManager` already provides a strong bounded foundation:

- caller supplies only one full lowercase 40-character commit;
- source repository is fixed to canonical `Blacksp1d3r/Runner-Fabric`;
- no caller repository URL, package, executable, argv, path or environment;
- source checkout is private and exact commit + clean worktree are verified;
- GitHub credential comes from private Runner MCP configuration and is passed through a temporary private askpass mechanism rather than argv/result output;
- build uses fixed Runner MCP Python with `pip wheel --no-deps --no-build-isolation` and `PIP_NO_INDEX=1`;
- install uses a private versioned release directory with `--no-deps --no-index`;
- Runner Fabric import/parser/version verification occurs before activation;
- activation uses a controlled `current` link plus fixed launcher and restores the previous link on activation-state failure;
- durable job state is private and bounded;
- queued/running jobs become `interrupted` after Runner MCP restart and are not replayed;
- operator emergency stop blocks start and is rechecked before activation;
- only bounded `fabric_bootstrap(commit)` and `fabric_bootstrap_status(job_id)` surfaces were added;
- exact-head validation #666 and post-merge validation #667 were green.

## Remaining issue #144 gaps

Issue #144 is **not yet complete** because three explicit first-install safeguards are not independently enforced.

### 1. Cross-operation exclusion with Runner MCP self-update/recovery

The bootstrap manager currently checks the operator emergency stop, but it does not independently refuse while Runner MCP has:

- an active self-update;
- pending restart/activation markers;
- pending or invalid self-update install recovery.

Bootstrap and self-update both mutate installed runtime/control-plane state. They must not overlap or proceed through unresolved recovery.

### 2. Explicit installed-runtime prerequisite preflight

The bootstrap currently relies on the later wheel build/import verification to fail if tooling/runtime dependencies are unavailable.

Issue #144 requires a bounded fail-fast preflight before source/build mutation. The smallest defensible preflight should prove:

- usable `python -m pip --version`;
- importable `setuptools.build_meta`;
- importable already-required runtime modules needed by Fabric bootstrap/runtime integration: `mcp`, `pydantic`, `starlette`, `uvicorn`.

No missing dependency may be installed automatically.

### 3. First-install-only conflict behavior

The current implementation is idempotent when the same commit is installed, but a different existing installed commit can proceed into a new release and activation.

Issue #144 explicitly describes this authority as first-install-only. Until the future Forgejo/artifact-custody update path is separately designed, a different installed commit must fail closed before source/network/build work.

## Required follow-up

Queue one bounded CODE task to close these three gaps without widening the existing bootstrap interface.

Acceptance:

- inject/read a bounded Runner MCP self-update/recovery guard; refuse before worker/source mutation when self-update is active, restart activation is pending, or install recovery is pending/invalid;
- preflight fixed installed-runtime packaging/runtime imports before source clone/build; bounded error categories only;
- if an installed Fabric commit exists:
  - same commit remains idempotent/completed with no subprocess;
  - different commit fails closed before subprocess as `already_installed_conflict`;
- no generic update path, rollback selector, arbitrary repository/package/path/argv/env, dependency auto-install or production mutation authority;
- preserve emergency-stop checks, durable no-replay job state and activation rollback;
- adversarial tests prove all three guards fire before Git/network/build subprocess execution;
- full Runner MCP CI remains green.

## Outcome

Task 52 is complete as a review.

Issue #144 remains open until the bounded hardening CODE follow-up is integrated and proven. Future Runner Fabric updates remain outside this bootstrap and belong to the separate Forgejo/artifact-custody design.
