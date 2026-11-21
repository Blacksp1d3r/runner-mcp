# #665 — Automatic tool recognition and fault detection

Status: PLANNED / UNCLAIMED. Parent: https://github.com/Blacksp1d3r/runner-mcp/issues/665 ; design PR #666.

## Dependency-safe children

| Order | Child | Main dependency |
|---|---|---|
| 1 | [registry](665-registry/TASK.md) | release policy #661/#663 and legacy contracts #664 |
| 2 | [attestation](665-attestation/TASK.md) | registry, source/live build #590 |
| 3 | [handshake](665-handshake/TASK.md) | registry, attestation, legacy support |
| 4 | [dispatcher](665-dispatcher/TASK.md) | handshake, #642 host authorization |
| 5 | [diagnostics](665-diagnostics/TASK.md) | dispatcher, #590 request lineage |
| 6 | [alerts](665-alerts/TASK.md) | diagnostics, Fabric #1471 ledger and notification |
| 7 | [compatibility](665-compatibility/TASK.md) | all, Fabric A6 #942 / A7 #943 for live activation |

Each child has exactly TASK.md and STATE.md. Claim scope and existing worker leases before code edits. Keep central project Failure Museum as the single defect ledger. Registry design and synthetic tests may proceed without host privileges; actual fleet activation remains gated. No shipping code without an incremented unique version. No installation, message-delivery or CI success is implied by planning files.

## Next action

Independent review of #666; reconcile #661 and #663 version policy; take only the first non-conflicting child. Append verified CI/commit/deployment status to child STATE and central handover upon completion.
