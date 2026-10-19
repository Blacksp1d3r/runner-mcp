## #739 preventive access-denial categories (no confirmed incident)

A future private-release access request may encounter a masked 301/302/307/308 redirection, proxy rerouting, 401, 403/rate limit, 404, malicious Location, excess JSON or changed tag. The standalone prerelease probe has bounded reason-only WAIT results, a fixed no-proxy/no-redirect transport and synthetic regressions. No real credential leak or production error has been observed in this source task. Physical original-host proof WAIT.

# 13-artifact-mirror-custody — Artifact custody, repository mirrors en Fabric update artifacts — failure register

| Failure ID | Status | Earliest layer | Symptom | Root cause/evidence | Prevention/regression | Tracking |
|---|---|---|---|---|---|---|
| RF-MCP-13-001 | ACTIVE | control-surface/storage admission | Immutable protected release archives exist but no independently verified physical copy can be claimed | Required second-volume target could not be safely admitted through the bounded first-party control surface; broad host access is not an acceptable workaround | zero-argument private-binding readiness with mount/containment/device fail-closed regressions | #585 / #586 |

A closed failure remains recorded with fix/revision and regression evidence.

| RF-MCP-13-002 | PREVENTIVE_SOURCE_TESTED | read-only Release metadata HTTP response length | A valid prefix of a deliberately shortened GitHub response could look like a complete JSON object despite larger Content-Length | Enforce positive bounded decimal Content-Length when present and match actual received bytes, 6 synthetic regression vectors; 39 local cases green; exact PR-head CI pending | #739 / PR #743 / RMCP-F-0047 |
