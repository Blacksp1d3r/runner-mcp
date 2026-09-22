# Runner MCP — Dependency / Integration Order

Last reconciled: 2026-09-22. GitHub current state wins.

## Current build order
1. Core safety/protocol invariants remain the base for every later slice.
2. Watcher/replay/result recovery must be healthy before relying on mailbox-driven self-update proof.
3. Self-update package transaction recovery and activation recovery must be proven before treating live self-update as routine.
4. PR #45 recovery-state visibility may merge independently of private-host bootstrap, but must be green/current.
5. Private-host bootstrap/proof comes after current main + recovery visibility are reconciled.
6. Public launch/release tagging comes only from an exact green commit after operational recovery proof.

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
