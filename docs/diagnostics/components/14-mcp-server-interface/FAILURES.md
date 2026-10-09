# 14-mcp-server-interface — MCP server, tool catalogue en public interface — failure register

| Failure ID | Status | Earliest layer | Symptom | Root cause/evidence | Prevention/regression | Tracking |
|---|---|---|---|---|---|---|
| RMCP-F-0004 | KNOWN | client catalogue/interface | Server capability is live but an already-open client cannot call it | client tool catalogue/schema was loaded before the server capability became available | distinguish runtime/tool-registration state from client-catalogue state; refresh client/session; never add duplicate proxy as workaround | historical qualification/update handoffs |

| RMCP-MCP-0005 | OPEN/UNLOCATED | connector invocation / MCP transport / runtime boundary | Four advertised read-only actions (`runtime_status`, `runtime_doctor`, `list_projects`, `worker_status`) all fail with the same generic `The tool failed internally.` and no structured error | 2026-10-09 ChatGPT connector probes; first failing edge not yet proven, neither runtime health nor server outage asserted | #590: inspect authorized client/catalogue/transport evidence first, then private bounded health; do not repeat blind calls or use unrestricted shell | #590 |

Use the repository failure-record template for a new recurrence with concrete bounded evidence.
