# #381 — Claude worker lifecycle (independent child roadmap)

State: SOURCE_MERGED; HOST_AND_FABRIC_ACCEPTANCE_BLOCKED; no Claude work dispatch; parent: Runner-MCP #381; priority HIGH (Claude multi-project acceleration).

## Hercontrole 2026-10-10 (12:52 CEST) — exact first blocker

**Current evidence:** #381 OPEN, #628 source MERGED and all CI green; Fabric readiness PR #1430 is MERGED (head `7b79664381602efd57869377c0a0ed8fac190745`, Foundation `38046362894` + attribution `38046362913` SUCCESS) but is only a non-authorizing review predicate, always `dispatch_authorized=false`. Fabric #1172 and draft #1422 cannot yet issue authenticated lease/fenced lifecycle authority to the fixed source actuator. AIfordable #370 rootless packaged lifecycle remains open; Fabric #972 exact loopback/read-back admission remains open.

**First non-duplicative engineering task:** Runner-MCP owner to define and qualify the **first-party trusted local verifier binding** to Fabric's finalized typed intent on the dedicated host, not a caller-injected boolean. No network/public status endpoint, no unit/user/path authority and no live service mutation until source contract finalization and owner approval. Fabric chat owns issuer/lease/fence/Agent Bus and AIfordable chat owns real right-host packaged service lifecycle. Claude project dispatch remains explicitly `NO_DISPATCH`.

Read-only attempts during this review: connected `fabric_operational_snapshot` failed internally; `list_services(project=aifordable)` produced an execution error. These do not prove absence of an installed service or identify which runtime answered, and must not drive speculative restarts or account changes.

**Correct operational acceptance:** trusted issuer/verifier+exact worker binding -> preinstalled fixed helper/user-manager authorization -> owner-controlled STATUS/START/STOP with loopback and listener-gone receipt -> Fabric #972 real authenticated non-billable availability/correlation/lease tests -> separate synthetic work admission. A static `READY_FOR_REVIEW` from Fabric #1430 does not grant dispatch.

## SOURCE safety milestone 2026-10-10 — PRE-ACTION child complete

[Runner-MCP PR #637](https://github.com/Blacksp1d3r/runner-mcp/pull/637) merged at `16230a35698abf43d274cae27150ad0eeecce3b9`, exact head `e8e696d880729705c1e88a2055d60828fc66558a`. Attribution `38052268180` and complete validation `38052268203` ALL SUCCESS: Ruff, 2,701 pytest, built release artifact and clean demo. Child `roadmap/children/381-preaction-snapshot/{TASK,STATE}.md` is COMPLETE_SOURCE_ONLY, without live service permission.

Fixed actuator now refuses START unless service INACTIVE + listener ABSENT, refuses STOP/RESTART unless ACTIVE + LOOPBACK_ONLY; foreign/existing listener, duplicate stop/start, unknown or incoherent snapshot blocks **before** any systemd action. This is a local supplementary guard, not process/socket owner attestation or Fabric trusted lease/fence. Parent #381 intentionally remains OPEN, AIfordable #370 and Fabric #972 still unqualified, Claude NO_DISPATCH.

External improvements: Fabric #1432 typed structural preflight merged but non-authorizing; Fabric #1433 typed response correlation is an unmerged draft, also non-authorizing; AIfordable #555 lifecycle evidence runbook merged. Actual first upstream blocker remains central signed authenticated durable #1172/#1400/#1398 Fabric authority + JIT fencing; then correct dedicated host enrollment/proof and Fabric #972 loopback. Never add generic user/systemctl authority or activate paid API as workaround.

## Authority / topology
- One Fabric control plane: policy/capability/lease/fence/plan owns admission (#1172/#240).
- Local Runner-MCP actuator: only fixed exact service and account on the correct rootless worker host.
- AIfordable #370 owns packaged dedicated-account start/stop/listener qualification.
- Fabric #972 owns real loopback availability and return-path qualification.
- Connected github-runner instance cannot assume that aifordable-lab service is registered. No cross-host run or privileged shell.

## TASK + STATE
- TASK-381-01: strict versioned Fabric issued envelope syntax (status/start/stop/restart) — PR #628 MERGED (CI all green), source tests.
- TASK-381-02: fixed `aifordable-coder` user-manager adapter — PR #628 MERGED (CI all green), source tests.
- TASK-381-03: local host identity and loopback-only observation — PR #628 MERGED (CI all green), source tests.
- TASK-381-04: operator-private Fabric authority and lease/fence adapter — BLOCKED on Fabric typed contract finalization; never substitute a caller-supplied `allowed` bit.
- TASK-381-05: dedicated-host rootless helper deployment and verified listener disappearance after STOP — BLOCKED on host/operator authority.
- TASK-381-06: final fixed coding-worker service projection with negative arbitrary user/unit injection — BLOCKED until ready.
- TASK-381-07: first synthetic Fabric lease/start/status/stop path with exact same correlation/fence — BLOCKED until prior gates; no real Claude task.
- TASK-381-08: first EnerCue #89 isolated ExperimentManifest coding task — NO_DISPATCH until readiness, independent CI and user-approved integration.

## Source implementation evidence
- PR [#628](https://github.com/Blacksp1d3r/runner-mcp/pull/628) exact head `e88e880c1c8db307d94c558250d12ee119c35e48`, attribution run `38045484328` SUCCESS and validation `38045484330` SUCCESS (Ruff, 2659 pytest pass, artifact, clean demo), squash main `4981fa648aa127e5d2e0538b9eefec170f816466`.
- GitHub erroneously auto-closed issue #381 on the source-only merge. Explicitly reopened because runtime acceptance is still unproven. Any subsequent PR description must avoid issue-closing keywords even in negated prose.
- All source actions are disabled without separately bound trusted Fabric verifier. Service is not installed and no Claude tasks have been dispatched.

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
