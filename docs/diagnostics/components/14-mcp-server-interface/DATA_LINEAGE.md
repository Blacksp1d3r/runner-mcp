# 14-mcp-server-interface — MCP server, tool catalogue en public interface — data lineage

`component capability -> server registration -> public schema -> client initialize/catalogue -> validated request -> owning component -> sanitized result -> client`

Trace:
- server build identity;
- tool name/schema version;
- owning component;
- client session/catalogue generation where bounded evidence exists;
- authentication outcome;
- request correlation context;
- public result/error category.

A client-side missing tool must be localized before modifying server code.

## 2026-10-09 #590 isolated server-vs-client evidence

PR #595 adds an in-process authenticated MCP HTTP smoke matrix: initialize/session acknowledgement, then independently call `list_projects`, `runtime_status`, and `runtime_doctor` through the same session. Checks structured output and sanitization, with no deployed tunnel or worker. If this passes, it supports only the tested local dispatch path; a separate live connector failure remains UNLOCATED until a fresh authorized client/catalogue and private transport evidence establish the first failing edge. Do not infer remote health, runner capacity or self-hosted CI isolation (#584) from a local green test.
