## 2026-09-30 — Tasks 50–52 reconciled

- Current reviewed main checkpoint: `0bade0af6ee574b09de42bb493f5ecffa41657d5`.
- Task 50 is COMPLETE via PR #149 / `469138077066b7b924ba867456ad44dc6372c85d`; issue #143 closed.
- Issue #151 is COMPLETE via PR #152 / `0bade0af6ee574b09de42bb493f5ecffa41657d5`; exact-head #669/#157 and post-merge #671/#159 are green; issue closed.
- Task 51 review is COMPLETE: keep service-journal output local-only. Generic redaction cannot prove arbitrary application/customer/personal data safe for remote disclosure. No remote log action is authorized.
- Task 52 review is COMPLETE: PR #150 provides a bounded Fabric bootstrap foundation, but #144 remains open because three explicit guards are still missing.
- Task 53 must add: self-update/restart/recovery exclusion; fixed installed-runtime preflight; different-installed-commit first-install conflict before subprocess.
- PR #153 refreshes unique PR #127 relay-core work; do not duplicate it. Task 54 owns integration/closure.
- PR #129 remains unique primary watcher work; Task 55 owns reconciliation after Task 54.

Immediate resume order:
1. integrate this review/coordination PR after exact-head CI;
2. implement Task 53 and close #144 only after exact-head + post-merge proof;
3. reconcile #153 and close #127 only after #153 is integrated;
4. then reconcile #129 against the new main;
5. keep remote service logs deferred.

## 2026-09-29 — Tasks 47 and 49 integrated; bounded queue refilled

- Runner MCP `main` checkpoint: `67954dea2117cce3a1819132f6d3c7480dd34c82`.
- Task 47 is COMPLETE via PR #145 / merge `67954dea2117cce3a1819132f6d3c7480dd34c82`.
  - local/private only: `runner-mcp service-log PROJECT ALIAS --lines N`;
  - per-service `allow_log_read: false` opt-in;
  - fixed no-symlink `journalctl`, fixed argv/env, 1–100 entries, <=10s, <=32 KiB retained stdout;
  - Task-41 redaction receives known local runtime secrets/private paths plus private unit/health URL;
  - disabled/unknown service fails before subprocess;
  - read remains available during emergency stop;
  - no MCP, bridge, mailbox or Agent-Bus log action exists.
  - exact-head validation #654 + attribution #140 and post-merge validation #655 + attribution #142 are green.
- Task 49 is COMPLETE via PR #124 / merge `da367081f88d6d2342cf938a9b67ec59d9d10de0`.
  - explicit additive async migration start/status exists;
  - `migration_async` approval is distinct from synchronous `migration`;
  - synchronous `apply_migrations` and deployment-triggered migrations remain unchanged;
  - exact-head validation #622 and post-merge validation #623 are green.
- Task 50 is the next small CODE lane: close the remaining issue #143 gap by preflighting installed-runtime `pip` + `setuptools.build_meta` before wheel-stage mutation.
- Task 51 is review-only: decide whether any remote service-journal disclosure is justified after Task 47; do not add remote log authority during the review.
- Task 52 is review-only: define the first-install Runner Fabric bootstrap safety boundary for issue #144 before any bootstrap mutation/tool is implemented.
- PR #127 and PR #129 remain open and contain unique Agent-Bus work. Do not duplicate or close them merely because #131/#132/#134 later merged; reconcile/rebase those PRs separately.
- Issue #130 remains open because its live activation proof is broader than the merged lifecycle code.
- Issue #143 remains open until Task 50 production preflight is integrated.
- Issue #144 remains open and high risk; Task 52 review comes first.

Immediate resume order:
1. integrate this coordination update after exact-head CI;
2. implement Task 50 as the next bounded CODE lane;
3. Task 51 and Task 52 can proceed as independent reviews if code work blocks;
4. do not duplicate PR #127/#129 Agent-Bus work;
5. keep remote service logs, generic package install, arbitrary VCS/package/shell authority and production mutation out of scope.

## 2026-09-28 — Task 44 integrated; Task 45 async migration boundary decided

- Runner MCP `main` checkpoint before this review branch: `6053b7c3d5aef757055c453d2fd5b7f581248e53`.
- Task 44 is COMPLETE via PR #118 / merge `6053b7c3d5aef757055c453d2fd5b7f581248e53`.
- Task 44 evidence is fully green: exact-head validation #607 + attribution #91 and post-merge validation #609 + attribution #94; full pytest, Registry/whitespace, release artifact and clean demo are green.
- The durable migration substrate is additive only: private strict migration-job storage, queued/running/terminal state, restart -> interrupted without replay, canonical plan revalidation, bounded public status and read-only `MIGRATION_JOB` completion delivery. Existing synchronous `apply_migrations`, direct `migration_status`, bridge `APPLY_MIGRATIONS` and deployment-triggered migrations remain unchanged.
- Task 45 review is COMPLETE in `claude_feedback/TASK45_ASYNC_MIGRATION_INTEGRATION_REVIEW.md`.
- Task 45 decision: do not version or silently change synchronous `apply_migrations`. If async remote execution is integrated, add explicit `start_migration_job` + `migration_job_status` tools / bridge actions.
- Async execution must use a separate human approval operation `migration_async`, with a fixed async execution discriminator in the approval binding, so sync and async approvals are not interchangeable.
- Required start ordering: require configured runner -> recompute canonical migration state -> consume async approval -> durable queued persistence -> worker start. A consumed approval with no job is safer than durable execution intent without consumed approval.
- Bridge persistence/finalize ambiguity after a job starts must never replay/enqueue a second job. Immediate start result means durable acceptance/queueing, not migration completion.
- Task 49 is the bounded CODE follow-up. It must not add cancellation, automatic retry/resume, arbitrary SQL/executable/cwd, production mutation, automatic restore, generic async execution, job listing or change the current synchronous path.
- Task 47 local bounded service-journal reader remains independently prerequisite-safe.
- PR #120 package-version identity fix is separate from this review; it is being revalidated against the Task-44 main before merge.
- Issues #108/#110/#101 retain their existing external/upstream gates.

Immediate resume order:
1. integrate this Task-45 review after exact-head CI;
2. Task 49 may implement only the explicit additive async migration start/status contract;
3. Task 47 remains a separate safe local-only lane and may proceed independently;
4. preserve synchronous `apply_migrations` until/unless Task 49 is separately green and integrated;
5. do not infer completion from bridge/audit records; terminal migration completion comes only from durable migration-job metadata.

## 2026-09-28 — Tasks 48 and 43 complete; migration-job substrate next

- Runner MCP `main` is `a95e75739bb71bcbaf653244e0ebf9c9bee7b0ee`.
- Task 48 is COMPLETE via PR #115 / merge `02475b4c5aa1f103b55f9e4ca6a71e0d09892c7c`: deploy/rollback now share one fixed private release-root `fcntl.flock` boundary in addition to the existing in-process thread lock. Exact-head and post-merge validation are green.
- Task 43 is COMPLETE via PR #116 / merge `a95e75739bb71bcbaf653244e0ebf9c9bee7b0ee`: local-only `retention prune-plan` / `retention prune-release` can remove exactly one freshly eligible staging orphan release per short-lived single-use plan after fresh current/metadata/policy revalidation under the shared release lock.
- Task 43 preserves the retained rollback/reference closure and migration boundaries, never deletes backups, never adds automatic pruning, and adds no MCP/mailbox/bridge deletion authority.
- Quarantine/transaction state is private and durable; post-quarantine failure is reported as manual-attention state rather than guessed success or replay.
- Exact-head Task 43 validation #592, attribution #76, build artifact and clean demo are green; post-merge validation #593 and attribution #77 are green.
- Task 44 durable migration-job substrate is now the preferred next independent CODE lane. Its scope remains additive: persisted migration jobs + read-only completion source only; existing synchronous MCP/bridge `apply_migrations` and deployment-triggered migrations remain unchanged.
- Task 47 local bounded service-journal reader remains independently prerequisite-safe.
- Issue #108 remains externally blocked by the authorized private-host connector quota. Issue #110 remains gated on upstream Fabric durable gateway/startup readiness. Issue #101 remains externally gated for actual secondary-directory submissions/claims.

