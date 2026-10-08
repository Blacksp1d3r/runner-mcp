# 14-mcp-server-interface — MCP server, tool catalogue en public interface — failure register

| Failure ID | Status | Earliest layer | Symptom | Root cause/evidence | Prevention/regression | Tracking |
|---|---|---|---|---|---|---|
| RMCP-F-0004 | KNOWN | client catalogue/interface | Server capability is live but an already-open client cannot call it | client tool catalogue/schema was loaded before the server capability became available | distinguish runtime/tool-registration state from client-catalogue state; refresh client/session; never add duplicate proxy as workaround | historical qualification/update handoffs |

Use the repository failure-record template for a new recurrence with concrete bounded evidence.
