# #540 — Stale MCP session replay elimination

- owner: Runner-MCP communication chat
- status: COMPLETE_SOURCE_ONLY; LIVE_ACCEPTANCE_BLOCKED
- branch: safety/540-stale-session-no-blind-replay
- PR: #650 MERGED
- exact_head_ci: source head 154b9444a1ea67023588ce75fdc86628687e60ff; attribution 38085233372 / 38085481144 SUCCESS; full validation 38085233326 SUCCESS (Ruff, 2781 pytest, built artifact, clean demo)
- affected_component: bridge_mcp_executor LocalMCPClient
- live_connected_acceptance: BLOCKED_EXTERNAL (#540/#590, A6/#942 + A7/#943)
- Fabric lease/fence: BLOCKED_EXTERNAL (#1398/#1400)
- Claude/EnerCue dispatch: NO_DISPATCH
- live_host_or_tunnel_changes: NONE

- squash_merge: 8608ddde46f228d045d64189f12e7464a1919fb9

## Observation
Pre-change `_call_tool` catches `_StaleMCPSessionError`, automatically reinitializes then resends the same `tools/call` without checking if earlier request caused side effects. New source refuses auto replay with a fixed uncertainty code and requires independent verified schema/build before a new caller request.

## Next
Exact-head full CI passed and #650 squash merged; no deployed host or connected client acceptance proven.  Publish relevant stable failure ID in central Failure Museum, handover #540/#590, and avoid closing live issues.
