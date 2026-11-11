# 02-project-source — Projectregistry en source control — roadmap

## Subcomponents
1. project catalogue
2. private project config
3. known-project local source
4. remote source preflight
5. clean checkout
6. revision verification
7. source identity normalization

## Dependencies
Upstream: private project registry/config + canonical repository identities.
Downstream: 01-runtime-self-update, 03-test-execution, 07-deploy-migrate-backup, 13-artifact-mirror-custody.

## Current implementation
config.py; known_project_catalog.py; known_project_local_source.py; source_control.py.

## Roadmap ledger
| Work item | Status | Evidence |
|---|---|---|
| current bounded contracts | IMPLEMENTED/PARTIAL | current main + TEST_EVIDENCE_MAP |
| diagnostic source/data/failure mapping | ACTIVE | #569 |
| physical-state evolution | versioned only | DATA_STORE_MAP |
| broader authority | BLOCKED unless separately approved | AGENTS/security rules |

## Definition of done
Every public result can be traced through bounded validation, trusted source/state, policy, executor, state revision and sanitized evidence; stale/replay/partial state fails closed; reusable failures have regression guards.
