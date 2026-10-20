# 02-project-source — Projectregistry en source control — failure register

| Failure ID | Status | Earliest layer | Symptom | Root cause/evidence | Prevention/regression | Tracking |
|---|---|---|---|---|---|---|
| RMCP-F-0003 | KNOWN | source/authorization | Runtime is healthy but project source preflight is unreachable/unauthorized | repository/source authorization and reachability are separate from runtime health | run source preflight separately; resolve canonical credential role + repository scope before changing credentials; never infer token failure from runtime status | historical #417 / AIfordable credential authority |

| RMCP-F-0043 | SOURCE_FIXED_NOT_INSTALLED / PHYSICAL_STAGE_COMPLETE | pinned recovery-tool checkout / Python import | Ignored `__pycache__` written by direct read-only inspect made later full Git cleanliness admission refuse, and outer shell failed silently | sibling module import wrote bytecode before preflight; original stage was preserved, and the operator later completed a separate non-serving recovery | direct CLI no-bytecode guard, real Python subprocess tests and visible outer Git guard; no auto cleanup, no remote enrollment/ACK | #732 / PR #734 / Fabric #1563 |

Use the existing repository failure-record template for detailed incidents. Keep the stable failure here after resolution with fix revision and regression evidence.
