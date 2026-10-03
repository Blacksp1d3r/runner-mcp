# NEXT ACTION

Updated: 2026-10-03

## Goal

Consume only the two remaining source-supported watcher restart markers, then continue directly with Runner Fabric / Agent Bus live qualification.

## Current invariant state

- Installed runtime-code commit: `9dc9d2bfa09b25deff7a5186b9f12252c84cdd52`.
- Successful self-update job: `c6602347fe0646ffa9e20a0f638a2967`.
- Runner MCP operational; emergency stop inactive; install recovery clear.
- Doctor: 0 failures / 0 warnings.
- Agent Bus convergence: `state=clear pending_results=0`.
- `last_installed_commit=9dc9d2bfa09b25deff7a5186b9f12252c84cdd52`.
- `install_recovery_pending=false`.
- `restart_pending=true`, `pending_restart_count=2`.
- Remaining markers: `github-watcher` and `completion-watcher` at the installed commit; `server` is clear.
- Source contract: each long-running watcher invokes `run_restart_if_requested`, which safely removes its validated marker and re-execs the fixed component; failed re-exec restores the marker.

## Next engineering action

1. Resume/start `runner-mcp github-watcher run` under the dedicated service-user runtime; allow one normal cycle to reach its restart check.
2. Resume/start `runner-mcp completion-watcher run` under the same runtime; allow one normal cycle to reach its restart check.
3. Confirm only `restart_pending=false` and `pending_restart_count=0`.
4. Run Runner Fabric #590 isolated Agent Bus work-unit qualification with GitHub/source-control credentials absent and GitHub HTTPS probes denied.
5. Prove one worker-process restart/replay with no duplicate execution and convergence back to `clear`.
6. Only after that qualify/register the separate GitHub fallback identity/pool, independent drain/disable, then persistent activation.

## Do not repeat

Do not repeat MCP health/server startup checks, mailbox end-to-end proof, lint/unit qualification, pip/setuptools checks, baseline wheel staging, origin/fetch/target reachability, queue/worker idle checks, stale site-packages investigation, or the self-update proof. Do not manually unlink restart markers.
