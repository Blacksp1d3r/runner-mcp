## 2026-10-09 — Windows source prerequisites integrated; runtime still gated

Source-only host platform contract #490 (merge `816c7e5abd5ddbf91d0e580e6a7102bb0308faf0`) and explicit non-Linux default service backend rejection #619 (merge `bac86a97f1493ff943ef5f3d01228814e3ed61c0`) both passed exact-head attribution and full Runner MCP validation. Windows is recognized but `serviceAdapterImplemented=false`, and `ServiceManager` now fails closed rather than attempting Linux systemd on a Windows/unknown host. This is **not** Windows SCM support, Windows autostart, customer-host qualification or activation. No live Windows test or deployment was attempted.

Next permissible #489 child: explicit fixed-alias Windows SCM adapter using the existing `ServiceBackend` Protocol, rights separation, state normalization, unsupported-backend denial and isolated Windows CI; only after its exact test proof may Windows service lifecycle be considered. Preserve existing Linux integration tests and zero generic PowerShell/argv/path/service selector authority. Do not conflate known-host capability with an admission token.

## 2026-10-09 — First-class Windows host without premature activation

- #489 owns OS-neutral service lifecycle adaptation; existing #490 is a source-only recognized-host contract, NOT operational Windows support. It now distinguishes `supported` (known host family) from `serviceAdapterImplemented` (service backend implemented). Windows is known but its SCM adapter remains unavailable and **must fail closed**.
- Current Linux `ServiceManager` already accepts an OS-neutral `ServiceBackend` Protocol with fixed project/service aliases and bounded start/stop/restart authorization, but its default is lazily `SystemdUserBackend`. Next child must choose the backend deterministically from approved host capabilities, never infer Windows readiness from platform recognition.
- Before any Windows action: implement and unit-test an explicit Windows SCM adapter behind that same alias/allowlist boundary, normalize service states, require a least-privilege service identity, and run isolated Windows CI with unsupported/no-backend rejection. No arbitrary PowerShell/argv/path/service selectors, WSL workaround, or customer-host activation before those gates.
- Exact-head #490 validation remains prerequisite for merging its contract; subsequent adapter activation is a separate PR and approval gate. This does not alter the existing Linux service behavior.

## 2026-10-09 — Source gates versus live operator authority (reconciled)

1. #388 enrollment CLI on main after all standard CI green, but no enrollment executed or admin credential provided; `RUNNER_MCP_CI_RUNNER_ADMIN_TOKEN` must remain independent of ordinary mailbox token. #387 manual-only, no-cache qualification workflow likewise merged but has **never proved** a live disposable runner. No PR source code may use deployment-capable host as a substitute.
2. Source-only #599 control-plane authenticated freshness complete; the documented default tunnel-client long-poll is 30s plus 5s deadline guard, the local maximum successful-poll age policy is 90s and future skew 5s. External #590 and #333 operator/session/route readiness are independent; a stale or failed auth poll is not a diagnosis that the MCP process is down.
3. #586 independent-volume read-only status source merged. AIfordable #537 machine-readable storage topology and Runner-Fabric #1397 fixed archive namespace are still OPEN; exact separate physical volume identity, owner-private mirror, real mounted second storage and fully qualified protected archive copy remain **BLOCKED**. #587 mirror mutation and #588 restore must not run/land ahead of separately approved real gates.
4. All checked-in admission results are synthetic or hosted CI source evidence unless identified as operator-owned live evidence. No physical backup move, filesystem privilege change, production action, extra paid service or secret disclosure occurred.

## 2026-10-09 — Runner registration CI isolation and credentials (issue #584)

