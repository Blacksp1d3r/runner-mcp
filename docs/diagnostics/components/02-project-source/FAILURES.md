# 02-project-source — Projectregistry en source control — failure register

| Failure ID | Status | Earliest layer | Symptom | Root cause/evidence | Prevention/regression | Tracking |
|---|---|---|---|---|---|---|
| RMCP-F-0003 | KNOWN | source/authorization | Runtime is healthy but project source preflight is unreachable/unauthorized | repository/source authorization and reachability are separate from runtime health | run source preflight separately; resolve canonical credential role + repository scope before changing credentials; never infer token failure from runtime status | historical #417 / AIfordable credential authority |

Use the existing repository failure-record template for detailed incidents. Keep the stable failure here after resolution with fix revision and regression evidence.
