# 01-runtime-self-update — Runtime en self-update — roadmap

## Subcomponents
1. build identity
2. self-update request
3. source sync
4. qualification tests
5. package install
6. baseline/recovery
7. restart markers
8. runtime convergence

## Dependencies
Upstream: 02-project-source, 03-test-execution, 08-safety-approval-retention.
Downstream: 10-service-lifecycle, 12-diagnostics-audit.

## Current implementation
self_update.py; self_update_install.py; runtime_smoke.py; build_identity.py.

## Roadmap ledger
| Work item | Status | Evidence |
|---|---|---|
| current bounded contracts | IMPLEMENTED/PARTIAL | current main + TEST_EVIDENCE_MAP |
| diagnostic source/data/failure mapping | ACTIVE | #569 |
| physical-state evolution | versioned only | DATA_STORE_MAP |
| broader authority | BLOCKED unless separately approved | AGENTS/security rules |

## Definition of done
Every public result can be traced through bounded validation, trusted source/state, policy, executor, state revision and sanitized evidence; stale/replay/partial state fails closed; reusable failures have regression guards.
