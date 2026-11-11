# 11-tunnel-connectivity — Tunnel, relay en connectivity readiness — sources

## Source classes
bounded tunnel config state; process evidence; local health; topology/heartbeat; first-party control-path evidence.

| Source class | Trust boundary | Freshness/version | Public diagnostic rule |
|---|---|---|---|
| local private state | Runner-MCP-owned | explicit state/revision | category/status only |
| canonical external authority | fixed provider/repository/Fabric authority | exact revision/freshness | sanitized evidence |
| infrastructure topology | AIfordable/Runner-Fabric upstream | freshness required | reference upstream; do not copy private details |
| caller | semantic request | validated each call | intent only |

Unknown/stale evidence is not healthy evidence.
