# 09-ci-runner — CI-runner lifecycle en guest isolation — failure register

| Failure ID | Status | Earliest layer | Symptom | Root cause/evidence | Prevention/regression | Tracking |
|---|---|---|---|---|---|---|
| RMCP-CI-0001 | PR_OPEN #591 | private registration handoff cleanup | `reap_expired` materialized the whole directory before checking names, allowing unbounded memory use when private handoff root fills | Source inspection #591, no live host incident claimed | bounded `islice` intake <=4097; fail closed above 4096 without deleting records; max/exact-bound unit tests, exact-head CI pending | #584 / #591 |

A closed failure remains recorded with fix/revision and regression evidence.