1. Public repository GitHub-hosted standard CI minutes are free; avoid exchanging a trusted hosted PR boundary for privileged self-hosted execution on a false cost assumption. Private Actions storage and hosted releases belong to separate project issues.
2. Source-level intake hardening COMPLETE on main: #600 symlink registration/label drift, #601 inventory page completeness, #602 work root traversal, #605 malformed inventory identity rows, #604 local group/world-write boundaries.
3. Local CLI #388 is still a PR, not live admission. Its proposed `RUNNER_MCP_CI_RUNNER_ADMIN_TOKEN` must be independent of ordinary mailbox `RUNNER_MCP_GITHUB_TOKEN`. A successful source merge does NOT authorize registration.
4. Before #387 self-hosted qualification/any workflow selector activation, prove dedicated disposable nonproduction VM per untrusted job, strict owner/mode, short-lived register token process visibility, negative tests, cache provenance, network/secret separation, exact custom labels, job teardown and stable required checks.
5. Live ChatGPT connector/runner capacity UNKNOWN while #590 remains unlocated; no inference from GitHub code or synthetic tests. No production/deployment runner can be the shortcut.
6. Preserve independent release/provenance/rollback gates and status `BLOCKED` for actual runner admission until verified. Do not start downstream tasks on a speculative future runner.

## 2026-10-06 customer update safety dependency

Tracking: #414; Fabric authority/policy: Blacksp1d3r/Runner-Fabric#1063; AIfordable contract: Blacksp1d3r/AIfordable#401.

Build order for this lane is intentionally downstream:
1. Fabric defines read-only semantic readiness and returning-node trust/quarantine contracts.
2. Runner-MCP may add the minimal local read-only projection needed to satisfy those contracts.
3. No live customer update mutation is added until Fabric rollout/recovery/fencing gates exist.
4. Exact release staging must complete and verify before destructive activation.
5. Durable phase/restart reconciliation is required before power/network interruption qualification.
6. Database/schema rollback remains separate from code rollback.

Do not turn #414 into fleet orchestration or generic host inspection.

# Runner MCP — Dependency / Integration Order

Last reconciled: 2026-10-04. GitHub current state wins.

## Current cross-product gates

- Runner Fabric transport foundation remains COMPLETE on Runner MCP `main` via PR #111 / merge
  `3ebd39981c358c307fa66afa32ad2f5fc32731cf`; issue #109 is complete. Do not duplicate this work.
- Issue #110 is COMPLETE. A real first-party client invocation traversed the bounded Runner MCP ->
  Runner Fabric coarse work-unit path, and bounded get/cancel/operator-safety evidence is reconciled.
  Do not rebuild the bridge or add a second primary transport.
- Runner MCP now has bounded managed Runner Fabric update/status/rollback support and accepts the
  canonical automatic control-plane bundle lane. Before any live Fabric runtime mutation, reconcile
  current Runner Fabric `main` and Runner MCP `fabric_update_active`; source-development activity
  in Runner Fabric is not itself evidence that a managed Fabric runtime update is active.
- Issue #108 is the remaining live self-update recovery proof. PR #262 / merge
  `ba35f70eb9e3e489fc6936d2bc2f0fc425710c81` provides a local-only deterministic recovery
  qualifier; the actual interrupted-install/overlap/local-recovery proof must still be executed on
  the qualified host and must not be bypassed with generic shell, package-manager or remote-control
  authority.
- Issue #101 remains an independent external-discovery lane; Glama/AllMCPs/launch-post actions are
  owner-controlled and non-blocking. Third-party stale install metadata is tracked separately in
  #263 and must not drive product/runtime changes.

