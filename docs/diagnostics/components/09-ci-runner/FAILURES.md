# 09-ci-runner — CI-runner lifecycle en guest isolation — failure register

| Failure ID | Status | Earliest layer | Symptom | Root cause/evidence | Prevention/regression | Tracking |
|---|---|---|---|---|---|---|
| RMCP-CI-0001 | GREEN/MERGED #591 | private registration handoff cleanup | `reap_expired` materialized the whole directory before checking names, allowing unbounded memory use when private handoff root fills | Source inspection #591, no live host incident claimed | bounded `islice` intake <=4097; fail closed above 4096 without deleting records; max/exact-bound unit tests, exact-head validation+attribution success; squash `ea519720...` | #584 / #591 |

| RMCP-CI-0002 | GREEN/MERGED #592 | public enrollment-handoff result contract | Direct construction with non-string handoff ID raised raw TypeError; nonpositive/oversized expiry accepted | Source review + exact-head CI #592 (squash `3c9e16b...`) | bounded CIRunnerSecretHandoffError for invalid types and safe positive 53-bit time range; negative tests | #592 |
| RMCP-CI-0003 | GREEN/MERGED #593 | registration secret creation order | Temporary secret file was created before clock was validated; invalid time could leave orphaned credential material | source review #593, no real incident claimed | preflight a single finite bounded TTL-safe clock sample before any file creation; assert no-file-on-error and stable mtime/expiry; exact-head validation/attribution green, squash `91299d1b...` | #593 |

| RMCP-CI-0004 | PR_OPEN #594 | attribution workflow concurrency | Repeated PR `synchronize`/`edited` triggers can leave older commit-attribution checks consuming GitHub-hosted minutes; validation already cancels superseded runs but attribution lacks this guard | Workflow source audit 2026-10-09, not a host fault | Per-PR/ref `concurrency` and `cancel-in-progress`, preserving check name, permissions and hosted runner; verify exact-head CI | #584 / #594 |

A closed failure remains recorded with fix/revision and regression evidence.