Immediate resume order:
1. integrate this coordination-only status update after exact-head CI;
2. implement Task 44 from its Task 42 review with a separate private migration-jobs root and strict restart-no-replay semantics;
3. after Task 44 integration, perform Task 45 review before any remote async migration contract change;
4. Task 47 may proceed independently if Task 44 blocks;
5. keep backup pruning, automatic pruning, restore execution and all remote deletion authority deferred.

## 2026-09-27 — Task 46 reconciled; Task 48 release-lock prerequisite queued

- Live Runner MCP `main` before this coordination branch: `37c78fd0d2a0e2f620dc225f81e72843413ef3c3`; PR #113 discovery hardening is merged and post-merge validation #582 / attribution #66 are green.
- The previously unintegrated Task 46 review was reconciled against current `DeploymentManager`. Its core finding still holds: deploy/rollback use only per-process `threading.Lock` instances, so a future local CLI pruning process cannot safely share that mutation boundary.
- Task 46 is therefore COMPLETE as a review and its canonical deliverable is `claude_feedback/TASK46_CROSS_PROCESS_RELEASE_LOCK_REVIEW.md`.
- Task 48 is the separate prerequisite-safe CODE follow-up: add one private release-root `fcntl.flock` primitive and integrate it into deploy/rollback while preserving the existing thread lock and release -> database lock ordering.
- Task 43 local one-release pruning remains BLOCKED until Task 48 is integrated and proven. Do not implement pruning inside Task 48.
- Task 44 durable migration-job substrate and Task 47 local bounded service-journal reader remain independent prerequisite-safe CODE lanes.
- Issue #108 private-host recovery proof remains externally blocked by the authorized remote-management connector quota; do not bypass it with broader authority.
- Issue #110 Fabric bridge activation remains upstream-blocked. Latest checkpoint: Fabric #258 and #266 are merged/green; #256 and #264 remain open on failing/non-mergeable heads; #268 remains open.
- Issue #101 secondary discovery remains externally gated for actual directory submissions/claims; canonical discovery metadata is now hardened on main and the official MCP Registry publicly indexes v0.1.2.

Immediate resume order:
1. integrate this coordination-only Task 46 review after exact-head CI;
2. implement Task 48 as its own bounded code PR with multi-process/adversarial lock tests;
3. only after Task 48, reconsider Task 43 pruning;
4. Task 44 or Task 47 may proceed independently if Task 48 becomes blocked;
5. keep #108/#110/#101 external gates honest; do not convert preparation into claimed proof/publication.

## 2026-09-27 — Runner Fabric coarse bridge transport merged

- Runner MCP transport integration is merged on `main` as `3ebd39981c358c307fa66afa32ad2f5fc32731cf` via PR #111; issue #109 closed automatically as completed.
- Exact PR head `872798831403515bc6944b62efaac5992897b253` passed Runner MCP validation run #571 and commit-attribution run #54 with zero review threads.
- The PR validation checked GitHub's synthetic merge `cd60179b8d8f7c5d8895beef6164a7cb932937fe`, combining #111 with then-current `main` `776b5d0fd3499ca6ed6674806b2075167fc59f9e`; current-main compatibility was therefore validated before merge.
- Post-merge commit-attribution run #55 and Runner MCP validation run #572 are both terminal green on exact merged `main` `3ebd39981c358c307fa66afa32ad2f5fc32731cf`.
- The bridge remains optional and fail-closed: without private loopback Fabric configuration, no Fabric tools are registered and normal Runner MCP behavior is unchanged.
- When configured, the only Fabric-facing tools are `fabric_run_work_unit`, `fabric_get_work_unit` and `fabric_cancel_work_unit`; no generic GitHub, Git, shell, filesystem, provider or status-polling proxy was added.
- Additional hardening on #111 gives each calling thread an independent local MCP session and fails closed on mismatched expected revision, mismatched work-unit identity, or inconsistent status/result pairs.
- Runner Fabric remains the orchestration/control-plane owner. Runner MCP only authenticates, bounds, audits and transports the coarse request/result.
- Issue #110 remains the live activation/end-to-end follow-up. Do not duplicate the merged transport work from #109/#111.
- At this checkpoint Runner Fabric prerequisites are not ready for live activation: #258 and #266 still have failing Foundation CI, #266 is not mergeable, and #268 remains open. Reconcile upstream live state before acting.

Immediate resume order:
1. confirm post-merge Runner MCP validation #572 is terminal green;
2. keep #110 blocked until the required Runner Fabric work-unit service/MCP/startup lanes are green, integrated and privately deployable;
3. once upstream is ready, configure only the private loopback bridge and prove one bounded end-to-end coarse work-unit without exposing infrastructure details;
4. benchmark the coarse handoff against the former many-call GitHub workflow without weakening existing Runner MCP approval, operator-stop or fault-containment boundaries;
5. independent open lanes remain #108 (private-host self-update recovery proof) and #101 (external discovery/authenticated submissions); do not use either to bypass their human/private-environment gates.

## 2026-09-27 — AI fault-containment regression proof merged

- PR #106 merged to `main` as `affc2c054b3072f480822675718baefedc2db619` after exact-head Runner MCP validation and commit-attribution policy both passed, with zero review-thread blockers.
- Cross-boundary security tests now prove that client/AI intent cannot select an unlisted executor capability, mutate an already approved plan, reuse approval across action classes, self-assert production mutation authority or override the external operator emergency stop.
- Read-only work remains available during the operator stop, preserving the proportional-security rule instead of turning every safety state into a blanket development block.
- No new runtime authority was introduced; this slice locks existing executor, approval and operator-safety boundaries with regression coverage.
- Open follow-up #101 tracks secondary discovery; #108 now tracks the remaining private-host proof for recovery-capable self-update. Canonical v0.1.2 publication is already complete, and neither lane should duplicate completed release/runtime work.

## 2026-09-27 — AI fault containment roadmap rule prepared

- Runner MCP now documents AI/client requests as intent rather than execution authority.
- Security gates are proportional to blast radius: contained read/test work stays automatic,
  controlled staging/mutation paths use deterministic policy/freshness/fencing, and protected
  production/credential/destructive actions require independent authority.
- Prompt-injected content cannot create capabilities, weaken policy or satisfy approval.
- This documentation change adds no new runtime authority.

## 2026-09-27 — v0.1.2 canonical distribution published

