# NEXT ACTION

Updated: 2026-10-03

## Goal

Complete the replacement-host Runner MCP self-update to the fixed runtime-code target, then resume Agent Bus / Runner Fabric live qualification.

## Current invariant state

- Installed/source rollback baseline on `aifordable-lab`: `a71f68b3c6375c22d9a10a7cfea9e28c9692cc0d`.
- Exact runtime-code self-update target: `9dc9d2bfa09b25deff7a5186b9f12252c84cdd52` (reachable from `origin/main`; handover-only commits do not need to move this target).
- Source tree is clean and restored to the baseline after the failed update.
- MCP server, auth/session bridge, bounded local lint/unit and mailbox lint are proven healthy.
- Failed self-update job `48a3cb362da249f0925b5cee18fdfe86` reached target validation.
- Target lint job `bf7e0872202a4b4d91d15e3f9762e4df` passed.
- Target unit job `eb64112264214b5cb88291ac4a04e540` failed collection because pytest imported stale baseline code from `.venv/site-packages`.
- PR #233 fixed this with pytest `pythonpath = ["src"]` and merged green as `9dc9d2bfa09b25deff7a5186b9f12252c84cdd52`.
- Persistent server/autostart is not installed yet; keep the qualification server alive in the foreground.

## Next engineering action

1. Remove only the exact untracked source-root artifact `aifordable_runner_mcp-0.1.3-py3-none-any.whl`.
2. Require `git status --short` to return no output; do not reset or clean anything else.
3. Submit one fresh bounded self-update request for exact runtime-code commit `9dc9d2bfa09b25deff7a5186b9f12252c84cdd52` while the local MCP server remains alive.
4. Process it once through the GitHub watcher and follow the resulting self-update job to terminal state.
5. On success, verify installed commit/version, `runner-mcp doctor`, restart state and `runner-mcp agent-bus convergence`.
4. Then run Runner Fabric #590 isolated Agent Bus work-unit qualification with GitHub credentials absent and GitHub network access denied.
5. Prove worker restart/replay and convergence.
6. Only then qualify/register the separate GitHub fallback and persistent activation.

## Do not repeat

Do not re-investigate pytest/ruff availability, MCP endpoint/auth, mailbox transport, baseline wheel staging, generic pip/setuptools availability, origin reachability, target reachability, or empty test queues unless new evidence contradicts the recorded proofs.


## Persisted proof / do-not-repeat

The following are already proven and must not be re-diagnosed without contradictory new evidence: MCP server startup/health; bridge auth/session/runtime_status; local lint/unit; mailbox lint end-to-end; pip/setuptools availability; actual SelfUpdatePackageInstaller baseline wheel staging; origin/fetch/target reachability; empty test queue/workers; stale-site-packages unit-collection root cause and PR #233 fix. Latest immediate blocker is only the untracked source-root wheel artifact.