## Current build order
1. Core safety/protocol invariants remain the base for every later slice.
2. Task 10 / issue #108 private-host live self-update/recovery proof is no longer blocked by host qualification or first-party control. The remaining step is an intentionally local operator recovery drill using the merged bounded qualifier; it does not block independent documentation/discovery work.
3. Tasks 16, 17, 18, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 35, 36 and 38 are complete on main; do not duplicate them.
4. Task 34 retention preview is COMPLETE on main via PR #92 / merge `36599fab6ed1b96d145a830fa45b935aba823db3`. Task 37 restore-execution review is COMPLETE on main via PR #93 / merge `81720ce24d6e309c72d6a06155c4e70d3b868dbf`. Task 39 adapter-contract refactor is COMPLETE on main via PR #94 / merge `163c5e0597cb8a6cc70f32fd3d8c99e30d08f7aa`. Task 40 pruning execute-boundary review is COMPLETE on main via PR #95 / merge `83453d9bb56f1bcbb69ccf68563699aab56e777b`.
5. Task 28 depended on Task 24 and is complete via merge `131e168e02b7d5781441bbc8256e65de434e6166`. Task 44 is now COMPLETE via PR #118 / merge `6053b7c3d5aef757055c453d2fd5b7f581248e53`, so migration completion has a real strict persisted `MIGRATION_JOB` source without changing synchronous execution.
6. Task 29 depended on Task 25 and is complete via merge `b0f54cb14d73fba3b7c5b8655b5b051af779fd0a`.
7. Task 31 depended on Task 27 and is complete via merge `e54a0684bdc9da3a32d062e0e0e45261c1616020`. Actual restore/PITR and remote restore authority remain deferred.
8. Task 34 depends on Task 30 and is complete via PR #92 / merge `36599fab6ed1b96d145a830fa45b935aba823db3`. Task 40 resolved the first deletion boundary; Task 48 supplied the required shared release lock; Task 43 is COMPLETE via PR #116 / merge `a95e75739bb71bcbaf653244e0ebf9c9bee7b0ee` for one local/manual non-migration orphan release. Backup pruning and automatic pruning remain deferred.
9. Task 32 is complete via review merge `e629515f9c7e7a5d44506dfb82a48343870f94da`; it demonstrated six documentation drift blockers before any alpha tag.
10. Task 36 depended on Task 32 and is complete via merge `8c971016e4fc3cd821dc52d28334567c20835ff4`. Runner MCP 0.1.3 was subsequently published from exact release commit `0aa013c279128e22fbd53be32c35bced3ae26834` through the protected release workflow; future release/tagging still requires explicit authorization and an exact green candidate.
11. Task 23 had Task 18 as its prerequisite; that prerequisite is satisfied by merge `5c4f5db350cdafa99066bdb091866b7d6979a7a9`.
12. Dependency/build/interpreter contract changes still require explicit bootstrap because self-update intentionally uses `--no-deps`.
13. Task 39 depends on Task 38; that dependency is satisfied by PR #91 merge `11b9a4d4e508ac93cd436037563c09d08cfa43ab`. Task 39 is COMPLETE on main via PR #94 / merge `163c5e0597cb8a6cc70f32fd3d8c99e30d08f7aa`.
14. Task 41 is COMPLETE on main via PR #97 / merge `9ce5fe94f417e4e7f910c9945727f70cffd33ecb`. Task 42 is COMPLETE via PR #96, Task 44 via PR #118, Task 45 review is complete, and Task 49 is COMPLETE via PR #124 / merge `da367081f88d6d2342cf938a9b67ec59d9d10de0`.
15. Task 43 is COMPLETE on main via PR #116 after Task 48 integration. The first release-pruning mutation remains local-only, one release per short-lived plan, and preserves backups plus the retained rollback/reference/migration boundary.
16. Task 45 is COMPLETE and Task 49 is COMPLETE via PR #124: synchronous `apply_migrations` remains unchanged while the additive `start_migration_job` / `migration_job_status` path uses separate `migration_async` human approval and durable Task 44 state.
17. Task 46 review is COMPLETE. Task 48 is COMPLETE on main via PR #115 / merge `02475b4c5aa1f103b55f9e4ca6a71e0d09892c7c`, providing the shared release-root `fcntl.flock` contract now used by deploy/rollback and Task 43.
18. Task 47 is COMPLETE via PR #145 / merge `67954dea2117cce3a1819132f6d3c7480dd34c82`. Local `service-log` is bounded, redacted and opt-in; no MCP/mailbox/Agent-Bus log action exists. Task 51 is the separate remote-disclosure review.
19. Issue #143 remains open only for the production packaging-capability preflight; PR #142 already made the environment-dependent wheel smoke conditional. Task 50 is the bounded CODE follow-up.
20. Issue #144 remains high-risk first-install Runner Fabric bootstrap design; Task 52 is review-only before any code or new bootstrap authority.
21. PR #127 and PR #129 remain open with unique Agent-Bus transport/runtime work. Later merged #131/#132/#134 do not make those branches safe to duplicate blindly; reconcile/rebase them separately.
22. Future public release/tagging requires explicit user authorization and an exact green candidate. The remaining private-host recovery limitation is tracked by #108 and must remain explicit until the live local drill is actually proven.