- Human-approved Publish Runner MCP run #2 completed successfully from exact main `83175f439c60346f92b5759a90993c3b8f5352f8`.
- PyPI published `aifordable-runner-mcp==0.1.2` successfully and the workflow verified that exact version became publicly visible.
- Official MCP Registry validation, GitHub OIDC authentication and publication all succeeded for `io.github.Blacksp1d3r/runner-mcp` version `0.1.2`.
- GitHub pre-release `v0.1.2` was created with wheel and sdist assets; tag `v0.1.2` points exactly to `83175f439c60346f92b5759a90993c3b8f5352f8`.
- Repository description and discovery topics are already live; README/distribution follow-up is moving canonical PyPI/Registry links and one consistent directory-submission packet into the first-party docs.
- Secondary discovery: Glama, Smithery, mcp.so and optional AllMCPs are the next channels. The current GitHub App cannot write to the external `chatmcp/mcpso` submission thread, so that submission needs a user-authenticated browser/CLI path rather than an integration bypass.
- Do not republish or overwrite PyPI 0.1.1. It remains historical evidence of the first PyPI-only attempt; 0.1.2 is the canonical cross-registry release.

## 2026-09-26 — v0.1.1 AIfordable PyPI identity integrated

- PR #102 merged to `main` as `d948945034e07616d673945467e9b2e44748fa10` after exact-head validation and commit-attribution checks were green with zero review threads.
- Post-merge `main` validation and attribution were green on the merge commit.
- Python distribution identity is now `aifordable-runner-mcp`; product/primary CLI remain Runner MCP / `runner-mcp`; `aifordable-runner-mcp` is also exposed as a launcher alias for uvx/Registry compatibility.
- Pending PyPI Trusted Publisher is configured for `aifordable-runner-mcp`, `Blacksp1d3r/runner-mcp`, `publish.yml`, environment `pypi`; GitHub `pypi` is main-only with required human review and no stored PyPI token.
- The previous umbrella brand is retired from current project materials; AIfordable is the current umbrella identity.
- Remaining release action is human-controlled: dispatch `Publish Runner MCP` from `main` with version `0.1.1`, approve the `pypi` environment deployment, then verify PyPI -> MCP Registry -> GitHub pre-release in that fail-closed order.

## 2026-09-26 — v0.1.1 PyPI identity reconciled

- Active branch: `release/v0.1.1-aifordable-pypi`.
- PyPI rejected the new project name `runner-mcp` as too similar to an existing project; no package was published under that name.
- The pending Trusted Publisher is now configured for `aifordable-runner-mcp`, repository `Blacksp1d3r/runner-mcp`, workflow `publish.yml`, environment `pypi`.
- The GitHub `pypi` environment is restricted to `main` and requires the repository owner as reviewer; no long-lived PyPI API token is used.
- This branch changes only distribution/branding metadata: PyPI package `aifordable-runner-mcp`, CLI/product name remains `runner-mcp` / Runner MCP, official MCP Registry identity remains `io.github.blacksp1d3r/runner-mcp`.
- Public umbrella branding is being reconciled to AIfordable; the previous umbrella brand is retired from current project materials. Runtime/security authority remains unchanged.
- Publication remains blocked until this branch is exact-head green, reviewed, merged to `main`, and the human-triggered `Publish Runner MCP` workflow is approved/run for version `0.1.1`.

## 2026-09-26 — v0.1.1 distribution/discovery release prepared

- Active branch: `release/v0.1.1-discovery`.
- This slice changes packaging, discovery, release automation and public positioning only; it adds no new Runner MCP runtime authority.
- Package/version metadata is prepared for `runner-mcp` 0.1.1 and official MCP Registry identity `io.github.blacksp1d3r/runner-mcp`.
- `server.json`, distribution metadata regression tests, PyPI Trusted Publishing guidance and a human-triggered publish workflow are included.
- Publication order is fail-closed: exact release validation and artifact build -> PyPI OIDC publication -> PyPI visibility proof -> MCP Registry GitHub-OIDC publication -> GitHub pre-release.
- External publication is NOT complete yet. The first PyPI release still requires the one-time pending Trusted Publisher configuration plus matching protected GitHub `pypi` environment; then the publish workflow must be explicitly run from merged `main`.
- README/launch copy now lead with the concrete problem: useful AI development/staging operations without making a general-purpose remote shell the normal interface.
## 2026-09-24 — v0.1.0 alpha released and public docs reconciled

- GitHub pre-release `v0.1.0` is published from exact validated release commit `f00ac3fd03df234cb186a4dfcd804136501c0cf7`; the published notes preserve the alpha limitations and validation provenance.
- Post-release docs PR #98 merged as `5647aa8839af90451189d2d943ce393edfacfe78`. Exact PR head `adc08c86628aed6256ba44271d0a55cd366ae3e8` passed run #514 / `36041142332`; merged-main run #515 / `36041352332` is fully green.
- README now links the current alpha, CHANGELOG records the dated 0.1.0 release, and launch-readiness no longer describes the first tag as pending.
- The immutable release reference remains the earlier exact green commit `f00ac3fd03df234cb186a4dfcd804136501c0cf7`; post-release documentation is intentionally later on `main`.
- GitHub repository metadata still needs the prepared public wording: description `Security-first self-hosted MCP for controlled AI development and staging operations without a general-purpose remote shell.`; topics `mcp`, `model-context-protocol`, `self-hosted`, `ai-tools`, `developer-tools`, `devops`, `staging`, `security`, `python`, `automation`.
- Runner Fabric remains a separate private/proprietary project and is not part of the Runner-MCP MIT release.
- Remaining broader-launch gates: clean-host install verification from published `v0.1.0`, repository metadata, then optional ecosystem/registry submission and human-controlled community timing.

## 2026-09-24 — release-track reconciliation after Task 41 integration

- Runner Fabric remains a separate private repository/project. Runner-MCP stays the small, auditable execution product intended for release and must not absorb Runner Fabric orchestration scope.
- PR #97 `feat: add reusable bounded text redaction` merged as `9ce5fe94f417e4e7f910c9945727f70cffd33ecb`.
- Exact PR head `91e0c1b1e737ad14a43b31750cfdfbf1bf582f24` passed validation run `36037258558` fully green: Ruff/pytest/whitespace, clean five-minute demo and built release artifact.
- Live reconciliation after the merge found no open Runner-MCP pull requests and no open Runner-MCP issues.
- This coordination update must itself receive exact-main green CI before any first alpha tag is considered.
- Task 10 private-host self-update/recovery proof remains unproven; release wording must keep that limitation explicit rather than implying live-host proof.
- The next release-track action after exact-main CI is a final alpha-candidate gate check. Tag/release, repository description/topics, registry submission and external posting remain explicit user-controlled actions.

## 2026-09-24 — Task 41 bounded redaction complete; Task 43 lock prerequisite found

- Task 41 implementation is COMPLETE on PR #97 pending final exact-head CI/integration.
- New shared bounded text-redaction primitive handles known secrets, known private paths and the existing bearer/password/token/GitHub-token patterns with explicit input/output byte limits and deterministic truncation.
- TestRunner now delegates its log scrubbing to the shared primitive; no journal reader or remote log authority was added.
- Direct implementation prep for Task 43 found a real safety prerequisite: `DeploymentManager._lock_for()` uses in-process `threading.Lock`, while Task 43 is a local CLI process and can therefore race deploy/rollback in the long-lived MCP process.
- Task 43 is blocked on Task 46 cross-process release-mutation lock review. Do not implement pruning until that boundary is resolved.
- Task 44 is now prerequisite-safe because Task 42 / PR #96 merged as `82ecef725d828b69e328f8f474553e01ef8548cb`.
- Task 47 is queued after Task 41 for a local/private service-journal reader with explicit per-service opt-in only; MCP/mailbox log exposure remains deferred.

## 2026-09-24 — Task 42 durable migration-job substrate review complete

