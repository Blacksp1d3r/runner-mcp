# 10-service-lifecycle — Managed service lifecycle en autostart — failure register

| Failure ID | Status | Earliest layer | Symptom | Root cause/evidence | Prevention/regression | Tracking |
|---|---|---|---|---|---|---|
| none-migrated | — | — | No additional component-specific reusable failure migrated yet | — | global failure taxonomy + existing component tests | #569 |

| RMCP-F-0017 | SOURCE_PR_CI_PENDING | local pre-action evidence | fixed worker START could be attempted while the expected loopback port was already occupied by another process; later listener check could be misread as worker success | fixed local service and listener were observed only after the command, not as a coherent pair before mutation | #637 adds synthetic pre-action coherence checks: START only INACTIVE+ABSENT, STOP/RESTART only ACTIVE+LOOPBACK_ONLY, malformed/foreign/transitioning state denies without mutation; keep PID ownership and trusted Fabric lease separately unqualified | #381 / PR #637 |

A closed failure remains recorded with fix/revision and regression evidence.
