# 08-safety-approval-retention — Operational safety, approvals, locks en retention — sources

## Source classes
operator safety state; approval records; release lock state; retention policy/state; exact current action context.

| Source | Authority | Required proof | Failure state |
|---|---|---|---|
| fixed local/private policy | owning Runner-MCP config/state | schema + permissions + scope | missing/unsafe |
| canonical source/revision | repository or trusted peer | exact revision/hash | mismatch/unavailable |
| peer/provider | fixed bounded integration | compatibility/preflight/result schema | unavailable/incompatible |
| caller | semantic bounded request | strict schema | denied/invalid |

Secrets and real deployment coordinates are never copied into this public source registry.
