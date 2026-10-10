# 14-mcp-server-interface — MCP server, tool catalogue en public interface — failure register

| Failure ID | Status | Earliest layer | Symptom | Root cause/evidence | Prevention/regression | Tracking |
|---|---|---|---|---|---|---|
| RMCP-F-0004 | KNOWN | client catalogue/interface | Server capability is live but an already-open client cannot call it | client tool catalogue/schema was loaded before the server capability became available | distinguish runtime/tool-registration state from client-catalogue state; refresh client/session; never add duplicate proxy as workaround | historical qualification/update handoffs |

| RMCP-MCP-0005 | OPEN/LIVE UNLOCATED | client/catalog/transport vs installed runtime | Doctor now returns old 12-check WARN (0 failed, 3 warnings), while runtime_status and build_identity failed generically through connected client | Current main has at least three additional doctor checks; source-only #627/#629 correct two potential opaque error paths, **not** proof of active installed version or correct tunnel return route | Exact-source/catalog/session plus private read-only ingress and response-delivery correlation; no speculative restarts or broad-shell bypass | #590 / PR #627 / PR #629 |

Use the repository failure-record template for a new recurrence with concrete bounded evidence.
