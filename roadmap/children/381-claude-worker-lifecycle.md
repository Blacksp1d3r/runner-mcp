# #381 — Claude worker lifecycle (independent child roadmap)

State: SOURCE_IMPLEMENTATION; parent: Runner-MCP #381; priority HIGH (Claude multi-project acceleration).

## Authority / topology
- One Fabric control plane: policy/capability/lease/fence/plan owns admission (#1172/#240).
- Local Runner-MCP actuator: only fixed exact service and account on the correct rootless worker host.
- AIfordable #370 owns packaged dedicated-account start/stop/listener qualification.
- Fabric #972 owns real loopback availability and return-path qualification.
- Connected github-runner instance cannot assume that aifordable-lab service is registered. No cross-host run or privileged shell.

## TASK + STATE
- TASK-381-01: strict versioned Fabric issued envelope syntax (status/start/stop/restart) — PR #TBD, source tests.
- TASK-381-02: fixed `aifordable-coder` user-manager adapter — PR #TBD, source tests.
- TASK-381-03: local host identity and loopback-only observation — PR #TBD, source tests.
- TASK-381-04: operator-private Fabric authority and lease/fence adapter — BLOCKED on Fabric typed contract finalization; never substitute a caller-supplied `allowed` bit.
- TASK-381-05: dedicated-host rootless helper deployment and verified listener disappearance after STOP — BLOCKED on host/operator authority.
- TASK-381-06: final fixed coding-worker service projection with negative arbitrary user/unit injection — BLOCKED until ready.
- TASK-381-07: first synthetic Fabric lease/start/status/stop path with exact same correlation/fence — BLOCKED until prior gates; no real Claude task.
- TASK-381-08: first EnerCue #89 isolated ExperimentManifest coding task — NO_DISPATCH until readiness, independent CI and user-approved integration.

## Acceptance evidence required
1. GitHub PR exact-head SHA; attribution + full Ruff/pytest, release build and clean demo.
2. Host-local dedicated identity, fixed helper integrity, installed source/version, exact unit and runtime context; no private strings published.
3. Fabric-issued owner/fence/lease/approval and zero unauthorized actions.
4. Rootless start and health only on exact loopback; stop removes listener; restart after fencing respects current policy.
5. Failure Museum for denied and partial action status; no fabricated complete result from a TCP port alone.
6. Fresh separate authenticated response lineage and no duplicate dispatch (issue #590) before real workload.
7. Source tests are never passed off as live operational acceptance.

## Security constraints
No generic sudo; no user/unit/host/path/command/env selector; no API billing fallback; no new scheduler; no live merge/deploy/production service enable. Preserve existing #587/#588 artifact retention and backup priorities as independent lanes.

See `docs/architecture/FIXED_CODING_WORKER_ACTUATOR.md`, issue #381 comments, and Fabric draft #1422.
