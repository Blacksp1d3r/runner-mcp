# #540 — Stale MCP session replay elimination

- owner: Runner-MCP communication chat
- status: SOURCE_IN_PROGRESS
- branch: safety/540-stale-session-no-blind-replay
- PR: PENDING
- exact_head_ci: PENDING
- affected_component: bridge_mcp_executor LocalMCPClient
- live_connected_acceptance: BLOCKED_EXTERNAL (#540/#590, A6/#942 + A7/#943)
- Fabric lease/fence: BLOCKED_EXTERNAL (#1398/#1400)
- Claude/EnerCue dispatch: NO_DISPATCH
- live_host_or_tunnel_changes: NONE

## Observation
Pre-change `_call_tool` catches `_StaleMCPSessionError`, automatically reinitializes then resends the same `tools/call` without checking if earlier request caused side effects. New source refuses auto replay with a fixed uncertainty code and requires independent verified schema/build before a new caller request.

## Next
Run all exact-head validation, merge only green with verified head. Publish relevant stable failure ID in central Failure Museum, handover #540/#590, and avoid closing live issues.
