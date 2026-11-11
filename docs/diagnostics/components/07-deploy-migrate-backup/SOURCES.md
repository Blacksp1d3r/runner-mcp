# 07-deploy-migrate-backup — Deployment, migration en database backup/restore — sources

## Source classes
known project config; deployment/migration profiles; current release/schema state; DB DSN secret reference; owner-private job/backup metadata.

| Source | Authority | Required proof | Failure state |
|---|---|---|---|
| fixed local/private policy | owning Runner-MCP config/state | schema + permissions + scope | missing/unsafe |
| canonical source/revision | repository or trusted peer | exact revision/hash | mismatch/unavailable |
| peer/provider | fixed bounded integration | compatibility/preflight/result schema | unavailable/incompatible |
| caller | semantic bounded request | strict schema | denied/invalid |

Secrets and real deployment coordinates are never copied into this public source registry.
