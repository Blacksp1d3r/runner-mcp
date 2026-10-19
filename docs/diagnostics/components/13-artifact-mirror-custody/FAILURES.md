# 13-artifact-mirror-custody — Artifact custody, repository mirrors en Fabric update artifacts — failure register

| Failure ID | Status | Earliest layer | Symptom | Root cause/evidence | Prevention/regression | Tracking |
|---|---|---|---|---|---|---|
| RF-MCP-13-001 | ACTIVE | control-surface/storage admission | Immutable protected release archives exist but no independently verified physical copy can be claimed | Required second-volume target could not be safely admitted through the bounded first-party control surface; broad host access is not an acceptable workaround | zero-argument private-binding readiness with mount/containment/device fail-closed regressions | #585 / #586 |

A closed failure remains recorded with fix/revision and regression evidence.
