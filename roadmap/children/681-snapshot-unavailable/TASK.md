# #681 child — bounded operational snapshot failure

## Goal
Return a structured, explicit, nonsecret read-only unavailable response for transient Fabric operational snapshot failures instead of masking every error as generic MCP tool failure.

## Source and ownership
- src/runner_mcp/fabric_bridge.py — bounded_snapshot_unavailable
- src/runner_mcp/server.py — return bounded failure on expected FabricBridgeError and retain denied audit
- tests/test_fabric_snapshot_unavailable.py — sanitized reason/invalid payload regressions
- Parent #681 intermittent Fabric peer reconnect. Distinct from complete #695 continuity child.
- Source-only candidate version 0.1.18.

## Invariants
- Successful Fabric snapshot still returns unchanged `runner.fabric/operational-snapshot/v1`.
- Failure emits `runner-mcp/fabric-operational-snapshot-error/v1` with state=unavailable, degraded=true, execution_enabled=false, mutation_enabled=false.
- No extra `preflight` probe, no tool retry, no potentially uncertain work replay, no secrets/raw exception text/host info.
- Unknown failures map to bounded unavailable. Known invalid or mutable Fabric payloads are distinguished from transport failures.
- Exact-head validation/Ubuntu/attribution required for source merge; tests synthetic only. Live original-client 0.1.9 unchanged.
- Does NOT heal Fabric relay/host or close parent #681.

## Blockers
- Runtime still installed 0.1.9 and genuine production rollout outside source scope.
- Rollbacktimer postponed until customer phase per operator decision.
