# 03-test-execution — Bounded test execution — roadmap

## Subcomponents
1. test profile resolution
2. queue admission
3. worker concurrency
4. adapter selection
5. bounded argv/cwd/env
6. timeout/cancel
7. redaction
8. job result

## Dependencies
Upstream: 02-project-source, 08-safety-approval-retention.
Downstream: 01-runtime-self-update, 12-diagnostics-audit.

## Current implementation
test_runner.py; adapters/base.py; adapters/generic.py; adapters/python.py; adapters/registry.py.

## Roadmap ledger
| Work item | Status | Evidence |
|---|---|---|
| current bounded contracts | IMPLEMENTED/PARTIAL | current main + TEST_EVIDENCE_MAP |
| diagnostic source/data/failure mapping | ACTIVE | #569 |
| physical-state evolution | versioned only | DATA_STORE_MAP |
| broader authority | BLOCKED unless separately approved | AGENTS/security rules |

## Definition of done
Every public result can be traced through bounded validation, trusted source/state, policy, executor, state revision and sanitized evidence; stale/replay/partial state fails closed; reusable failures have regression guards.