- Task 42 review is COMPLETE on PR #96 pending integration.
- A dedicated persisted migration-job substrate is justified, but it must be additive first: the current MCP/bridge `apply_migrations` path remains synchronous until the substrate is independently proven.
- Future migration jobs must durably persist queued state before worker start, revalidate the exact approval-bound migration plan, call existing `DatabaseManager.apply_migrations()` at most once, and never replay queued/running work after restart.
- Restarted queued/running migration jobs become terminal `interrupted`; ambiguous success is reported for attention rather than guessed or retried.
- Deployment-triggered migrations remain synchronous inside deployment.
- Task 44 is queued for the private job substrate plus read-only completion scanner. Task 45 is separately blocked on Task 44 for any later remote asynchronous integration decision.
- Task 43 is prerequisite-safe after Task 40 / PR #95; Task 39 is already integrated on main via PR #94.

## 2026-09-24 — Task 39 adapter preset boundary refactor complete on PR #94

- Task 39 implementation is COMPLETE on PR #94 pending final exact-head CI/integration.
- Built-in pytest, Ruff and Alembic recipe materialization moved out of generic `config_manager.py` framework branches and behind typed adapter methods.
- Python adapter executable discovery remains project-local, rejects symlinked roots/virtualenvs/executables, requires executable access and verifies the resolved executable remains under the project root.
- The generic adapter has no built-in recipe authority. Unknown/ambiguous presets fail closed.
- The `custom` path remains explicit/local with the previous validation and no shell command string.
- Direct adapter/config-manager regression coverage and extension documentation were updated.
- No dynamic plugin loading, framework dependency, speculative adapter or new execution authority was added.
- Tasks 37 and 40 are already integrated on main; Task 43 remains blocked only on its explicit ownership/implementation claim, not on Task 40.

## 2026-09-24 — Task 40 retention pruning execute-boundary review complete

- Task 40 review is COMPLETE on `chatgpt/task40-retention-pruning-review` pending integration.
- Task 34 evidence is sufficient for one conservative next mutation only: local/manual pruning of exactly one old non-migration orphan release outside the entire retained rollback chain.
- The first executable slice must preserve current/direct rollback/reference closure and every migration-boundary release, acquire the deployment lock, recompute eligibility, bind a short-lived local plan, quarantine atomically, and use only symlink-safe fd-relative recursive deletion.
- Manual backups remain indefinite-retention/non-candidates. Backup pair pruning remains separately deferred because flat dump+metadata deletion needs its own durable crash-recovery transaction.
- Automatic/unattended pruning and all MCP/mailbox deletion authority remain deferred.
- Task 43 is queued but blocked until Task 40 is integrated.

## 2026-09-24 — Task 34 read-only retention preview implementation complete on PR #92

- Task 34 implementation is COMPLETE on PR #92 pending final exact-head CI/integration.
- New local CLI: `runner-mcp retention preview PROJECT`.
- Preview is advisory only and explicitly reports `deletion_authorized=false`; no release, backup or metadata deletion/rewrite path was added.
- Strict scanning fails closed on unsafe/symlink/broad-permission/malformed release or backup metadata, incomplete backup pairs and dump-size mismatch.
- Current release, direct rollback target, retained release references and migration-recovery references are protected; manual backups are never automatically eligible.
- Production/non-staging projects remain read-only; preview remains available while the emergency stop is active.
- Public output contains only bounded project/environment/ID/timestamp/kind/category state and does not expose filesystem paths, DSN, service units, health URLs, dump content or private configuration.
- Focused tests plus the full suite have passed during implementation; final exact-head PR CI remains authoritative before merge.
- Actual pruning/deletion remains deferred. A later execute-boundary review must separately resolve locking, crash-safe deletion, rollback-chain semantics and typed confirmation.
- PR #91 already merged as `11b9a4d4e508ac93cd436037563c09d08cfa43ab`, completing Tasks 33, 35 and 38.
- Task 37 restore-execution boundary review is proceeding independently on PR #93; Task 39 is now prerequisite-safe after Task 38 integration.

## 2026-09-24 — Tasks 32 and 36 alpha-readiness work landed

- Task 32 COMPLETE: PR #89 merged as `e629515f9c7e7a5d44506dfb82a48343870f94da`.
- Task 32 exact PR head `99c72037eff4ed54cf7e92f7a08b278b48af4e45` passed CI run 35967246877 fully green: Ruff, whitespace, 1267 pytest tests, built release artifact and clean demo.
- Audit conclusion: package/build/demo mechanics are suitable for an alpha candidate, but six public-documentation drift items had to be reconciled before any tag.
- Task 36 COMPLETE: PR #90 merged as `8c971016e4fc3cd821dc52d28334567c20835ff4`.
- Task 36 exact PR head `1b3567b5de1f5a4ac5a67db16c609db2edac25dd` passed CI run 35967550375 fully green: Ruff, whitespace, 1267 pytest tests, built release artifact and clean demo.
- CHANGELOG now treats 0.1.0 as an unreleased alpha candidate; restore/security wording, mailbox launch copy, README rendering, public-data hygiene wording and connectivity limitation are reconciled.
- Live GitHub still has no `v0.1.0` tag or GitHub release. Repository description/topics, tag/release, registry submission and external posts remain explicit user-controlled actions.
- Task 10 private-host live self-update/recovery proof remains externally BLOCKED and must not be overclaimed in release wording.
- Current bounded queue: Tasks 33–35. No release/publication action was performed.

## 2026-09-24 — Task 31 local read-only restore preflight landed

- Task 31 COMPLETE: PR #88 merged as `e54a0684bdc9da3a32d062e0e0e45261c1616020`.
- Exact PR head `fc08b60c6feed85824b6097bf1479e7e41a29844` passed CI run 35966414093 fully green: Ruff, whitespace, 1267 pytest tests, built release artifact and clean demo.
- Local CLI now supports `runner-mcp database restore-plan PROJECT BACKUP_ID` for a read-only PostgreSQL backup preflight.
- The preflight validates strict backup identity/shape, private regular-file modes, size, symlink-free storage and fixed trusted `pg_restore --list` parseability without reading the configured DSN or connecting to a database.
- The archive is opened once with no-follow semantics, streamed through SHA-256 privately, passed to `pg_restore` over stdin so the private dump path is not placed in argv, and revalidated/hash-checked after parse to detect content/permission races.
- Production projects report ineligible. Emergency stop does not block the read-only preflight.
- Database restore execution, pre-restore backup, restore approval authority, WAL/PITR, production recovery and MCP/bridge/mailbox restore exposure remain deferred.
- Current bounded queue: Tasks 32–34. Task 10 remains externally BLOCKED.

## 2026-09-24 — Task 30 retention-pruning boundary review landed

- Task 30 COMPLETE: PR #87 merged as `99d081cd242642bfa8346031a22079b7397869bc`.
- Exact PR head `0a6e09fe4e4cd403c6ee6c4cc66461694b019a2a` passed CI run 35958661041 fully green: Ruff, whitespace, 1237 pytest tests, built release artifact and clean demo.
- Review conclusion: existing age/count predicates are policy inputs, not destructive authorization. Manual backups have no automatic-deletion policy; current/rollback/reference/migration-recovery relationships require additional protection.
- Automatic deletion remains deferred. Task 34 is queued as the smallest safe follow-up: local read-only retention preview only.
- Current bounded queue: Tasks 31–34. Task 10 remains externally BLOCKED.
- No backup/release deletion, metadata rewrite, retention change, approval expansion or mailbox deletion authority was performed.

## 2026-09-24 — Task 29 privacy-safe connectivity guidance landed

