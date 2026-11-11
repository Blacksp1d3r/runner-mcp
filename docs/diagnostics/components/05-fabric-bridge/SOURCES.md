# 05-fabric-bridge — Runner-Fabric bridge en peer compatibility — sources

## Source classes
fixed Fabric bridge config; peer MCP initialize metadata; allowed tool set; exact peer result schemas; bounded source/continuity evidence.

| Source | Authority | Required proof | Failure state |
|---|---|---|---|
| fixed local/private policy | owning Runner-MCP config/state | schema + permissions + scope | missing/unsafe |
| canonical source/revision | repository or trusted peer | exact revision/hash | mismatch/unavailable |
| peer/provider | fixed bounded integration | compatibility/preflight/result schema | unavailable/incompatible |
| caller | semantic bounded request | strict schema | denied/invalid |

Secrets and real deployment coordinates are never copied into this public source registry.
