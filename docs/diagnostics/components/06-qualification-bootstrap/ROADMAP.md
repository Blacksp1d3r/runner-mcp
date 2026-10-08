# 06-qualification-bootstrap — Worker qualification, disposable target en bootstrap — roadmap

## Subcomponents
1. qualification policy
2. agent lifecycle
3. worker qualification provision
4. disposable target readiness
5. bootstrap
6. recovery
7. A6 binding repair
8. project-specific qualification adapters

## Dependencies
Upstream: 05-fabric-bridge, 13-artifact-mirror-custody, private host-owned policy.
Downstream: 05-fabric-bridge, 12-diagnostics-audit.

## Current implementation
fabric_agent_qualification.py; fabric_agent_runtime.py; fabric_worker_qualification_provisioning.py; fabric_disposable_target.py; fabric_bootstrap.py; fabric_a6_binding_repair.py; bounded project-specific qualification modules.

## Roadmap ledger
| Work item | Status | Evidence |
|---|---|---|
| bounded current contract | IMPLEMENTED/PARTIAL | current main + tests |
| source/data/failure mapping | ACTIVE | #569 |
| peer/provider evolution | versioned + fail-closed | SOURCES/DATA_LINEAGE |
| broader authority | BLOCKED unless separate accepted capability exists | AGENTS/security model |

## Definition of done
Every transition is exact-revision/scope bound, authorization/policy is explicit, external state can remain unknown, private state never leaks, and negative/replay/stale paths have regression coverage.
