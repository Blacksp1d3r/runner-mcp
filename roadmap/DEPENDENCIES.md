# Runner MCP — Dependency / Integration Order

Last reconciled: 2026-09-24. GitHub current state wins.

## Current build order
1. Core safety/protocol invariants remain the base for every later slice.
2. Task 10 private-host live self-update/recovery proof remains externally blocked; it does not block independent public hardening work.
3. Tasks 16, 17, 18, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 35, 36 and 38 are complete on main; do not duplicate them.
4. Task 34 retention preview is COMPLETE on main via PR #92 / merge `36599fab6ed1b96d145a830fa45b935aba823db3`. Task 37 restore-execution review is COMPLETE on main via PR #93 / merge `81720ce24d6e309c72d6a06155c4e70d3b868dbf`. Task 39 adapter-contract refactor is COMPLETE on PR #94 pending final integration. Task 40 pruning execute-boundary review is complete on its review branch pending integration.
5. Task 28 depended on Task 24 and is complete via merge `131e168e02b7d5781441bbc8256e65de434e6166`. Migration completion remains blocked on a separate persisted migration-job substrate.
6. Task 29 depended on Task 25 and is complete via merge `b0f54cb14d73fba3b7c5b8655b5b051af779fd0a`.
7. Task 31 depended on Task 27 and is complete via merge `e54a0684bdc9da3a32d062e0e0e45261c1616020`. Actual restore/PITR and remote restore authority remain deferred.
8. Task 34 depends on Task 30 and is complete via PR #92 / merge `36599fab6ed1b96d145a830fa45b935aba823db3`. Task 40 resolves the first deletion boundary; Task 43 depends on Task 40 integration and is limited to one local/manual non-migration orphan release. Backup pruning and automatic pruning remain deferred.
9. Task 32 is complete via review merge `e629515f9c7e7a5d44506dfb82a48343870f94da`; it demonstrated six documentation drift blockers before any alpha tag.
10. Task 36 depended on Task 32 and is complete via merge `8c971016e4fc3cd821dc52d28334567c20835ff4`; release documentation drift is reconciled, but no tag/release/publication is authorized.
11. Task 23 had Task 18 as its prerequisite; that prerequisite is satisfied by merge `5c4f5db350cdafa99066bdb091866b7d6979a7a9`.
12. Dependency/build/interpreter contract changes still require explicit bootstrap because self-update intentionally uses `--no-deps`.
13. Task 39 depends on Task 38; that dependency is satisfied by PR #91 merge `11b9a4d4e508ac93cd436037563c09d08cfa43ab`. Task 39 is COMPLETE on PR #94 pending final integration.
14. Task 41 is COMPLETE on main via PR #97 / merge `9ce5fe94f417e4e7f910c9945727f70cffd33ecb`. Task 42 is COMPLETE on main via PR #96 / merge `82ecef725d828b69e328f8f474553e01ef8548cb`; Task 44 is prerequisite-safe.
15. Task 43's Task 40 dependency is satisfied, but Task 43 is now BLOCKED on Task 46 because local CLI pruning cannot safely share the existing process-local DeploymentManager threading lock with the long-lived MCP process.
16. Task 45 is blocked on Task 44 integration and is the separate review for any future asynchronous MCP/bridge migration contract change.
17. Task 46 is prerequisite-safe and must resolve the cross-process release-mutation lock contract before Task 43 starts.
18. Task 47 is prerequisite-safe after Task 41 integration and is the bounded local service-journal reader; remote log exposure remains separately deferred.
19. Public release/tagging requires explicit user authorization and an exact green candidate; private-host proof limitation must remain explicit until actually proven.


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
