# 05-fabric-bridge — Runner-Fabric bridge en peer compatibility — roadmap

## Subcomponents
1. fixed peer config
2. MCP initialize/preflight
3. protocol version
4. server/build identity
5. interface digest/tool schema
6. bounded tool allow-list
7. request/response validation
8. operational snapshot
9. continuity status

## Dependencies
Upstream: 04-mailbox-watchers, 11-tunnel-connectivity, private fixed peer binding.
Downstream: 06-qualification-bootstrap, 09-ci-runner, 12-diagnostics-audit.

## Current implementation
fabric_bridge.py; bridge_mcp_executor.py; fabric_live_overview.py; fabric_continuity_status.py; fabric_coding_availability.py.

## Roadmap ledger
| Work item | Status | Evidence |
|---|---|---|
| bounded current contract | IMPLEMENTED/PARTIAL | current main + tests |
| source/data/failure mapping | ACTIVE | #569 |
| peer/provider evolution | versioned + fail-closed | SOURCES/DATA_LINEAGE |
| broader authority | BLOCKED unless separate accepted capability exists | AGENTS/security model |

## Definition of done
Every transition is exact-revision/scope bound, authorization/policy is explicit, external state can remain unknown, private state never leaks, and negative/replay/stale paths have regression coverage.
