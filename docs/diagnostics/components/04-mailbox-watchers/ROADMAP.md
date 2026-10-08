# 04-mailbox-watchers — Mailbox, bridge request processing en watchers — roadmap

## Subcomponents
1. strict request protocol
2. GitHub mailbox transport
3. watcher polling
4. replay/fencing
5. bounded dispatch
6. durable result sink
7. heartbeat
8. completion delivery/feedback

## Dependencies
Upstream: fixed mailbox config + bounded protocol + transport/provider state.
Downstream: 05-fabric-bridge, 12-diagnostics-audit.

## Current implementation
github_mailbox.py; github_watcher.py; github_runtime.py; bridge_processor.py; bridge_protocol.py; bridge_replay.py; bridge_resilience.py; completion_delivery.py; completion_feedback.py.

## Roadmap ledger
| Work item | Status | Evidence |
|---|---|---|
| current bounded contracts | IMPLEMENTED/PARTIAL | current main + TEST_EVIDENCE_MAP |
| diagnostic source/data/failure mapping | ACTIVE | #569 |
| physical-state evolution | versioned only | DATA_STORE_MAP |
| broader authority | BLOCKED unless separately approved | AGENTS/security rules |

## Definition of done
Every public result can be traced through bounded validation, trusted source/state, policy, executor, state revision and sanitized evidence; stale/replay/partial state fails closed; reusable failures have regression guards.
