# 08-safety-approval-retention — Operational safety, approvals, locks en retention — roadmap

## Subcomponents
1. action classification
2. emergency stop
3. approval request/evidence
4. release operation lock
5. retention preview
6. retention pruning
7. precondition gates

## Dependencies
Upstream: trusted local operator policy/private config.
Downstream: 01-runtime-self-update, 03-test-execution, 07-deploy-migrate-backup, 09-ci-runner, 10-service-lifecycle.

## Current implementation
operational_safety.py; approval_manager.py; release_operation_lock.py; retention_preview.py; retention_pruning.py.

## Roadmap ledger
| Work item | Status | Evidence |
|---|---|---|
| bounded current contract | IMPLEMENTED/PARTIAL | current main + tests |
| source/data/failure mapping | ACTIVE | #569 |
| peer/provider evolution | versioned + fail-closed | SOURCES/DATA_LINEAGE |
| broader authority | BLOCKED unless separate accepted capability exists | AGENTS/security model |

## Definition of done
Every transition is exact-revision/scope bound, authorization/policy is explicit, external state can remain unknown, private state never leaks, and negative/replay/stale paths have regression coverage.