- Task 29 COMPLETE: PR #86 merged as `b0f54cb14d73fba3b7c5b8655b5b051af779fd0a`.
- Exact PR head `7d4c264fbfac6881badbdf8f9bc69ea7a7ab12e8` passed CI run 35958283065 fully green: Ruff, whitespace, 1237 pytest tests, built release artifact and clean demo.
- `runner-mcp guide` now reports only a generic connectivity category and bounded next steps. Configured external hostnames/resource URLs/auth issuers/tokens/private paths are not printed.
- Public setup is now documented consistently as external HTTPS identity only; it does not bind publicly or configure TLS, DNS, firewall, proxy or tunnel state.
- Current Secure MCP Tunnel guidance is linked to canonical OpenAI documentation; Runner MCP remains loopback-first and vendor provisioning stays external.
- Current bounded queue: Tasks 30–32. Task 10 remains externally BLOCKED.
- No network exposure, TLS/DNS/firewall, tunnel, tag, release or publication action was performed.

## 2026-09-24 — Task 28 deployment/rollback completion delivery landed

- Task 28 COMPLETE: PR #85 merged as `131e168e02b7d5781441bbc8256e65de434e6166`.
- Exact PR head `87f1d0c8295b059b4504e2971c5ef89ed9dc8422` passed CI run 35951310986 fully green: Ruff, whitespace, 1235 pytest tests, built release artifact and clean demo.
- Completion delivery now scans configured deployment/rollback job metadata read-only and never instantiates `DeploymentJobRunner`.
- Strict validation requires exact lowercase 32-hex job identity, explicit deploy/rollback operation, safe project, known state, private regular metadata and timezone-aware terminal timestamp; malformed/duplicate/non-finite/oversized/unsafe metadata fails closed.
- Deploy and rollback events use source-scoped deterministic IDs and the existing bootstrap cutoff, local delivery ledger and remote marker idempotency.
- Notification bodies omit `Test profile: None` for non-test events and expose only validated project, allow-listed operation, state and event ID. Deployment result/error/commit/release/path metadata is not copied.
- Migration completion remains blocked pending a separately reviewed durable migration-job substrate.
- Current bounded queue: Tasks 29–31. Task 10 remains externally BLOCKED.
- No tag, release, publication, deployment, rollback, migration or external mutation was performed by this task.

## 2026-09-24 — Task 27 database restore/recovery review landed

- Task 27 COMPLETE: PR #84 merged as `f1e92bb2997ad8b9d26e978892319289e1b7e4f1`.
- Exact PR head `a90667259b7dea7d6dcddf1ead26fc982d4fb893` passed CI run 35949363983 fully green: Ruff, whitespace, 1211 pytest tests, built release artifact and clean demo.
- Review preserves the hard separation between code rollback, one-backup logical restore and WAL/PITR. Automatic/remote restore remains unavailable; production restore remains outside Runner MCP mutation authority.
- Task 31 queued as the smallest safe follow-up: local read-only restore preflight/plan only, with strict backup identity/privacy and fixed pg_restore parseability checks; no database mutation or MCP/mailbox restore action.
- Task 10 remains externally BLOCKED. Current bounded queue: Tasks 28–31.
- No tag, release, publication, deployment, migration, restore, deletion or external database action was performed.

## 2026-09-24 — Task 26 bounded service-journal review landed

- Task 26 COMPLETE: PR #83 merged as `b08a0b10afcce754440c37025230773da72c6c05`.
- Exact PR head `faa5126548021c9294e3a395c6b71344505e545d` passed CI run 35949004101 fully green: Ruff, whitespace, 1211 pytest tests, built release artifact and clean demo.
- Review conclusion: remote/MCP service-journal access stays deferred. Current alias/process boundaries are strong, but arbitrary application journal content needs an explicit per-service log-read opt-in and a reusable bounded text-redaction prerequisite before any local reader is justified.
- Task 30 was added from the roadmap's explicit deferred retention-pruning work to keep the public queue dependency-safe.
- Task 10 remains externally BLOCKED. Current bounded queue: Tasks 27–30.
- No tag, release, publication, deployment, migration, restore, log exposure or deletion was performed.

## 2026-09-24 — Task 25 private connectivity/TLS onboarding review landed

- Task 25 COMPLETE: PR #82 merged as `f2c1d6a135133033ab1e0059f9a92cfec3021d88`.
- Exact PR head `38b3143d53d49c58af896adfe96b943e34c2ee5a` passed CI run 35948648167 fully green: Ruff, whitespace, 1211 pytest tests, built release artifact and clean demo.
- Review confirms Runner MCP already preserves the required runtime safety boundary: setup does not mutate network exposure, serve/autostart remain loopback-first, non-loopback bind requires explicit override, and non-loopback HTTP is rejected/flagged.
- Demonstrated onboarding drift: `security/CONNECTIVITY.md` still describes Secure MCP Tunnel as a future connection, while current official OpenAI guidance and Runner MCP's own README/Quickstart describe it as available for supported products.
- Task 29 queued for documentation + privacy-safe guide reconciliation only; it must not configure TLS, DNS, firewall, reverse proxy or tunnel state.
- Task 10 remains externally BLOCKED. Current bounded queue: Tasks 26–29.
- No tag, release, publication, deployment, migration, restore or network mutation was performed.

## 2026-09-24 — Task 24 completion-delivery expansion review landed

- Task 24 COMPLETE: PR #81 merged as `d9f7d40f952ab39478d4a0286d317f160d6b46ce`.
- Exact PR head `22d5e9a7c7e5ab854b81d84b7b9997202837caf4` passed CI run 35915217076 fully green: Ruff, whitespace, 1211 pytest tests, built release artifact and clean demo.
- Review finding: persisted deployment and rollback jobs are safe candidates for one bounded read-only completion-delivery integration; migration completion is blocked because no dedicated persisted migration-job substrate exists.
- Task 28 queued from this evidence for deployment/rollback completion delivery only.
- Task 10 remains externally BLOCKED. Current bounded queue: Tasks 25–28.
- No tag, release, publication, deployment, migration or database action was performed.

## 2026-09-23 — Task 23 completion watcher diagnostics landed

- Task 23 COMPLETE: PR #80 merged as `873f905c64cdfbfc0ec6ac4b5091c04877b84d59`.
- Exact PR head `595bb6466e7eca50b4b21a9dbc8695a59b248c11` passed CI run 35914643900 fully green: Ruff, whitespace, 1211 pytest tests, built release artifact and clean demo.
- `CompletionNotifierRuntime.run_forever()` now emits only enum-rendered lifecycle, healthy/degraded cycle and bounded restart-failure diagnostics through an optional sink.
- Delivery/replay/idempotency behavior remains unchanged; tests inject repository/path/token/event/URL/exception literals and prove they cannot enter diagnostics.
- Task 10 remains externally BLOCKED. Current bounded queue: Tasks 24, 25 and 26.
- No tag, release, publication, deployment or migration was performed.

## 2026-09-23 — Task 22 cron supervisor diagnostics landed

- Task 22 COMPLETE: PR #79 merged as `1bfeb9e7e8991058fb82a31b6d93b94f77c5ba72`.
- Exact PR head `65e15a9654e131073d8e90dc90cfa5e0536b9781` passed CI run 35903803377 fully green: Ruff, whitespace, 1208 pytest tests, built release artifact and clean demo.
- `run_cron_component()` now emits only enum-rendered `cron_supervisor` diagnostics for lock-held, exec handoff and bounded start/restart failure states through an optional sink.
- Diagnostics contain no selected component, argv, executable/config path, environment value or raw exception text; adversarial tests inject sensitive literals and prove they cannot escape.
- Cron ownership, locking, command construction and execution authority were not changed.
- Task 10 remains externally BLOCKED. Current bounded queue: Tasks 23, 24 and 25.
- No tag, release, publication, deployment or migration was performed.