## 2026-10-04 reconciliation

- #110 is COMPLETE; the first-party Runner MCP -> Runner Fabric coarse work-unit path is live-proven. Do not recreate that bridge or its client packaging lane.
- #198, #225 and #237 are COMPLETE: replacement-host qualification and persistent managed Agent Bus worker recovery are no longer activation blockers.
- #108 is OPEN and is the only remaining technical live-proof lane in Runner MCP. The managed runtime baseline is `ba35f70e...`; current exact forward qualifier target is `d0077215...` until `main` changes. The local qualifier/recovery sequence is recorded on #108.
- #101 is non-blocking discovery/launch work. Runner MCP 0.1.3 publication is complete; Smithery is deliberately skipped unless a repository-only path emerges, while Glama/AllMCPs and the technical launch post remain owner-controlled.
- #263 tracks stale third-party directory metadata. Canonical `pyproject.toml` / `server.json` are already correct; do not change package identity, Python requirement, transport or launch semantics merely to match crawler output.
- Managed Runner Fabric runtime updates remain a separate bounded action. Reconcile live `fabric_update_active` and exact Fabric `main` immediately before any update so parallel Fabric development is not crossed.

## Parallel work that is safe
- documentation/CLI contract drift audits;
- direct regression coverage;
- installer/operator UX that does not alter self-update authority;
- secure-I/O inventory/design;
- scrubbed diagnostics design.

## Integration points
- `bridge_protocol.py`, watcher/replay lifecycle and private transport must stay mutually compatible;
- `self_update.py`, `self_update_install.py`, source-control guards and local CLI recovery form one safety boundary;
- dependency-set changes require explicit bootstrap because self-update intentionally uses `--no-deps`.

## Do not parallelize blindly
Avoid overlapping edits to self-update/restart/transaction code from multiple agents. Coordinate through `handover/AGENT_EXCHANGE.md`.


## 2026-09-30 reconciliation

- Task 50 is COMPLETE via PR #149 / merge `469138077066b7b924ba867456ad44dc6372c85d`; issue #143 is closed.
- Task 51 is COMPLETE as a review: local Task-47 service logs remain local-only. A future remote path would require a second independent remote-disclosure opt-in and a separate privacy justification; no remote log CODE task is queued.
- Task 52 is COMPLETE as a review. PR #150 / merge `00ce316124ebc13c65e8a26762f7ea1f69404f50` provides the bounded async Runner Fabric bootstrap foundation, but issue #144 is not complete.
- Task 53 is the bounded #144 hardening prerequisite: self-update/recovery exclusion, installed-runtime preflight, and strict first-install conflict behavior.
- PR #153 is retained only as a green comparison/fallback reference; Task 54 current-main refresh is PR #164 and must not create a second primary transport beside Runner Fabric Agent Bus.
- PR #129 is closed; Task 55 must be retired/reframed rather than reintroducing its direct watcher path.
- Issue #151 is closed, with installer/runtime integrity hardening extended on main by PR #161 / merge `a7041bd8537df7f787e39e1019a259e578661541`. Live clean-host/private-host proof remains tracked separately and must not be inferred from CI.
- Issue #155 tracks the separate bounded host-runtime integrity activation gate; design is intentionally local-only and does not add journal authority to MCP/mailbox/Agent Bus.
