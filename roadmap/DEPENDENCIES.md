# Runner MCP — Dependency / Integration Order

Last reconciled: 2026-09-23. GitHub current state wins.

## Current build order
1. Core safety/protocol invariants remain the base for every later slice.
2. Task 10 private-host live self-update/recovery proof remains externally blocked; it does not block independent public hardening work.
3. Tasks 16, 17, 18, 20, 21, 22, 23, 24, 25 and 26 are complete on main; do not duplicate them.
4. Tasks 27–30 are the current bounded public queue after ownership reconciliation: database restore/recovery boundary review, deployment/rollback completion-delivery integration, privacy-safe guided connectivity reconciliation, and automated retention-pruning boundary review.
5. Task 28 depends on Task 24 and that dependency is satisfied by merge `d9f7d40f952ab39478d4a0286d317f160d6b46ce`. Migration completion remains blocked on a separate persisted migration-job substrate.
6. Task 29 depends on Task 25 and that dependency is satisfied by merge `f2c1d6a135133033ab1e0059f9a92cfec3021d88`.
7. Task 23 had Task 18 as its prerequisite; that prerequisite is satisfied by merge `5c4f5db350cdafa99066bdb091866b7d6979a7a9`.
8. Dependency/build/interpreter contract changes still require explicit bootstrap because self-update intentionally uses `--no-deps`.
9. Public release/tagging requires explicit user authorization and an exact green candidate; private-host proof limitation must remain explicit until actually proven.

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