## 2026-09-23 — Task 21 managed autostart secure I/O landed

- Task 21 COMPLETE: PR #78 merged as `22e14fff99a4f02a30f2edf9abffd98a8b1792ea`.
- Exact PR head `01ee0c0bfeaeae8f3a07a47f4162d4f9560304ab` passed CI run 35903107229 fully green: Ruff, whitespace, 1207 pytest tests, built release artifact and clean demo.
- `autostart._write_managed_unit` now uses the shared private atomic-replace primitive while preserving the existing managed-marker ownership refusal.
- Regressions prove unmanaged unit content is preserved, successful writes end at 0600, fsync/replace failures keep the previous managed unit and emit only bounded errors, and a symlink swap cannot alter its referent.
- Cron, job metadata, ledgers, create-only writers, deployment activation/tar extraction and self-update were not changed.
- Queue refilled from explicit roadmap items: Tasks 22 and 23 remain CODE lanes; Tasks 24 and 25 are bounded CHAT REVIEW lanes for completion-delivery expansion and private connectivity/TLS onboarding.
- Task 10 remains externally BLOCKED on a usable private-host proof path. No tag, release, publication, deployment or migration was performed.

## 2026-09-23 — Task 20 bridge adversarial matrix landed

- Task 20 COMPLETE: PR #77 merged as `4bfd71d85cb5228ba328ee17fc60414c84c43e0a`.
- Exact PR head `666a399803db41bae4deae73fc4f205de5e97854` passed CI run 35895116909 fully green: Ruff, whitespace, 1203 pytest tests, built release artifact and clean demo.
- Test-only hardening: one minimal valid fixture now exists for every BridgeAction, every syntactically valid non-owned optional field is rejected per action, action case/hyphen/prefix variants fail closed, duplicate request_id and request-side NaN/Infinity fail closed, and uppercase self-update commit remains rejected.
- Every adversarial rejection is exercised through BridgeProcessor with fail-if-reached replay/result boundaries and an executor invocation counter, proving invalid requests do not reach execution.
- No production protocol, action enum, alias, normalization, identifier regex, replay state, executor mapping or capability changed.
- Current UNCLAIMED bounded public queue: Tasks 21, 22 and 23. Task 10 remains externally BLOCKED.
- No tag, release, publication, deployment or migration was performed.

## 2026-09-23 — Task 18 private atomic-replace hardening landed

- Task 18 COMPLETE: PR #76 merged as `5c4f5db350cdafa99066bdb091866b7d6979a7a9`.
- Exact PR head `97fcde693d6264171920c386d10e9e63403a9a9a` passed CI run 35894315537 fully green: Ruff, whitespace, 794 pytest tests, built release artifact and clean demo.
- Added one internal `secure_io.atomic_replace_private` overwrite primitive using a random same-directory temp, exact 0600 descriptor mode, file fsync before atomic replace, symlink refusal, ordinary-failure cleanup and bounded errors.
- `config_manager` and `approval_manager` now use the primitive while retaining their existing higher-level locks and serialization/state ordering.
- Completion notifier config/bootstrap private JSON state now uses the primitive while retaining size/schema checks and parent-creation behavior.
- Autostart, cron, high-churn job metadata, in-place ledgers, create-only writers, deployment activation/tar extraction and self-update were not changed.
- Queue refilled from existing review evidence: Tasks 20, 21, 22 and 23 are UNCLAIMED; Task 10 remains externally BLOCKED on a private-host proof path.
- No tag, release, publication, deployment or migration was performed.

## 2026-09-23 — Tasks 16/17 landed and session reconciled

- Canonical main checkpoint after PR #74: `3d7792ee088a10ca44126415394e74c8e3c29ce3`.
- Task 16 COMPLETE: adversarial protocol review merged via PR #72; no runtime capability-expansion defect demonstrated; bounded follow-up Task 20 queued for exhaustive fail-closed regression coverage.
- Task 17 COMPLETE: append-only audit writer hardening merged via PR #73. Exact final head `60466a72b1c8492eac54e4963b9d7ef4bb572977` passed CI run 35891213181 fully green.
- PR #74 merged the queue/agent handoff evidence for Tasks 16/17.
- Task 10 remains externally BLOCKED pending a usable private-host proof path.
- Next safe implementation work is Task 18 or Task 20 after live ownership reconciliation.
- No release/tag/publication was authorized or performed.

## 2026-09-23 — v0.1.0 public release docs prepared

- PR #57 merged: the changelog now has a dated v0.1.0 release-candidate section and Unreleased is reopened.
- `docs/RELEASE_NOTES_0.1.0.md` now covers the completed self-update hardening, bounded runtime visibility and the no-dependency bootstrap boundary.
- The release notes explicitly state that the newest private-host self-update recovery matrix has not yet been freshly re-proven.
- No tag, GitHub release or external publication has been created.
- After this handoff-only update lands, the resulting exact `main` commit must pass public CI and a final privacy review before it can be considered a tag candidate.
- The remaining non-public evidence item is the private-host live self-update proof; if it is not completed before release, the limitation must remain explicit.

## 2026-09-23 — Tasks 2–9 queue complete

Current public repository state:
- PR #53 merged as `0c46bbefb8fcad6ae5c7f87450e638c40492a41a`: Task 6 documentation/CLI contract audit complete; `runtime_doctor` is documented and the stale evergreen pre-tag test count is gone.
- PR #54 merged as `69e604935bfe0fef0dd61b48dfdde76fed8f46ba`: Task 7 dependency compatibility/bootstrap design complete; `docs/SELF_UPDATE_COMPATIBILITY.md` is the canonical boundary.
- PR #55 merged as `358f8f6345a7ff6f094eb6c8e4d7db4b9943aed7`: Task 9 release-candidate hygiene dry run complete.
- Tasks 2–9 are complete; no open Runner-MCP PR existed when this checkpoint was reconciled.
- No tag, release or external artifact has been created.

Next safe release-preparation work:
- finalize the v0.1.0 changelog and release-notes draft;
- validate the exact candidate commit and repeat public-repository privacy review before any tag;
- keep dependency/build/interpreter contract changes on the normal dependency-resolving bootstrap path;
- reconcile the remaining private-host self-update live proof, or explicitly retain that limitation in release notes.

Private runtime state:
- this batch did not re-probe the private host;
- older watcher recovery-attention observations remain historical/last-known, not current health evidence;
- never reset watcher replay/cursor/transaction state as a shortcut.

## 2026-09-22 — Task 8 checkpoint

- PR #52 merged as `d6821ddb0773b586b6a106b66b2e18154c90cc7a`.
- local release validation now has one fail-fast wrapper: `bash scripts/release-check.sh`;
- the wrapper covers compile, Ruff, pytest, branch/local whitespace, built-artifact smoke and clean-demo smoke while explicitly leaving GitHub CI authoritative;
- the clean demo no longer creates or deletes the repository's developer `.venv`; its project virtualenv lives under the temporary demo root;
- Task 6 audit has one demonstrated documentation drift ready for the next slice: `runtime_doctor` exists in the bridge protocol/executor/server but is omitted from README and the public bridge supported-action list;
- private watcher/recovery state was not re-probed in this batch.

## 2026-09-22 — current reconciliation checkpoint

