# 12-diagnostics-audit — Safe diagnostics, audit, build identity en host integrity — sources

## Source classes
component outcomes; bounded typed categories; build/package identity; sanitized host-integrity evidence; audit event schema.

| Source class | Trust boundary | Freshness/version | Public diagnostic rule |
|---|---|---|---|
| local private state | Runner-MCP-owned | explicit state/revision | category/status only |
| canonical external authority | fixed provider/repository/Fabric authority | exact revision/freshness | sanitized evidence |
| infrastructure topology | AIfordable/Runner-Fabric upstream | freshness required | reference upstream; do not copy private details |
| caller | semantic request | validated each call | intent only |

Unknown/stale evidence is not healthy evidence.
