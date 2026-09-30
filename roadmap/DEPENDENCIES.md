# Runner MCP — Dependency / Integration Order

Last reconciled: 2026-09-30. GitHub current state wins.

## Current cross-product gates

- Runner Fabric transport foundation is COMPLETE on Runner MCP `main` via PR #111 / merge
  `3ebd39981c358c307fa66afa32ad2f5fc32731cf`; issue #109 is complete. Do not duplicate this work.
- Issue #110 is the remaining activation/end-to-end lane. It is BLOCKED until the required Runner
  Fabric work-unit service, loopback MCP adapter and startable private service are exact-head green,
  integrated and privately deployable. Reconcile Runner Fabric live state before acting.
- At the latest 2026-09-27 checkpoint, Runner Fabric #258 and #266 are merged and green. #256
  (transport-neutral agent gateway) and #264 (durable fenced work-unit journal) remain open on
  failing/non-mergeable heads, while #268 (startable private agent MCP service) remains open.
  These are checkpoint facts; reconcile Fabric live state before activation.
- Issue #108 remains an independent private-host recovery proof and may proceed only through the
  existing bounded interfaces without exposing private infrastructure.
- Issue #101 remains an independent external-discovery lane; account/OAuth/browser submission gates
  remain human-controlled and must not be bypassed.

## Current build order
1. Core safety/protocol invariants remain the base for every later slice.
2. Task 10 private-host live self-update/recovery proof remains externally blocked; it does not block independent public hardening work.
3. Tasks 16, 17, 18, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 35, 36 and 38 are complete on main; do not duplicate them.
4. Task 34 retention preview is COMPLETE on main via PR #92 / merge `36599fab6ed1b96d145a830fa45b935aba823db3`. Task 37 restore-execution review is COMPLETE on main via PR #93 / merge `81720ce24d6e309c72d6a06155c4e70d3b868dbf`. Task 39 adapter-contract refactor is COMPLETE on main via PR #94 / merge `163c5e0597cb8a6cc70f32fd3d8c99e30d08f7aa`. Task 40 pruning execute-boundary review is COMPLETE on main via PR #95 / merge `83453d9bb56f1bcbb69ccf68563699aab56e777b`.
5. Task 28 depended on Task 24 and is complete via merge `131e168e02b7d5781441bbc8256e65de434e6166`. Task 44 is now COMPLETE via PR #118 / merge `6053b7c3d5aef757055c453d2fd5b7f581248e53`, so migration completion has a real strict persisted `MIGRATION_JOB` source without changing synchronous execution.
6. Task 29 depended on Task 25 and is complete via merge `b0f54cb14d73fba3b7c5b8655b5b051af779fd0a`.
7. Task 31 depended on Task 27 and is complete via merge `e54a0684bdc9da3a32d062e0e0e45261c1616020`. Actual restore/PITR and remote restore authority remain deferred.
8. Task 34 depends on Task 30 and is complete via PR #92 / merge `36599fab6ed1b96d145a830fa45b935aba823db3`. Task 40 resolved the first deletion boundary; Task 48 supplied the required shared release lock; Task 43 is COMPLETE via PR #116 / merge `a95e75739bb71bcbaf653244e0ebf9c9bee7b0ee` for one local/manual non-migration orphan release. Backup pruning and automatic pruning remain deferred.
9. Task 32 is complete via review merge `e629515f9c7e7a5d44506dfb82a48343870f94da`; it demonstrated six documentation drift blockers before any alpha tag.
10. Task 36 depended on Task 32 and is complete via merge `8c971016e4fc3cd821dc52d28334567c20835ff4`; release documentation drift is reconciled, but no tag/release/publication is authorized.
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
22. Public release/tagging requires explicit user authorization and an exact green candidate; private-host proof limitation must remain explicit until actually proven.


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
- PR #153 is the clean refresh of unique PR #127 relay-core work; Task 54 owns its reconciliation.
- PR #129 remains unique watcher work; Task 55 owns its reconciliation after Task 54.
- Issue #151 is COMPLETE via PR #152 / merge `0bade0af6ee574b09de42bb493f5ecffa41657d5` and is closed.