Current public GitHub state:
- `main` includes PR #46 installer/operator robustness, PR #47 secure-I/O inventory, PR #48 self-update durability fsync hardening, PR #49 safe diagnostics contract, PR #50 CLI removal-confirmation deduplication and PR #51 reconciled self-update recovery visibility.
- PR #51 merged as `011fcbfec4e0b75a93820ca1c4c487111da6b495` after current-main CI passed Ruff, 773 pytest tests, whitespace validation, clean demo and built release artifact.
- stale PR #45 was closed unmerged after its functionality was rebuilt on current main in #51.
- there are no open Runner-MCP pull requests at this checkpoint.
- self-update transaction and installed-state markers now flush/fsync the file before replace and fsync the parent directory after replace.
- local `status` exposes install recovery only as `clear`, `REQUIRED` or `INVALID`; `doctor` warns/fails on pending/invalid recovery without exposing transaction details.
- watcher/notifier/supervisor diagnostics now have a category-only safe contract; production logging integration remains a separate later slice.
- ordinary REMOVE-style CLI confirmations share one narrow helper; emergency-stop, approval, watcher-recovery and self-update-recovery confirmations remain separate.

Agent-capacity policy:
- analysis/design-heavy Claude work is marked `CHAT REVIEW` and should be done in normal Claude chat rather than Claude Code;
- ChatGPT is the default implementer for CODE work unless explicitly reassigned;
- a Claude rate limit never blocks the critical path.

Private runtime state was not re-probed during this GitHub-only reconciliation. The prior handoff's degraded watcher/recovery-attention observation therefore remains historical/last-known, not a newly verified current fact.

## Controlled multi-project concurrency — 2026-09-21

Bounded fair multi-project concurrency is merged and validated. Runner MCP now separates mailbox acceptance from durable test execution, maintains fair logical per-project queues, returns immediate job IDs, exposes safe queue/worker/job state, and keeps same-project overlap opt-in only. High-risk mailbox actions remain excluded.

The authenticated MCP request limit was also raised from 60 to a still-bounded 600 requests per minute so concurrent mailbox workers and normal status polling do not hit a transport bottleneck before worker or queue capacity. Test-worker, project-lock and queue limits remain independent safety controls.

## Shared watcher migration proof — 2026-09-21

A private deployment has been migrated from the pilot poller to the shared `runner-mcp github-watcher run` runtime. The watcher was explicitly bootstrapped at the current request head, so historical mailbox entries were not replayed. After fresh requests and a package restart, the private cursor matched the request head, the replay ledger contained only completed records, and the heartbeat reported healthy with zero recovery attention.

Live protocol-v1 checks completed for `project_status`, `project_capabilities`, `list_test_profiles`, `queue_status` and `worker_status`. A real predefined test request was accepted asynchronously and later reached a terminal passed state through `job_status`. During that proof, the MCP SDK's multi-item encoding for list-returning tools exposed a compatibility gap; the loopback executor was hardened to accept bounded object-only multi-item list results while scalar tools remain fail-closed.

The legacy private poller is disabled in that deployment. Completion-notification transport remains an independent capacity concern and is not part of mailbox execution authority.

# Current state

Date: 2026-09-21

## Safe project sync and adapter test presets — 2026-09-21
- Added a narrow `sync_project(project, commit)` mailbox capability for staging validation. The request accepts only an allow-listed project code and a full 40-character commit ID.
- Source sync requires a clean worktree, blocks submodules, validates that `origin` is exactly the configured GitHub repository, fetches with Git hooks disabled and terminal prompting off, verifies the commit is reachable from `origin/*`, and checks out the exact commit detached.
- Source sync refuses to run while that project's tests are queued or active. No branch, remote, filesystem path, executable, command, service or environment variable can be supplied by the mailbox.
- Python projects now expose fixed safe adapter presets `pytest` and `ruff` when the required executable is detected in `.venv/bin` or `venv/bin`. Configured profiles still take precedence.
- Adapter presets use fixed argv/cwd/env/timeout definitions. `custom` is deliberately excluded from implicit mailbox availability.
- Added protocol, executor, source-control and test-runner regression coverage for commit pinning, extra-field rejection, busy-project rejection, safe preset discovery/execution and custom-preset denial.
- This change does not enable migration, deployment, rollback, arbitrary shell or arbitrary Git ref execution through the mailbox.

Runtime observability bridge — 2026-09-21:
- added fixed read-only `runtime_status` and `runtime_doctor` MCP/bridge actions;
- output is intentionally host-neutral: version, safe capacity/configuration booleans and bounded check summaries only;
- private paths, endpoints, hostnames, environment values, service units and raw process output remain excluded;
- this is the first self-operations step toward removing routine dependence on general-purpose remote desktop tooling.

Shared Playwright runtime — 2026-09-21:
- Runner MCP E2E jobs previously replaced HOME and therefore could not see a shared Playwright/Chromium cache unless it was passed through manually;
- test profiles can now declare `runtime: playwright`;
- the browser cache comes only from private `RUNNER_MCP_PLAYWRIGHT_BROWSERS_PATH`, is locally validated and is scrubbed from logs;
- missing or unsafe browser runtime fails closed; PastEntrance does not need a project-code workaround for this boundary.

Runner MCP self-update — 2026-09-21:
- added fixed `self_update(commit)` and `self_update_status(job_id)` operations for the configured canonical Runner MCP project;
- commits are lowercase full object IDs and must be reachable from `origin/main`; direct MCP calls and mailbox calls enforce the same lowercase boundary;
- lint and unit profiles gate installation, and the source commit is rechecked immediately before the fixed local install;
- server, GitHub watcher and completion watcher use component-specific restart/reexec paths; callers cannot choose executables, commands, services or paths;
- private job/state/restart metadata is permission-restricted and restart recovery marks unfinished update jobs interrupted rather than replaying them;
- the current read-only `runtime_status` and `runtime_doctor` behavior is preserved, with self-update readiness/state added to runtime status;
- the local MCP bridge allow-list now explicitly includes both observability actions as well as the two self-update actions, closing the gap where protocol support existed but local dispatch could still reject runtime observability;
- arbitrary package-manager arguments, repositories, refs, paths, environment values, process controls and general remote-shell behavior remain excluded.


Self-update hardening follow-up — 2026-09-22:
- review of PR #37 found and fixed three integration gaps before merge: local MCP dispatch had not allow-listed runtime observability, the direct self-update capability normalized uppercase commits instead of rejecting them, and `self_update_status` was present in the enum/mapping but missing from strict request validation;
- the self-update source is now guarded across post-sync verification, lint, unit and install, closing the window where another source sync could change the checkout between validation steps;
- the project source guard was made re-entrant so the self-update orchestration can hold it while existing test-start/install paths safely re-enter it;
- PR #37 merged as `8570f842ffad5282bb28a89a77bcbcba5dd01bcd` after clean five-minute demo, built-artifact validation, Ruff and 704 pytest tests all passed.

Self-update activation recovery — 2026-09-22:
- follow-up work makes restart intent durable across fixed-component re-exec failure rather than consuming the marker before an unsuccessful activation;
- restart markers now cover server, GitHub watcher and completion watcher, are create-once and are batch-prepared so partial marker creation is rolled back;
- a new self-update is refused while any fixed activation marker remains pending;
- runtime status exposes only a boolean pending state and bounded fixed-component count, not paths/process identifiers;
- server self-reexec retries are bounded; watcher/notifier re-exec failure restores the marker so managed systemd/cron supervision can retry after process restart;
- failures after package installation are distinguished as activation failures with restart required, while pre-install failures remain ordinary self-update failures;
- package-install rollback remains a separate future hardening item; this slice improves activation recovery without claiming atomic package rollback.

