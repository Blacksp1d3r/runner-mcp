# 06-qualification-bootstrap — Worker qualification, disposable target en bootstrap — sources

## Source classes
Fabric revision and request fingerprints; private qualification authority; fixed capability profiles; artifact/evidence custody; disposable-target state.

| Source | Authority | Required proof | Failure state |
|---|---|---|---|
| fixed local/private policy | owning Runner-MCP config/state | schema + permissions + scope | missing/unsafe |
| canonical source/revision | repository or trusted peer | exact revision/hash | mismatch/unavailable |
| peer/provider | fixed bounded integration | compatibility/preflight/result schema | unavailable/incompatible |
| caller | semantic bounded request | strict schema | denied/invalid |

Secrets and real deployment coordinates are never copied into this public source registry.
