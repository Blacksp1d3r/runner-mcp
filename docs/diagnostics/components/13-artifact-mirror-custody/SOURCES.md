# 13-artifact-mirror-custody — Artifact custody, repository mirrors en Fabric update artifacts — sources

## Source classes
canonical repository identity; exact commit; content hash/size; private mirror/inventory config; validated update bundle metadata.

| Source class | Trust boundary | Freshness/version | Public diagnostic rule |
|---|---|---|---|
| local private state | Runner-MCP-owned | explicit state/revision | category/status only |
| canonical external authority | fixed provider/repository/Fabric authority | exact revision/freshness | sanitized evidence |
| infrastructure topology | AIfordable/Runner-Fabric upstream | freshness required | reference upstream; do not copy private details |
| independent-volume bindings | host-owned private config | complete + current filesystem evidence | status/reason only; never paths/devices |
| caller | semantic request | validated each call | intent only |

Unknown/stale evidence is not healthy evidence.
