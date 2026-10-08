# 12-diagnostics-audit — Safe diagnostics, audit, build identity en host integrity — failure register

| Failure ID | Status | Earliest layer | Symptom | Root cause/evidence | Prevention/regression | Tracking |
|---|---|---|---|---|---|---|
| RMCP-F-0001 | KNOWN | status aggregation | Local test queue reports idle while the complete first-party execution path is still busy | local queue state was incorrectly tempting as an end-to-end health/idle proxy; upstream relay/Agent-Bus/Fabric states are separate | operational snapshot must distinguish every observable layer and use explicit unknown/unavailable instead of false green | #269 |

A closed failure remains recorded with fix/revision and regression evidence.
