# #681 child — no implicit Fabric follow-up after failed host inspection

## Functional issue
The existing `fabric_host_inspect` failure handler automatically invoked an additional Fabric `preflight` request after an inspection error, potentially turning one intermittent original-client read into more network traffic and obscuring the first failing edge. The explicit `fabric_bridge_preflight` tool already exists and can be invoked separately when desired.

## Implementation
- `src/runner_mcp/fabric_bridge.py`: pure bounded_host_inspection_unavailable with strict fixed reason categories.
- `src/runner_mcp/server.py`: remove automatic bridge preflight from failed inspection result and use pure safe mapping; preserve denied audit and unchanged successful payload.
- `tests/test_fabric_host_inspection_unavailable.py`: fail-closed no-token/error-reflection results.
- Candidate 0.1.19; parent #681 / #590.

## Safety and acceptance
- No second network request, no automatic retry of uncertain-effect calls, no mutation or broad host authority.
- Original failed host inspection returns bounded `runner-mcp/fabric-host-inspection-error/v1` with state unavailable and mutation_enabled false, no private diagnostic text.
- Successful `runner.fabric/host-inspection/v1` remains unchanged.
- Source CI exact head lint/pytest/artifact/demo/Ubuntu/attribution required before merge. No live update; original client v0.1.9 unchanged.
- Independent real Fabric reconnect/session stability requires separate validation. Rollback timer postponed to customer rollout.
