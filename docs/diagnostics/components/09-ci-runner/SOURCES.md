# 09-ci-runner — CI-runner lifecycle en guest isolation — sources

## Source classes
fixed runner policy; GitHub registration result; Fabric guest evidence; private secret-handoff state; lifecycle/supervisor state.

| Source class | Trust boundary | Freshness/version | Public diagnostic rule |
|---|---|---|---|
| local private state | Runner-MCP-owned | explicit state/revision | category/status only |
| canonical external authority | fixed provider/repository/Fabric authority | exact revision/freshness | sanitized evidence |
| infrastructure topology | AIfordable/Runner-Fabric upstream | freshness required | reference upstream; do not copy private details |
| caller | semantic request | validated each call | intent only |

Unknown/stale evidence is not healthy evidence.
