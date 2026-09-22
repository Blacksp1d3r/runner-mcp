# Runner MCP — Session Handoff

Last reconciled: 2026-09-22.

## Purpose
Runner MCP is a small, auditable, deny-by-default operations interface. GitHub is the code/collaboration surface; Runner MCP is the local execution and safety boundary. It must never become a generic remote shell.

## Architecture
- public project-agnostic core in this repository;
- private configuration holds real host/repository/ref/credential values;
- strict GitHub mailbox protocol for bounded remote operations;
- replay protection, safe result envelopes and restart-safe watcher coordination;
- predefined test profiles and bounded workers/queues;
- explicit operator emergency stop;
- commit-pinned self-update with staged wheels, transaction markers, activation markers and rollback/recovery controls.

## Current state
GitHub current state wins if anything below is stale.
- `main`: `f5d2586674d30cc12a526273da6c352312f2ac9a` at this handoff.
- PR #45 is open and CI-green: “Surface self-update install recovery in status and doctor”.
- PR #44 was merged as `3ce122012d56ead3fbf75dfbf8fe770572f3ed47`: bounded local self-update install recovery.
- The private GitHub watcher is live, but its heartbeat is currently degraded with 4 recovery-attention items.
- A read-only `runtime_status` mailbox probe `runner-runtime-status-20260922-0640` was submitted and had no result yet at this handoff.
- The current watcher behavior deliberately does not advance its cursor while recovery observations remain.

## Important decisions
- no arbitrary shell/executable/path/environment/process/package-manager input through MCP/mailbox;
- production restore/PITR and generic transaction reset remain outside the mailbox;
- self-update targets exact lowercase commits reachable from canonical `origin/main`;
- install recovery is local operator-only and requires the emergency stop;
- GitHub live PR/issue/CI state is authoritative over stale handoff text.

## Open PRs / issues
- PR #45 — recovery state visibility in local `status` / `doctor`; mergeable and CI-green at last check.
- No open Runner-MCP issues at last check.

## Blockers
- private watcher recovery backlog: 4 recovery-attention items keep the cursor from advancing cleanly;
- private host still needs bootstrap/proof of the newest recovery-capable self-update baseline;
- Desktop Commander is unavailable due monthly limit; prefer GitHub + Runner-MCP bridge.

## Current assignment
1. reconcile/resolve the four watcher recovery-attention items without replaying operations;
2. confirm the live `runtime_status` probe result;
3. merge PR #45 only after confirming GitHub state is still green/current;
4. bootstrap and live-prove the newest self-update baseline through the safe operating model.

## Next safe steps
- inspect exact recovery observations and use only existing fail-closed operator recovery/quarantine mechanisms;
- never reset replay/cursor state generically;
- once watcher health is clean, re-run one read-only runtime probe;
- then prove same-commit self-update, forward update, failed/retried activation and interrupted/recovered package-install paths.

## Definition of done for a work batch
Tests/evidence must be terminal, blockers must be recorded or resolved, and this file plus `CURRENT_STATE.md` / `AGENT_EXCHANGE.md` must make the next safe action obvious.
