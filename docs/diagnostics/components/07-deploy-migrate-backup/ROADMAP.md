# 07-deploy-migrate-backup — Deployment, migration en database backup/restore — roadmap

## Subcomponents
1. deployment plan/preflight
2. deployment job state
3. rollback
4. migration planning
5. migration job state
6. database status
7. backup
8. restore preflight
9. restore
10. bounded output/redaction

## Dependencies
Upstream: 02-project-source, 08-safety-approval-retention.
Downstream: 12-diagnostics-audit.

## Current implementation
deployment_manager.py; deployment_jobs.py; migration_jobs.py; migration_planning.py; database_manager.py.

## Roadmap ledger
| Work item | Status | Evidence |
|---|---|---|
| bounded current contract | IMPLEMENTED/PARTIAL | current main + tests |
| source/data/failure mapping | ACTIVE | #569 |
| peer/provider evolution | versioned + fail-closed | SOURCES/DATA_LINEAGE |
| broader authority | BLOCKED unless separate accepted capability exists | AGENTS/security model |

## Definition of done
Every transition is exact-revision/scope bound, authorization/policy is explicit, external state can remain unknown, private state never leaks, and negative/replay/stale paths have regression coverage.
