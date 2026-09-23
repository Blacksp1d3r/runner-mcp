# Runner MCP — Dependency / Integration Order

Last reconciled: 2026-09-23. GitHub current state wins.

## Current build order
1. Core safety/protocol invariants remain the base for every later slice.
2. Task 10 private-host live self-update/recovery proof remains externally blocked; it does not block independent public hardening work.
3. Tasks 16, 17 and 18 are complete on main; do not duplicate them.
4. Tasks 20–23 are the current bounded public hardening queue after ownership reconciliation: bridge adversarial regression tests, managed-autostart private-write migration, cron safe-diagnostics integration, and completion-watcher safe-diagnostics integration.
5. Task 21 and Task 23 had Task 18 as their prerequisite; that prerequisite is now satisfied by merge `5c4f5db350cdafa99066bdb091866b7d6979a7a9`.
6. Dependency/build/interpreter contract changes still require explicit bootstrap because self-update intentionally uses `--no-deps`.
7. Public release/tagging requires explicit user authorization and an exact green candidate; private-host proof limitation must remain explicit until actually proven.

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
