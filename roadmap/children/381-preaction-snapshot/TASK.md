# #381 — Child: coherent local service snapshot before lifecycle mutation

## Objective
Deny exact-target lifecycle requests *before* they can modify a user service if the observed fixed service state and fixed listener state disagree or show a pre-existing occupancy conflict.

## Parent / scope / ownership
Runner-MCP issue #381, independent source-only hardening after PR #628. Runner-MCP owner. Does NOT own Fabric #1172/#1400 durable signed intent admission, AIfordable #370 rootless service deployment or Fabric #972 authentic availability/return-path validation.

## Input -> policy -> bounded result
Already syntactically valid intent with an independently injected trusted authorization verifier -> fixed local service state + fixed local listener observation -> deny coherent-state conflict before action -> fixed user-service action only if coherent -> post-action observed bounded result. Never accept arbitrary user/unit/path/port/command selectors; no caller-control over local identity.

Accepted PRE-states, following Fabric JIT admission (which remains external and unimplemented):
- START: fixed service INACTIVE, fixed listener ABSENT.
- STOP or RESTART: fixed service ACTIVE, fixed listener LOOPBACK_ONLY.
- STATUS: read-only evidence; unsafe listener returns a bounded blocked observation.

Unsafe/public/foreign, conflicting or transitional service/listener combinations: no mutation. A failure before the command returns mutationTriggered=false; a failure once a command is attempted returns mutationTriggered=true (unknown actual effect, requiring reconciliation).

This is a local *additional* guard, not a proof of listener PID ownership, host identity, durable lease, JIT side-effect safety or two-actor exclusion. Snapshot and action are not atomic; no live activation or authorization from this child.

## Acceptance / validation
1. Inactive service with pre-existing fixed-loopback listener blocks START without action.
2. Active service with absent listener blocks STOP and RESTART.
3. Already active service blocks duplicate START; stopped service blocks duplicate STOP.
4. Unknown, failed, transitional, unsafe/public listener, or read errors do not trigger mutations.
5. Coherent snapshots allow correct fixed action (synthetic tests); status still read-only.
6. CI exact-head Ruff/pytest, release build, clean demo and commit attribution all terminal success.
7. Source-only PR merged only after CI and review; parent #381 remains OPEN until independent Fabric and AIfordable live proof.

## Constraints
No live service/tunnel changes; no paid coding API; no GitHub issue auto-close syntax; preserve other owners' private authority and project scope.
