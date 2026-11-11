# Runner-MCP data-store map

Physical storage is recorded by class, never by real deployment path.

| Store class | Logical owner | Implementation | Security/retention notes |
|---|---|---|---|
| project registry/config | project-source | YAML/private config contracts | public examples contain placeholders only |
| private runtime environment | runtime/config | owner-private environment file/state | secret values never exposed |
| test job metadata/logs | test-execution | owner-private job directory | bounded size, redacted output |
| deployment job metadata | deploy/migration | owner-private JSON job records | state/revision bound |
| migration job metadata | deploy/migration | owner-private job records | exact project/operation lineage |
| database backups | database manager | owner-private backup custody | DB-specific config; restore separately gated |
| audit log | diagnostics/audit | owner-private append-only JSON lines | bounded event fields + build identity |
| mailbox state | mailbox/watchers | GitHub mailbox refs + local watcher state | protocol/replay bounded |
| self-update state | runtime/update | owner-private transaction/job/restart metadata | baseline/recovery and exact commit lineage |
| artifact custody | artifact/mirror | content-addressed owner-private objects | digest + size verified |
| repository mirrors | artifact/mirror | private mirror/inventory state | canonical repository identities only |
| Fabric qualification/update state | Fabric bridge/qualification | private config/evidence contracts | fixed peer/tool/revision bindings |
| tunnel readiness/topology state | tunnel/connectivity | private bounded evidence | public output excludes deployment details |

A store path is not an API. Callers receive semantic IDs/status only.
