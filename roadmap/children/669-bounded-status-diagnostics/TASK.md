# #669/#341 — bounded read-only status/Doctor errors (release candidate 0.1.94)

Owner: Runner-MCP workstream A; Fabric owns fleet policy, A6 and A7.

## Problem

The connected 0.1.88 instance returns version-only `build_identity`; `runtime_status` and `runtime_doctor` calls may return a generic internal tool failure. On main, read-only Doctor paths call independent managers and bridge peers that can raise unexpected storage/shape errors. The normal path must report a bounded WAIT instead of throwing arbitrary private details or incorrectly reporting PASS.

## Bounded implementation

- Reuse the existing status and Doctor tools, not a new updater, relay, endpoint or authority.
- One pure, fail-closed reader wrapper accepts only a builtin status dictionary, returning no private exception text.
- Apply it to existing runtime manager aggregation, self-update baseline, A6 private-root observation, Fabric Actions readiness, continuity and worker qualification.
- Preserve existing response shapes and explicit WARN/degraded status; do not reclassify an unverified source/wheel/host as proven.
- Test expected categorical values, malformed shape, attribute-key errors and private exceptions. Source-only: never modify a live runtime.

## Acceptance

Exact PR-head Ruff, pytest, version reservation, clean Ubuntu installer and attribution SUCCESS; then guarded source merge. A healthy installed host and restored six-role provenance still need independent operator proof. No self-update until real A6/A7 recovery and original-client same-campaign ACK.
