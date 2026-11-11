# 02-project-source — Projectregistry en source control — sources

## Source classes
ProjectRegistry; known project catalogue; private local-source bindings; fixed source-control provider contracts.

| Source class | Authority | Freshness/version | Failure behavior |
|---|---|---|---|
| repository/config | canonical project or private config | exact revision/config parse | fail closed |
| runtime/private state | owning Runner-MCP component | explicit state/revision | stale/unsafe != ready |
| peer/provider | fixed bounded adapter | preflight/response evidence | unknown/unavailable explicit |
| caller input | semantic intent only | schema validated per request | never becomes authority |

No source record may disclose private path, endpoint or credential value in public diagnostics.
