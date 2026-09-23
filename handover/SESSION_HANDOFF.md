# Runner MCP — Session Handoff

Last reconciled: 2026-09-23.

## Current checkpoint
- Live GitHub reconciled after Tasks 18 and 20 through coordination checkpoint `182ba9c24b927001257be85454cffe018a4f9cb1`; live GitHub always wins over this recorded checkpoint.
- Task 18 COMPLETE: PR #76 merged as `5c4f5db350cdafa99066bdb091866b7d6979a7a9`. Exact PR head `97fcde693d6264171920c386d10e9e63403a9a9a` passed CI run 35894315537 fully green: Ruff, whitespace, 794 pytest tests, built release artifact and clean demo.
- Task 18 added `runner_mcp.secure_io.atomic_replace_private` and migrated only config-manager, approval-manager and completion notifier private JSON state. Existing locks/serialization/state ordering and completion size/schema/parent semantics were preserved. Autostart/cron, job metadata, ledgers, create-only writers, deployment activation/tar extraction and self-update were untouched.
- Task 20 COMPLETE: PR #77 merged as `4bfd71d85cb5228ba328ee17fc60414c84c43e0a`. Exact PR head `666a399803db41bae4deae73fc4f205de5e97854` passed CI run 35895116909 fully green: Ruff, whitespace, 1203 pytest tests, built release artifact and clean demo.
- Task 20 was test-only. It pins a valid fixture for every BridgeAction, exhaustive non-owned optional-field rejection, action case/hyphen/prefix rejection, duplicate request_id rejection, request-side NaN/Infinity rejection, lowercase-only self-update commit enforcement and zero executor invocation for rejected requests.
- No production bridge protocol/capability code changed in Task 20.
- Open Runner-MCP PRs/issues at the post-merge reconciliation checkpoint: none.
- Task 10 remains BLOCKED on a usable private-host self-update/recovery proof path. Never reset replay/cursor/transaction state as a shortcut.
- Current UNCLAIMED bounded public queue: Task 21 managed-autostart secure-I/O migration; Task 22 cron supervisor safe diagnostics; Task 23 completion-watcher safe diagnostics. Task 18 prerequisites for Tasks 21/23 are satisfied.
- Before claiming any next task, reconcile live GitHub plus `claude_feedback/CURRENT_ASSIGNMENT.md`; do not duplicate work if another agent has claimed it.
- No tag, GitHub release, package publication, deployment, migration or external publication has been authorized/performed in this session.
- Desktop Commander remains unavailable due the previously reached monthly limit; private-host proof therefore remains unresolved.

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
- Task 8 merged via PR #52 (`d6821ddb0773b586b6a106b66b2e18154c90cc7a`): fail-fast local release-check wrapper plus isolated clean-demo project venv.\n- Task 6 has one demonstrated docs drift queued: `runtime_doctor` is implemented but omitted from README/public bridge action documentation.\nGitHub current state wins if anything below is stale.
- `main`: `011fcbfec4e0b75a93820ca1c4c487111da6b495` at this reconciliation checkpoint.
- No open Runner-MCP pull requests at this checkpoint.
- PR #46 merged as `a50fe7eca0c74dff8aa337e431feadf55fa3e287`: installer/operator missing-sudo robustness.
- PR #47 merged as `5d2f21409723578e7b6873f31746fac1d8ada459`: secure-I/O inventory.
- PR #48 merged as `4f84a192581015e219774b8d0a40e1172124c12b`: self-update file + directory fsync durability.
- PR #49 merged as `57d9f114dcab22df434aaa051796ae036b71ebb9`: category-only safe diagnostics contract.
- PR #50 merged as `07d9a4b1041cd20e7b2201aa4a83b674a1a1c85c`: narrow REMOVE-confirmation helper.
- PR #51 merged as `011fcbfec4e0b75a93820ca1c4c487111da6b495`: current-main recovery visibility; stale PR #45 was closed unmerged.
- The last recorded private-runtime handoff said the watcher had 4 recovery-attention items and a read-only runtime probe was pending. That private state was not re-probed in this GitHub-only session and must be treated as historical until checked again.

## Important decisions
- no arbitrary shell/executable/path/environment/process/package-manager input through MCP/mailbox;
- production restore/PITR and generic transaction reset remain outside the mailbox;
- self-update targets exact lowercase commits reachable from canonical `origin/main`;
- install recovery is local operator-only and requires the emergency stop;
- GitHub live PR/issue/CI state is authoritative over stale handoff text.

## Open PRs / issues
- No open Runner-MCP pull requests at this checkpoint.
- No open Runner-MCP issues were re-established as blockers during this GitHub reconciliation.

## Blockers
- private watcher/recovery health still needs a fresh bounded probe before mailbox-driven self-update proof; the previous degraded observation is not assumed current;
- private host still needs bootstrap/proof of the newest recovery-capable self-update baseline;
- Desktop Commander is unavailable due monthly limit; prefer GitHub + bounded Runner-MCP bridge when available.

## Current assignment
1. keep Task 6 and Task 7 as normal-chat analysis/review work, not Claude Code work;
2. use ChatGPT for Task 8 implementation unless explicitly reassigned;
3. before live self-update proof, obtain a fresh bounded private-runtime watcher/recovery status;
4. bootstrap and live-prove the current recovery-capable self-update baseline only after watcher/recovery state is clean enough for safe proof.

## Next safe steps
- Task 6: documentation/CLI contract drift audit as a CHAT REVIEW; return findings only, no code.
- Task 7: dependency-set / `--no-deps` compatibility analysis as a CHAT REVIEW.
- Task 8: local release-check convenience as ChatGPT CODE work.
- independently, re-probe private watcher/recovery state before relying on mailbox-driven self-update proof;
- never reset replay/cursor/transaction state generically.

## Definition of done for a work batch
Tests/evidence must be terminal, blockers must be recorded or resolved, and this file plus `CURRENT_STATE.md` / `AGENT_EXCHANGE.md` must make the next safe action obvious.
