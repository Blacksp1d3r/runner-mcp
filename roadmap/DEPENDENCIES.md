## 2026-10-10 — This Runner-MCP lane excludes #381; blueprint #630 source children reconciled
User explicitly assigned operational Claude #381 to a **different active chat**. Do not claim, branch on, restart, deploy or duplicate that work; issue #381 remains operationally OPEN there.

Independent #630 outcomes:
- BPA-03 legacy/new-child mapping [PR #632](https://github.com/Blacksp1d3r/runner-mcp/pull/632), exact HEAD `a3614c5172a06879ac672c34033a9fb462aa8223`, attribution `38046631374` + full validation `38046631455` ALL SUCCESS, reviewed, squash MERGED `a59875b943441b19ba864ae6643ef9458541020c`. `roadmap/children/bpa-03/STATE.md` COMPLETE. Historical #381 and diagnostic components indexed **without edits**.
- BPA-02 symbolic manifest **proposal only** [PR #633](https://github.com/Blacksp1d3r/runner-mcp/pull/633), exact final HEAD `bcf90a3c7525c46956bb2a11a3d7a426d7455817`, attribution `38046821035` + full validation `38046821043` ALL SUCCESS; reviewed, squash MERGED `261aed632fd2539af33896ba6574ff4d6b05d536`. Strict proposal-only `project_manifest_candidate.yml` + JSON Schema and adversarial synthetic unit tests. Earlier CI `38046762677` failed a Ruff I001 blank-import separator only, corrected on final head. No root `project.yml`, no proven local Git primary, storage namespace, independent restore or Fabric lease; `BPA-02/STATE.md` COMPLETE applies **only to source design**.
- Remaining real authority is [#634](https://github.com/Blacksp1d3r/runner-mcp/issues/634) / BPA-02B. Docs-only [draft PR #635](https://github.com/Blacksp1d3r/runner-mcp/pull/635) proposed the blocked child contract and index; HEAD `014445d226b6da6f03b77ab87bad3d02433e43fe`, attribution `38047164866` and validation `38047164865` **PENDING** at checkpoint. Keep #630/#634 OPEN for verified owner-authorized physical authority, single-writer fenced Git, isolated restore and approved future operational schema/manifest. No source-only PR can grant machine authority.
- AIfordable #537 / Fabric #1397/#1428 remain separate operators; #587/#588 independent release custody and restoration remain OPEN without physical receipts; #590 current connector/source generation still unqualified. No production services, tunnel, credentials, host storage, GitHub artifacts or #381 workers touched.

Next safe step here: check PR #635 exact-head all CI and review; if source-docs green merge while keeping #634 BLOCKED; then reconcile GitHub/current handover and stop only if remaining tasks need real independent operator authority. Never infer successful restore or runner health from source CI.

## 2026-10-10 — Shared blueprint #630 BPA-01 landed, remaining children blocked/independent

BPA-01 PR #631 source-only docs merge `20c19970d14b9402ce6a2393477f3056602498bd`, attribution `38045941135` and full CI `38045941103` ALL SUCCESS; see `roadmap/children/bpa-01/{TASK,STATE}.md` and `docs/standards/REPOSITORY_BLUEPRINT_COMPATIBILITY.md`. Parent #630 remains OPEN. BPA-02 requires independently qualified project identity/local Git/storage authority and safe symbolic manifest schema, no false authority assertion; BPA-03 mapping of existing children and future TASK+STATE depends on BPA-01 but requires no mass legacy migration. Future Fabric scaffold plan/apply is an independent Fabric owner/approval lane. No dependency of #381/#590/#587/#588 is bypassed by blueprint documentation.

## 2026-10-10 — Claude priority #381: fixed host-local rootless source slice #628 MERGED; live worker STILL BLOCKED
User explicitly prioritized Runner-MCP #381 to enable Claude on multiple projects. After issue #381 and Fabric/AIfordable dependencies review, [PR #628](https://github.com/Blacksp1d3r/runner-mcp/pull/628) source-only fixed rootless Claude actuator was merged: branch `feat/381-fixed-rootless-coder-actuator`, exact reviewed HEAD `e88e880c1c8db307d94c558250d12ee119c35e48`, attribution `38045484328` SUCCESS and full validation `38045484330` SUCCESS (Ruff, **2,659 pytest PASS**, built artifact, clean five-minute demo). Squash commit `4981fa648aa127e5d2e0538b9eefec170f816466` on main. Tests cover denied unsupported fields/UID/actions/versions, expired/invalid fence and lease syntax, central verifier unavailable/denied, fixed `systemctl --user` only, loopback port and unsafe listener checks, rootless wrong identity and attempted-but-unverified lifecycle action.

The source module `src/runner_mcp/fixed_coding_worker_actuator.py` is NOT a registered MCP tool/CLI/network endpoint, installed daemon, worker control plane or active scheduler. It hardcodes `aifordable-coder` and the exact coding-worker unit, accepts no user/unit/path/command/environment selectors, refuses actions without separately installed trusted Fabric authorizer, performs no sudo/cross-user switch, observes loopback-only port 8030 with bounded status and partial-mutation evidence. See `docs/architecture/FIXED_CODING_WORKER_ACTUATOR.md` and [child roadmap](https://github.com/Blacksp1d3r/runner-mcp/blob/main/roadmap/children/381-claude-worker-lifecycle.md).

**GitHub automatically CLOSED issue #381 on merge**, even though this was source-only; it was explicitly **REOPENED** immediately, because issue acceptance is operational, not simply code-present. Avoid auto-close issue keywords even in negated PR prose. Issue #381 comment #6096664381 records exact state. Physical acceptance still unmet: Fabric #1172/#1422 authenticated typed lifecycle issuer/verifier with durable lease/fence/expiry/idempotency/authorization and ONE scheduler; right-host fixed endpoint and managed installation under the dedicated rootless identity (AIfordable #370); actual packaged preflight/status/start/stop, disabled by default and loopback listener-gone proof; Fabric #972 authenticated availability/response correlation/fenced synthetic work claim; only then EnerCue #89 or other Claude project tasks. Fabric #1172 and AIfordable #370 owners received coordination comments, no competing edits. The github-runner ChatGPT-connected instance does NOT have AIfordable alias and cannot control another host user manager by registry guesswork. **#381 OPEN, Claude dispatch BLOCKED**, no live services or paid API calls.

Next safe action for Runner-MCP/AIfordable/Fabric owners: finish trusted first-party Fabric authority to local rootless actuator across correct host, prove only the fixed unit and dedicated account, then real rootless lifecycle and Fabric end-to-end availability/correlation. Keep existing #587/#588 storage work independent; no archive deletion/host mutation from this code merge. Current priority #381 until end-to-end readiness, then resume remaining roadmap.

## 2026-10-10 — #629 build identity fail-closed source MERGED; #590 LIVE UNQUALIFIED
Runner-MCP [PR #629](https://github.com/Blacksp1d3r/runner-mcp/pull/629) exact head `53614092bafac8e528b4905fc962da72ffde4621`: attribution `38045401691` SUCCESS; full CI `38045401730` SUCCESS, all Ruff/pytest, built artifact and clean demo; reviewed then squash MERGED `7deb63cd8d623a74389c9f582d6e2d1ec688b2eb`. Now valid `build_identity` remains seven-field, invalid/unavailable identity returns fixed `runner-mcp/build-identity-unavailable/v1` / `identityEvidenceComplete=false` without private text or fabricated build evidence. Source-only; do not claim installed runtime fixed. Issue #590 was independently checked still OPEN; original doctor read returned 12 older checks and `runtime_status` failed, first live divergence unknown. No new live probe, restart or provider artifact deletion permitted without approved private evidence.

Parallel #381 Claude work now occupies [draft PR #628](https://github.com/Blacksp1d3r/runner-mcp/pull/628), latest observed head `e88e880c1c8db307d94c558250d12ee119c35e48`; do not duplicate or modify its branch. Fabric #1428 likewise remains independent active owner. Backup #587/#588 remain OPEN for physically independent 2/2 mirror plus offline restore after qualified AIfordable/Fabric volume delegation. Current source success does not grant physical custody.

Next safe #590 operator step: approved read-only installed source/build/interface + client catalog and ingress↔response lineage on an authorized fresh session, then verify new bounded identity/status tools once. In parallel, safely review independent roadmap children only after claim/PR check. No tunnel/host/mount/service changes, no shell bypass.

## 2026-10-10 — #590 second source-only identity diagnostic PR #629 (draft, exact CI pending)
Reconciled both Library standards (master v1.2; repository blueprint v1.0), main HEAD `efac9975390da699da4373e34c0dbe774bebdc8f` at branch point, AGENTS, roadmap, dependencies, handover and current GitHub owners. The connected `runtime_doctor` independently again returned the old **12 checks**, WARN with 0 failed/3 warnings; `runtime_status` returned generic internal tool failure. Installed source, client catalog generation and exact return route remain UNKNOWN. Do not infer an outage or assume PR #627 code is live.

Runner-MCP #590 new isolated source-only [draft PR #629](https://github.com/Blacksp1d3r/runner-mcp/pull/629), exact head `53614092bafac8e528b4905fc962da72ffde4621`, adds fixed `runner-mcp/build-identity-unavailable/v1` with `identityEvidenceComplete=false` for missing/invalid/failed provider while preserving valid seven-field identity payload. Unit and authenticated MCP HTTP negative regressions cover fail-closed private error paths. Attribution CI `38045401691` SUCCESS; full validation `38045401730` IN_PROGRESS at this checkpoint. No runtime rollout or bridge repair claimed. Keep #590 OPEN for approved private source/catalog/ingress→response matching, even after source merge.

Independent Fabric #1397 remains owned by Fabric draft #1428; no parallel changes in that branch. AIfordable #553 already merged but storage binding is not live qualified; #587/#588 remain OPEN without two independent protected copies or genuine offline restore. No mount/copy/tunnel/restart/credential/artifact cleanup authorized. #618 remains separate green-CI review, no duplicate intervention.

Next safe action: inspect #629 exact-head Ruff/pytest, build, clean demo and attribution; resolve only confirmed failures, obtain review before merge, record updated head and preserve #590 live verification blocker. In parallel review other conflict-free source children only after claims/CI reconciliation; preserve Fabric and recovery owners.

## 2026-10-10 — User priority changed to #381 Claude worker bridge; source implementation PR #628
User explicitly prioritized [Runner-MCP #381](https://github.com/Blacksp1d3r/runner-mcp/issues/381) over unrelated roadmap work to unblock Claude multi-project assistance. Reconciled existing issue, cross-owner comments, Fabric draft [#1422](https://github.com/Blacksp1d3r/Runner-Fabric/pull/1422), Fabric #1172/#240/#972, AIfordable #370 and existing same-user ServiceManager. No competing #381 branch/PR existed. **ONE Runner-Fabric control plane** owns scheduling, worker eligibility, lease/fence, authorization, idempotency, audit and return correlation. Runner-MCP is only a fixed host-local mechanism; dedicated Claude user manager must never be accessed via sudo or arbitrary cross-account systemctl.

New source-only [PR #628](https://github.com/Blacksp1d3r/runner-mcp/pull/628), branch `feat/381-fixed-rootless-coder-actuator`, exact head at this checkpoint `e7b0c4866fcbf1767e9ea73ad048c8ec89d7ae48`, DRAFT/OPEN, CI `38045392637` attribution QUEUED and `38045392668` validation QUEUED. Earlier CI head `af1838bd097e40e231fcca06b1752dfec7155bbe` FAILED Ruff UP022 (stdout+stderr PIPE) before pytest; corrected on latest head to `capture_output=True`, must check new exact-head CI. No merge before Ruff/pytest, clean demo, built artifact and attribution all SUCCESS.

Implemented isolated `src/runner_mcp/fixed_coding_worker_actuator.py`: fixed symbolic Claude coding capability and typed Fabric intent fields, strict no-extra-field/no arbitrary UID/unit/path/argv/env, short expiry and positive lease/fence/revision syntax. Absent Fabric authority verifier = BLOCKED; no runtime tool/CLI/endpoint registered. Dedicated identity `aifordable-coder`, exact rootless user service `aifordable-subscription-coding-worker.service`, fixed user-manager owner/private bus check and hardcoded fixed `systemctl --user` selectors; local port 8030 loopback-only observation with no raw output. Result always bounded with attempted-mutation flag (cannot misrepresent partial failed start as no mutation). Added synthetic negative tests and independent architecture and child-roadmap docs `docs/architecture/FIXED_CODING_WORKER_ACTUATOR.md` / `roadmap/children/381-claude-worker-lifecycle.md`.

**NOT YET #381 operational acceptance:** uninstalled/unregistered local helper, no trusted Fabric lease/fencing verifier bound, no authorized service endpoint, no `list_services(aifordable)` projection, no cross-identity execution, no live AIfordable #370 packaged service start/status/stop, no Fabric #972 loopback+return qualification, no actual Claude task dispatched. `aifordable` intentionally absent in current github-runner instance; do not spoof it. Keep #381 OPEN even after PR merge until real right-host first-party qualification under one Fabric controller. EnerCue #89 NO_DISPATCH; existing Claude subscription worker itself previously qualified, do NOT reinstall or switch to paid API. No live host, credential, service, tunnel, disk, runner or provider billing changes.

Safe next action: confirm #628 exact HEAD and all CI jobs; focused fix for concrete CI failures; merge source-only only after complete green CI and review while keeping #381 OPEN. Then operator/Fabric coordination for trusted intent verifier, dedicated-user rootless helper installation, post-start loopback and post-stop absence under AIfordable #370, Fabric #972 end-to-end correlation/fence, and first synthetic claim before permitting real Claude work.

## 2026-10-10 — Fabric #1397 owner has active #1428; exact lint blocker localized
Fabric #1397 is actively continuing in a separate owner lane via [draft PR #1428](https://github.com/Blacksp1d3r/Runner-Fabric/pull/1428), exact HEAD `e3521f49ba996b378fdc132b8a922cc04b2bebcf`. CI attribution `38042060760` SUCCESS. Foundation `38042060585` FAILED strictly `foundation.lint` Ruff `C408` in `tests/test_storage_binding_evidence_gate.py:9` (`dict()` to literal). `foundation.tests` and `foundation.doctor` are SUCCESS. Read-only diagnosis passed to its owner as PR comment #6096292386; no competing Fabric branch or workflow rerun. After owner correction require fresh exact-head Foundation+attribution CI. #1428 is read-only fail-closed AF-SB evidence work, NOT live service/physical namespace delegation; its ongoing work must not be duplicated by Runner-MCP. Issue #1397 OPEN; #587/#588 physical acceptance remains blocked.

## 2026-10-10 — Read-only connector split evidence and #618 CI reclassified
#590 further same-session read-only evidence: `fabric_operational_snapshot` returned structured `runner.fabric/operational-snapshot/v1`, `degraded=true`, `agent-bus.relay` unknown with `reason_code=evidence-unavailable`, `execution_enabled=false`, `mutation_enabled=false`, capacity unknown. `list_projects` failed with generic internal tool error. Alongside `runtime_doctor` WARN (older 12-check vocabulary) and generic failures from `runtime_status` / `build_identity`, these prove **mixed tool outcomes**, not confirmed shared installed/runtime identity or healthy worker queue. Issue #590 comment #6096271084. No tool retry loops, host changes, tunnel resets, credential rotation or live deployment.

Independent #618 read-only review (ownership preserved): draft/open exact head `eb7e9fdc8699cd461e39176ff52f89d71669428a` is currently mergeable/clean but left OPEN. Attribution `37963241193` SUCCESS, latest validation `37963241191` all 3 jobs SUCCESS (Ruff/pytest, built artifact, clean five-minute demo). The former external MCP Registry timeout no longer blocks the current CI; source-only quarantine ledger still needs missing-vs-ever-initialized semantics and power-loss/rearm/cursor convergence review under #615/#616/#617 before merge/activation. Owner informed in PR comment #6096268341; publisher check must not be bypassed. No code changes to #618.

Source #590 PR #627 is ALREADY MERGED at `e06fe5b7f44c92ae22d4fa291a142b6b67803db3` with full exact CI green, but installed connector version/return lineage remains unknown. Physical protected archive custody still BLOCKED by AIfordable #537 `qualified:false` and Fabric #1397 unbootstrapped dedicated namespace; Runner-MCP #587/#588 remain OPEN, no 2/2 off-primary copies and no offline restore proof. Retain GitHub artifacts.

## 2026-10-10 — #627 bounded status source security MERGED; connected runtime still unqualified
Runner-MCP independent #590 source-only [PR #627](https://github.com/Blacksp1d3r/runner-mcp/pull/627): exact head `e70e11702504c3fe161900ced4afceff8c7df084`, attribution `38042225385` SUCCESS, full validation `38042225393` all 3 jobs SUCCESS (Ruff/pytest, built artifact, clean demo), squash MERGED `e06fe5b7f44c92ae22d4fa291a142b6b67803db3`. Source `runtime_status` now returns fixed `runner-mcp/runtime-status-degraded/v1` / `state=degraded` / bounded per-manager reason code / `runtimeEvidenceComplete=false` on first-party manager read/error/non-object; keeps normal success unchanged. Four authenticated HTTP regressions prove no private exception or partial manager evidence leak. First CI heads failed Ruff I001 third-party import grouping only and were corrected on exact merged head. Issue #590 **OPEN** for actual client/installed source/catalog/return-route qualification; no active server/runner/tunnel deployment/credential/storage change.

Additional #590 read-only observation: connected `runtime_doctor` returned 12-check WARN (0 failures, 3 warnings) omitting `self_update_source_baseline`, `self_update_runtime_activation`, and `fabric_a6_binding_state` checks that current main source necessarily emits. Connected `runtime_status` and `build_identity` returned generic internal errors. This supports SOURCE-RUNTIME/CATALOGUE GENERATION MISMATCH possibility but cannot prove responding instance. Issue comments #6096224333 and #6096255810; bounded operator-private diagnostic required before claiming tool response correlation and installed version. Don't retry old tunnel restarts or reuse stale doctor evidence.

Cross-project back-up chain: AIfordable issue #537 first source slice PR #553 exact head `dedbc8296313ec8a455a98cae85499dcd28ad9e2`, CI `38038298136` SUCCESS, squash MERGED `486896fe0feac1ffbda51a8b8c3ca002f1161eb5`. Private registry binding still `qualified:false`; this does NOT authorize mirror writes. Fabric #1397 owner notified in issue comment #6096212348, remains OPEN for admitted live first-party same-host release namespace/bootstrap. Runner-MCP #587/#588 remain OPEN with **0 verified physically independent 2/2 copies / 0 genuine offline restore receipts**. Next authorized order: qualify machine runtime/volume/binding -> Fabric #1397 host-owned namespace -> fresh #586 read-only readiness -> #587 protected pair immutable mirror+verification -> #588 offline isolated real reader/bootstrap restore+cleanup -> only then evaluate GitHub artifact deletion. Existing provider artifacts retained.

Next safe independent Runner-MCP task after #627: source-only review of bounded build identity *unavailable* semantics, but do not fabricate healthy identity or change production runtime. Priority live gap #590 requires fresh approved read-only installed build/route evidence by operator; source merge alone is not live repair. No unapproved host, tunnel, mount, archive, self-update or credential changes.

## 2026-10-10 — #590 bounded runtime-status diagnostics; AIfordable #553 source dependency MERGED
GitHub first reconciled after #626: Runner-MCP #587/#588 **OPEN** without any actual 2/2 independent physical mirror or offline recovery receipts. AIfordable [#553](https://github.com/Blacksp1d3r/AIfordable/pull/553) exact head `dedbc8296313ec8a455a98cae85499dcd28ad9e2`, exact CI `38038298136` verify SUCCESS, squash `486896fe0feac1ffbda51a8b8c3ca002f1161eb5`; however private release-archive custody binding remains `qualified:false`. Fabric #1397 still OPEN for separately admitted live host-owned fixed namespace/bootstrap; dependency update posted in Fabric #1397 issue comment. No storage mutation or artifact pruning permitted.

#590 independent source-only security child: [draft PR #627](https://github.com/Blacksp1d3r/runner-mcp/pull/627), branch `safety/590-bounded-runtime-status-degradation`, exact HEAD `e70e11702504c3fe161900ced4afceff8c7df084`. `runtime_status` no longer propagates private manager `str(exc)` in `ValueError`; when self-update/bootstrap/update status is unavailable/malformed it returns a categorical fixed-schema `degraded`, `runtimeEvidenceComplete=false` and no partial/secret-bearing manager status. Four authenticated MCP HTTP regression cases cover each failing manager and malformed nonobject evidence, check sanitized audit. CI attribution run `38042225385` SUCCESS; full validation `38042225393` Ruff/pytest SUCCESS and built artifact SUCCESS; clean five-minute demo IN_PROGRESS at last observation. Two earlier heads failed Ruff import-group I001 only, corrected at exact current HEAD; do not merge unless clean demo also terminal SUCCESS and exact PR HEAD unchanged. No runtime deployment, connector/tunnel/server restart or workspace permissions changed.

New read-only evidence #590 (issue comment #6096224333): connected `runtime_doctor` returned a structured 12-check WARN (0 failed, 3 warnings); current `main` server doctor unconditionally includes `self_update_source_baseline`, `self_update_runtime_activation` and `fabric_a6_binding_state` names but none returned via live connector. `runtime_status` and `build_identity` returned generic internal failures. This proves doctor-result vocabulary does not match current source's expected complete checks, consistent with installed version/catalog/route drift, without proving which edge or runtime answered. #627 improves error handling only and does not prove live connector recovery. Do not equate client tool listing or doctor return with exact current source; require approved safe private installed-build + interface/route identity evidence and fresh session, no speculative host or transport changes.

Next safe steps: check #627 exact HEAD attribution + ALL 3 full-validation jobs; after exact green perform independent review, mark ready, merge with explicit head lease (title must avoid issue auto-close), confirm #590 stays OPEN; update canonical handover and Failure Index. Otherwise classify concrete CI failure and fix only focused source/tests. Then continue bounded #590 diagnosis or await separately authorized Fabric #1397 / #586 volume and release archive proofs.

## 2026-10-10 — #626 complete; physical custody prerequisites unchanged
Runner-MCP #626 source final copy-integrity gate merged `5aba8423594290a7837208e53721234dfe0df778`, exact-head full CI green. Security code complete, not a physical backup: #587/#588 remain OPEN and require separately trusted AIfordable #537 volume binding -> Fabric #1397 distinct fixed host-owned release-custody namespace/bootstrap -> #586 live zero-arg readiness -> #587 verified exact 2/2 release mirror on independent physical storage -> #588 isolated no-network real reader/bootstrap restore+cleanup proof. Do not delete GitHub provider artifacts or alter any host/mount/credential to bypass.

Secondary independent issue #590: per-tool live behavior differs and `runtime_status` has a plausible uncategorized exception re-raise; source-only bounded/error-sanitized contract and integration regressions would be useful, but live cause unconfirmed. AIfordable #553 owner to fix CI fixture date before #537 can be marked qualified.

## 2026-10-10 — Release-archive custody gates (latest)
- Runner-MCP #587 source-only finish: child PR #626 draft HEAD `abd2c4eb05348b86b87e09f65acd5cf149d98972`, attribution `38038139765` SUCCESS, validation `38038139723` IN_PROGRESS. Requires full exact-head CI and review; source proof is not real storage receipt.
- AIfordable #537 / draft #553 is still unqualified (`AF-SB-0001` qualified=false). CI `38035068769` FAILED solely in the Test API step with 9 dated topology-guard fixture failures; 1352 other tests passed. Canonical registry dated 2026-10-10 but test `TODAY`/mock clock 2026-10-08 => `TOPOLOGY_FUTURE_DATED` (fail closed correctly). Owning lane to repair fixtures, preserve negative future-date coverage; no concurrent branch work.
- Runner-Fabric #1397: source-only #1426 and #1427 merged; still needs first-party qualified private same-host authority provider, fixed separate archive namespace bootstrap, mount/owner/no-follow/fsync evidence. Do not share F34 repository mirror namespace.
- Physical order remains #537 qualified authority -> #1397 trusted bootstrap -> Runner-MCP #586 host-admitted fresh volume readiness -> #587 verified EXACT active + rollback 2/2 physical second-device mirror -> #588 genuine offline disposable local-reader/bootstrap preflight/apply/rollback and cleanup -> only then GitHub artifact disposition.
- No production copy, restore, prune or storage-owner authority is granted by the source merges. #587/#588 OPEN until observed live receipts; provider archives remain preserved.
- External operational issue #590 partly improving: doctor structured WARN but runtime_status/build_identity still fail internally. Do not use unrestricted shell/tunnel restart as workaround. #618 draft with green local CI does not imply published external registry acceptance.

## 2026-10-09 — Windows source prerequisites integrated; runtime still gated

Source-only host platform contract #490 (merge `816c7e5abd5ddbf91d0e580e6a7102bb0308faf0`) and explicit non-Linux default service backend rejection #619 (merge `bac86a97f1493ff943ef5f3d01228814e3ed61c0`) both passed exact-head attribution and full Runner MCP validation. Windows is recognized but `serviceAdapterImplemented=false`, and `ServiceManager` now fails closed rather than attempting Linux systemd on a Windows/unknown host. This is **not** Windows SCM support, Windows autostart, customer-host qualification or activation. No live Windows test or deployment was attempted.

Next permissible #489 child: explicit fixed-alias Windows SCM adapter using the existing `ServiceBackend` Protocol, rights separation, state normalization, unsupported-backend denial and isolated Windows CI; only after its exact test proof may Windows service lifecycle be considered. Preserve existing Linux integration tests and zero generic PowerShell/argv/path/service selector authority. Do not conflate known-host capability with an admission token.

## 2026-10-09 — First-class Windows host without premature activation

- #489 owns OS-neutral service lifecycle adaptation; existing #490 is a source-only recognized-host contract, NOT operational Windows support. It now distinguishes `supported` (known host family) from `serviceAdapterImplemented` (service backend implemented). Windows is known but its SCM adapter remains unavailable and **must fail closed**.
- Current Linux `ServiceManager` already accepts an OS-neutral `ServiceBackend` Protocol with fixed project/service aliases and bounded start/stop/restart authorization, but its default is lazily `SystemdUserBackend`. Next child must choose the backend deterministically from approved host capabilities, never infer Windows readiness from platform recognition.
- Before any Windows action: implement and unit-test an explicit Windows SCM adapter behind that same alias/allowlist boundary, normalize service states, require a least-privilege service identity, and run isolated Windows CI with unsupported/no-backend rejection. No arbitrary PowerShell/argv/path/service selectors, WSL workaround, or customer-host activation before those gates.
- Exact-head #490 validation remains prerequisite for merging its contract; subsequent adapter activation is a separate PR and approval gate. This does not alter the existing Linux service behavior.

## 2026-10-09 — Source gates versus live operator authority (reconciled)

1. #388 enrollment CLI on main after all standard CI green, but no enrollment executed or admin credential provided; `RUNNER_MCP_CI_RUNNER_ADMIN_TOKEN` must remain independent of ordinary mailbox token. #387 manual-only, no-cache qualification workflow likewise merged but has **never proved** a live disposable runner. No PR source code may use deployment-capable host as a substitute.
2. Source-only #599 control-plane authenticated freshness complete; the documented default tunnel-client long-poll is 30s plus 5s deadline guard, the local maximum successful-poll age policy is 90s and future skew 5s. External #590 and #333 operator/session/route readiness are independent; a stale or failed auth poll is not a diagnosis that the MCP process is down.
3. #586 independent-volume read-only status source merged. AIfordable #537 machine-readable storage topology and Runner-Fabric #1397 fixed archive namespace are still OPEN; exact separate physical volume identity, owner-private mirror, real mounted second storage and fully qualified protected archive copy remain **BLOCKED**. #587 mirror mutation and #588 restore must not run/land ahead of separately approved real gates.
4. All checked-in admission results are synthetic or hosted CI source evidence unless identified as operator-owned live evidence. No physical backup move, filesystem privilege change, production action, extra paid service or secret disclosure occurred.

## 2026-10-09 — Runner registration CI isolation and credentials (issue #584)

1. Public repository GitHub-hosted standard CI minutes are free; avoid exchanging a trusted hosted PR boundary for privileged self-hosted execution on a false cost assumption. Private Actions storage and hosted releases belong to separate project issues.
2. Source-level intake hardening COMPLETE on main: #600 symlink registration/label drift, #601 inventory page completeness, #602 work root traversal, #605 malformed inventory identity rows, #604 local group/world-write boundaries.
3. Local CLI #388 is still a PR, not live admission. Its proposed `RUNNER_MCP_CI_RUNNER_ADMIN_TOKEN` must be independent of ordinary mailbox `RUNNER_MCP_GITHUB_TOKEN`. A successful source merge does NOT authorize registration.
4. Before #387 self-hosted qualification/any workflow selector activation, prove dedicated disposable nonproduction VM per untrusted job, strict owner/mode, short-lived register token process visibility, negative tests, cache provenance, network/secret separation, exact custom labels, job teardown and stable required checks.
5. Live ChatGPT connector/runner capacity UNKNOWN while #590 remains unlocated; no inference from GitHub code or synthetic tests. No production/deployment runner can be the shortcut.
6. Preserve independent release/provenance/rollback gates and status `BLOCKED` for actual runner admission until verified. Do not start downstream tasks on a speculative future runner.

## 2026-10-06 customer update safety dependency

Tracking: #414; Fabric authority/policy: Blacksp1d3r/Runner-Fabric#1063; AIfordable contract: Blacksp1d3r/AIfordable#401.

Build order for this lane is intentionally downstream:
1. Fabric defines read-only semantic readiness and returning-node trust/quarantine contracts.
2. Runner-MCP may add the minimal local read-only projection needed to satisfy those contracts.
3. No live customer update mutation is added until Fabric rollout/recovery/fencing gates exist.
4. Exact release staging must complete and verify before destructive activation.
5. Durable phase/restart reconciliation is required before power/network interruption qualification.
6. Database/schema rollback remains separate from code rollback.

Do not turn #414 into fleet orchestration or generic host inspection.

# Runner MCP — Dependency / Integration Order

Last reconciled: 2026-10-04. GitHub current state wins.

## Current cross-product gates

- Runner Fabric transport foundation remains COMPLETE on Runner MCP `main` via PR #111 / merge
  `3ebd39981c358c307fa66afa32ad2f5fc32731cf`; issue #109 is complete. Do not duplicate this work.
- Issue #110 is COMPLETE. A real first-party client invocation traversed the bounded Runner MCP ->
  Runner Fabric coarse work-unit path, and bounded get/cancel/operator-safety evidence is reconciled.
  Do not rebuild the bridge or add a second primary transport.
- Runner MCP now has bounded managed Runner Fabric update/status/rollback support and accepts the
  canonical automatic control-plane bundle lane. Before any live Fabric runtime mutation, reconcile
  current Runner Fabric `main` and Runner MCP `fabric_update_active`; source-development activity
  in Runner Fabric is not itself evidence that a managed Fabric runtime update is active.
- Issue #108 is the remaining live self-update recovery proof. PR #262 / merge
  `ba35f70eb9e3e489fc6936d2bc2f0fc425710c81` provides a local-only deterministic recovery
  qualifier; the actual interrupted-install/overlap/local-recovery proof must still be executed on
  the qualified host and must not be bypassed with generic shell, package-manager or remote-control
  authority.
- Issue #101 remains an independent external-discovery lane; Glama/AllMCPs/launch-post actions are
  owner-controlled and non-blocking. Third-party stale install metadata is tracked separately in
  #263 and must not drive product/runtime changes.

## Current build order
1. Core safety/protocol invariants remain the base for every later slice.
2. Task 10 / issue #108 private-host live self-update/recovery proof is no longer blocked by host qualification or first-party control. The remaining step is an intentionally local operator recovery drill using the merged bounded qualifier; it does not block independent documentation/discovery work.
3. Tasks 16, 17, 18, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 35, 36 and 38 are complete on main; do not duplicate them.
4. Task 34 retention preview is COMPLETE on main via PR #92 / merge `36599fab6ed1b96d145a830fa45b935aba823db3`. Task 37 restore-execution review is COMPLETE on main via PR #93 / merge `81720ce24d6e309c72d6a06155c4e70d3b868dbf`. Task 39 adapter-contract refactor is COMPLETE on main via PR #94 / merge `163c5e0597cb8a6cc70f32fd3d8c99e30d08f7aa`. Task 40 pruning execute-boundary review is COMPLETE on main via PR #95 / merge `83453d9bb56f1bcbb69ccf68563699aab56e777b`.
5. Task 28 depended on Task 24 and is complete via merge `131e168e02b7d5781441bbc8256e65de434e6166`. Task 44 is now COMPLETE via PR #118 / merge `6053b7c3d5aef757055c453d2fd5b7f581248e53`, so migration completion has a real strict persisted `MIGRATION_JOB` source without changing synchronous execution.
6. Task 29 depended on Task 25 and is complete via merge `b0f54cb14d73fba3b7c5b8655b5b051af779fd0a`.
7. Task 31 depended on Task 27 and is complete via merge `e54a0684bdc9da3a32d062e0e0e45261c1616020`. Actual restore/PITR and remote restore authority remain deferred.
8. Task 34 depends on Task 30 and is complete via PR #92 / merge `36599fab6ed1b96d145a830fa45b935aba823db3`. Task 40 resolved the first deletion boundary; Task 48 supplied the required shared release lock; Task 43 is COMPLETE via PR #116 / merge `a95e75739bb71bcbaf653244e0ebf9c9bee7b0ee` for one local/manual non-migration orphan release. Backup pruning and automatic pruning remain deferred.
9. Task 32 is complete via review merge `e629515f9c7e7a5d44506dfb82a48343870f94da`; it demonstrated six documentation drift blockers before any alpha tag.
10. Task 36 depended on Task 32 and is complete via merge `8c971016e4fc3cd821dc52d28334567c20835ff4`. Runner MCP 0.1.3 was subsequently published from exact release commit `0aa013c279128e22fbd53be32c35bced3ae26834` through the protected release workflow; future release/tagging still requires explicit authorization and an exact green candidate.
11. Task 23 had Task 18 as its prerequisite; that prerequisite is satisfied by merge `5c4f5db350cdafa99066bdb091866b7d6979a7a9`.
12. Dependency/build/interpreter contract changes still require explicit bootstrap because self-update intentionally uses `--no-deps`.
13. Task 39 depends on Task 38; that dependency is satisfied by PR #91 merge `11b9a4d4e508ac93cd436037563c09d08cfa43ab`. Task 39 is COMPLETE on main via PR #94 / merge `163c5e0597cb8a6cc70f32fd3d8c99e30d08f7aa`.
14. Task 41 is COMPLETE on main via PR #97 / merge `9ce5fe94f417e4e7f910c9945727f70cffd33ecb`. Task 42 is COMPLETE via PR #96, Task 44 via PR #118, Task 45 review is complete, and Task 49 is COMPLETE via PR #124 / merge `da367081f88d6d2342cf938a9b67ec59d9d10de0`.
15. Task 43 is COMPLETE on main via PR #116 after Task 48 integration. The first release-pruning mutation remains local-only, one release per short-lived plan, and preserves backups plus the retained rollback/reference/migration boundary.
16. Task 45 is COMPLETE and Task 49 is COMPLETE via PR #124: synchronous `apply_migrations` remains unchanged while the additive `start_migration_job` / `migration_job_status` path uses separate `migration_async` human approval and durable Task 44 state.
17. Task 46 review is COMPLETE. Task 48 is COMPLETE on main via PR #115 / merge `02475b4c5aa1f103b55f9e4ca6a71e0d09892c7c`, providing the shared release-root `fcntl.flock` contract now used by deploy/rollback and Task 43.
18. Task 47 is COMPLETE via PR #145 / merge `67954dea2117cce3a1819132f6d3c7480dd34c82`. Local `service-log` is bounded, redacted and opt-in; no MCP/mailbox/Agent-Bus log action exists. Task 51 is the separate remote-disclosure review.
19. Issue #143 remains open only for the production packaging-capability preflight; PR #142 already made the environment-dependent wheel smoke conditional. Task 50 is the bounded CODE follow-up.
20. Issue #144 remains high-risk first-install Runner Fabric bootstrap design; Task 52 is review-only before any code or new bootstrap authority.
21. PR #127 and PR #129 remain open with unique Agent-Bus transport/runtime work. Later merged #131/#132/#134 do not make those branches safe to duplicate blindly; reconcile/rebase them separately.
22. Future public release/tagging requires explicit user authorization and an exact green candidate. The remaining private-host recovery limitation is tracked by #108 and must remain explicit until the live local drill is actually proven.


## 2026-10-04 reconciliation

- #110 is COMPLETE; the first-party Runner MCP -> Runner Fabric coarse work-unit path is live-proven. Do not recreate that bridge or its client packaging lane.
- #198, #225 and #237 are COMPLETE: replacement-host qualification and persistent managed Agent Bus worker recovery are no longer activation blockers.
- #108 is OPEN and is the only remaining technical live-proof lane in Runner MCP. The managed runtime baseline is `ba35f70e...`; current exact forward qualifier target is `d0077215...` until `main` changes. The local qualifier/recovery sequence is recorded on #108.
- #101 is non-blocking discovery/launch work. Runner MCP 0.1.3 publication is complete; Smithery is deliberately skipped unless a repository-only path emerges, while Glama/AllMCPs and the technical launch post remain owner-controlled.
- #263 tracks stale third-party directory metadata. Canonical `pyproject.toml` / `server.json` are already correct; do not change package identity, Python requirement, transport or launch semantics merely to match crawler output.
- Managed Runner Fabric runtime updates remain a separate bounded action. Reconcile live `fabric_update_active` and exact Fabric `main` immediately before any update so parallel Fabric development is not crossed.

## Parallel work that is safe
- documentation/CLI contract drift audits;
- direct regression coverage;
- installer/operator UX that does not alter self-update authority;
- secure-I/O inventory/design;
- scrubbed diagnostics design.

## Integration points
- `bridge_protocol.py`, watcher/replay lifecycle and private transport must stay mutually compatible;
- `self_update.py`, `self_update_install.py`, source-control guards and local CLI recovery form one safety boundary;
- dependency-set changes require explicit bootstrap because self-update intentionally uses `--no-deps`.

## Do not parallelize blindly
Avoid overlapping edits to self-update/restart/transaction code from multiple agents. Coordinate through `handover/AGENT_EXCHANGE.md`.


## 2026-09-30 reconciliation

- Task 50 is COMPLETE via PR #149 / merge `469138077066b7b924ba867456ad44dc6372c85d`; issue #143 is closed.
- Task 51 is COMPLETE as a review: local Task-47 service logs remain local-only. A future remote path would require a second independent remote-disclosure opt-in and a separate privacy justification; no remote log CODE task is queued.
- Task 52 is COMPLETE as a review. PR #150 / merge `00ce316124ebc13c65e8a26762f7ea1f69404f50` provides the bounded async Runner Fabric bootstrap foundation, but issue #144 is not complete.
- Task 53 is the bounded #144 hardening prerequisite: self-update/recovery exclusion, installed-runtime preflight, and strict first-install conflict behavior.
- PR #153 is retained only as a green comparison/fallback reference; Task 54 current-main refresh is PR #164 and must not create a second primary transport beside Runner Fabric Agent Bus.
- PR #129 is closed; Task 55 must be retired/reframed rather than reintroducing its direct watcher path.
- Issue #151 is closed, with installer/runtime integrity hardening extended on main by PR #161 / merge `a7041bd8537df7f787e39e1019a259e578661541`. Live clean-host/private-host proof remains tracked separately and must not be inferred from CI.
- Issue #155 tracks the separate bounded host-runtime integrity activation gate; design is intentionally local-only and does not add journal authority to MCP/mailbox/Agent Bus.
