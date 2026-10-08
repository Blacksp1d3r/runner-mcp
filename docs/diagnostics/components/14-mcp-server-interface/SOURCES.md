# 14-mcp-server-interface — MCP server, tool catalogue en public interface — sources

## Source classes
- registered server tool definitions;
- Pydantic/MCP input and result contracts;
- authentication/configuration state;
- build/package/plugin metadata;
- client initialize/session/tool-catalogue evidence;
- bounded component implementations.

The server interface is a projection of bounded capabilities. Presence in a client catalogue is not proof that the runtime implementation is healthy; runtime health is not proof that an already-open client has refreshed its catalogue.

No private deployment address, bearer value or client secret belongs in this public source registry.
