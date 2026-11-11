# 10-service-lifecycle — Managed service lifecycle en autostart — sources

## Source classes
service allow-list; private lifecycle config; bounded service/journal evidence; autostart state.

| Source class | Trust boundary | Freshness/version | Public diagnostic rule |
|---|---|---|---|
| local private state | Runner-MCP-owned | explicit state/revision | category/status only |
| canonical external authority | fixed provider/repository/Fabric authority | exact revision/freshness | sanitized evidence |
| infrastructure topology | AIfordable/Runner-Fabric upstream | freshness required | reference upstream; do not copy private details |
| caller | semantic request | validated each call | intent only |

Unknown/stale evidence is not healthy evidence.