Activation recovery merged — 2026-09-22:
- PR #40 merged as `1d160afdb9c0b6e0d3ebb3a74b88644b84eb348e`;
- validation was fully green: Ruff, 708 pytest tests, clean five-minute demo and built-release artifact;
- fixed-component restart intent now survives a failed re-exec, pending activation blocks overlapping self-updates, and runtime status reports only a bounded pending state/count;
- issue #7 (mailbox liveness/stale-request recovery) was closed as completed because its heartbeat, retry and fail-closed recovery scope is already implemented and live-proven;
- next self-update hardening target is package-install rollback/staging; current activation recovery does not claim atomic recovery from a failed in-place pip installation.


## 2026-09-22 — external review triage and low-risk cleanup

Claude's read-only review branch `claude/roadmap-review-suggestions-xxbhfo` was evaluated against the newer main baseline rather than merged wholesale. The review branch was based on `319259c7...`, before the commit-pinned self-update and recoverable activation work, so its exact test counts and some roadmap observations were already stale.

Accepted low-risk findings in this slice:
- gate the demo-smoke and release-artifact CI jobs on the main validate job so obviously invalid commits do not spend extra runner time;
- expose the validation workflow status from README and clarify that the operator wrapper is unnecessary for same-account installs;
- define status authority explicitly: roadmap for architectural phase status, handover for chronology, CI/release records for exact validation results;
- reconcile stale roadmap "Next" items that still described watcher migration, coordinator integration, completion proof and self-operation work that is already implemented;
- add direct unit coverage for the append-only audit logger and its 0600 file-permission contract.

Deferred rather than applied blindly:
- a shared `secure_io` rewrite: worthwhile, but the existing atomic/private-write call sites have different lifecycle and failure semantics, so this needs an inventory plus dedicated regression tests rather than a mechanical replacement;
- a generic audited-tool decorator: potentially useful, but audit payloads and failure categories differ by tool family and should not be homogenized without a separate design/test slice;
- watcher `logging`: operationally useful, but must first define a scrubbed, category-only logging contract so diagnostics cannot become a new private-data leak;
- large `server.py`/`cli.py` splits and adapter plug-in discovery: maintenance work, not current safety or self-update blockers;
- a full roadmap status table: not added because it would duplicate per-phase status and create another drift surface. The source-of-truth rule and stale-status cleanup address the underlying problem with less duplication.

The next functional priority remains the staged/rollback-capable self-update package-install strategy, plus live bootstrap/proof on the private host when that host can be upgraded through an available safe path.


Review cleanup merged — 2026-09-22:
- PR #41 merged as `0e66368ca1377359019de1d594833377892db7aa`;
- validation: Ruff and whitespace checks green, pytest 711 passed with one known third-party warning, clean demo green, built release artifact green;
- Claude's review branch remains unmerged by design; only independently revalidated low-risk findings were adopted;
- next functional target remains staged/rollback-capable self-update installation plus live private-host bootstrap/proof.


Self-update package-install recovery hardening — 2026-09-22:
- PR #43 stages the validated target as a private wheel instead of installing directly from the checkout;
- when a known installed baseline exists, a private recovery wheel is built before source sync while the project source guard remains held across baseline staging, target sync, lint/unit validation, target staging and package mutation;
- a strict private 0600 install-transaction marker is persisted before the in-place pip operation; pending recovery is exposed only as a bounded boolean and blocks overlapping self-updates;
- target installation must also pass a fresh-process Runner MCP import verification;
- a caught target install/import failure rolls back only when both baseline-package reinstall/import verification and exact baseline source restoration succeed; otherwise the transaction remains fail-closed as `install_recovery_required`;
- same-commit self-update requests still verify reachability through `origin/main` and then avoid unnecessary reinstall/restart;
- clean CI exposed that offline `--no-build-isolation` wheel staging requires the setuptools build backend to remain available at runtime, so `setuptools>=75` is now an explicit runtime dependency; this dependency-set change reinforces that the first private-host bootstrap must use the normal dependency-resolving installation path;
- the current design deliberately does not claim atomic in-place pip mutation. A process interruption can leave an install transaction pending; the next hardening slice is a bounded local recovery command before live package-install fault injection.


Package-install recovery merged — 2026-09-22:
- PR #43 merged as `2b7dac9fb3c9e5168c07c7967333995b646957de`;
- final validation was fully green: Ruff, whitespace, 742 pytest tests with one known third-party warning, clean five-minute demo and built release artifact;
- the source guard now remains held through installed-state persistence, restart-marker preparation and install-transaction finalization, closing a final post-install source-race window;
- the next hardening target is a bounded local operator recovery command for persisted install transactions; live package-interruption fault injection remains deferred until that local recovery path exists.


## 2026-09-22 — bounded local self-update install recovery

A local operator-only recovery path is being added for persisted rollback-capable self-update install transactions:
- `runner-mcp self-update-recovery` is local CLI only; it is not mapped into MCP or the GitHub mailbox;
- recovery requires the operator emergency stop to be active and exact confirmation `RECOVER SELF UPDATE`;
- only the private staged baseline wheel from the persisted transaction can be used;
- the installed package is reinstalled and import-verified, source is restored to the exact baseline commit reachable from `origin/main`, and installed-state metadata is reset to that same commit;
- the transaction is cleared only after all of those checks succeed; otherwise recovery remains pending and further self-update stays blocked;
- bootstrap/first-install transactions without a known baseline are deliberately not auto-recoverable;
- pending activation markers and install recovery are not allowed to overlap.


Local install recovery merged — 2026-09-22:
- PR #44 merged as `3ce122012d56ead3fbf75dfbf8fe770572f3ed47`;
- validation was fully green: Ruff, whitespace, 753 pytest tests with one known third-party warning, clean five-minute demo and built release artifact;
- persisted rollback-capable self-update transactions can now be recovered only through local `runner-mcp self-update-recovery`, with the operator emergency stop active and exact confirmation;
- the recovery path restores the private staged baseline package, fresh-process import validity, exact baseline source commit and installed-state metadata before clearing the transaction;
- bootstrap/no-baseline transactions and overlapping activation recovery remain fail-closed;
- no install-recovery action was added to MCP or the GitHub mailbox;
- next: bootstrap this merged baseline on the private host and prove same-commit, forward-update and deliberately interrupted/recovered package-install paths through the safe operating model.

## Coordination checkpoint — 2026-09-22

Canonical coordination now uses `SESSION_HANDOFF.md`, `AGENT_EXCHANGE.md` and `RESUME_PROMPT.md`. GitHub live state wins over stale handoff text.

Immediate priority:
1. reconcile the four private watcher recovery-attention items without replay/reset shortcuts;
2. confirm the pending read-only runtime-status probe;
3. reconcile and, if still green/current, merge PR #45;
4. bootstrap/prove the newest recovery-capable self-update baseline on the private host.

Current blocker: watcher heartbeat is degraded by four recovery-attention items, so cursor advancement is intentionally withheld. Desktop Commander is unavailable; use GitHub plus the bounded Runner-MCP bridge.


## Agent Bus architecture correction — 2026-09-29

A GitHub primary-rate-limit incident proved that the mailbox cannot remain operationally primary.
The required target is now explicit: AIfordable-owned durable relay + outbound-only Runner Fabric
Agent Bus. GitHub remains source/CI during migration and later optional mirror/bootstrap/fallback.
Runner MCP #125/#130 and Runner Fabric #356 track the implementation and live cutover.
