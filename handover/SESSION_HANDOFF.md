## 2026-09-26 — distribution/discovery handoff

- Runner MCP remains released at public `v0.1.0`; `v0.1.1` is being prepared on `release/v0.1.1-discovery`.
- The slice adds PyPI/MCP Registry metadata, tokenless OIDC publishing automation, metadata consistency tests and stronger first-screen/launch copy.
- Runtime/security authority is unchanged: authenticated Streamable HTTP, local private setup and deny-by-default capability boundaries remain intact.
- Do not publish 0.1.1 until branch CI is exact-head green, the change is integrated to `main`, and the one-time PyPI Trusted Publisher + GitHub `pypi` environment setup is complete.
- After those gates, run the human-triggered `Publish Runner MCP` workflow with version `0.1.1`; it publishes PyPI first, then the official MCP Registry, then creates the GitHub pre-release.
- After Registry publication is verified, proceed to secondary MCP directories and community launch posts using `docs/LAUNCH_COPY.md`.
## 2026-09-24 — v0.1.0 published; next session starts post-release

- Runner-MCP `v0.1.0` is now a published GitHub pre-release from exact validated commit `f00ac3fd03df234cb186a4dfcd804136501c0cf7`.
- PR #98 reconciled README, CHANGELOG and launch-readiness after publication and merged as `5647aa8839af90451189d2d943ce393edfacfe78`; exact-head run #514 and merged-main run #515 are fully green.
- Do not retag or move `v0.1.0`. Post-release `main` being ahead of the release tag is expected.
- First next actions: reconcile live GitHub; confirm no new blockers; verify a clean-host install from the published tag; set the prepared repository description/topics if still missing.
- Keep Task 10 private-host self-update/recovery proof as an explicit alpha limitation until actually proven.
- Runner Fabric stays separate and must not be pulled into Runner-MCP scope.

## 2026-09-24 — RELEASE-CANDIDATE RECONCILIATION CHECKPOINT

- Runner Fabric is a separate private project/repository. Keep this repository focused on Runner-MCP release work only.
- PR #97 is merged as `9ce5fe94f417e4e7f910c9945727f70cffd33ecb`; exact PR head `91e0c1b1e737ad14a43b31750cfdfbf1bf582f24` passed run `36037258558` fully green.
- Live reconciliation after the merge shows no open Runner-MCP PRs and no open Runner-MCP issues.
- Task 41 is integrated. Task 47 is now prerequisite-safe. Task 43 remains blocked on Task 46 cross-process release-mutation locking. Task 44 is prerequisite-safe; Task 45 remains blocked on Task 44.
- None of Tasks 43–47 is automatically a blocker for the first tagged alpha; the public release gate remains exact-green candidate + accurate documented limitations.
- Task 10 private-host self-update/recovery proof is still unproven. Do not claim it in release notes; preserve the limitation unless it is safely proven later.
- After this coordination commit, require exact-main green CI before any tag/release decision.
- No tag, GitHub release, package publication, repository-setting mutation, registry submission or external announcement has been performed.

# Runner MCP — Session Handoff

Last reconciled: 2026-09-24.

## Latest checkpoint — Task 34 PR #92

- PR #91 merged to main as `11b9a4d4e508ac93cd436037563c09d08cfa43ab`; Tasks 33, 35 and 38 are complete and must not be duplicated.
- Task 34 is COMPLETE on PR #92 pending final exact-head CI/integration.
- Task 34 adds only local read-only `runner-mcp retention preview PROJECT`; no pruning/deletion, approval, MCP or mailbox authority was added.
- Retention preview is fail-closed on unsafe release/backup storage and reports advisory categories only. Manual backups remain non-eligible without a dedicated retention policy.
- Actual pruning remains deferred.
- Task 37 review is independently active on PR #93; Task 39 adapter refactor is now prerequisite-safe.
- Task 10 private-host self-update/recovery proof remains externally BLOCKED; no tag/release/publication is authorized.
- Reconcile live GitHub before any next claim; exact-head CI is authoritative.

## Current checkpoint
- Live GitHub reconciled through Tasks 32 and 36 merge plus final coordination; live GitHub always wins over this recorded checkpoint.
- Tasks 21–32 and Task 36 are COMPLETE and must not be duplicated.
- Task 31 local read-only PostgreSQL restore preflight is implemented; restore execution, restore approvals, WAL/PITR, production recovery and MCP/bridge/mailbox restore authority remain deferred.
- Task 32 COMPLETE: PR #89 merged as `e629515f9c7e7a5d44506dfb82a48343870f94da`; exact head `99c72037eff4ed54cf7e92f7a08b278b48af4e45`; CI 35967246877 fully green with Ruff, whitespace, 1267 tests, built artifact and clean demo.
- Task 36 COMPLETE: PR #90 merged as `8c971016e4fc3cd821dc52d28334567c20835ff4`; exact head `1b3567b5de1f5a4ac5a67db16c609db2edac25dd`; CI 35967550375 fully green with Ruff, whitespace, 1267 tests, built artifact and clean demo.
- The six demonstrated alpha-release documentation drifts are reconciled. `0.1.0` remains explicitly unreleased; no `v0.1.0` tag or GitHub release exists at the audited checkpoint.
- Repository description/topics, v0.1.0 tag/GitHub release, package/registry/ecosystem publication and external community posts remain explicit user-controlled actions.
- Task 10 remains BLOCKED on usable private-host self-update/recovery proof. Public alpha wording must not imply that private-host live proof exists.
- Current bounded public queue: Task 33 optional graphical administration boundary review; Task 34 local read-only retention preview; Task 35 manual historical rollback selection boundary review.
- No new task is claimed at this checkpoint. Reconcile live GitHub plus `claude_feedback/CURRENT_ASSIGNMENT.md` before the next claim.
- No tag, GitHub release, package publication, deployment, rollback, migration, restore, deletion, network exposure change, repository-setting mutation or external publication has been authorized/performed in this session.
- Desktop Commander remains unavailable due the previously reached monthly limit; private-host proof remains unresolved.
- Before asking for alpha-release authorization, verify full GitHub CI is green on the exact latest `main` commit after these final coordination updates.

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
