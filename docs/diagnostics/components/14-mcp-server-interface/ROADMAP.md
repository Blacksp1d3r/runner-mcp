# 14-mcp-server-interface — MCP server, tool catalogue en public interface — roadmap

## Subcomponents
1. server construction
2. authentication middleware
3. tool registration
4. input schemas
5. public result schemas
6. plugin/package metadata
7. client initialize/session compatibility
8. tool-catalogue refresh boundary
9. HTTP trace/correlation context
10. public error sanitization

## Dependencies
Upstream: all bounded components that expose tools.
Downstream: clients, 12-diagnostics-audit.

## Current implementation
`server.py`; `http_middleware.py`; `plugin_package.py`; MCP/HTTP integration tests.

## Roadmap ledger
| Work item | Status | Evidence |
|---|---|---|
| bounded tool surface | IMPLEMENTED/ONGOING | server + integration tests |
| catalogue/schema lineage | ACTIVE | #569 |
| client/server compatibility observability | PARTIAL | historical catalogue-refresh failures |
| generic remote execution | FORBIDDEN | AGENTS/security policy |

## Definition of done
Every visible tool can be mapped to one owning component, exact input/result schema and security boundary; client catalogue staleness is diagnosable without duplicating tools or broadening authority.
