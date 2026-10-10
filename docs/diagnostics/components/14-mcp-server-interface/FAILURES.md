# 14-mcp-server-interface — MCP server, tool catalogue en public interface — failure register

| Failure ID | Status | Earliest layer | Symptom | Root cause/evidence | Prevention/regression | Tracking |
|---|---|---|---|---|---|---|
| RMCP-F-0004 | KNOWN | client catalogue/interface | Server capability is live but an already-open client cannot call it | client tool catalogue/schema was loaded before the server capability became available | distinguish runtime/tool-registration state from client-catalogue state; refresh client/session; never add duplicate proxy as workaround | historical qualification/update handoffs |

| RMCP-MCP-0005 | OPEN/LIVE UNLOCATED | client/catalog/transport vs installed runtime | Doctor now returns old 12-check WARN (0 failed, 3 warnings), while runtime_status and build_identity failed generically through connected client | Current main has at least three additional doctor checks; source-only #627/#629 correct two potential opaque error paths, **not** proof of active installed version or correct tunnel return route | Exact-source/catalog/session plus private read-only ingress and response-delivery correlation; no speculative restarts or broad-shell bypass | #590 / PR #627 / PR #629 |

| RMCP-MCP-0005 / 2026-10-10 reconfirmed | OPEN/LIVE UNLOCATED | partial read-only tool dispatch | `list_projects`, `queue_status`, `safety_status`, `project_capabilities` return structured; `project_status`, `build_identity`, `worker_status` and mirror admission fail; doctor has only 12 checks | See [bounded matrix](../../CONNECTOR_PROBE_MATRIX_2026-10-10.md); mixed success constrains diagnosis but still does not prove same target runtime/client route | Approved opaque-ID ingress → dispatch → response-delivery correlation; separately prove build/catalogue generation, no blind restart | #590 / #634 |

Use the repository failure-record template for a new recurrence with concrete bounded evidence.
