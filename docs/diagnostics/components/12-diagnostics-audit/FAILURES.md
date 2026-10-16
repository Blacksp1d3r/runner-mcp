# 12-diagnostics-audit — Safe diagnostics, audit, build identity en host integrity — failure register

| Failure ID | Status | Earliest layer | Symptom | Root cause/evidence | Prevention/regression | Tracking |
|---|---|---|---|---|---|---|
| RMCP-F-0001 | KNOWN | status aggregation | Local test queue reports idle while the complete first-party execution path is still busy | local queue state was incorrectly tempting as an end-to-end health/idle proxy; upstream relay/Agent-Bus/Fabric states are separate | operational snapshot must distinguish every observable layer and use explicit unknown/unavailable instead of false green | #269 |

A closed failure remains recorded with fix/revision and regression evidence.
| RMCP-F-0029 | SOURCE_FIX_PENDING_CI | #669 candidate receipt publisher | A caller-selected path containing `..` or a linked ancestor could escape the designated receipt directory; concurrently a publication collision must not overwrite another receipt | Previously only the final parent was checked and `os.link` prevented overwriting but parent path traversal lacked explicit rejection; production code is NOT wired to this prototype | Reject `..` and any symlinked ancestor, direct regression, actual two-thread race, preserve atomic create-once and uncertain-publication classification | #669 / PR #689, exact HEAD pending CI |
