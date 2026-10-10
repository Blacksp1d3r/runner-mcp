## 2026-10-10 — Final #630 issue closure reconciliation
After docs-only PR #635 merged, GitHub read-only checks unexpectedly found parent #630 `CLOSED` while #634 remained `OPEN`. The closure trigger/actor is not independently proven; it must not be interpreted as acceptance. Explicitly REOPENED #630 via GitHub, with `state_reason=reopened`, and kept operator gate #634 OPEN. Failure Museum `RMCP-F-0016` records this recurrence. #381 still belongs to other active chat, not this lane. All three blueprint PRs #632/#633/#635 are merged with exact full CI green; no approved root project.yml, physical Git authority, independent restore, Fabric lease, service/tunnel/host change or archive deletion. Next owner action is read-only #634 authority qualification, not rerunning completed source changes.

## 2026-10-10 — #630 blueprint source children LANDED; #634 operational Git authority BLOCKED (final checkpoint)
This chat did **not** touch #381 (separate active Claude owner/chat).

BPA-03 [PR #632](https://github.com/Blacksp1d3r/runner-mcp/pull/632), exact head `a3614c5172a06879ac672c34033a9fb462aa8223`, attribution `38046631374` and validation `38046631455` ALL SUCCESS; merge `a59875b943441b19ba864ae6643ef9458541020c`. Legacy task index and future TASK/STATE convention merged; `bpa-03/STATE.md` COMPLETE. Historical #381 child never modified.
BPA-02 draft-only symbolic YAML and JSON Schema [PR #633](https://github.com/Blacksp1d3r/runner-mcp/pull/633), exact head `bcf90a3c7525c46956bb2a11a3d7a426d7455817`, attribution `38046821035` and validation `38046821043` ALL SUCCESS, merge `261aed632fd2539af33896ba6574ff4d6b05d536`. Synthetic invalid authority/private-field tests added; early Ruff I001 corrected, Failure Museum RMCP-F-0014. `bpa-02/STATE.md` COMPLETE means *design source only*, no qualified root manifest.
Remaining host/source authority [issue #634](https://github.com/Blacksp1d3r/runner-mcp/issues/634) has blocked `bpa-02b/{TASK,STATE}.md` from docs [PR #635](https://github.com/Blacksp1d3r/runner-mcp/pull/635), exact head `014445d226b6da6f03b77ab87bad3d02433e43fe`, attribution `38047164866` + full CI `38047164865` ALL SUCCESS, reviewed and MERGED `5e364a0224afce8ce7004bd4fd65ad326e0e9c6b`. `bpa-02b/STATE.md` remains BLOCKED explicitly; #630 and #634 must remain OPEN.

There is **no root `project.yml`**, no verified local Git primary, delegated independent storage/fenced mirror/restore evidence or true Fabric lease/approval. The proposed `project_manifest_candidate.yml` is documentation outside root, `BLOCKED_AUTHORITY` and `UNKNOWN`, not an authorized runtime input. No GitHub artifact deletion, live backup copies, restore, host/tunnel/service/restart/credential/mount/storage changes. #587/#588 still waiting for independent physical custody, #590 installed version/response lineage unqualified, Fabric #1397 owned separately.

Next safe operator-owned step: #634 BPA-02B.1 **approved private read-only** canonical Git/source authority admission; then isolated restore/fencing and separate strict promoted manifest/approval. Do not resume issue #381 from this lane or bypass AIfordable/Fabric authority. No further safe independent code mutation is implied by these docs.

## 2026-10-10 — This Runner-MCP lane excludes #381; blueprint #630 source children reconciled
User explicitly assigned operational Claude #381 to a **different active chat**. Do not claim, branch on, restart, deploy or duplicate that work; issue #381 remains operationally OPEN there.

Independent #630 outcomes:
- BPA-03 legacy/new-child mapping [PR #632](https://github.com/Blacksp1d3r/runner-mcp/pull/632), exact HEAD `a3614c5172a06879ac672c34033a9fb462aa8223`, attribution `38046631374` + full validation `38046631455` ALL SUCCESS, reviewed, squash MERGED `a59875b943441b19ba864ae6643ef9458541020c`. `roadmap/children/bpa-03/STATE.md` COMPLETE. Historical #381 and diagnostic components indexed **without edits**.
- BPA-02 symbolic manifest **proposal only** [PR #633](https://github.com/Blacksp1d3r/runner-mcp/pull/633), exact final HEAD `bcf90a3c7525c46956bb2a11a3d7a426d7455817`, attribution `38046821035` + full validation `38046821043` ALL SUCCESS; reviewed, squash MERGED `261aed632fd2539af33896ba6574ff4d6b05d536`. Strict proposal-only `project_manifest_candidate.yml` + JSON Schema and adversarial synthetic unit tests. Earlier CI `38046762677` failed a Ruff I001 blank-import separator only, corrected on final head. No root `project.yml`, no proven local Git primary, storage namespace, independent restore or Fabric lease; `BPA-02/STATE.md` COMPLETE applies **only to source design**.
- Remaining real authority is [#634](https://github.com/Blacksp1d3r/runner-mcp/issues/634) / BPA-02B. Docs-only [draft PR #635](https://github.com/Blacksp1d3r/runner-mcp/pull/635) proposed the blocked child contract and index; HEAD `014445d226b6da6f03b77ab87bad3d02433e43fe`, attribution `38047164866` and validation `38047164865` **PENDING** at checkpoint. Keep #630/#634 OPEN for verified owner-authorized physical authority, single-writer fenced Git, isolated restore and approved future operational schema/manifest. No source-only PR can grant machine authority.
- AIfordable #537 / Fabric #1397/#1428 remain separate operators; #587/#588 independent release custody and restoration remain OPEN without physical receipts; #590 current connector/source generation still unqualified. No production services, tunnel, credentials, host storage, GitHub artifacts or #381 workers touched.

Next safe step here: check PR #635 exact-head all CI and review; if source-docs green merge while keeping #634 BLOCKED; then reconcile GitHub/current handover and stop only if remaining tasks need real independent operator authority. Never infer successful restore or runner health from source CI.

## 2026-10-10 12:52 CEST — user-requested #381 recheck; authoritative issue scope corrected
Runner-MCP [#381](https://github.com/Blacksp1d3r/runner-mcp/issues/381) confirmed **OPEN** and deliberately NOT operationally finished. Issue body now reconciled with accepted one-Fabric-control-plane ADR; original `list_services(aifordable)`/same-user ServiceManager wording was unsafe for the separate `aifordable-coder` rootless account and is now explicitly historical. Source-only #628 merged `4981fa648aa127e5d2e0538b9eefec170f816466`, exact-head CI `38045484328` and `38045484330` SUCCESS (2,659 pytest). No actual host-local helper installed/bound; no live lifecycle action or Claude task.

New cross-repo progress: Fabric [PR #1430](https://github.com/Blacksp1d3r/Runner-Fabric/pull/1430), exact head `7b79664381602efd57869377c0a0ed8fac190745`, Foundation `38046362894` SUCCESS + attribution `38046362913` SUCCESS, squash MERGED as `2c3b3e0f6c3bbb5b6ff896811d900ead400f655c`. This provides a **pure synthetic readiness evaluator**, NOT a signed intent issuer or dispatched worker: even complete evidence yields `READY_FOR_REVIEW` and `dispatch_authorized=false`. Fabric [#1172](https://github.com/Blacksp1d3r/Runner-Fabric/issues/1172) and draft [#1422](https://github.com/Blacksp1d3r/Runner-Fabric/pull/1422) still lack trusted finalized lease/generation/fence/correlation issuer+verifier. AIfordable [#370](https://github.com/Blacksp1d3r/AIfordable/issues/370) lacks real packaged right-host rootless service lifecycle acceptance. Fabric [#972](https://github.com/Blacksp1d3r/Runner-Fabric/issues/972) authenticated loopback/return-path qualification OPEN. Division of owners confirmed by Fabric chat: Runner-MCP owns #381, AIfordable owns #370, Fabric owns #972/#1172. Do not duplicate their active work.

Fresh read-only client `fabric_operational_snapshot` returned generic internal tool failure; `list_services(aifordable)` returned an execution error. Failure alone provides **no evidence** of which host/version answered, whether worker service exists or whether system health is good. Do not retry-loop, restart or silently use an unrestricted shell, sudo, cross-host service alias or billed Anthropic API fallback. Claude/EnerCue #89 remains NO_DISPATCH.

**Next #381-safe action:** agree on exact first-party trusted verifier/attested local target binding with Fabric #1172 owner; then review the fixed helper under the right dedicated identity, package/operator-private lifecycle qualification, and actual Fabric #972 loopback+fence/correlation proof. No new host mutation or public lifecycle endpoint without that completed authority. `roadmap/children/381-claude-worker-lifecycle.md` contains current TASK+STATE and the per-owner gating sequence. Other independent work (#630 blueprint, #587/#588 physical backup) unaffected.

## 2026-10-10 — Shared repository blueprint BPA-01 landed; BPA-02/BPA-03 still gated
[Runner-MCP #630](https://github.com/Blacksp1d3r/runner-mcp/issues/630) is OPEN. BPA-01 docs-only [PR #631](https://github.com/Blacksp1d3r/runner-mcp/pull/631), exact HEAD `f23c12079b2a2cdbb15b6ce2a2fa24c9b68c66f9`, attribution `38045941135` SUCCESS, full validation `38045941103` Ruff/pytest + artifact + clean demo all SUCCESS, reviewed and MERGED `20c19970d14b9402ce6a2393477f3056602498bd`. Final `roadmap/children/bpa-01/STATE.md` marked COMPLETE. `AGENTS.md` now references Library master v1.2 and repository blueprint v1.0; `docs/standards/REPOSITORY_BLUEPRINT_COMPATIBILITY.md` explicitly maps legacy structure and gaps. No mass rename, manifest/authority fabrication or runtime change.

Next #630 BPA-02: independently qualify symbolic project manifest schema and canonical local Git/storage authority before asserting local-first or creating `project.yml`; status BLOCKED/REVIEW_REQUIRED where not proven. BPA-03: map old issue/roadmap children while requiring TASK+STATE on new children, without duplicating canonical truth or clobbering active claims. Separate Fabric-owned automatic scaffolding remains unimplemented, not authorized here. Claude #381 source PR #628 landed but operational issue OPEN pending Fabric/AIfordable trusted lifecycle; #590 source #627/#629 merged but installed catalog/return-route unqualified; #587/#588 still no real 2/2 independent mirror or offline recovery, retain provider artifacts. Other AI owners' work untouched.

## 2026-10-10 — Claude priority #381: fixed host-local rootless source slice #628 MERGED; live worker STILL BLOCKED
User explicitly prioritized Runner-MCP #381 to enable Claude on multiple projects. After issue #381 and Fabric/AIfordable dependencies review, [PR #628](https://github.com/Blacksp1d3r/runner-mcp/pull/628) source-only fixed rootless Claude actuator was merged: branch `feat/381-fixed-rootless-coder-actuator`, exact reviewed HEAD `e88e880c1c8db307d94c558250d12ee119c35e48`, attribution `38045484328` SUCCESS and full validation `38045484330` SUCCESS (Ruff, **2,659 pytest PASS**, built artifact, clean five-minute demo). Squash commit `4981fa648aa127e5d2e0538b9eefec170f816466` on main. Tests cover denied unsupported fields/UID/actions/versions, expired/invalid fence and lease syntax, central verifier unavailable/denied, fixed `systemctl --user` only, loopback port and unsafe listener checks, rootless wrong identity and attempted-but-unverified lifecycle action.

The source module `src/runner_mcp/fixed_coding_worker_actuator.py` is NOT a registered MCP tool/CLI/network endpoint, installed daemon, worker control plane or active scheduler. It hardcodes `aifordable-coder` and the exact coding-worker unit, accepts no user/unit/path/command/environment selectors, refuses actions without separately installed trusted Fabric authorizer, performs no sudo/cross-user switch, observes loopback-only port 8030 with bounded status and partial-mutation evidence. See `docs/architecture/FIXED_CODING_WORKER_ACTUATOR.md` and [child roadmap](https://github.com/Blacksp1d3r/runner-mcp/blob/main/roadmap/children/381-claude-worker-lifecycle.md).

**GitHub automatically CLOSED issue #381 on merge**, even though this was source-only; it was explicitly **REOPENED** immediately, because issue acceptance is operational, not simply code-present. Avoid auto-close issue keywords even in negated PR prose. Issue #381 comment #6096664381 records exact state. Physical acceptance still unmet: Fabric #1172/#1422 authenticated typed lifecycle issuer/verifier with durable lease/fence/expiry/idempotency/authorization and ONE scheduler; right-host fixed endpoint and managed installation under the dedicated rootless identity (AIfordable #370); actual packaged preflight/status/start/stop, disabled by default and loopback listener-gone proof; Fabric #972 authenticated availability/response correlation/fenced synthetic work claim; only then EnerCue #89 or other Claude project tasks. Fabric #1172 and AIfordable #370 owners received coordination comments, no competing edits. The github-runner ChatGPT-connected instance does NOT have AIfordable alias and cannot control another host user manager by registry guesswork. **#381 OPEN, Claude dispatch BLOCKED**, no live services or paid API calls.

Next safe action for Runner-MCP/AIfordable/Fabric owners: finish trusted first-party Fabric authority to local rootless actuator across correct host, prove only the fixed unit and dedicated account, then real rootless lifecycle and Fabric end-to-end availability/correlation. Keep existing #587/#588 storage work independent; no archive deletion/host mutation from this code merge. Current priority #381 until end-to-end readiness, then resume remaining roadmap.

## 2026-10-10 — #629 build identity fail-closed source MERGED; #590 LIVE UNQUALIFIED
Runner-MCP [PR #629](https://github.com/Blacksp1d3r/runner-mcp/pull/629) exact head `53614092bafac8e528b4905fc962da72ffde4621`: attribution `38045401691` SUCCESS; full CI `38045401730` SUCCESS, all Ruff/pytest, built artifact and clean demo; reviewed then squash MERGED `7deb63cd8d623a74389c9f582d6e2d1ec688b2eb`. Now valid `build_identity` remains seven-field, invalid/unavailable identity returns fixed `runner-mcp/build-identity-unavailable/v1` / `identityEvidenceComplete=false` without private text or fabricated build evidence. Source-only; do not claim installed runtime fixed. Issue #590 was independently checked still OPEN; original doctor read returned 12 older checks and `runtime_status` failed, first live divergence unknown. No new live probe, restart or provider artifact deletion permitted without approved private evidence.

Parallel #381 Claude work now occupies [draft PR #628](https://github.com/Blacksp1d3r/runner-mcp/pull/628), latest observed head `e88e880c1c8db307d94c558250d12ee119c35e48`; do not duplicate or modify its branch. Fabric #1428 likewise remains independent active owner. Backup #587/#588 remain OPEN for physically independent 2/2 mirror plus offline restore after qualified AIfordable/Fabric volume delegation. Current source success does not grant physical custody.

Next safe #590 operator step: approved read-only installed source/build/interface + client catalog and ingress↔response lineage on an authorized fresh session, then verify new bounded identity/status tools once. In parallel, safely review independent roadmap children only after claim/PR check. No tunnel/host/mount/service changes, no shell bypass.

## 2026-10-10 — #381 source PR #628 exact-head CI checkpoint (supersedes previous)
#381 remains highest-priority user request: Claude project acceleration. Source draft [#628](https://github.com/Blacksp1d3r/runner-mcp/pull/628) branch `feat/381-fixed-rootless-coder-actuator`, exact HEAD `e88e880c1c8db307d94c558250d12ee119c35e48`. Current attribution run `38045484328` SUCCESS; validation `38045484330` Ruff/pytest SUCCESS (after fixing duplicate `action` test-helper invocation; previous run had 2 fixture-only errors, 2,657 passes), built artifact SUCCESS, clean five-minute demo IN_PROGRESS as last confirmed. No merge until all terminal SUCCESS and exact head/mergeability reconfirmed. Original Ruff UP022 corrected on earlier branch revision. Source-only fixed rootless actuator, trusted Fabric verifier absent by default, no live service activation/Claude dispatch. Coordinated source readiness with Fabric #1172 (issue comment #6096633905), Fabric typed proposal #1422 still draft. Operator host and Fabric lease/fencing/return path remain blockers. Keep #381 OPEN after source-only merge until AIfordable #370 and Fabric #972 live proof plus safe capability projection are complete.

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

## 2026-10-10 — Final mirror re-verification #626 MERGED, #587/#588 remain physically BLOCKED
Runner-MCP source-only PR [#626](https://github.com/Blacksp1d3r/runner-mcp/pull/626), branch `fix/587-final-mirror-reverification`, exact head `abd2c4eb05348b86b87e09f65acd5cf149d98972`, attribution `38038139765` SUCCESS and validation `38038139723` SUCCESS (Ruff/pytest, clean demo, built artifact), merged squash `5aba8423594290a7837208e53721234dfe0df778`. Final mirror reporting now revalidates operator BACKUP permission, pinned release pair, full #586 independent-volume readiness, both secondary archives after the second copy, then pins again. Four added regressions confirm late unmount, first archive corruption, operator stop and pin promotion all BLOCK overall success. PR title changed from auto-close keyword before merge; **GitHub #587 and #588 independently rechecked OPEN**. No actual physical mirror or restore was performed.

#590 code/transport diagnosis documented in [issue comment](https://github.com/Blacksp1d3r/runner-mcp/issues/590#issuecomment-6095722626): `runtime_doctor` returns structured WARN, whereas `runtime_status` and `build_identity` fail internally. In server source, doctor handles `SelfUpdateError` as WARN whereas runtime_status merges runtime managers then raises a `ValueError(str(exc))` on certain errors; hypothesis only pending authorized runtime traces, and raw exception text should be sanitized in a separately tested source fix. No tunnel/host restart, credential changes or mounted volume actions.

External gate remains AIfordable #537 / PR #553 draft red test-date regression (CI `38035068769`: 9 test failures, 1352 pass; stale test clock versus 2026-10-10 authority; owner notified) then Fabric #1397 fixed release-archive namespace and owner-private host bootstrapping. Only then fresh #586 readiness -> actual 2/2 #587 independent immutable copies -> real offline #588 restore and cleanup -> artifact deletion review. Existing provider archives retained. Canonical source, roadmap and agent files reconciled in main; do not resume at stale in-progress #625/#626 checkpoints below.

## 2026-10-10 — Reconciled after chat rollback; #626 final mirror safety PR OPEN
Repository: `Blacksp1d3r/runner-mcp`; base: `main`. Canonical master: v1.2. Do not replay already merged PRs #621–#625 after an older UI/chat view. #624 merged `8460283b1fe34ffd2fe4be9426682ff3d1cf6f83`, #625 merged `2e274c5b4ed9bf14842803a832689f79cbb805c9`; #625 exact-head attribution `38030008919` and validation `38030008996` all four jobs SUCCESS. Handover/agent exchange had an outdated in-progress #625 entry; this checkpoint supersedes it.

New source-only PR [#626](https://github.com/Blacksp1d3r/runner-mcp/pull/626), branch `fix/587-final-mirror-reverification`, exact HEAD `abd2c4eb05348b86b87e09f65acd5cf149d98972`, status `PR_OPEN / WAITING_CI` (draft). It guards the window between the second copy and final "verified": reasserts BACKUP operator safety, exact protected pair, full #586 independent-volume readiness, both secondary checksums/custody verifications and pins again after final checks. Adds 4 regression tests for late mount loss, first-copy corruption during second copy, late operator stop and last-moment pin promotion. Attribution run `38038139765` SUCCESS; full validation run `38038139723` IN_PROGRESS at checkpoint. Reinspect exact HEAD, full Ruff/pytest, built artifact, clean demo and attribution before marking ready/merging. Do not close #587 on merge: this is not a physical backup.

External blocker: AIfordable issue #537 / [draft #553](https://github.com/Blacksp1d3r/AIfordable/pull/553), head `fea120cb18ab87d8ece7627b539ff27a981bd5a7`, CI `38035068769` FAILED in Test API (9 failed / 1352 passed). The registry `last_reviewed=2026-10-10` is newer than the hard-coded 2026-10-08 test clock in topology-guard tests, so the fail-closed guard rightly yields `TOPOLOGY_FUTURE_DATED/REVIEW_REQUIRED`. Exact issue diagnosed and commented on #553; owner should update fixture time without weakening runtime future-date rejection, then run full CI and separately qualify binding (currently false). Avoid duplicating concurrent AIfordable owner changes.

Fabric #1397 source-only PRs #1426/#1427 MERGED but trusted live provider/bootstrap is OPEN. Runner-MCP #587/#588 OPEN: **zero demonstrated physical 2/2 independent mirrors and zero real offline recovery proofs**. Fixed first-party same-host namespace/bootstrap and fresh private authority are prerequisites; no GitHub release/provider artifact deletions, archive pruning, generic shell/privilege escalation or live host changes. Dependency sequence: #537 qualified private machine storage registry -> Fabric #1397 host-owned namespace admission/bootstrap -> #586 live fresh readiness -> fixed protected 2/2 mirror #587 -> actual isolated no-network local-reader/bootstrap restore #588 -> only then artifact-retirement review.

Partial connector progress #590: `runtime_doctor` returned structured `warn` (0 failures, 3 warnings: continuity config, worker qualification, migration storage), while `runtime_status` and `build_identity` still returned generic transport failure; F34 mirror activation readiness returned unconfigured/storage-binding-unavailable. This is not full transport/runbook acceptance; do not restart tunnel blindly. PR #618 remains draft OPEN at `eb7e9fdc8699cd461e39176ff52f89d71669428a`; the queried validation run `37963241191` has Ruff/pytest + release artifact + demo SUCCESS and attribution `37963241193` SUCCESS, but external registry acceptance/merge remains a separate exact-head review. No production deployments, mounts, archive copy, cleanup, or credential changes in this chat.

Next safe actions: (1) reconcile PR #626 exact HEAD/CI; (2) fix failing test assumptions only in the AIfordable owning lane, not concurrently here; (3) continue source-only #590 connector diagnostic or other independent roadmap work without claiming live backup; (4) refresh canonical handover and dependencies after each material transition.

## 2026-10-10 — Mirror and restore protected pin drift guards MERGED

Source-only PR #624 head `b962dcaff11a78b2ae244fe14f59399555c41837`, attribution `38029722100` SUCCESS, validation `38029722174` SUCCESS, squash `8460283b1fe34ffd2fe4be9426682ff3d1cf6f83`. Denies MIRROR before each copy/final success if protected active/rollback pair changed.

Source-only PR #625 restacked on latest main head `ea88bb010cfc866bdf0ee8e1de7299be8c4fd8e9`, attribution `38030008919` SUCCESS, validation `38030008996` SUCCESS, squash `2e274c5b4ed9bf14842803a832689f79cbb805c9`. Denies RESTORE qualification before each disposable proof/final success if protected active/rollback pair changed. Exact-head CI includes Ruff/pytest, release artifact and clean demo.

Fabric namespace admission source #1426 and read-only authority gate source #1427 merged, but AIfordable #537 authoritative private fresh host-runtime-storage mapping and Fabric #1397 qualified live namespace/bootstrap still OPEN. No 2/2 physical second-device copy receipts, no installed reader offline recovery, no deletion authority. Keep #587 and #588 OPEN regardless source PR merge, preserve provider artifacts. No runtime host, storage, service, runner or tunnel mutation.

## 2026-10-10 — Protected pair drift hardening while physical backup gated

#587 accidental closure corrected: issue explicitly REOPENED. Fabric #1426 first policy-only admission MERGED, but #1397 fixed live namespace bootstrap and AIfordable #537 private fresh host/runtime/physical volume authority OPEN; no 2/2 second-volume archive receipts exist. Source-only PR #624 exact head `b962dcaff11a78b2ae244fe14f59399555c41837`, attribution `38029722100` SUCCESS, full validation `38029722174` SUCCESS; squash merged `8460283b1fe34ffd2fe4be9426682ff3d1cf6f83`. It compares the trusted active+rollback pin pair before every copy and final success, refusing a mid-copy release promotion; tests cover change after first and after both copies. No physical copy happened.

#588 restore source-only drift safeguard PR #625 at head `f3428d75dc0e84ed448e1da7efbc5a37ab84c2ac`, attribution `38029868858` SUCCESS, full validation `38029868889` Ruff/pytest+build SUCCESS, clean demo IN_PROGRESS at last observation. Protects against active+rollback change between disposable restore receipts or before final qualification. DO NOT MERGE before exact-head complete CI and reconciling base with newly merged #624. #588 stays OPEN; no real offline independent-volume reader/bootstrap proof. Preserve existing provider artifacts and protected release archives, no deletion, live mounts, service or tunnel modification.

## 2026-10-10 — #587 live storage still blocked; drift safety child underway

Verified at latest GitHub read: Fabric #1426 first source-only topology admission slice MERGED, but Fabric #1397 parent remains OPEN and its #1427 private authority bridge is still only source work; AIfordable #537 authoritative host/runtime/physical volume binding OPEN. There is no evidence of two actually copied immutable releases on an independent physical volume; #587 had accidentally CLOSED and was explicitly REOPENED; #588 remains OPEN without disposable off-volume recovery proof. Preserve old provider archives, no deleting to unblock other chats.

New PR #624 `fix/587-pin-snapshot-drift-gate`, exact head `b962dcaff11a78b2ae244fe14f59399555c41837`: recheck the trusted protected active+rollback pair before each copy and before final verified result, fail closed if promotion occurs. Two synthetic regressions for mid-run and finalization drift. Attribution workflow `38029722100` and validation `38029722174` started; pytest still running at last check. DO NOT merge without full exact-head green. No live storage, mounts, privilege, service, runner or tunnel touched. Next required real admission: #537 -> #1397 -> #586 live full readiness -> first-party exact pair mirroring 2/2 -> #588 isolated offline reader/bootstrap restore with cleanup; all on authorized storage-owning host.

## 2026-10-10 — #623 full storage re-admission MERGED (supersedes prior WAITING_CI)

Draft #623 head `80058882e30487d251ff347c5e34af3ecbb30c40`: attribution `38029219757` SUCCESS and full validation `38029219729` SUCCESS, including Ruff/pytest, release artifact, clean demo; squash merged `d755cce23a18130189335d8ad6775f80f19d8525`. Pre-copy admission in the source-only protected mirror orchestrator now rechecks full versioned #586 readiness before EVERY copy, not just `ready=True`; regression tests cover device/mount degradation after first copy and schema drift before first. Real independent storage remains NOT connected: AIfordable #537 and Fabric #1397 open, #587 and #588 live physical acceptance open. No backup copy, archive pruning, server/tunnel/runner mutation or restore performed.

## 2026-10-10 — #587 full pre-copy revalidation CI gate

2026-10-10 targeted source hardening for #587: existing merged mirror orchestrator rechecked full #586 readiness only during preflight but then merely `.get('ready')` before each copy. Draft PR #623 head `80058882e30487d251ff347c5e34af3ecbb30c40` replaces per-copy check with exact full versioned schema (mounted, distinct device, mirror root, no mutation enabled, etc.), tests device identity loss after first copy and schema downgrade before first copy. Attribution `38029219757` SUCCESS; validation `38029219729` Ruff/pytest SUCCESS and release artifact SUCCESS; clean five-minute demo job `114146556625` remains IN_PROGRESS at latest check and running-job log unavailable (provider 404). **DO NOT MERGE without exact-head full terminal CI**, do not blind rerun shared CI. AIfordable #537 and Fabric #1397 still OPEN; no real mirror/restore or private storage activation. #587/#588 remain OPEN; no deletion/prune. Next: review CI state, merge #623 only when full green, then integrate fixed first-party adapter only after authoritative physical machine-volume and archive namespace admission.

## 2026-10-10 — #588 auto-closure corrected

After source-only PR #622 merged, GitHub auto-closed #588 as `completed` even though the independent second-volume recovery lifecycle has NOT happened. Reopened #588 explicitly on 2026-10-10; acceptance remains blocked by actual 2/2 physical protected-mirror receipts (#587), AIfordable #537 topology and Fabric #1397 namespace authority, and real disposable no-network reader/bootstrap preflight/apply/rollback+cleanup. Never treat source-only CI as recovery proof. Both #587 and #588 now OPEN.

## 2026-10-10 — HIGH PRIORITY backup safety gates integrated; PHYSICAL BACKUP STILL BLOCKED

User explicitly prioritized #587 (real independently mirrored protected releases) then #588 (actual restore proof) to unblock other projects. Both issues MUST remain OPEN until on-host authoritative physical evidence. Existing #586 zero-arg read-only separate-volume readiness already merged via #610; its live status was not available in this conversation (runtime/safety connector generic internal failure). Do not mistake source tests or device-number difference for genuine independent physical disk readiness.

#587 child PR #621 exact head `832cf4ea4157cfa32797038df297fd37831cf7f1`: attribution `38026327476` SUCCESS; validation `38026327510` SUCCESS (Ruff, pytest, release build, clean demo); squash merged `823b11160f7c0b671ae6d0b250ac1f24aae2015e`. Source-only `ProtectedReleaseMirror` orchestrator: backup action+stop/retention gate, exact two trusted distinct protected SHAs, complete exact #586 readiness schema, independent-device admission, verify primary custody before each copy, fixed-adapter exact mirror receipt, verify secondary each, success only both; partial copy cannot yield success; negative tests included. No MCP mutation endpoint or concrete private adapter/pins bound; **0 verified live copies**, source-only.

#588 child PR #622 exact head `d7d2eed1d97a4637769efd717a6c7b350652e62b`: attribution `38026689570` SUCCESS; validation `38026689559` SUCCESS (Ruff/pytest, release artifact, clean demo); squash merged `b62efbda768c7cf2f56eea22ec3764f18788e94c`. Source-only `ProtectedReleaseRestoreQualification` proof gate: requires two exact protected SHA-bound secondary archive receipts, real installed local-custody reader, offline disposable bootstrap preflight/apply/rollback, cleanup receipt, transaction unchanged and no live changes; synthetic negative tests. NOT wired to actual isolated first-party import/reader/bootstrap lifecycle; **0 independent-volume restore proofs**. Do not close #588.

Owner dependencies before ANY physical action: AIfordable #537 private machine-readable primary runtime -> independent physical storage volume + freshness authority; Runner-Fabric #1397 fixed release-archive namespace admission/bootstrap distinct from F34 repository mirror namespace. Cross-project owner priority comments posted. Only then do #586 live readiness under correct managed identity, bind real trusted protected active+rollback pins, invoke first-party `control_plane_bundle_mirror.py` immutable copy semantics with full verification for both and no overwrite/delete, then #588 via `control_plane_archive_import.py`, installed `FabricUpdateManager._validated_bootstrap`, and isolated no-network preflight/apply/rollback against disposable owner-private state with cleanup+no live transaction change. No generic shell/Desktop Commander/sudo/mount bypass; zero private paths/devices/credentials in public docs; do not delete provider archives. Keep #585/#587/#588 open. No host, tunnel, runner, credential, service, rollout, deletion or production update was changed in this session.

## 2026-10-10 — PRIORITY SHIFT: independent release custody #587/#588 ahead of other work

User prioritizes safe file preservation across project chats. #586 read-only independent-volume readiness was already merged via #610, but **no live physical-volume admission has been evidenced** through this conversation (read-only connector returned generic internal error). Fabric #1397 namespace qualification/bootstrap and private AIfordable #537 runtime-to-physical-volume authority are HARD prerequisites, and service runtime must be on qualified storage-owner host; never infer paths or devices from memory, and never reuse F34 repository mirror namespace. No generic shell/Desktop Commander/mount/sudo workaround or GitHub provider artifact deletion.

#587 source-only protected two-revision mirror orchestration PR #621 exact head `832cf4ea4157cfa32797038df297fd37831cf7f1`, attribution `38026327476` SUCCESS, full validation `38026327510` SUCCESS, squash merge `823b11160f7c0b671ae6d0b250ac1f24aae2015e`. It enforces ActionClass.BACKUP, retention/operator stop, exact two trusted distinct pinned commits, complete versioned #586 readiness, recheck readiness+primary custody before each revision, fixed first-party mirror adapter evidence and independent secondary verification. Unit tests cover copied/already/mixed, source/target failures, idempotency and denial. This is an UNBOUND gate only: no real protected pin source or mirror adapter configured, no live MCP action and zero archives copied. #587 REMAINS OPEN for private authority bindings + actual first-party Runner-Fabric separate-volume mirror and BOTH real mirror receipts.

#588 source-only restore proof gate in draft PR #622 branch `feature/588-independent-restore-proof-gate`, restacked on #621 merge/current main, latest head `d7d2eed1d97a4637769efd717a6c7b350652e62b`, CI pending exact-head. Requires both verified independent archives, real local reader, isolated no-network preflight/apply/rollback, verified disposable cleanup and unchanged live transaction per pinned revision, with receipt SHA equal to the protected pin. Tests synthetic ONLY; no actual independent volume restore or offline bootstrap performed. #588 REMAINS OPEN. Real adapter must invoke Runner-Fabric `control_plane_archive_import.stage_archive`, installed `FabricUpdateManager._validated_bootstrap` and isolated bootstrap lifecycle; cannot claim acceptance from mocked receipts.

First-party Fabric sources confirmed: `scripts/control_plane_bundle_mirror.py` enforces immutable source/target checksums, physical mount and distinct st_dev, exclusive atomic filesystem writes+fsync; `scripts/control_plane_archive_import.py` maps archive to consumer-only local bundle files; actual installed Runner-MCP parser previously accepted two primary-custody fixtures but does NOT prove independent-volume recovery. Fabric #1397 draft #1426 and AIfordable #537 are active elsewhere; avoid duplicating their branches. Next: finish exact CI #622, integrate only source-safe gate, then wait for private topology/namespace qualified admission before fixed first-party storage mutation and real #588 proof. No deletion or offsite disaster recovery claim.

## 2026-10-09 — Final landing: A6 doctor #518 and F36 read-only relay #412 exact green MERGED

- Existing #519 source-baseline drift PR CLOSED WITHOUT MERGE because current main already has stronger, tested source/installed drift and unavailability checks, active runtime revision evidence and sanitized `runtime_doctor` source status. Never overwrite current main with stale #519. Separate queued-to-activation TOCTOU review remains open.
- A6 sanitized diagnostic PR #518 exact head `8c9683a16dcbccece78a0d08a6722fa19dee5cf2`: attribution `37984556255` SUCCESS, full validation `37984556225` SUCCESS (Ruff/pytest, artifact, clean demo), squash merge `62c6832338370190e9b9dcee69478fa288031c61`. Adds fixed A6 state-root classification / binding count to existing `runtime_doctor` with no private values; A6 root expression was checked identical to existing restart resolver; deferred onboarding env import avoids module startup circular dependency. No live self-update, agent restart or A6 campaign. #509 live acceptance remains separate.
- Existing F36 continuity relay PR #412 was selectively restacked in place to retain already merged MCP tool/managed Runner-Fabric operation. Adds only fixed no-argument `fabric_continuity_status` over existing Agent Bus bridge, explicit loopback MCP executor dispatch and adversarial field validation. Exact head `2c5e7c0233613ac8da76b4b734f2163efb8e1e2e`: attribution `37985552722` SUCCESS, full validation `37985552667` SUCCESS (Ruff/pytest, artifact, clean demo), squash merge `7ccb65a6ad5d734614e2384a309c126c5607d47b`. Issue #410 CLOSED as SOURCE completed, not proof of deployed Agent Bus route.
- Separate dormant self-update supervisor PR #438 reviewed: `ServerActivationProofMiddleware` may consume restart marker before downstream ASGI handler returns success; potential premature activation proof. Review posted on existing PR, no merge/host mutation.
- External ChatGPT connector/tunnel return-generation identity #590 STILL OPEN and unproven. No active tunnel/service, customer production, CI runner, credentials or runtime deployment changed. Next safe task: reconcile existing #438/#618 and other owned PRs with current main; do NOT activate supervisor without successful-readiness marker regression tests; runtime A6/F36 acceptance remains separately gated.

## 2026-10-09 — Continuation: source drift duplicate closed, A6 doctor landed, F36 relay CI

- Existing #519 self-update source-baseline drift PR CLOSED WITHOUT MERGE: current main already has stronger installed/source alignment, active runtime revision, sanitized `runtime_doctor` source baseline and fail-closed pre-queue checks; security tests cover aligned/drift/unavailable and private error containment. Do not resurrect outdated large-file changes. Queue-to-activation TOCTOU acceptance remains a separate review.
- Existing #518 A6 `runtime_doctor` binding-state inspection was selectively restacked in-place on current main. Fixed Ruff imports and an onboarding/server circular-import hazard by deferring env-file loader import to invocation time. Exact head `8c9683a16dcbccece78a0d08a6722fa19dee5cf2`, attribution `37984556255` SUCCESS, full validation `37984556225` SUCCESS, squash merge `62c6832338370190e9b9dcee69478fa288031c61`. No A6 agent restart, private runtime query, self-update or campaign activation. Its state-root resolver was verified identical to existing restart resolver; layout qualification beyond that remains separate.
- Existing #412 F36 read-only continuity Agent Bus bridge was selectively restacked, retaining already existing MCP continuity-status tool and Fabric wrapper on main. Branch `f36-continuity-status-bridge`, current head `2c5e7c0233613ac8da76b4b734f2163efb8e1e2e`; exact-head attribution `37985552722` and validation `37985552667` IN_PROGRESS. Fixed complete adversarial action-matrix fixture and zero-argument `bridge_tool_call` mapping following pytest failures on previous heads. No merge until full exact-head green. No production connector/tunnel/Agent Bus mutation or new privilege.
- #590 intermittent external ChatGPT connector reply return/generation remains OPEN and unqualified. No live deployment, reboot, runner mutation or secret exposure.

## 2026-10-09 — Self-update source alignment and A6 dependency reconciliation

Existing PR #519 was CLOSED UNMERGED after explicit live-main proof that its requested source baseline protection is already implemented with stronger current `source_commit`, `source_baseline_aligned`, active runtime revision and `runtime_doctor` evidence. Main `SelfUpdateManager.start` rejects source drift and unavailability before queuing; current security tests cover aligned, drift, unavailable and nonleaking error outcomes. Prior #519 branch is stale; do not reopen or override current source. Queue-to-activation TOCTOU remains independently reviewable and not proven solved by queue-time checking alone.

Open PR #518 still adds a distinct, sanitized A6 binding diagnostic, NOT yet on main. Review identified possible unverified derivation of its state root from projects-config folder nesting; owner must prove it matches the same private canonical A6 root as restart on nondefault configurations or fail closed. No A6 prepare, agent restart or live update until exact proof. Reviewed on original PR, no duplicate branch created.

External #590 intermittent ChatGPT tunnel response route still OPEN. No live host, tunnel, credentials, CI runner, server service or customer workload touched.

## 2026-10-09 — Final autonomous checkpoint: #620/#526 merged, #511 superseded

- Exact-green PR #620 explicit ServiceBackend injection test: head `82a918902636376b2bc26b5a3f22475295d279b8`, attribution `37981372498` SUCCESS, Runner MCP validation `37981372754` SUCCESS, squash merged `4f7a7d8e16ac9fe23760800bed8a313c37eb8a4e`. Test-only. No Windows SCM adapter/service activation.
- Existing PR #526 bounded Fabric local-custody failures was selectively restacked on current main without losing unrelated changes; head `e44bd321c0551db68560ac99bc99e36368dc6e32`, attribution `37982010408` SUCCESS, validation `37982010409` SUCCESS, squash merged `cfd7101c9f370728d0aa0b5117d2ef0a40244700`. Known exact failure classes return bounded `blocked/reasonCode`, untrusted details are never emitted. No live Fabric staging/host/runtime mutation. #525 auto-closed and independently checked.
- PR #537 independent review noted `/proc/stat` busy CPU delta may be host-wide under Incus containers, so it cannot automatically be labelled OCR process CPU/page. Require verified VM/cgroup-process scope or treat CPU metric unknown; do not infer actual OCR speed gain. No OCR runtime change.
- PR #511 OLD disposable-target reason projection was investigated. Main already implements a STRICTER single-line prefix + allowlisted reason parser (`_bounded_failure_reason`) and returns structured `state=invalid` directly from the runner; main server generically blocks exceptions. Old #511 would reintroduce direct `str(exc)` MCP exposure and duplicate already merged functionality. Despite experimental branch-only hardening commits, PR #511 was CLOSED UNMERGED as SUPERSEDED after verified current-main comparison; do not resurrect/rebase or duplicate it. No main/deployed mutation from #511.
- External ChatGPT tunnel response-return issue #590 remains OPEN and unproven; current tunnel untouched. Next safe work: reconcile other stale PRs to main without overwriting stronger existing features; document first failing edge when qualified private response-delivery/dispatcher counters are available. No Desktop Commander, reboot, credentials, release or runner activation.

## 2026-10-09 — Latest continuation: #620 and #526 exact green MERGED

PR #620 test-only explicit service backend injection, exact head `82a918902636376b2bc26b5a3f22475295d279b8`: attribution `37981372498` SUCCESS, full validation `37981372754` SUCCESS, squash merge `4f7a7d8e16ac9fe23760800bed8a313c37eb8a4e`. Tests injected backend remains selected on Linux, Windows, unknown host families. No SCM implementation or live runtime mutation.

Existing Fabric custody PR #526 requalified in-place by selective source patch onto current main (four files, current content preserved), exact head `e44bd321c0551db68560ac99bc99e36368dc6e32`: attribution `37982010408` SUCCESS, full validation `37982010409` SUCCESS (Ruff/pytest, artifact, clean demo), squash merge `cfd7101c9f370728d0aa0b5117d2ef0a40244700`. Known allowlisted local-custody `FabricUpdateError` values return bounded `blocked/reasonCode`, unknown categories generic. This is a source-only diagnostic improvement; no live Fabric staging, server update or credentials changed. #525 may be auto-closed by merge; verify before manual state change.

Independent review on existing Bewind OCR PR #537 notes CPU time from `/proc/stat` may include host-wide load under Incus containers and must not be interpreted as OCR-only CPU/page without VM/cgroup qualification. No OCR job performed. External connector response path #590 remains unproven. No Desktop Commander, no production host/tunnel change.

## 2026-10-09 — Autonomous continuation: Windows adapter-injection test merged; Fabric custody #526 requalified

Test-only #620 (explicit injected ServiceBackend preserved across detected Linux/Windows/unsupported families) exact head `82a918902636376b2bc26b5a3f22475295d279b8`, commit attribution `37981372498` SUCCESS, full validation `37981372754` SUCCESS, squash merge `4f7a7d8e16ac9fe23760800bed8a313c37eb8a4e`. No production mutation, Windows SCM implementation, service action or runtime deployment.

Existing PR #526 `fix/525-local-custody-reasons` was selectively restacked in-place against that exact main without replacing unrelated current content, preserving its bounded allowlist and JSON/HTTP tests across four changed files. Latest exact head `e44bd321c0551db68560ac99bc99e36368dc6e32`; attribution `37982010408` SUCCESS, validation `37982010409` Ruff/pytest SUCCESS, built artifact and clean demo pending at last check. State WAITING_CI; do not merge before full terminal exact-head green. Purpose: return only allowlisted semantic Fabric local-custody failure reasons; never leak raw exception/path/secret. Does not authorize live Fabric staging/restart or change deployed runtime.

Separate #590 intermittent external connector response-return path remains unqualified; no tunnel action. Other owned open branches remain untouched.

## 2026-10-09 — Follow-up #489 explicit backend selection regression (WAITING_CI)

Existing source #490/#619 are already merged and preserve Linux behavior while refusing automatic systemd backend selection on Windows. Fresh tiny test-only PR #620 `test/489-explicit-backend-platform-qualification`, head `82a918902636376b2bc26b5a3f22475295d279b8`, ensures an explicitly injected `ServiceBackend` is not replaced by automatic systemd selection regardless of detected Linux, Windows or unsupported family. Exact-head attribution `37981372498` SUCCESS, validation `37981372754` Ruff/pytest SUCCESS, release/demo IN_PROGRESS as of the last observation. No production code or runtime changes in #620. Do not merge until both full validation and attribution are terminal green; broad Windows SCM adapter remains unimplemented (#489).

PR #526 read-only review: its bounded Fabric custody reason-code allowlist changes shared server/fabric files and is stale/nonmergeable against current main. Do not restack by blindly overwriting large shared files; reconcile owner and changes before progressing. The live tunnel return-path issue #590 is still separate and unproven.

## 2026-10-09 — #619 exact-head GREEN and MERGED (supersedes WAITING_CI)

New bounded source-only PR #619 (`fix/windows-service-backend-admission-20261009`) exact head `b426692798092edf263d0182a205ae7ba9a6dc2b`, attribution run `37975695602` SUCCESS, full validation run `37975695551` SUCCESS (Ruff/pytest, built release artifact, clean demo), squash merge `bac86a97f1493ff943ef5f3d01228814e3ed61c0`. `ServiceManager._backend()` refuses default Linux SystemdUserBackend on Windows/unsupported host before instantiation; existing Linux and explicitly injected backends unchanged. Three regression cases passed. This does NOT implement Windows SCM, change actual Windows startup, grant remote authority, or activate any server. Broader #489 remains open for least-privilege SCM adapter and isolated Windows CI.

This session's other exact-green source merges: Faster shadow #460 `6a9ed29197ee7b58c8c6a672c313dfc4edccc160`, first platform contract #490 `816c7e5abd5ddbf91d0e580e6a7102bb0308faf0`. All are GitHub source changes only; no runtime/self-update/tunnel, CI enrollment, credentials, production/worker mutation. #590 remains OPEN, external response return route unqualified. Prior temporary WAITING_CI paragraphs below are superseded. Safe next independent work is review/reconcile existing owned open PRs (#526, #519, #518 etc.), not duplicate or merge without fresh head and ownership checks.

## 2026-10-09 — Windows host admission and Faster-13 integration checkpoint

Existing Faster-13 PR #460 head `26580dbead954e19e1732db0770ca66a51841eaa`: exact attribution `37974721744` SUCCESS and full validation `37974721750` SUCCESS, squash merge `6a9ed29197ee7b58c8c6a672c313dfc4edccc160`. Shadow-only memfd/eventfd includes bounded response wait, fail-closed worker timeout cleanup, and positive/negative tests. No live runtime change or OCR speedup claim. Broader #383 remains open.

Existing #490 host family recognition PR head `a82f7d90bd8eb400aed329a0e9b414d6ff0f7771`: attribution `37975249864` SUCCESS and validation `37975249793` SUCCESS, squash merge `816c7e5abd5ddbf91d0e580e6a7102bb0308faf0`. Explicit `serviceAdapterImplemented` distinguishes Windows recognized family (true) from unimplemented Windows SCM backend (false), preserving Linux source behavior. First CI failure (Windows constructor missing field) corrected; full rerun green.

New bounded source-only child #619 branch `fix/windows-service-backend-admission-20261009`, head `b426692798092edf263d0182a205ae7ba9a6dc2b`, adds fail-closed default backend selection: Windows/unsupported host must not instantiate Linux SystemdUserBackend; injected test backend and Linux path unchanged. Attribution run `37975695602` SUCCESS, full validation `37975695551` IN_PROGRESS at last check. State WAITING_CI; do not merge before exact-head full green. This does not implement Windows SCM or authorize Windows service operations. Issue #489 remains open for later real Windows backend CI/qualification. No live servers, tunnels, credentials or workers changed.

#590 external connector return-path intermittence remains unqualified. Do not infer a live fix from server-side source tests or tunnel readiness alone. Existing #519 separate self-update source baseline PR received review warning about queue-time vs activation-time TOCTOU; no code mutation.

## 2026-10-09 — Faster-13 #460 merged; Windows source contract #490 pending exact CI

#460 existing shadow memfd/eventfd benchmark: head `26580dbead954e19e1732db0770ca66a51841eaa`, attribution `37974721744` SUCCESS, full Runner MCP validation `37974721750` SUCCESS, squash `6a9ed29197ee7b58c8c6a672c313dfc4edccc160`. Fixed a potential infinite `eventfd_read` wait via bounded select and guaranteed worker cleanup; added positive and timeout tests. Entirely synthetic: no live transport switch, host workload or OCR speed claim. #383 overall remains open.

#490 existing branch `feature/489-host-platform-contract` source-only Linux/Windows contract was reviewed and restacked on live main. Added explicit `serviceAdapterImplemented` flag (Linux true, Windows false, unsupported false) so Windows recognition cannot imply working SCM adapter; no production behavior changed. First new CI run `37975043315` Ruff GREEN but pytest found missing Windows constructor field (2 failures, 2539 pass); fixed in new head `a82f7d90bd8eb400aed329a0e9b414d6ff0f7771`. Validation `37975249793` IN_PROGRESS at last check; DO NOT MERGE until terminal exact-head success. #489 source-only next adapter sequence remains controlled; no Windows service activation or local host mutation.

#590 external connector response association still unqualified; prior local reply-ID gate #613 was merged. No changes to working tunnel, runner enrollment, or credentials. Source freshness #599 previously merged and closed.

## 2026-10-09 — ARCHITECTURE DECISION: ONE FABRIC CONTROL PLANE (operator accepted)
Canonical local copy: [ADR-2026-10-09-ONE-FABRIC-CONTROL-PLANE](../docs/architecture/ADR-2026-10-09-ONE-FABRIC-CONTROL-PLANE.md). **Runner Fabric alone** owns worker admission/registration/scheduling, capability/evidence, lifecycle intent, leases/fencing, recovery, audit and Cockpit control. Runner-MCP/Agent Bus provides bounded communications and host-local execution only; AIfordable Claude worker runs under dedicated coder identity with fixed actuator; EnerCue consumes qualified Fabric work units. No second control plane, no generic cross-user shell/sudo, no live activation from this decision. Cross-repo coordination: Fabric #1172/#240; runner-mcp #381/#590; AIfordable #370; EnerCue #88/#89 (dispatch BLOCKED pending end-to-end READY).

## 2026-10-09 — Final landing: #456 fully GREEN and MERGED

Supersedes earlier #456 WAITING_CI: PR #456 exact head `c2ff700ed4e87cd0a6dd400975a5c47c4016c2a8`, attribution `37962833940` SUCCESS, validation `37962833262` SUCCESS (Ruff/pytest, release artifact, clean demo), squash merge `fc034b094c633b51889e2a13cc86727e2b1941fe`. Together with exact-green merges #465 `365a7a1f32f82e01da75004b800ed2948516fa9e`, #467 `4bba36e877d96246c93eb8064d6bf0d4af72de05` and #613 `ae2eac3f4e38574d4405460e14f7b8cad122e4d4`, all four code PRs are integrated; no live server, CI selector, tunnel, credential or production transport mutation. New next-safe CI-aware action in following session: reconcile existing stacked PR #460 against merged #456 and newest main (do NOT duplicate PR), inspect CI and rebase only using exact branch name. #458 is a temporary hosted benchmark lab and explicitly DO NOT MERGE. #590 external connector response delivery still OPEN despite local JSON-RPC ID guard; remote health dispatcher/response-delivery snapshots remain unproven. #599 source-level auth freshness is closed. No OCR throughput claims from synthetic measurements.

## 2026-10-09 — Faster-13 shadow merges #467 and #465; #456 awaiting clean demo

Exact-head attribution and full validation SUCCESS: existing PR #467 Unix-envelope E2E head `f918a91c9824f747c1a3ad429cf28d9f8960dc91`, attribution `37962618491`, validation `37962618480`, squash merge `4bba36e877d96246c93eb8064d6bf0d4af72de05`; existing PR #465 compact-envelope head `9d1344beaef929acc9bac236a6c8d692dd48b988`, attribution `37962706609`, validation `37962706712`, squash merge `365a7a1f32f82e01da75004b800ed2948516fa9e`. #456 same-Linux-host Unix IPC head `c2ff700ed4e87cd0a6dd400975a5c47c4016c2a8`, attribution `37962833940` SUCCESS, validation `37962833262`: Ruff/pytest and built artifact SUCCESS, clean demo IN_PROGRESS at last check, state `WAITING_CI`. #460 is STACKED on #456 and must not merge first. #458 hosted synthetic lab DO NOT MERGE. These are measurements only: no actual OCR speedup, live worker load, runtime transport change, service or tunnel mutation. Prior #467 GraphQL diagnostic retracted: incorrect branch name caused failure; exact branch solved it. #590 external connector still OPEN despite #613 local bridge reply-ID hardening.

## 2026-10-09 — Faster-13 restored existing PRs (CI pending)

After exact-green merge #613 (`ae2eac3f4e38574d4405460e14f7b8cad122e4d4`) and source-level #599 closure, existing measurement PRs were reconciled instead of duplicated:
- #467 original head branch `perf/faster13-unix-envelope-e2e`, expected old head `78fa2f7832edcb85c6ec18d079900e62b8a836a5` -> restack head `f918a91c9824f747c1a3ad429cf28d9f8960dc91`; attribution `37962618491` SUCCESS, full validation `37962618480` IN_PROGRESS. Earlier GraphQL ref errors were caused by a **wrong guessed branch name**, not proven GitHub outage; correct original comment via later #467 reply. No duplicate PR.
- #465 original branch `perf/faster13-envelope-shadow` -> head `9d1344beaef929acc9bac236a6c8d692dd48b988`; attribution `37962706609` SUCCESS, validation `37962706712` IN_PROGRESS.
- #456 existing stacked PR (base old #514 feature branch) corrected to base `main` while retaining only the new Unix IPC benchmark file; exact branch `perf/faster13-unix-ipc-shadow` new head `c2ff700ed4e87cd0a6dd400975a5c47c4016c2a8`; attribution `37962833940` SUCCESS (superseding cancelled older attribution attempts), validation `37962833262` IN_PROGRESS.
All are synthetic shadow-only, no live runner, OCR, tunnel, port, service or transport switching. DO NOT merge before full latest-head green. #460 stays stacked on #456 and must not be merged ahead of it. Temporary hosted measurement PR #458 explicitly says DO NOT MERGE. Status: `WAITING_CI` for #467/#465/#456.

## 2026-10-09 — #613 exact-green MERGED; supersedes WAITING_CI below

PR #613 response-ID guard exact head `6b5dc2c2c646aba0fdc45a0ae9a08a6af83a8f97`, attribution `37962077429` SUCCESS, validation `37962077446` SUCCESS (Ruff/pytest, release, clean demo), squash merged `ae2eac3f4e38574d4405460e14f7b8cad122e4d4`. Nine tests include JSON and SSE normal/mismatched ID; missing/type-confused IDs fail closed. First Ruff and synthetic SSE fixture failures were investigated and fixed (not service faults). No live tunnel or runtime deployment. #590 remains OPEN: external ChatGPT connector responses intermittently generic internal error and actual tunnel delivery correlation unproven. Official upstream `openai/tunnel-client/docs/health.md` confirms local-only dispatcher vs response-delivery counters; see issue #590 and `docs/diagnostics/CONNECTOR_READONLY_TRIAGE.md`. #599 previously merged/closed; do not repeat. Existing #467 ref move was blocked by GitHub GraphQL; reconcile before continuation.

## 2026-10-09 — Current continuation: #599 closed; #613 source hardening awaiting CI

GitHub truth supersedes earlier handoff: #599 was already merged via PR #609 `ee29a791bb8dab96275ae3efc9987c6548a57bdd`; exact-head full validation `37957581774` SUCCESS, attribution `37958136637` SUCCESS. Current source enforces RFC3339 freshness (90-second max age, 5-second future skew; documented 30-second poll + 5-second guard). Issue #599 has now been closed as source COMPLETE. This does NOT prove live external tunnel routing; #590 remains open.

#590 internal LocalMCPClient gap discovered: requests had JSON-RPC ids but _post did not enforce reply id. Draft PR #613 branch `fix/590-local-mcp-jsonrpc-response-id-20261009` adds exact numeric reply matching, rejecting missing/mismatched/type-confused IDs, including SSE fixture regression tests. Last recorded head `6b5dc2c2c646aba0fdc45a0ae9a08a6af83a8f97`; attribution `37962077429` SUCCESS, full validation `37962077446` IN_PROGRESS; first attempts fixed Ruff and incorrect synthetic SSE line separators. State `WAITING_CI`; DO NOT merge before exact-head full green. This is LOCAL bridge hardening, not external client/tunnel proof. No deployed bridge/host/tunnel/credential modification.

Existing #467 shadow benchmark in-place restack blocked by two guarded GitHub update_ref GraphQL errors. Candidate detached Git commit `057de0267542ae5296d7c2e66891d6d0ff75d47e`; original PR #467 head remained `78fa2f7832edcb85c6ec18d079900e62b8a836a5`. No duplicate branch, rerun or merge. Temporary lab PR #458 explicitly DO NOT MERGE. #490 Windows contract reviewed: recognized host family should not be mistaken for operational Windows adapter readiness; note posted on original PR. No live environment changes. Next safe actions: await #613 exact-head CI, repair proof if needed, merge when fully green, update #590 and handover; then only resume safe independent roadmap work.

## 2026-10-09 — Next autonomous session: existing Faster-13 PR reconciliation

Latest GitHub open-PR review: #514 was already merged and removed from open set; temporary benchmark runner PR #458 explicitly states DO NOT MERGE. Existing #467 Unix-envelope E2E benchmark contains a single shadow script, not a runtime transport change. A clean tree/commit candidate `057de0267542ae5296d7c2e66891d6d0ff75d47e` was created against observed main `f9ac09a52b11f55c5b0ee9612b7dc63130d55db6`, but guarded update_ref failed twice with GitHub GraphQL internal errors. Original PR #467 head remains `78fa2f7832edcb85c6ec18d079900e62b8a836a5`; **NOT UPDATED, NOT MERGED, NO NEW CI**. Issue comment on #467 records blocking evidence. Do not blindly repeat branch rewrite or create duplicate PR; reconcile platform health and fresh main/head before any future change. #460 remains stacked on #456; cannot bypass dependency. #599 remains open pending poll producer cadence; no guessed TTL. #590 remains open for live client/tunnel response correlation. No live runner/tunnel/product changes.

## 2026-10-09 — Multi-lane exact-green landing: CI runner, tunnel freshness, release archive

Canonical handoff: `MASTER_AI_ENGINEERING_SESSION_HANDOFF_PROTOCOL.md` v1.2 in the Library. This entry supersedes earlier `WAITING_CI`/open-source-PR statuses for the items below. Main verified after latest merge: `3077381bc5d82856e6f815033dc19e833cb227bb`.

- #388 bounded runner registration CLI: exact head `ffc7f6961cacacb017047bb4d3eeb30ea190fb4c`; attribution #37955004451 SUCCESS, validation #37955004467 SUCCESS (Ruff/pytest, demo, release artifact), squash merged `13a60429cacb3f8561c1342c092dca62fb34b4d9`. Admin token separate and unequal to mailbox token, operator checklist. This is SOURCE capability only; no local registration, no host/credential mutation.
- #387 isolated qualification workflow: exact head `cd16081fd1e96d1e1c5192b44e24a842573b0921`; attribution #37956932210 SUCCESS, validation #37956932189 SUCCESS, squash merged `08bd1f9683d57df6d25ae68f66f21afc73b7eb0b`. Manual main-only dispatch; removes persisted wheelhouse/tool cache reuse, fresh no-cache dependency install and per-run SHA-verified publisher. Not an actual self-hosted job qualification.
- #609 (issue #599) bounded tunnel control-plane authentication freshness: head `04d0f493db9ba0ea00c4aa10e403e3823785e30b`, attribution #37957581720 SUCCESS and full validation #37957581774 SUCCESS (Ruff, 2470 pytest cases, registry, artifact, demo), merged `ee29a791bb8dab96275ae3efc9987c6548a57bdd`. RFC3339 `last_success` age <=90s, future skew <=5s with injected clock, conservative default based on official tunnel-client 30s long poll and 5s guard; customized longer polling/backpressure may yield unproven, NOT a diagnosis of outage. Issue #599 closed; external #590 remains unresolved.
- #610 (issue #586) previously parked immutable release-archive independent-volume read-only readiness: head `28cd7f638225c7743c9b8843d6816e185f02b298`, attribution #37958021693 and #37958297809 SUCCESS, validation #37958021764 SUCCESS (full Python/MCP integration, artifact, demo), merged `3077381bc5d82856e6f815033dc19e833cb227bb`. Issue #586 closed for SOURCE. No archive mirror/restore/copy/mount/delete/volume config occurred.

**Still blocked on live authority/evidence:** #584 disposable runner admission (do not migrate public free hosted PR checks to production/staging runner); #590 external ChatGPT connector invocation / tunnel return path; #585/#587/#588 real physical second-copy and restore (AIfordable #537 storage topology and Runner-Fabric #1397 fixed private archive namespace remain OPEN). `st_dev` mismatch proves distinct filesystem devices only, NOT a physically independent disk by itself. No production deploy, role/permission broadening, paid CI minute purchase, host changes or backup deletion.

Next safe work: qualified operator-only read-only runtime/volume evidence to locate the first failing edge, then actual separate-volume operator admission before any mirror, always preserving protected active + rollback archive custody. New code PRs must derive from current main and avoid duplicating other agents' Faster-13, #590 or Fabric ownership.

## 2026-10-09 — Faster-13 #514 exact-green MERGED (supersedes WAITING_CI above)

PR #514 existing branch `perf/faster13-local-mcp-benchmark` exact head `1f329ff57e1ef5b8262f813b4a72100aa410820a`: attribution run `37957744577` SUCCESS, full validation `37957744262` SUCCESS (Ruff/pytest, build artifact, clean demo), squash merged `46f9a8b86dc00586cfa24a2368e146f234345d2f`. Includes synthetic bounded loopback MCP benchmark + seven CLI fail-closed checks. #383 stays OPEN for later measurements and polling/event path; synthetic benchmark does not demonstrate OCR throughput or authorize production transport migration. No live benchmark/worker/server/tunnel deployment. PR #607 and #608 already merged as below; #590 external response return path and #599 poll freshness remain open. State COMPLETE #514 code merge; no further immediate dependency-safe rollout.

## 2026-10-09 — Faster-13 #514 existing-PR restack and CI checkpoint

Existing Faster-13 benchmark PR #514 was not duplicated; its original single-file benchmark was preserved and restacked onto current main via a Git object tree with an exact expected-head lease. Extra negative CLI input tests were added. First test head `080417e41941c07378265a0b93db70ebe774304d` failed **Ruff-only** import-block spacing in run `37957558080` (not an infrastructure or benchmark logic error). Corrected current head `1f329ff57e1ef5b8262f813b4a72100aa410820a`; attribution `37957744577` SUCCESS; validation `37957744262` IN_PROGRESS at last check. State `WAITING_CI`, no merge until exact-head full success. Historic synthetic benchmark results do not prove real OCR throughput. No live runner/tunnel/credential/server action. Existing #383 is tracking. Next action: inspect exact-head validation, repair any actual code failure; merge only after terminal success; then update issue/roadmap. Keep #590 external tunnel lineage unqualified and #599 freshness independent.

## 2026-10-09 — Connector response tracing qualification merged

Canonical Library master v1.2 re-read and followed. Live GitHub: PR #608 head `43176d1894250dd7dc7ac71c1754df038d633984`, attribution run `37956025846` SUCCESS, full Runner MCP validation run `37956026036` SUCCESS (Ruff/pytest, release, clean demo), squash merge `e0250205ee33cd39f5ffc501ff8fa86861679d30`. Tests cover existing HTTP RequestIdMiddleware 8-way concurrency, per-response IDs, parent span isolation and malformed inbound trace. Local endpoint test only; **does not prove remote tunnel response-route lineage**. Sanitized operational documentation PR #607 was fully green and merged `6dc5160c93815b223214302ffb50cebbb304e49d`, superseding closed unmerged #603. #590 stays OPEN pending authorized live first-failing-edge correlation. Operator observed tunnel active/enabled, local ready 200, no restarts; reboot not tested. No production/tunnel/worker/credential changes. Issue #388 now CLOSED (prior handoff showed OPEN); do not duplicate enrollment work. #599 remains OPEN: freshness of control-plane poll last_success; actual poll cadence must be sourced before picking threshold. Next safe action: reconcile #599 writer timing/spec and build deterministic clock-bounded guard; keep live tunnel unchanged. State: COMPLETE for #608/#607, BLOCKED external lineage #590.

## 2026-10-09 — CI runner admission safety, public billing and secret separation

Canonical master: Library `MASTER_AI_ENGINEERING_SESSION_HANDOFF_PROTOCOL.md` v1.2. Source of truth: GitHub current main, PR state and exact-head CI, not chat history.

**Main verified when branch was cut:** `d4d41c7bae76e42e93d90d152edcba99a670f3a4`. Previous confirmed green merges:
- #605 head `54438e950b97409f372e82dcb72d6c1494590d6e`, attribution #37953567350 SUCCESS and Foundation #37953568018 SUCCESS (Ruff/pytest, demo and built release artifact); squash merged `07362be6e13a735fe72548629b15178b2d7125ae`. Complete GitHub runner inventory now refuses any malformed/missing identity row.
- #604 head `d8b37be2b155f9860e821fd1ce26644e114ab999`, attribution #37953755539 SUCCESS and Foundation #37953755592 SUCCESS; squash merged `d4d41c7bae76e42e93d90d152edcba99a670f3a4`. Runner root, config.sh, existing work root and its nested parents must not be group/world-writable before short-lived runner-token minting. Residual process argv and TOCTOU/ownership risks require dedicated trusted VM/user; file modes alone are NOT full isolation.
- #589 admission document already merged `f597d76a4665e2c6aa6ff500caae1dc2189a442d` after stale-base recovery. Do not resurrect older snapshots.

**Still open/blocked (not reported complete):**
- #388 existing local enrollment-CLI PR, branch `ci/bounded-runner-enroll-cli`, now uses an explicit `RUNNER_MCP_CI_RUNNER_ADMIN_TOKEN` separate from `RUNNER_MCP_GITHUB_TOKEN`. Tests and operator checklist are on PR branch; exact head/CI must be reconciled before any merge. No admin credential was configured or used, and no live runner was enrolled.
- #387 existing dedicated self-hosted qualification workflow PR remains open. Its persisted `RUNNER_TOOL_CACHE` is NOT disposable-job isolation; no live runner proof. Preserve the review and do not start PR-sourced code on an untrusted shared host.
- #584 was retitled to reflect the billing correction: Runner-MCP is PUBLIC and standard GitHub-hosted runners there are free. Self-hosted migration is OPTIONAL and requires actual isolation benefit; private repo Actions artifacts/storage remain a separate billing concern.
- #590 external Runner-MCP connector generic internal errors still unqualified. Local authenticated dispatch smoke in #595 is NOT a live ChatGPT connector success.

**What was NOT done:** no runner registration, CI selector switch, local host/service/VM/credential mutation, production deployment, stored artifact deletion, paid tier change, or backup removal.

Next safe action: verify exact latest #388 CI and review its elevated auth semantics, preserve #387/#584 admission gate, then use authorized operator-only evidence to prove a disposable nonproduction runner. No downstream `runs-on` change before that proof. If CI awaits, classify `WAITING_CI`, not test failure.

## 2026-10-09 ~14:22 CEST — Runner-MCP master v1.2 safe landing reconciliation

This session's first material GitHub toolcall was approx 14:04 CEST; useful Runner-MCP-only development and reconciliation continued through the prescribed >=18-minute master window when safe. Do NOT resume Runner-Fabric implementation from this chat. No live server/tunnel, credential, worker, host, CI runner enrollment, port or customer-production changes.

**Four own PRs are exact-head GREEN and squash MERGED:**
- #595 head `0c66f43f7abede4cfa938d3f54a4e6737a720d81`, attribution 37927827207 and validation 37927827247 SUCCESS, merge `beb192fba89a0dbcadac8a5b06348e03a8d716b8`. Authenticated in-process MCP HTTP read-only smoke for list_projects/runtime_status/runtime_doctor; local schema/dispatch proof only, NOT external connector health.
- #596 head `febc3a27776c806cd81af8a7ae2dc3798e9e4e28`, attribution 37928039438 and validation 37928039405 SUCCESS, merge `30e9e50b6e7c675a1779abf57f9ec223bbcdad17`. Invalid clock in private CI secret handoff cleanup fails closed without deleting files.
- #597 head `beabb7889642ac61ae8de3de6d620de3beb22970`, attribution 37928933459 and validation 37928933273 SUCCESS, merge `6491d2972e95ec7af0bf6a0b6c5a2d7b95e801d9`. Exact bool tunnel readiness evidence, 25 negative cases; initial Ruff TRY004 diagnosed and corrected to TypeError.
- #598 head `4a0786abf6f5fa89d1b312f610a123e341e62de6`, attribution 37928825612 and validation 37928825684 SUCCESS, merge `d720a2192f0228e0b1863c27674c8eb39ff368b7`. Explicit degraded/error/stopped current local MCP health defeats stale startup success.

Existing blocked tracks remain explicitly distinct:
- #590 current ChatGPT connector generic internal errors on four read-only tools; local smoke #595 GREEN does not prove live connection. Historical #333 Oct5 tunnel loss is a plausible *pattern*, not proven present cause; Oct8 operational tunnel's different topology_refresh wrapper issue already resolved #523/#524. #540 stale catalogue fencing still open. Read-only private client/tunnel first-failing-edge evidence needed before any repair or live health claim.
- #584 hosted CI cost goal still BLOCKED on real isolated disposable runner proof; draft #589 and #387/#388 already own admission/enrollment. No workflow selector or protected host changes.
- #599 new focused risk: `collect_control_plane_authenticated` accepts any nonempty last_success timestamp as current auth. Next child must first derive actual health poll cadence and deterministic clock bounds; no speculative TTL.
- OCR full qualification previously finished. Existing #514/#458/#467/#537 own Faster microbench and timing; don't duplicate or claim synthetic transport improvements as real OCR speedup.

Permanent docs: component11 DATA_LINEAGE/FAILURES RMCP-TUN-0001/0002 (green) and 0003 (open), component14 RMCP-MCP-0005, component09 CI guard; `docs/diagnostics/CONNECTOR_READONLY_TRIAGE.md`; issue comments #333/#590. No new own code PR remains pending. Continue safe independent work from real main state in next session; do not claim connector recovered without external evidence.


## 2026-10-09 ~14:20 CEST — scope-correct Runner-MCP continuation checkpoint

This chat owns Runner-MCP ONLY, not Runner-Fabric. First material toolcall ~14:04 CEST; canonical Library master v1.2 requires productive independent work through >=18 minutes when safe and no new major lane after minute 18. Do not pretend a tooltime budget can be read directly. Public GitHub files must not expose private tunnel/host/token/port/path/credential data.

Exact-green merged this session:
- #595 head `0c66f43f7abede4cfa938d3f54a4e6737a720d81`, validation 37927827247 and attribution 37927827207 SUCCESS, squash `beb192fba89a0dbcadac8a5b06348e03a8d716b8`: authenticated in-process MCP regression tests for list_projects/runtime_status/runtime_doctor, structured/sanitized response. Does NOT prove ChatGPT live connector.
- #596 head `febc3a27776c806cd81af8a7ae2dc3798e9e4e28`, validation 37928039405 and attribution 37928039438 SUCCESS, squash `30e9e50b6e7c675a1779abf57f9ec223bbcdad17`: fail-closed cleanup clock preflight before any temporary CI registration-secret handoff deletion.
- #598 head `4a0786abf6f5fa89d1b312f610a123e341e62de6`, validation 37928825684 and attribution 37928825612 SUCCESS, squash `d720a2192f0228e0b1863c27674c8eb39ff368b7`: explicit degraded/error/failed/stopped tunnel MCP health overrides historic succeeded/auth-required startup probe.

One current session PR still waiting full CI:
- #597 branch `fix/333-tunnel-readiness-exact-bool-evidence`, latest head `beabb7889642ac61ae8de3de6d620de3beb22970`. Commit attribution 37928933459 SUCCESS; Foundation/Runner MCP validation 37928933273 IN_PROGRESS (Ruff/pytest and release artifact green; clean demo still running at last check). Initial head had only Ruff TRY004; fixed code to use TypeError for nonboolean field and test expectation. 25 negative cases cover strings/numbers/null across all five readiness gates. Merge only if entire exact-head workflow SUCCESS.

Current #590 connector generic internal error remains OPEN/UNLOCATED. Earlier read-only tool attempts (runtime_status, doctor, list_projects, worker_status) returned no structured payload. New local smoke #595 green narrows local server behavior, **not** the live client/tunnel/server boundary. Historical #333 Oct5 loss of tunnel client and Oct8 live-but-specific topology_refresh generic error; latter was already fixed in #523/#524, do not reimplement. Existing #540 handles exact runtime catalogue generation. Live read-only owner checks of connector/catalogue/tunnel needed before claiming health; no host restart attempted.

#584 isolated self-hosted CI cost migration BLOCKED on actual disposable runner proof, draft #589 owns admission docs, #387/#388 other owned lanes. Prior #594 already reduces overlapping hosted attribution jobs. No workflow selector/permission or live runner changed.

#599 newly filed: `collect_control_plane_authenticated` treats any nonempty last_success as fresh auth; must inspect actual writer/poll cadence before implementing RFC3339 freshness. Coordinate with #598 (same source file) and #333 evidence owner. No stale assumption or arbitrary TTL yet.

Other docs: component 11 DATA_LINEAGE/FAILURES maps tunnel evidence gates; component 14 maps read-only connector failures. OCR core qualification complete; only existing Faster #514/#458/#467/#537 stage-performance analysis, no duplicate tests or live OCR workloads. No customer/server/worker/credential/port/runtime mutations this session.

Next safe actions: reconcile exact-head #597 required CI, merge only if GREEN; update component11 Failure Museum / #333 and this handover with SHA. If still in progress near master landing, classify WAITING_CI and leave exact commit/run. For #590 wait for authorized private tunnel/client evidence, no blind retries or unqualified production changes.

## 2026-10-09 ~13:34 CEST — master-safe Runner-MCP completed work/landing

Scope is Runner-MCP only; do not duplicate Runner-Fabric code, #584 admission docs draft #589 or existing Runner-MCP FASTER benchmark PRs. This session continued through approximately the 18-minute productive minimum before landing. No live host, runner, credentials, tunnel, process or production state was modified.

Four independently qualified exact-head green PRs merged:
1. #591 `ea519720454b54c326ebadc2fed51e8b384fe18f` — private CI registration-secret reaper caps candidate directory scan to <=4097; refuse before deleting anything when >4096.
2. #592 `3c9e16b56d2b62978bdf5b0802dac1327e32217f` — canonical handoff ID type and positive 53-bit expiry boundaries.
3. #593 `91299d1bc71474440c923b42d5fa922253421217` — validate single bounded clock before any secret file creation; negative tests require no leftover file; exact-head CI green after fixing TRY004 authoring error.
4. #594 `3c3a2b04238d4491a7470ef87d1d96b8e78708bc` — attribution workflow now cancels superseded PR/ref runs (required check name, trigger, permissions and hosted runner selector unchanged); exact-head commit attribution 37924161842 and validation 37924161737 SUCCESS before squash merge.

Outstanding Runner-MCP blockers are **separate** and NOT claimed resolved:
- #584: actual isolated disposable self-hosted CI runner admission absent; #589 draft, #387 and #388 owners unchanged. Four workflow jobs remain hosted; #594 reduces avoidable overlap, not total hosted minutes to zero. Direct Actions runner inventory unavailable through current GitHub connector.
- #590: all four read-only connector calls previously failed internally with no structured response. Read-only triage and RMCP-MCP-0005 indexed; actual runtime health, isolation and worker capacity UNKNOWN. Authorized connector repair required before live probes.
- OCR qualification is historical COMPLETE; improvement is measurement only. Existing #514/#458/#467/#537 active, synthetic transport CI evidence noted in #514, and new `docs/OCR_ACCELERATION_MEASUREMENT_PLAN.md` guides stage timing with integrity/privacy gates. No fresh OCR job executed.

Main diagnostic/roadmap and handover notes reconciled with RMCP-CI-0001..0004, RMCP-MCP-0005 and tested commits. No new PR from this session remains open. Next: safely qualify #590 connector transport and #584 disposable runner admission without duplicated work or unapproved runtime mutation; continue Faster shadow analysis rather than requalifying OCR.


## 2026-10-09 ~13:33 CEST — Runner-MCP continuation / master-safe reconciliation

This handover supersedes the preceding pending #593 state; GitHub main and exact run state remain authoritative.

**Three green, exact-head merges in the Runner-MCP lane:**
- #591 `ea519720454b54c326ebadc2fed51e8b384fe18f`: cap and fail-close temporary CI secret-handoff directory scan, no deletion if over 4096 entries.
- #592 `3c9e16b56d2b62978bdf5b0802dac1327e32217f`: public CI handoff ID type and positive 53-bit expiry validation.
- #593 `91299d1bc71474440c923b42d5fa922253421217`: sample/validate finite, positive, TTL-safe clock BEFORE writing any CI registration secret; one sample for returned expiry and record mtime. Initial Foundation failed only Ruff TRY004, corrected on exact head `cc55d30b916f260132de9fa33151af7af145b86c`; rerun via new commit completed attribution 37924023172 and Foundation 37924023194 both SUCCESS before merge.

**One open CI PR, independent cost-saving child of #584:**
- #594 branch `ci/584-cancel-superseded-attribution`, head `57467a40bfd8a4a2c25424e416dbd9b0aab68c10`: add per-PR/ref `concurrency` with `cancel-in-progress` to commit-attribution-policy workflow (normal validation already had it); no changed job/check name, permissions, triggers, hosted runner selector, branch protections or trusted release rules. Attribution run 37924161842 SUCCESS. Foundation validation 37924161737 IN_PROGRESS at 13:32:47; Ruff/pytest and built artifact completed green; clean demo still in progress. DO NOT MERGE before entire exact-head run shows SUCCESS. This can reduce redundant GitHub-hosted minutes but is not $0 hosted migration.

**#584 isolation still BLOCKED:** Draft #589 already holds admission docs; #387 qualification workflow and #388 enrollment CLI exist; current GitHub integration disallows direct Actions runner inventory endpoint. No independent safe disposable runner capacity proven, no `runs-on` change/enrollment/deployment. Shared/private infrastructure untouched.

**#590 connector still UNLOCATED:** four read-only MCP tools all returned generic internal error (runtime_status, runtime_doctor, list_projects, worker_status). Generic error does not prove server crash or worker capacity. Read-only triage `docs/diagnostics/CONNECTOR_READONLY_TRIAGE.md` indexed from diagnostics README and failure RMCP-MCP-0005 under component14. Do not blind retry or shell/tunnel/restart bypass.

**Faster/OCR:** prior OCR qualification completed; speed improvement is distinct. Reused hosted shadow CI #458 run 37522524389 job 112471504336, noted synthetic p50 urllib 0.7799ms vs persistent HTTP 40.9038ms and Unix E2E 52.288us vs reference 132.698us. These are *not* real OCR throughput measurements. Existing #514/#458/#467/#537 own bench/measurement; no duplicate benchmarks, paid CI speed runs, OCR jobs, production workloads. New `docs/OCR_ACCELERATION_MEASUREMENT_PLAN.md` separates source/queue/VM boot/transfer/language detection/OCR CPU/postprocess/cleanup stages with privacy and safety gates.

Updated main: component 09 ROADMAP/FAILURES (RMCP-CI-0001..0004), component14 FAILURES (RMCP-MCP-0005), diagnostic README/read-only connector triage, OCR measurement plan and issue comments #584/#514/#537. Public docs exclude private deployment identifiers and secrets.

Next: check exact SHA #594 Foundation CI, merge only all green, reconcile #584 cost-saving note; then restore connector #590 through authorized owner evidence (client catalogue/transport/private bounded health) before any runtime activation or live performance assertion. This chat stays in Runner-MCP, **not** Runner-Fabric. Continue separate ongoing projects without interference.


## 2026-10-09 — Runner-MCP CI safety / connector / Faster checkpoint (updated)

This is the **Runner-MCP** lane only. Do not resume Runner-Fabric F17/F20 code from this chat. Check active PRs first; do not duplicate #584 docs-only #589, admission workflow #387 or enrollment CLI #388. No production/worker/host/port/credential/tunnel mutations performed.

Exact green merges this session:
- #591 squash `ea519720454b54c326ebadc2fed51e8b384fe18f`, head `e365787148f456ed49eb7cf4d3859d56ae4f07df`: bound private CI registration-handoff reap directory materialization to 4096 entries, fail closed with no deletion over limit.
- #592 squash `3c9e16b56d2b62978bdf5b0802dac1327e32217f`, head `09bfd4dee7bf20dacc8b29176b655ce06fdec6a0`: reject wrong-type handoff IDs and invalid public expiry timestamps with sanitized error.

Active exact-head PRs:
- #593, `fix/ci-handoff-clock-preflight`, head `cc55d30b916f260132de9fa33151af7af145b86c`: check finite/positive/TTL-safe numeric clock **before** writing any registration secret, one sample shared for mtime/expiry. First validation run failed Ruff TRY004 only; fixed exact diagnostic on new head. Commit attribution 37924023172 SUCCESS; validation 37924023194 IN_PROGRESS at checkpoint. Merge only exact green.
- #594, `ci/584-cancel-superseded-attribution`, head `57467a40bfd8a4a2c25424e416dbd9b0aab68c10`: per-PR/ref concurrency cancellation for redundant commit-attribution Actions, existing triggers/check names/permissions/runs-on remain unchanged. Commit attribution 37924161842 SUCCESS; validation 37924161737 IN_PROGRESS. Partial hosted-minute savings only, NOT #584 runner isolation.
- #584 still BLOCKED on proven disposable self-hosted runner admission. Draft #589 already contains admission docs; #387/#388 have distinct owners. GitHub runners inventory endpoint is not accessible via available connector; do not assert eligible capacity or relabel PR workflows.
- #590 live connector: four read-only tools (runtime_status, runtime_doctor, list_projects, worker_status) all return `The tool failed internally.`; no structured runtime result. Generic transport/app layer unlocated. No blind retry, shell, process or tunnel restart. Diagnosable guide `docs/diagnostics/CONNECTOR_READONLY_TRIAGE.md`, canonical RMCP-MCP-0005.
- FASTER/OCR: OCR qualification is already historical/complete; acceleration measurements only. Existing #514/#458/#467/#537 active, do not duplicate. Hosted CI #458 log showed synthetic persistent HTTP p50 ~40.90ms vs urllib ~0.78ms (slower), Unix envelope p50 52.288us vs reference 132.698us (synthetic, not real OCR throughput). Tracked in #514 comment and `docs/OCR_ACCELERATION_MEASUREMENT_PLAN.md`. No OCR job or live worker executed.

Docs updated: component 09 ROADMAP/FAILURES including RMCP-CI-0001..0004; component 14 FAILURES including RMCP-MCP-0005; diagnostic README/connector guide; OCR stage measurement plan; #584 and #514 issue comments. Public GitHub contains no private coordinates or secret values.

Next: check exact-head CI #593/#594, inspect logs before fixing failures, merge only fully green, update this handover with merge SHA. Isolated CI admission #584 requires separate host-owner proof/approval; do not move workflow selectors prematurely. Once connector #590 is resolved by authorized operator, confirm bounded list_projects/status/doctor and then measure actual OCR stage timing only if needed, not whole qualification.


## 2026-10-09 — Runner-MCP scope-correct continuation (CI admission / connector / Faster)

This session belongs exclusively to Runner-MCP; the Runner-Fabric active implementation lane remains owned by its other project chat. Read GitHub current state before edits; no production or shared infrastructure mutation has been performed.

**#584 self-hosted CI migration:** still BLOCKED on proof of a dedicated disposable isolated runner, not missing policy text. Existing docs-only draft PR #589 owns admission and selector-change plan; separate pre-existing #387 and #388 own qualification/enrollment CLI. Do not duplicate any of them or retarget untrusted PR jobs to privileged/shared runners.

**Completed in this session:** PR #591 (branch `fix/590-ci-handoff-reap-bounds`) exact head `e365787148f456ed49eb7cf4d3859d56ae4f07df` passed attribution run 37922815224 and validation run 37922815197, then squash-merged `ea519720454b54c326ebadc2fed51e8b384fe18f`. It caps private CI registration-secret handoff root scanning to 4097 candidate entries; if >4096, refuse with NO deletion, protecting against unbounded `list(root.iterdir())` memory cost. Exact-bound and over-bound tests are present. This does NOT enroll or qualify any runner. Failure record RMCP-CI-0001 linked in component 09.

**Actual connector blocker #590:** `runtime_status`, `runtime_doctor`, `list_projects`, `worker_status` all fail in this ChatGPT session with generic `The tool failed internally.` No structured payload is available, so actual runtime/worker/isolation health cannot be determined. The first failing network/catalogue/application edge has NOT been established; do not restart servers or replay arbitrary shell actions. Failure RMCP-MCP-0005 logged under component 14. Next owner-safe diagnostics: fresh client/catalogue + bounded connector/session check, then private read-only transport/health proof, then single runtime status/doctor verification.

**Faster/OCR optimization:** core OCR qualification has already been completed; only acceleration/measurement remains interesting. Existing Runner-MCP PRs #514 baseline (green last known exact head), #458 hosted shadow lab, #467 Unix envelope E2E, #537 measurement hardening are OPEN/owned and must not be duplicated/merged blindly. Read-only evidence from hosted CI #458 run 37522524389 job 112471504336: urllib loopback p50 0.7799 ms, persistent HTTP p50 40.9038 ms (worse in this setup); Unix-envelope synthetic p50 52.288 µs versus reference 132.698 µs, stated 2.538x p50 speedup. These are TRANSPORT synthetic measurements, not OCR runtime performance. Note added to #514. Next performance step: isolate staging/transfer/worker startup/OCR/page/post-process costs before optimizing transport; no real OCR work rerun without need.

Updated main docs: component 09 ROADMAP/FAILURES, component 14 FAILURES, this handover; issue #584 has an independent progress note; #590 is the generic connector error tracker. Do not publish private host paths, addresses, credentials, tunnel configuration or keys in public repo.

Next safe work: review #590 authorized connector diagnostics and #584 runner-admission evidence when tools recover; investigate other unrelated CI admission fail-safe bugs only in new bounded children after checking active projects. Preserve exact-head validation before merging.


## 2026-10-08 — Diagnostic-topology handoff

Runner-MCP #569 is a docs-only cross-project diagnostic rollout. Use `docs/diagnostics/README.md` + `component_registry.yml` for troubleshooting after this change lands. The structure deliberately does not alter or claim completion of active Fleet A6, Bewind OCR, update, qualification or runtime work.

The four migrated reusable failure classes are:
- RMCP-F-0001: local queue idle does not prove end-to-end idle;
- RMCP-F-0002: healthy Fabric agent process does not prove peer tools/private qualification binding;
- RMCP-F-0003: source authorization/reachability is independent of runtime health;
- RMCP-F-0004: live server capability does not imply an already-open client refreshed its tool catalogue.

Future fixes should register the earliest failing lineage edge and link the regression test rather than adding another ad-hoc handover-only explanation.

## 2026-10-08 — Bewind OCR qualification staging + execution live; client schema refresh next

Runner-MCP #529 / PR #532 merged as `7f53f92a721dbc6ab9493030bb264e0bab50a277`: fixed zero-argument content-addressed staging for the canonical Bewind German OCR sentinel. Runner-MCP #528 / PR #533 merged as `b6a50eedad8b7448f73e3d13dc9c8be08c1a0668`: fixed zero-argument one-shot Bewind OCR qualification execution using the canonical `pre1997-ocrmypdf-sidecar-0.2.0` contract with exact `nld+fra+deu`, bounded hash/timing/load/failure evidence, final disposable-target destruction and staged-input cleanup. Both keep normal activation false and do not touch active Bewind v3.

Exact-head #528 validation is fully green: attribution, compile, Ruff, pytest, MCP Registry metadata, whitespace, built release artifact and clean demo. Initial CI had only five Ruff authoring diagnostics (three SIM102 cleanup conditions and two overly broad test exception catches); these were corrected on the same branch and are not treated as a reusable operational Failure Museum class.

Live Runner-MCP self-update job `5e8b7494552a436792f3f44ca236399d` completed successfully to exact `b6a50eedad8b7448f73e3d13dc9c8be08c1a0668`. Runtime status then proved installed/source/active runtime revisions all exactly aligned with no restart or install-recovery pending.

Immediately after update, the Fabric loopback bridge was unavailable. The fixed zero-argument `fabric_worker_qualification_policy_configure` restored the trusted Bewind worker policy (generation 1, policy valid, source target ready, normal activation false), after which bounded `fabric_agent_restart` returned restarted/pid_changed/healthy. Final live proof:
- Fabric bridge preflight: ready;
- Fabric source revision: `3bd24f96844341e418618ea44adcbd625cc7bb60`;
- worker: `aifordable-lab`;
- capability: `bewind-ocr-qualification-v1`;
- generation: 1;
- capabilityAllowed/policyValid/activationReady: true;
- normalActivationEnabled: false;
- Runner-MCP doctor: 0 failed checks.

Current blocker is client schema only: this already-open ChatGPT runner-mcp-control tool catalog was loaded before #528/#529 became live, so `bewind_ocr_qualification_stage` and `bewind_ocr_qualification_run` are not callable in this session. Do not use shell/Desktop Commander as a bypass.

Next exact action in a fresh first-party client/chat after connector tool refresh:
1. confirm both new zero-argument tools are visible;
2. call `bewind_ocr_qualification_stage` exactly once;
3. require ready state, canonical source id `2026/02/03_1.pdf`, content hash/size evidence, singleUse=true and normalActivationEnabled=false;
4. call `bewind_ocr_qualification_run` exactly once;
5. require `state=qualified`, exact `nld+fra+deu`, pipeline `pre1997-ocrmypdf-sidecar-0.2.0`, German sentinel verified, page/output hashes, cleanupReceipt.targetDestroyed=true, cleanupReceipt.stagedInputRemoved=true, normalActivationEnabled=false;
6. return bounded result to Runner-Fabric #1114/#1110 for canonical-route equivalence comparison before any multi-host/production activation.

## 2026-10-06 — A6 live proof candidate after provenance repair

Runner-MCP #454/#455 is merged and live. `build_identity.source_revision` now derives from the canonical private self-update state and exactly matches `runtime_status.last_installed_commit` after restart convergence.

The A6 private journal/evidence bindings are configured on `aifordable-lab`; the Fabric qualification agent is healthy. This documentation-only revision is intentionally the next candidate for the canonical live A6 proof so no unrelated runtime behavior is mixed into the campaign.

Required order remains: A6 prepare -> existing bounded self_update -> restart convergence -> fresh A3 probe -> A6 finalize. Do not update to this candidate before prepare succeeds.

## 2026-10-06 — resume #451 Bewind-only source token

#445 is complete/live at `1d4957ff...`.

Active #451 branch: `source/451-bewind-dedicated-token`.
It introduces only fixed private env `RUNNER_MCP_BEWIND_GITHUB_TOKEN` plus an internal project-id credential selector. Bewind uses the dedicated token when present; all other known projects and mailbox remain on the global token. No MCP credential input/output exists.

After merge/live update, owner only needs to place the already-created Bewind read token into the private env. Then run `known_project_source_preflight(bewind)` -> `prepare_known_project(bewind)` -> `register_known_project(bewind)`. Do not replace the global token and do not touch active Bewind v3.

## 2026-10-06 — resume #445 worker qualification provisioning

Active branch: `fabric/445-worker-qualification-provision-v2`, based on main `10df2c8b...`.

Implemented: strict `fabric_worker_qualification_provision`; host-owned private template; exact fingerprint/expiry/generation/Fabric-slot checks; fixed owner-only qualification config; durable runtime binding; immediate handoff to existing `fabric_disposable_target_qualify`; normal activation false; no OCR or Bewind v3 mutation.

Next: exact-head CI/merge, live Runner-MCP update, then Fabric #1130 -> #1113 -> #1114 -> #1115. Runner-MCP #451 separately owns the least-privilege Bewind-only source token needed to close Fabric #1112 without replacing the global GitHub credential.

## 2026-10-06 — A6 live candidate after Fabric lifecycle binding fix

Runner-MCP #446/#447 is live on `0d7d281a5382d822b5cfd0fb7af263145ae51743`. The fixed qualification-agent launch and bounded restart now preserve only the exact all-or-nothing A6 private binding keys required by Runner-Fabric #1049. Live `fabric_agent_restart` after installation returned restarted/pid_changed/healthy.

Runner-Fabric is managed on exact `7ebe95ca853e45734463d3dd605474ff5e70d178`, and Runner-Fabric source plus Actions-read are healthy after least-privilege token repair.

This documentation-only revision is the next exact-main Runner-MCP candidate for the canonical A6 proof:
`prepare -> self_update -> restart convergence -> fresh A3 probe -> finalize`.

Do not count the #447 installation as A6 evidence because it occurred before this prepare boundary.

## 2026-10-06 — resume A6 after Runner-Fabric runtime authorization/update

Do not redo the connector refresh or #427/#428. Both A6 proxies are visible; the fixed Fabric qualification agent can now recover after process loss.

Current live Runner-MCP: `55fa3d1ba46d6d6bb41b2e43d3d94e97376cf309`, operational, restart/recovery clear after diagnostic restart.

Current blocker is below A6:
1. built-in `runner-fabric` source preflight says credential configured but source unreachable/unauthorized and main unavailable;
2. Actions read remains unavailable/unauthorized;
3. no tested A6-capable/current Fabric bundle is present in local custody;
4. therefore the older managed Fabric slot cannot yet be advanced to #1049+.

Once least-privilege Runner-Fabric read access or a trusted local-custody bundle is restored:
1. update Fabric through existing bounded `fabric_update` or explicit `fabric_local_update`;
2. restart/recover the fixed qualification agent if needed;
3. verify bounded Fabric read operations;
4. reconcile exact Runner-MCP main and call A6 prepare before mutation;
5. self-update to that same exact commit;
6. require restart convergence and fresh A3 probe;
7. finalize and require qualified/off_target plus succeeded update/reconnect/probe;
8. only then close Fabric #942 and begin A7/#943.

## 2026-10-06 — A6 live qualification candidate after bounded Fabric-agent recovery

Runner-MCP #427/#428 restored bounded recovery of the fixed qualification-only Runner Fabric Agent MCP after genuine process loss. Live recovery on `86708c18fe075993590caa28b32f1d73221e40ef` returned `state=restarted`, `pid_changed=true`, `healthy=true`.

The earlier A6 candidate `7493a2500411614b91fad6d298210acc74baa211` was not mutated because prepare failed before journal evidence existed. This documentation-only revision is the next exact-main candidate for the canonical A6 sequence:
`prepare -> self_update -> restart convergence -> fresh A3 probe -> finalize`.

Do not claim A6 complete or start A7 unless finalization returns qualified/off-target evidence with successful update, reconnect and probe reconstruction.

## 2026-10-06 — A6 live qualification candidate marker

The runner-mcp-control client schema now exposes both bounded A6 qualification proxies. A concurrent bounded self-update advanced the live runtime cleanly to `877f80423724cc197e3ccd39d0869f8a5611faec` before A6 prepare could start, so that update is not claimed as A6 evidence.

This documentation-only revision intentionally creates the next exact-main candidate without changing runtime behavior. Once merged, use that exact merge commit for the canonical A6 sequence only:
`prepare -> self_update -> restart convergence -> fresh A3 probe -> finalize`.

Do not start A7 unless finalization returns qualified/off-target evidence with successful update, reconnect and probe reconstruction.

## 2026-10-06 — Fleet A6 resume gate and separate #417 access issue

A6/#942 remains gated by ChatGPT client tool-schema refresh. The two bounded A6 proxy tools already exist server-side and must not be duplicated.

Separate Runner-MCP issue #417 tracks private Runner-Fabric source and Actions read access. Keep it independent from A6 qualification.

After the A6 proxy tools become visible: reconcile exact Runner-MCP main, prepare that newer exact commit, self-update to the same commit, wait for restart convergence, require a fresh post-completion A3 probe, finalize, and require qualified/off_target with succeeded update/reconnect/probe before closing Fabric #942. Start A7/#943 only afterwards.

## 2026-10-06 — customer update safety counterpart #414

Do not start with mutation. Wait for/consume Runner Fabric #1063 contracts, then add only the smallest read-only local projection needed. Keep cohort/canary/soak/freeze policy in Fabric and customer semantics in AIfordable #401. Explicitly fail closed on insufficient RAM/storage and unknown required health evidence.

## 2026-10-06 — next action: use newly live A6 proxies after connector refresh

Do not redo #411. Runner-MCP is already live on `e88e76ba...`.

After runner-mcp-control tools are refreshed in ChatGPT:
1. call `fabric_a6_update_qualification_prepare` for a newer exact Runner-MCP main commit;
2. call existing `self_update` for that same commit;
3. wait for terminal success/restart convergence;
4. require a fresh post-update A3 probe;
5. call `fabric_a6_update_qualification_finalize` with the returned correlation id and self-update job id.

If finalization is qualified, Fabric #942 may close. Only then start A7/#943.

## 2026-10-05 — resume #333 only when A3 end-to-end evidence is ready

Repository: Blacksp1d3r/runner-mcp
Canonical main at checkpoint: 9a4f9d7a2916625617aa2ef144fc40679e549129
Primary issue: #333
Completed in this continuation: #370, #371, #372, #373.

Do not redo managed tunnel autostart, process evidence, local MCP health evidence, or control-plane authentication evidence.

Current chain: COMPLETE config -> managed process active -> local /health/mcp proven -> local /health/control-plane successful poll -> end_to_end_not_routable.

Evidence boundaries: no generic process scan; health URL must come from the fixed private mode-0600 tunnel-health.url and be direct 127.0.0.1; MCP evidence requires schema v1, component mcp, status ok, initialized/discovered; control-plane evidence requires schema v1, status ok, idle/polling/backpressured plus non-empty last_success; proxy environment is disabled for local probes.

Important topology fact: tunnel-client emits X-Tunnel-Client-Instance-Id to the service, but local code cannot authoritatively enumerate all active instances. For Runner-MCP's localhost-per-host backend, keep one active client per tunnel ID. Do not infer uniqueness from the local instance id.

Next action is cross-repo: reconcile Fabric #939 and wait for its existing qualification synthetic work-unit to become a continuous bounded probe with durable evidence. Add only a minimal adapter if Fabric exposes a narrow first-party result suitable for end_to_end_routable; otherwise keep Runner-MCP fail-closed and use explicit live/topology proof. Do not build a second probe engine or direct provider client enumeration.

No live tunnel/autostart mutation was performed.
## 2026-10-05 — resume #333 from managed tunnel autostart admission

Repository: Blacksp1d3r/runner-mcp
Canonical main at landing: `2a27fb0d8236e6c06f2fd0da3b04dfced558d471`
Primary issue: #333
Completed PRs in this lane: #364, #366, #367, #368.
Parallel A3 trace PR #363 is merged; duplicate #365 is closed.

Do not redo config readiness, doctor fail-closed behavior, tunnel-status, or the fixed tunnel runtime wrapper.

Current fixed runtime contract from #368:
- local hidden command: `runner-mcp tunnel-run --port PORT`;
- PORT is bounded to 1..65535;
- only installed `tunnel-client` is resolved;
- only `tunnel-client run` is executed;
- MCP target is fixed to `http://127.0.0.1:PORT/mcp`;
- existing private `tunnel.env` must classify COMPLETE;
- `CONTROL_PLANE_TUNNEL_ID` and `CONTROL_PLANE_API_KEY` are explicitly exported to the child and never printed;
- health listener is fixed to ephemeral loopback and health URL is written to the fixed private `tunnel-health.url` path;
- unsafe/symlink health evidence path fails closed.

Exact next safe implementation:
1. add fixed `tunnel` component to `autostart.py` and `cron_autostart.py`;
2. include it only when private tunnel restart config is COMPLETE;
3. systemd unit depends on the Runner-MCP server and invokes only `tunnel-run --port <same bounded port>`;
4. cron supervision uses the existing per-component lock and the same hidden command;
5. extend bounded autostart status/tests to show tunnel installed/enabled/active;
6. then connect active evidence to `tunnel-status` / readiness classifier in a separate smallest slice;
7. later probe only the fixed private health URL for local-ready evidence. Do not collapse local ready into control-plane-authenticated or end-to-end-routable.

Upstream fact already checked against openai/tunnel-client current public source: env tunnel ID/runtime API key, fixed `--mcp-server-url`, `--health-listen-addr` and `--health-url-file` are supported; upstream writes the health URL file mode 0600.

No live runtime mutation, deployment or migration was performed. Reconcile live main and active PRs before starting. Fabric #939 has its own active lane; do not duplicate it.

## 2026-10-05 — resume Fleet Update after Runner-MCP #355

Main checkpoint: `98bd8ca0de5ecdb2c16b70bbe3ff620b882e432c`.

Do not redo #346, #348, #349 or #355.

Runner-MCP now provides aligned full BuildIdentity fields on every durable audit row, including request_id-bearing tool events. Unknown source revision/artifact digest/protocol/interface facts are explicit null by design.

Next cross-repo dependency is Fabric #938 request/connection identity stamping. Only add Runner-MCP code if Fabric needs a bounded fact that Runner-MCP uniquely owns:
- installed source revision/artifact digest from trustworthy active-runtime provenance;
- supported protocol range;
- interface/tool-schema digest.

Do not add paid observability/update software. Do not broaden shell/path/endpoint authority. Claude review remains UNCLAIMED and non-blocking.

## 2026-10-05 — resume Fleet Update work with historical-failure reproduction

Fabric umbrella #924 and reviewed v2 define the sequence. Runner-MCP should begin with A1-compatible test work: reproduce an incompatible/stale control-path peer in a lab/integration test and classify where it fails. Do not start supervisor implementation until the reproduction/observability steps are understood.

Later Runner-MCP responsibilities: build identity/log stamping, trace propagation hooks, handshake/interface digest, N/N-1 compatibility CI, bounded evidence, and #341/#943 supervisor support.

Current self-update fact: baseline wheel rollback exists for install/verification failure; durable previous-release retention plus an external commit-confirmed revert timer after activation does not yet exist.

Software budget is EUR 0 until revenue. Prefer existing/free/open-source software; paid services/tools remain out of scope.

## 2026-10-04 — bounded operational snapshot proxy in validation

Issue #269 now has PR #286 on branch `ops/269-operational-snapshot-proxy`, head `d43e472bb265a7314e59bb3109bcdddbab650e18`. It adds zero-argument `fabric_operational_snapshot`, calls only Fabric's fixed `operational_snapshot` tool, validates exact `runner.fabric/operational-snapshot/v1` shape, count relationships, capacities, ages and read-only flags, and reuses bounded/private-detail validation. Runner MCP does not reconstruct relay/Fabric truth. Commit attribution is green and Runner MCP validation is still in progress. Do not merge before Runner-Fabric #876 is green/merged and #286 validation is terminal green.

## 2026-10-04 — #108 is now a one-command local qualification drill

Runner MCP #262 is merged as `ba35f70eb9e3e489fc6936d2bc2f0fc425710c81` and the managed runtime has self-updated to that exact commit with no restart or install-recovery state pending.

New local-only command: `runner-mcp self-update-recovery-qualify <exact-current-main-commit>`. It is deliberately absent from MCP/mailbox/Agent Bus. It performs the normal exact-main validation and target wheel install, then interrupts at the deterministic post-install/pre-verification boundary so the real persisted recovery transaction remains. Ordinary self-update must then fail closed. Recovery still requires the operator emergency stop plus the existing local `runner-mcp self-update-recovery` confirmation path.

Important coordination: Runner MCP #260 also landed in parallel and the live runtime already consumed that automatic-Fabric-bundle compatibility change before #262. No managed Fabric runtime update is active.

Immediate resume:
1. read current Runner MCP main after the coordination commits and use that exact SHA as the qualifier target;
2. perform the local qualifier on the qualified service-user host;
3. from the first-party client verify `install_recovery_pending=true` and normal self-update overlap refusal;
4. locally activate emergency stop and run recovery;
5. verify exact baseline restoration and clear state;
6. self-update normally back to exact main and close #108 with scrubbed evidence.

## 2026-10-04 — Runner MCP live on exact-main guard; next session must refresh tool schemas

Runner MCP PR #258 is merged and the managed runtime successfully self-updated to exact code commit `82e4b0f133bae3a709bb29a89a9be2d98122aef9`. Live restart convergence is clean: `self_update_ready=true`, `restart_pending=false`, `pending_restart_count=0`, and no install recovery is pending. Issue #246 is also closed after the orphan-marker acceptance was proven live.

The important behavioral change is now active: normal self-update accepts only the exact fetched current `origin/main` tip. Stale normal targets fail closed; older verified baselines remain recovery-only.

Current-chat limitation:
The already-open first-party client cached its Runner MCP MCP schema before the managed Fabric update/host-inspection tools were added. The server code contains them, but this chat cannot call tool names that were absent from its startup catalog. Do not use Desktop Commander or generic shell as a workaround.

Immediate resume:
1. start a fresh first-party client session;
2. confirm `fabric_update`, its bounded status/rollback surface, and `fabric_host_inspect` are visible;
3. re-read Runner Fabric current `main` and its canonical bundle workflow at that time; select only an exact commit whose `control-plane-update-bundle` run succeeded, because Fabric may have advanced beyond the earlier #800 merge target;
4. run the bounded managed Fabric update and prove status/rollback readiness;
5. continue #110 first-party coarse work-unit proof, then #108 deliberate self-update recovery proof without widening authority.

## 2026-10-04 — first fully automatic managed Fabric update target ready

Runner Fabric #800 merged as exact target `ada2d6a691214959f88809f049c6dfa8f5db3c2a`. Its canonical control-plane bundle workflow now triggers automatically on every trusted `main` push, while keeping manual dispatch only as fallback.

Runner-MCP live code remains `cb7804bf0dbd10e9e343520aefb7b5df0f45ccc4` with self-update/restart state clear and bounded managed Fabric update code active.

Current-chat limitation:
This chat loaded the Runner-MCP connector schema before `fabric_update`, `fabric_update_status` and `fabric_update_rollback` were added, so those tools are not callable here even though the server runtime contains them.

Next:
Start a fresh first-party client session and invoke `fabric_update` for exact Fabric commit `ada2d6a691214959f88809f049c6dfa8f5db3c2a`; monitor with `fabric_update_status`. Do not use Desktop Commander/local shell merely to bypass stale client schema.

## 2026-10-04 — Runner MCP self-update and managed Fabric update are live

Live Runner MCP is now `cb7804bf0dbd10e9e343520aefb7b5df0f45ccc4` and fully converged:
- `self_update_ready=true`;
- `restart_pending=false`;
- `pending_restart_count=0`;
- `install_recovery_pending=false`;
- `fabric_update_active=false`.

Merged milestones:
- #252 fixes stale optional restart markers;
- #255 fixes public-resource/local-bind restart inference;
- #256 closes #251 and adds exact managed Runner Fabric update/status/rollback.

Important client note:
- the current chat/client tool schema was loaded before #256, so the new `fabric_update`, `fabric_update_status`, and `fabric_update_rollback` tools may require a fresh first-party client session to appear;
- do not fall back to Desktop Commander or generic shell merely because this already-open session cannot see the newly added schema.

Immediate resume:
1. reconcile Runner Fabric current `main` and its control-plane update artifact availability;
2. eliminate any remaining manual `workflow_dispatch` dependency if necessary using a bounded canonical workflow change;
3. open a fresh client session, verify the new update tools, then upgrade the managed Runner Fabric runtime by exact commit;
4. continue I5/#110 remote-control-retirement proof with bounded host inspection/work-units.

## 2026-10-03 — First-party client path replaces routine broad remote control

Canonical code base before this slice: `1196630299387d2f254629941790ee9b9cd70dca`.

Current direction:
- the canonical `aifordable-runner` service-user Agent Bus restart/replay acceptance is complete;
- Runner Fabric #479 is closed; GitHub-denied bounded work-unit execution, durable replay/fencing and convergence evidence no longer block the Runner MCP bridge;
- Agent Bus is the primary runtime control path; GitHub mailbox/direct GitHub choreography are fallback/bootstrap paths;
- broad remote-host tooling such as Desktop Commander is break-glass only and must not be the normal development path;
- Runner MCP already exposes exactly three configured coarse Fabric tools: `fabric_run_work_unit`, `fabric_get_work_unit`, and `fabric_cancel_work_unit`; do not add another bridge or a generic remote shell.

Issue #240 / PR #241 add the missing first-party client packaging layer:
- local ChatGPT/Codex plugin packages reuse the existing Runner MCP MCP server;
- registered-app mode stores only a validated technical app identifier;
- HTTP/self-hosted mode stores only a validated MCP URL plus bearer-token environment-variable name, never the token value;
- generated packages are private by default and contain a bounded skill that directs agents to coarse Fabric work-units and treats broad host tooling as break-glass.

Remaining #110 acceptance is now narrow: prove one real first-party client invocation through
`client -> Runner MCP fabric_run_work_unit -> private Fabric MCP -> work-unit service`, then record bounded get/cancel/operator-safety evidence and the coarse-call reduction. No new execution authority is justified.

Next:
1. land #241 only after exact-head attribution and full Runner MCP validation are green;
2. connect/register the private Runner MCP MCP server in an eligible first-party ChatGPT/Codex environment without weakening local-first/private connectivity;
3. start a fresh client session so plugin tools reload, run one bounded Fabric work-unit, and reconcile #110;
4. resume #108 recovery proof on the now-qualified replacement host after the first-party control path is usable.

## 2026-10-03 — Self-update succeeded; watcher restart activation is the only immediate Runner MCP gate

Live replacement-host facts supplied from the completed bounded self-update:
- installed runtime-code commit is `9dc9d2bfa09b25deff7a5186b9f12252c84cdd52`;
- successful self-update job: `c6602347fe0646ffa9e20a0f638a2967`;
- runtime status is operational; emergency stop inactive; install recovery clear;
- doctor reports 0 failures / 0 warnings;
- Agent Bus convergence is `clear` with 0 pending results;
- `last_installed_commit` is the exact target and `install_recovery_pending=false`;
- only restart activation remains: `restart_pending=true`, `pending_restart_count=2`;
- exact remaining markers are `github-watcher=9dc9d2bf...` and `completion-watcher=9dc9d2bf...`; server marker is already clear.

Source-supported restart path was re-verified on current main:
- long-running GitHub watcher calls `run_restart_if_requested(config_dir, "github-watcher", ...)` after each cycle;
- long-running completion watcher calls the same bounded helper for `completion-watcher` after each notification cycle;
- the helper validates the marker, removes it, and re-execs the fixed Runner MCP component; if re-exec fails it restores the exact marker instead of silently consuming it;
- therefore do not manually delete restart marker files and do not repeat the completed self-update proof.

Immediate live sequence:
1. start/resume the dedicated service-user `github-watcher run` and `completion-watcher run` paths long enough for each to reach its normal restart check;
2. verify only that `restart_pending=false` and `pending_restart_count=0`;
3. proceed directly to Runner Fabric #590 isolated Agent Bus qualification with GitHub/source-control credentials absent and fixed GitHub HTTPS probes denied;
4. prove one real worker restart, durable result replay without duplicate execution, and convergence back to clear;
5. only then qualify the separate GitHub fallback identity/pool, independent drain/disable, and persistent activation.

Current external limitation of this coordination session: the replacement host is not reachable from the available remote-management device, so no live marker mutation/restart was attempted from an untrusted or guessed path.

## 2026-10-02 — Live update paths proven; remaining gates narrowed

- Current reviewed Runner MCP main checkpoint: `61da54c38b150ac1c04bd4b78da47833cf72260c`.
- Runner MCP was updated on the controlled host through the existing bounded mailbox `self_update` action to exact main `61da54c…`. The job completed successfully and the installed runtime now reports 0.1.3 with install recovery clear.
- Re-submitting the exact same commit completed as a safe no-op with `restart_required=false`; this closes that live acceptance item in #108.
- The new local `autostart preflight` is available and fails closed as `runtime_smoke_failed`. Persistent autostart/Agent-Bus activation remains blocked by #198; no force/repair/reinstall loop was used.
- The remaining destructive #108 activation/package-interruption recovery drill is deliberately deferred to a stable replacement host so product recovery evidence is not mixed with the known unstable hardware/runtime substrate.
- Runner Fabric was updated through its reviewed exact-wheel side-by-side slot path to exact Fabric main `a8cb6835d33269bfb96ea3d8e40bc505f91b107b`. Live apply, explicit rollback to the prior runtime and re-apply all succeeded while `runner-fabric doctor` remained foundation OK with mutation capabilities disabled.
- The live Fabric CLI now exposes `agent-serve-qualification`, and the existing private Runner MCP Agent Bus config was migrated with the fixed loopback Agent-MCP bridge binding without exposing/replacing the relay credential.
- Fabric #545/#549 are complete. The old “live Fabric runtime too old” blocker is gone.
- #110/#125/Fabric #479 are now blocked only on a legitimate authenticated AIfordable Control Center submission of the fixed synthetic `fabric_run_work_unit`, followed by one-shot replay/fencing proof. Do not write relay queue/storage directly and do not reconstruct a control credential on the runner.
- No additional prerequisite-safe Runner-MCP code lane is justified. Continue only with bounded operator/live proof, replacement-host qualification, or optional external discovery.

## 2026-10-02 — Live runner readiness narrowed to controlled runtime update

- Current reviewed Runner MCP main checkpoint before this coordination update: `2732308ee0d6e74ba7bc63f9df8ee287f2787eac`.
- The bounded live runner is reachable again; the previous remote-connector quota is no longer the blocker.
- Local Runner MCP status reports operational mode, emergency stop inactive and self-update install recovery clear; `doctor` reports no failures and no warnings.
- Agent Bus configuration is present, but the installed Runner MCP runtime still reports 0.1.2. The newer read-only `autostart preflight` command is therefore not yet available on that installed runtime; no autostart activation was attempted.
- The deployed Runner Fabric CLI does not yet expose merged `agent-serve-qualification` from Fabric #482/#483. Normal `agent-serve` remains RESERVED and was not started.
- Fabric's security foundation already includes terminal replay without re-execution (#403), identity rotation/revocation (#418), split-brain fencing (#420) and primary operation with fallback disabled (#445).
- The remaining #110/#125 live gate is therefore operational: update the live Runner MCP/Fabric runtimes through their existing bounded control paths, then run Fabric #479's synthetic GitHub-denied work-unit/replay/fencing drill.
- #108 likewise remains open because this chat does not expose the bounded self-update dispatch action. Do not substitute manual pip/curl/package/source mutation for that missing control-plane action.
- Secondary discovery work under #101 remains optional and external; PR #222 made this independence rule mandatory in bootstrap/docs.

## 2026-10-02 — Task 69 self-update hardening integrated

- Current reviewed Runner MCP main checkpoint: `4b5351de6e03ab8938ebb799e2847e2195e8ee3a`.
- Issue #217 is COMPLETE via PR #219.
- Exact-head attribution #285 and validation #790 are green, including Ruff/pytest, built release artifact and clean five-minute demo.
- Autostart CLI tests no longer observe real systemd/cron state or the host's runtime-smoke result.
- Pre-install self-update failures now restore the clean source checkout to the starting/installed main commit before any install transaction becomes authoritative.
- A successful source rollback preserves the original bounded failure category; source rollback failure becomes `source_recovery_required`.
- If an install transaction was persisted or became unreadable, install-recovery remains authoritative and artifacts are preserved; post-install recovery behavior is unchanged.
- The remaining Runner MCP lanes are not safe autonomous code work: #108 is a private-host proof, #198 waits on replacement-host/CPU qualification, and #110/#125 depend on Fabric #479 plus live Agent-Bus proof. #101 is external/public discovery follow-up.
- Do not reactivate the unreliable i9 host or duplicate Fabric durability/live-proof work from Runner MCP.

## 2026-10-02 — Fabric live-cutover dependency reconciled

- Runner Fabric was reconciled against current main after the 0.1.3 release.
- The former #256/#264 checkpoint is obsolete: coarse work-unit service/MCP, reserved loopback runtime and durable journal substrate are integrated through Fabric #258/#266/#355/#357, with Agent-Bus work-unit bridging also present.
- Fabric issue #479 now owns the remaining live bounded work-unit qualification with GitHub credentials/network denied, including exactly-once replay/restart/fencing evidence.
- Current Fabric `AgentWorkUnitService` still keeps active request/result ownership in its in-memory `_records` map and does not consume `FilesystemWorkUnitJournal`; do not infer service-level restart durability merely because the journal substrate exists.
- Fabric #486 adds concrete source-write adapters but explicitly does not activate live work-unit execution.
- Runner MCP #110 has been updated to this checkpoint. Task 58 remains blocked on the private-host qualification plus the live Fabric proof; no duplicate Runner-MCP implementation is justified.

## 2026-10-02 — Runner MCP 0.1.3 published

- Task 68 is COMPLETE.
- Protected workflow run `36962568072` ran against exact main `0aa013c279128e22fbd53be32c35bced3ae26834`.
- Final version-metadata verification, full release check, wheel/sdist build and immutable workflow artifact all passed before publication.
- PyPI publication via OIDC passed and the workflow confirmed exact version `0.1.3` became visible before continuing.
- Official MCP Registry publication passed using the pinned publisher and GitHub OIDC.
- GitHub pre-release `v0.1.3` was created with wheel and sdist assets; the tag resolves exactly to `0aa013c279128e22fbd53be32c35bced3ae26834`, matching current main at release time.
- Do not rerun publication or move `v0.1.3`. Subsequent work starts from post-release hardening/live-proof lanes (#198, #108, #110/#125) or a new bounded task.

## 2026-10-01 — Runner MCP 0.1.3 release candidate integrated

- Current reviewed main checkpoint: `ee6ab95bec9be4d8d2f7b75854e1b2a17503da76`.
- Task 67 is COMPLETE via PR #208.
- Candidate version metadata is synchronized at `0.1.3` across `pyproject.toml`, `server.json`, `src/runner_mcp/__init__.py`, `glama.json` and the publish-workflow default.
- CHANGELOG now separates already-published 0.1.1/0.1.2 history from the current unreleased 0.1.3 delta.
- `docs/RELEASE_NOTES_0.1.3.md` records security-relevant changes, unchanged dependency contract, upgrade notes and known activation limits.
- Exact candidate head `6e5f7ddb28c8d9dfe1a1cabe5a7f1153a854c5f9`: attribution #265 green; Runner MCP validation #772 green; built release artifact green; Clean Ubuntu installer proof #5 green.
- The first clean-demo attempt hit an external `files.pythonhosted.org` pip read timeout. The failed job was rerun on the exact same candidate SHA and passed; no product-code workaround was introduced.
- No tag, PyPI upload, MCP Registry publication or GitHub release has been performed.
- Publication is a separate release action and must use the exact green main revision after a final release check.

## 2026-10-01 — Task 64 integrated; Fabric activation blocker narrowed

- Runner MCP current reviewed main checkpoint: `f666876ac3096fdd6663b368b2f1fe4ecbbed279`.
- Task 64 is COMPLETE via PR #202. The shared local autostart gate now requires emergency-stop/recovery/restart clear state, fresh fixed runtime smoke and `host_integrity_clear` before systemd or cron mutation.
- Direct systemd/cron installer entry points independently reject a missing/non-clear activation permit before touching unit files, systemctl or crontab.
- Exact-head PR #202 attribution #253 and validation #761 are green, including Ruff/pytest, built release artifact and clean five-minute demo.
- Stale overlapping PRs #199 and #201 are closed as superseded.
- Runner Fabric reconciliation: #357 durable journal, #355 loopback agent runtime and #383 Agent-Bus work-unit bridge are merged. However `AgentWorkUnitService` on current Fabric main still keeps work-unit ownership/result state only in its in-memory `_records` map and does not consume the durable `FilesystemWorkUnitJournal`.
- Therefore Runner MCP issue #110 remains blocked on upstream Fabric durable service/resume integration plus private-host qualification (#198); do not activate the coarse bridge yet.
- No new Runner-MCP code lane should duplicate Fabric durability work. Continue with public/documentation or live/operator work only when its prerequisites are available.

## 2026-09-30 — Tasks 50–52 reconciled

- Current reviewed main checkpoint: `0bade0af6ee574b09de42bb493f5ecffa41657d5`.
- Task 50 is COMPLETE via PR #149 / `469138077066b7b924ba867456ad44dc6372c85d`; issue #143 closed.
- Issue #151 is COMPLETE via PR #152 / `0bade0af6ee574b09de42bb493f5ecffa41657d5`; exact-head #669/#157 and post-merge #671/#159 are green; issue closed.
- Task 51 review is COMPLETE: keep service-journal output local-only. Generic redaction cannot prove arbitrary application/customer/personal data safe for remote disclosure. No remote log action is authorized.
- Task 52 review is COMPLETE: PR #150 provides a bounded Fabric bootstrap foundation, but #144 remains open because three explicit guards are still missing.
- Task 53 must add: self-update/restart/recovery exclusion; fixed installed-runtime preflight; different-installed-commit first-install conflict before subprocess.
- PR #153 refreshes unique PR #127 relay-core work; do not duplicate it. Task 54 owns integration/closure.
- PR #129 remains unique primary watcher work; Task 55 owns reconciliation after Task 54.

Immediate resume order:
1. integrate this review/coordination PR after exact-head CI;
2. implement Task 53 and close #144 only after exact-head + post-merge proof;
3. reconcile #153 and close #127 only after #153 is integrated;
4. then reconcile #129 against the new main;
5. keep remote service logs deferred.

## 2026-09-29 — Tasks 47 and 49 integrated; bounded queue refilled

- Runner MCP `main` checkpoint: `67954dea2117cce3a1819132f6d3c7480dd34c82`.
- Task 47 is COMPLETE via PR #145 / merge `67954dea2117cce3a1819132f6d3c7480dd34c82`.
  - local/private only: `runner-mcp service-log PROJECT ALIAS --lines N`;
  - per-service `allow_log_read: false` opt-in;
  - fixed no-symlink `journalctl`, fixed argv/env, 1–100 entries, <=10s, <=32 KiB retained stdout;
  - Task-41 redaction receives known local runtime secrets/private paths plus private unit/health URL;
  - disabled/unknown service fails before subprocess;
  - read remains available during emergency stop;
  - no MCP, bridge, mailbox or Agent-Bus log action exists.
  - exact-head validation #654 + attribution #140 and post-merge validation #655 + attribution #142 are green.
- Task 49 is COMPLETE via PR #124 / merge `da367081f88d6d2342cf938a9b67ec59d9d10de0`.
  - explicit additive async migration start/status exists;
  - `migration_async` approval is distinct from synchronous `migration`;
  - synchronous `apply_migrations` and deployment-triggered migrations remain unchanged;
  - exact-head validation #622 and post-merge validation #623 are green.
- Task 50 is the next small CODE lane: close the remaining issue #143 gap by preflighting installed-runtime `pip` + `setuptools.build_meta` before wheel-stage mutation.
- Task 51 is review-only: decide whether any remote service-journal disclosure is justified after Task 47; do not add remote log authority during the review.
- Task 52 is review-only: define the first-install Runner Fabric bootstrap safety boundary for issue #144 before any bootstrap mutation/tool is implemented.
- PR #127 and PR #129 remain open and contain unique Agent-Bus work. Do not duplicate or close them merely because #131/#132/#134 later merged; reconcile/rebase those PRs separately.
- Issue #130 remains open because its live activation proof is broader than the merged lifecycle code.
- Issue #143 remains open until Task 50 production preflight is integrated.
- Issue #144 remains open and high risk; Task 52 review comes first.

Immediate resume order:
1. integrate this coordination update after exact-head CI;
2. implement Task 50 as the next bounded CODE lane;
3. Task 51 and Task 52 can proceed as independent reviews if code work blocks;
4. do not duplicate PR #127/#129 Agent-Bus work;
5. keep remote service logs, generic package install, arbitrary VCS/package/shell authority and production mutation out of scope.

## 2026-09-28 — Task 44 integrated; Task 45 async migration boundary decided

- Runner MCP `main` checkpoint before this review branch: `6053b7c3d5aef757055c453d2fd5b7f581248e53`.
- Task 44 is COMPLETE via PR #118 / merge `6053b7c3d5aef757055c453d2fd5b7f581248e53`.
- Task 44 evidence is fully green: exact-head validation #607 + attribution #91 and post-merge validation #609 + attribution #94; full pytest, Registry/whitespace, release artifact and clean demo are green.
- The durable migration substrate is additive only: private strict migration-job storage, queued/running/terminal state, restart -> interrupted without replay, canonical plan revalidation, bounded public status and read-only `MIGRATION_JOB` completion delivery. Existing synchronous `apply_migrations`, direct `migration_status`, bridge `APPLY_MIGRATIONS` and deployment-triggered migrations remain unchanged.
- Task 45 review is COMPLETE in `claude_feedback/TASK45_ASYNC_MIGRATION_INTEGRATION_REVIEW.md`.
- Task 45 decision: do not version or silently change synchronous `apply_migrations`. If async remote execution is integrated, add explicit `start_migration_job` + `migration_job_status` tools / bridge actions.
- Async execution must use a separate human approval operation `migration_async`, with a fixed async execution discriminator in the approval binding, so sync and async approvals are not interchangeable.
- Required start ordering: require configured runner -> recompute canonical migration state -> consume async approval -> durable queued persistence -> worker start. A consumed approval with no job is safer than durable execution intent without consumed approval.
- Bridge persistence/finalize ambiguity after a job starts must never replay/enqueue a second job. Immediate start result means durable acceptance/queueing, not migration completion.
- Task 49 is the bounded CODE follow-up. It must not add cancellation, automatic retry/resume, arbitrary SQL/executable/cwd, production mutation, automatic restore, generic async execution, job listing or change the current synchronous path.
- Task 47 local bounded service-journal reader remains independently prerequisite-safe.
- PR #120 package-version identity fix is separate from this review; it is being revalidated against the Task-44 main before merge.
- Issues #108/#110/#101 retain their existing external/upstream gates.

Immediate resume order:
1. integrate this Task-45 review after exact-head CI;
2. Task 49 may implement only the explicit additive async migration start/status contract;
3. Task 47 remains a separate safe local-only lane and may proceed independently;
4. preserve synchronous `apply_migrations` until/unless Task 49 is separately green and integrated;
5. do not infer completion from bridge/audit records; terminal migration completion comes only from durable migration-job metadata.

## 2026-09-28 — Tasks 48 and 43 complete; migration-job substrate next

- Runner MCP `main` is `a95e75739bb71bcbaf653244e0ebf9c9bee7b0ee`.
- Task 48 is COMPLETE via PR #115 / merge `02475b4c5aa1f103b55f9e4ca6a71e0d09892c7c`: deploy/rollback now share one fixed private release-root `fcntl.flock` boundary in addition to the existing in-process thread lock. Exact-head and post-merge validation are green.
- Task 43 is COMPLETE via PR #116 / merge `a95e75739bb71bcbaf653244e0ebf9c9bee7b0ee`: local-only `retention prune-plan` / `retention prune-release` can remove exactly one freshly eligible staging orphan release per short-lived single-use plan after fresh current/metadata/policy revalidation under the shared release lock.
- Task 43 preserves the retained rollback/reference closure and migration boundaries, never deletes backups, never adds automatic pruning, and adds no MCP/mailbox/bridge deletion authority.
- Quarantine/transaction state is private and durable; post-quarantine failure is reported as manual-attention state rather than guessed success or replay.
- Exact-head Task 43 validation #592, attribution #76, build artifact and clean demo are green; post-merge validation #593 and attribution #77 are green.
- Task 44 durable migration-job substrate is now the preferred next independent CODE lane. Its scope remains additive: persisted migration jobs + read-only completion source only; existing synchronous MCP/bridge `apply_migrations` and deployment-triggered migrations remain unchanged.
- Task 47 local bounded service-journal reader remains independently prerequisite-safe.
- Issue #108 remains externally blocked by the authorized private-host connector quota. Issue #110 remains gated on upstream Fabric durable gateway/startup readiness. Issue #101 remains externally gated for actual secondary-directory submissions/claims.

Immediate resume order:
1. integrate this coordination-only status update after exact-head CI;
2. implement Task 44 from its Task 42 review with a separate private migration-jobs root and strict restart-no-replay semantics;
3. after Task 44 integration, perform Task 45 review before any remote async migration contract change;
4. Task 47 may proceed independently if Task 44 blocks;
5. keep backup pruning, automatic pruning, restore execution and all remote deletion authority deferred.

## 2026-09-27 — Task 46 reconciled; Task 48 release-lock prerequisite queued

- Live Runner MCP `main` before this coordination branch: `37c78fd0d2a0e2f620dc225f81e72843413ef3c3`; PR #113 discovery hardening is merged and post-merge validation #582 / attribution #66 are green.
- The previously unintegrated Task 46 review was reconciled against current `DeploymentManager`. Its core finding still holds: deploy/rollback use only per-process `threading.Lock` instances, so a future local CLI pruning process cannot safely share that mutation boundary.
- Task 46 is therefore COMPLETE as a review and its canonical deliverable is `claude_feedback/TASK46_CROSS_PROCESS_RELEASE_LOCK_REVIEW.md`.
- Task 48 is the separate prerequisite-safe CODE follow-up: add one private release-root `fcntl.flock` primitive and integrate it into deploy/rollback while preserving the existing thread lock and release -> database lock ordering.
- Task 43 local one-release pruning remains BLOCKED until Task 48 is integrated and proven. Do not implement pruning inside Task 48.
- Task 44 durable migration-job substrate and Task 47 local bounded service-journal reader remain independent prerequisite-safe CODE lanes.
- Issue #108 private-host recovery proof remains externally blocked by the authorized remote-management connector quota; do not bypass it with broader authority.
- Issue #110 Fabric bridge activation remains upstream-blocked. Latest checkpoint: Fabric #258 and #266 are merged/green; #256 and #264 remain open on failing/non-mergeable heads; #268 remains open.
- Issue #101 secondary discovery remains externally gated for actual directory submissions/claims; canonical discovery metadata is now hardened on main and the official MCP Registry publicly indexes v0.1.2.

Immediate resume order:
1. integrate this coordination-only Task 46 review after exact-head CI;
2. implement Task 48 as its own bounded code PR with multi-process/adversarial lock tests;
3. only after Task 48, reconsider Task 43 pruning;
4. Task 44 or Task 47 may proceed independently if Task 48 becomes blocked;
5. keep #108/#110/#101 external gates honest; do not convert preparation into claimed proof/publication.

## 2026-09-27 — Runner Fabric coarse bridge transport merged

- Runner MCP transport integration is merged on `main` as `3ebd39981c358c307fa66afa32ad2f5fc32731cf` via PR #111; issue #109 closed automatically as completed.
- Exact PR head `872798831403515bc6944b62efaac5992897b253` passed Runner MCP validation run #571 and commit-attribution run #54 with zero review threads.
- The PR validation checked GitHub's synthetic merge `cd60179b8d8f7c5d8895beef6164a7cb932937fe`, combining #111 with then-current `main` `776b5d0fd3499ca6ed6674806b2075167fc59f9e`; current-main compatibility was therefore validated before merge.
- Post-merge commit-attribution run #55 and Runner MCP validation run #572 are both terminal green on exact merged `main` `3ebd39981c358c307fa66afa32ad2f5fc32731cf`.
- The bridge remains optional and fail-closed: without private loopback Fabric configuration, no Fabric tools are registered and normal Runner MCP behavior is unchanged.
- When configured, the only Fabric-facing tools are `fabric_run_work_unit`, `fabric_get_work_unit` and `fabric_cancel_work_unit`; no generic GitHub, Git, shell, filesystem, provider or status-polling proxy was added.
- Additional hardening on #111 gives each calling thread an independent local MCP session and fails closed on mismatched expected revision, mismatched work-unit identity, or inconsistent status/result pairs.
- Runner Fabric remains the orchestration/control-plane owner. Runner MCP only authenticates, bounds, audits and transports the coarse request/result.
- Issue #110 remains the live activation/end-to-end follow-up. Do not duplicate the merged transport work from #109/#111.
- At this checkpoint Runner Fabric prerequisites are not ready for live activation: #258 and #266 still have failing Foundation CI, #266 is not mergeable, and #268 remains open. Reconcile upstream live state before acting.

Immediate resume order:
1. confirm post-merge Runner MCP validation #572 is terminal green;
2. keep #110 blocked until the required Runner Fabric work-unit service/MCP/startup lanes are green, integrated and privately deployable;
3. once upstream is ready, configure only the private loopback bridge and prove one bounded end-to-end coarse work-unit without exposing infrastructure details;
4. benchmark the coarse handoff against the former many-call GitHub workflow without weakening existing Runner MCP approval, operator-stop or fault-containment boundaries;
5. independent open lanes remain #108 (private-host self-update recovery proof) and #101 (external discovery/authenticated submissions); do not use either to bypass their human/private-environment gates.

## 2026-09-27 — v0.1.2 published; discovery phase active

- Canonical release is now `v0.1.2` on exact commit `83175f439c60346f92b5759a90993c3b8f5352f8`.
- Publish run #2 succeeded end-to-end: PyPI `aifordable-runner-mcp==0.1.2` -> official MCP Registry `io.github.Blacksp1d3r/runner-mcp` 0.1.2 -> GitHub pre-release v0.1.2.
- The failed 0.1.1 Registry attempt was recovered by PR #103; do not reopen the lowercase Registry identity or attempt to mutate immutable PyPI 0.1.1.
- Current focus is discoverability/distribution with no runtime-authority changes: first-party links/metadata, then Glama, Smithery, mcp.so and selected developer directories.
- External directory writes that require a separate account/OAuth/browser remain human-controlled. Do not replace them with paid submission shortcuts or spammy bulk-directory tooling.

## 2026-09-26 — v0.1.1 ready for human publication gate

- PR #102 is merged; exact merge commit `d948945034e07616d673945467e9b2e44748fa10` passed post-merge validation and attribution.
- Final package identity: `aifordable-runner-mcp`; normal command remains `runner-mcp`; the package-name alias exists for `uvx`/MCP Registry launch.
- PyPI Trusted Publisher and GitHub `pypi` environment are configured with exact environment binding and no API token.
- Do not create another distribution-fix branch. The next action is the explicit human workflow dispatch/approval for 0.1.1, followed by public verification of all three publication stages.

## 2026-09-26 — PyPI pending publisher ready; package-name fix active

- Pending Trusted Publisher is configured for `aifordable-runner-mcp` with GitHub owner `Blacksp1d3r`, repository `runner-mcp`, workflow `publish.yml`, environment `pypi`.
- `runner-mcp` was rejected by PyPI as too similar to an existing project; do not retry or bypass that protection.
- Active fix branch: `release/v0.1.1-aifordable-pypi`.
- Product/CLI remain Runner MCP / `runner-mcp`; only the PyPI distribution identifier changes to `aifordable-runner-mcp`.
- The previous umbrella brand is retired from current project materials; AIfordable is the current umbrella identity.
- Next gate: exact-head CI and review on this branch -> merge -> exact-main green -> manually dispatch `Publish Runner MCP` 0.1.1 and approve the `pypi` environment deployment.

## 2026-09-26 — distribution/discovery handoff

- Runner MCP remains released at public `v0.1.0`; `v0.1.1` is being prepared on `release/v0.1.1-discovery`.
- The slice adds PyPI/MCP Registry metadata, tokenless OIDC publishing automation, metadata consistency tests and stronger first-screen/launch copy.
- Runtime/security authority is unchanged: authenticated Streamable HTTP, local private setup and deny-by-default capability boundaries remain intact.
- Do not publish 0.1.1 until branch CI is exact-head green, the change is integrated to `main`, and the one-time PyPI Trusted Publisher + GitHub `pypi` environment setup is complete.
- After those gates, run the human-triggered `Publish Runner MCP` workflow with version `0.1.1`; it publishes PyPI first, then the official MCP Registry, then creates the GitHub pre-release.
- After Registry publication is verified, proceed to secondary MCP directories and community launch posts using `docs/LAUNCH_COPY.md`.
## 2026-09-24 — v0.1.0 published; next session starts post-release

- Runner-MCP `v0.1.0` is now a published GitHub pre-release from exact validated commit `f00ac3fd03df234cb186a4dfcd804136501c0cf7`.
- PR #98 reconciled README, CHANGELOG and launch-readiness after publication and merged as `5647aa8839af90451189d2d943ce393edfacfe78`; exact-head run #514 and merged-main run #515 are fully green.
- Do not retag or move `v0.1.0`. Post-release `main` being ahead of the release tag is expected.
- First next actions: reconcile live GitHub; confirm no new blockers; verify a clean-host install from the published tag; set the prepared repository description/topics if still missing.
- Keep Task 10 private-host self-update/recovery proof as an explicit alpha limitation until actually proven.
- Runner Fabric stays separate and must not be pulled into Runner-MCP scope.

## 2026-09-24 — RELEASE-CANDIDATE RECONCILIATION CHECKPOINT

- Runner Fabric is a separate private project/repository. Keep this repository focused on Runner-MCP release work only.
- PR #97 is merged as `9ce5fe94f417e4e7f910c9945727f70cffd33ecb`; exact PR head `91e0c1b1e737ad14a43b31750cfdfbf1bf582f24` passed run `36037258558` fully green.
- Live reconciliation after the merge shows no open Runner-MCP PRs and no open Runner-MCP issues.
- Task 41 is integrated. Task 47 is now prerequisite-safe. Task 43 remains blocked on Task 46 cross-process release-mutation locking. Task 44 is prerequisite-safe; Task 45 remains blocked on Task 44.
- None of Tasks 43–47 is automatically a blocker for the first tagged alpha; the public release gate remains exact-green candidate + accurate documented limitations.
- Task 10 private-host self-update/recovery proof is still unproven. Do not claim it in release notes; preserve the limitation unless it is safely proven later.
- After this coordination commit, require exact-main green CI before any tag/release decision.
- No tag, GitHub release, package publication, repository-setting mutation, registry submission or external announcement has been performed.

# Runner MCP — Session Handoff

Last reconciled: 2026-09-24.

## Latest checkpoint — Task 34 PR #92

- PR #91 merged to main as `11b9a4d4e508ac93cd436037563c09d08cfa43ab`; Tasks 33, 35 and 38 are complete and must not be duplicated.
- Task 34 is COMPLETE on PR #92 pending final exact-head CI/integration.
- Task 34 adds only local read-only `runner-mcp retention preview PROJECT`; no pruning/deletion, approval, MCP or mailbox authority was added.
- Retention preview is fail-closed on unsafe release/backup storage and reports advisory categories only. Manual backups remain non-eligible without a dedicated retention policy.
- Actual pruning remains deferred.
- Task 37 review is independently active on PR #93; Task 39 adapter refactor is now prerequisite-safe.
- Task 10 private-host self-update/recovery proof remains externally BLOCKED; no tag/release/publication is authorized.
- Reconcile live GitHub before any next claim; exact-head CI is authoritative.

## Current checkpoint
- Live GitHub reconciled through Tasks 32 and 36 merge plus final coordination; live GitHub always wins over this recorded checkpoint.
- Tasks 21–32 and Task 36 are COMPLETE and must not be duplicated.
- Task 31 local read-only PostgreSQL restore preflight is implemented; restore execution, restore approvals, WAL/PITR, production recovery and MCP/bridge/mailbox restore authority remain deferred.
- Task 32 COMPLETE: PR #89 merged as `e629515f9c7e7a5d44506dfb82a48343870f94da`; exact head `99c72037eff4ed54cf7e92f7a08b278b48af4e45`; CI 35967246877 fully green with Ruff, whitespace, 1267 tests, built artifact and clean demo.
- Task 36 COMPLETE: PR #90 merged as `8c971016e4fc3cd821dc52d28334567c20835ff4`; exact head `1b3567b5de1f5a4ac5a67db16c609db2edac25dd`; CI 35967550375 fully green with Ruff, whitespace, 1267 tests, built artifact and clean demo.
- The six demonstrated alpha-release documentation drifts are reconciled. `0.1.0` remains explicitly unreleased; no `v0.1.0` tag or GitHub release exists at the audited checkpoint.
- Repository description/topics, v0.1.0 tag/GitHub release, package/registry/ecosystem publication and external community posts remain explicit user-controlled actions.
- Task 10 remains BLOCKED on usable private-host self-update/recovery proof. Public alpha wording must not imply that private-host live proof exists.
- Current bounded public queue: Task 33 optional graphical administration boundary review; Task 34 local read-only retention preview; Task 35 manual historical rollback selection boundary review.
- No new task is claimed at this checkpoint. Reconcile live GitHub plus `claude_feedback/CURRENT_ASSIGNMENT.md` before the next claim.
- No tag, GitHub release, package publication, deployment, rollback, migration, restore, deletion, network exposure change, repository-setting mutation or external publication has been authorized/performed in this session.
- Desktop Commander remains unavailable due the previously reached monthly limit; private-host proof remains unresolved.
- Before asking for alpha-release authorization, verify full GitHub CI is green on the exact latest `main` commit after these final coordination updates.

## Purpose
Runner MCP is a small, auditable, deny-by-default operations interface. GitHub is the code/collaboration surface; Runner MCP is the local execution and safety boundary. It must never become a generic remote shell.

## Architecture
- public project-agnostic core in this repository;
- private configuration holds real host/repository/ref/credential values;
- strict GitHub mailbox protocol for bounded remote operations;
- replay protection, safe result envelopes and restart-safe watcher coordination;
- predefined test profiles and bounded workers/queues;
- explicit operator emergency stop;
- commit-pinned self-update with staged wheels, transaction markers, activation markers and rollback/recovery controls.

## Current state
- Task 8 merged via PR #52 (`d6821ddb0773b586b6a106b66b2e18154c90cc7a`): fail-fast local release-check wrapper plus isolated clean-demo project venv.\n- Task 6 has one demonstrated docs drift queued: `runtime_doctor` is implemented but omitted from README/public bridge action documentation.\nGitHub current state wins if anything below is stale.
- `main`: `011fcbfec4e0b75a93820ca1c4c487111da6b495` at this reconciliation checkpoint.
- No open Runner-MCP pull requests at this checkpoint.
- PR #46 merged as `a50fe7eca0c74dff8aa337e431feadf55fa3e287`: installer/operator missing-sudo robustness.
- PR #47 merged as `5d2f21409723578e7b6873f31746fac1d8ada459`: secure-I/O inventory.
- PR #48 merged as `4f84a192581015e219774b8d0a40e1172124c12b`: self-update file + directory fsync durability.
- PR #49 merged as `57d9f114dcab22df434aaa051796ae036b71ebb9`: category-only safe diagnostics contract.
- PR #50 merged as `07d9a4b1041cd20e7b2201aa4a83b674a1a1c85c`: narrow REMOVE-confirmation helper.
- PR #51 merged as `011fcbfec4e0b75a93820ca1c4c487111da6b495`: current-main recovery visibility; stale PR #45 was closed unmerged.
- The last recorded private-runtime handoff said the watcher had 4 recovery-attention items and a read-only runtime probe was pending. That private state was not re-probed in this GitHub-only session and must be treated as historical until checked again.

## Important decisions
- no arbitrary shell/executable/path/environment/process/package-manager input through MCP/mailbox;
- production restore/PITR and generic transaction reset remain outside the mailbox;
- self-update targets exact lowercase commits reachable from canonical `origin/main`;
- install recovery is local operator-only and requires the emergency stop;
- GitHub live PR/issue/CI state is authoritative over stale handoff text.

## Open PRs / issues
- No open Runner-MCP pull requests at this checkpoint.
- No open Runner-MCP issues were re-established as blockers during this GitHub reconciliation.

## Blockers
- private watcher/recovery health still needs a fresh bounded probe before mailbox-driven self-update proof; the previous degraded observation is not assumed current;
- private host still needs bootstrap/proof of the newest recovery-capable self-update baseline;
- Desktop Commander is unavailable due monthly limit; prefer GitHub + bounded Runner-MCP bridge when available.

## Current assignment
1. keep Task 6 and Task 7 as normal-chat analysis/review work, not Claude Code work;
2. use ChatGPT for Task 8 implementation unless explicitly reassigned;
3. before live self-update proof, obtain a fresh bounded private-runtime watcher/recovery status;
4. bootstrap and live-prove the current recovery-capable self-update baseline only after watcher/recovery state is clean enough for safe proof.

## Next safe steps
- Task 6: documentation/CLI contract drift audit as a CHAT REVIEW; return findings only, no code.
- Task 7: dependency-set / `--no-deps` compatibility analysis as a CHAT REVIEW.
- Task 8: local release-check convenience as ChatGPT CODE work.
- independently, re-probe private watcher/recovery state before relying on mailbox-driven self-update proof;
- never reset replay/cursor/transaction state generically.

## Definition of done for a work batch
Tests/evidence must be terminal, blockers must be recorded or resolved, and this file plus `CURRENT_STATE.md` / `AGENT_EXCHANGE.md` must make the next safe action obvious.
