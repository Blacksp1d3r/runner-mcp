# 03-test-execution — Bounded test execution — sources

## Source classes
project TestProfile; adapter registry; safety state; private job metadata; bounded process output.

| Source class | Authority | Freshness/version | Failure behavior |
|---|---|---|---|
| repository/config | canonical project or private config | exact revision/config parse | fail closed |
| runtime/private state | owning Runner-MCP component | explicit state/revision | stale/unsafe != ready |
| peer/provider | fixed bounded adapter | preflight/response evidence | unknown/unavailable explicit |
| caller input | semantic intent only | schema validated per request | never becomes authority |

No source record may disclose private path, endpoint or credential value in public diagnostics.
