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
