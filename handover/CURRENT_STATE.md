## 2026-10-20 — #669 source v0.1.53 MERGED; live correct-host attestation WAIT

Runner-MCP [PR #769](https://github.com/Blacksp1d3r/runner-mcp/pull/769) SOURCE MERGED v0.1.52 squash `6a227aa3af380e99878d3083a1ae9eb1fe0bd76d`: manager-supplied stale `self_update_ready=true` can no longer survive fail-closed projection when loaded wheel/source remain unverified. Exact-head validation #39400157473, Ubuntu #39400157458, attribution #39400157524 ALL SUCCESS; RMCP-F-0056. Official pushed artifact #12254268229 rehashed OFF-HOST (wheel SHA256 `0873f5bee3d813fadcbe62259538c96cba98863f4ed684746f973e3568be6ec0`, sdist SHA256 `8eb20b97a00472df1525b1a3086a69fa69e1a71e8481c1d0bdcb237a6f5915a9`, 123/123 RECORD, 117/117 wheel/sdist Python modules). Does NOT attest a loaded process.

Runner-MCP [PR #771](https://github.com/Blacksp1d3r/runner-mcp/pull/771) SOURCE MERGED v0.1.53 squash `6b352d89c196790e5b6bfdb73f05e786934aa4a5`: standalone receipt preflight refuses symlinked ancestors, relative and lexical `..` aliases for receipt, wheel, installed package. Nine negative tests, exact-head validation #39401119807, clean Ubuntu #39401119744, attribution #39401119762 ALL SUCCESS; RMCP-F-0057. No host mutation.

Fabric source progress independently verified: PRs #1625 (`2575d497` fixed no-follow A6 root chain), #1626 (`54f10654` existing LOCAL journal hash-chain readback), #1627 (`7ceff5ac` existing A7 baseline wheel/receipt opened-inode custody), and #1628 (`77d1054c` canonical handover) MERGED. These are **source progress, NOT physically proven independent storage or exercised disconnected rollback**. Do not duplicate Fabric's code.

Live original-client central last verified 0.1.38, installed version 0.1.38, source/wheel NULL, `self_update_ready=false`, Doctor two FAIL and A6 0/11 (legacy Doctor `pass/not_configured_0_of_11` is absence), Fabric read-only, Agent Bus relay layer UNKNOWN, dispatch/mutation disabled. No six-role replacement, tunnel, credential or disk changes.

Next real #669 deliverable: correct-host loaded interpreter/imported module to independently trusted pinned wheel/source binding for all six roles plus immutable previous-generation escrow and a one-use signed host-specific witness, consumed by the same original authenticated client. Fabric #1617/#942 must prove physically separate A6 journal and #943 independently exercised offline rollback before Fabric #924 one-node cutover, with original result/durable ACK #609. A signed OFFLINE candidate statement is not authority; don't enable self_update or OIDC/MFA from this source checkpoint.

---

## 2026-10-20 — #669 v0.1.53 standalone receipt path guard (SOURCE ONLY)

Following source-merged #769 v0.1.52 (unverified active generation always `self_update_ready=false`), the standalone offline receipt comparator still had a linked-grandparent acceptance gap even after the #767 evidence-chain guard. This new source candidate applies the same safe lexical-path constraints independently to receipt, wheel and installed-package inputs; nine regression cases cover linked ancestors, relative paths and `..` traversal. Failure Museum RMCP-F-0057, exact-head CI required. Unlike a production signer/observer, these are offline byte-check helpers only: original-client central live remains 0.1.38, source/wheel not verified, A6 0/11, self-update not ready. Fabric #1617/#942 off-target A6, #943 A7 and #924 one-target lease plus #609 original-client ACK remain separately WAIT. Six serving roles, storage, credentials and tunnels are untouched.

---

## 2026-10-20 — #669 false-green self-update readiness guard, v0.1.52 SOURCE ONLY

Fresh source main 0.1.51 and original first-party central runtime 0.1.38 remain separate. Source audit found `fail_closed_runtime_provenance()` suppressed stale active revision and wheel digest but could still inherit `self_update_ready=True` from historical self-update status, even though `active_build_provenance_verified=False`. v0.1.52 candidate explicitly refuses that conflicting release authority, including malformed manager readiness, before exposing `runtime_status`. It preserves transaction history without making it active identity and tests in-memory loaded-version vs newer dist-info; Failure Museum RMCP-F-0056. No host restart, source promotion, disk/credential alteration, paid model call or OIDC/MFA work. Exact-head CI required before source merge.

Missing original-client physical proof still under Runner-MCP #669: operator-trusted correct-host loaded process/wheel and complete six-role escrow; Fabric #1617/#942 independently off-target A6, #943 A7 offline rollback and AIfordable #609 original requester ACK; Fabric #924 owns one-target rollout. A source fix alone does not install onto live 0.1.38.

---

## 2026-10-20 — #669 offline source v0.1.51 MERGED / correct-host LIVE WAIT

- [PR #766](https://github.com/Blacksp1d3r/runner-mcp/pull/766) SOURCE MERGED v0.1.50, squash `b1300b57b114c0970deb35c565b3fb5fe16ef5cd`, exact head `2bd545b8ef88db1f10df95d7b7526bf15ca0c520`, CI validation #39390108398, Ubuntu #39390108426 and attribution #39390108361 ALL PASS. Installed-RECORD offline comparator only permits known pip CLI/metadata extras, refuses unapproved/duplicate/malformed exterior records; RMCP-F-0054.
- [PR #767](https://github.com/Blacksp1d3r/runner-mcp/pull/767) SOURCE MERGED v0.1.51, squash `8104f244085adc68b8b705e9f7ec7a38dd69b2be`, exact head `bc11541c4eb2870f9203dbf5f23651c941d64b6d`, CI validation #39390980634, Ubuntu #39390980640 and attribution #39390980656 ALL PASS. Offline evidence chain refuses lexical `..`, relative inputs and symlinked lexical ancestors on all five files; RMCP-F-0055.
- Original authenticated central Runner-MCP remains **0.1.38** installed and loaded with source/wheel NULL, active provenance false, `self_update_ready=false`, Doctor two FAIL; A6 0/11 is safe absence (historical 0.1.38 Doctor PASS != A6 qualified). Fabric bridge READY read-only, A6 prepare false, mutation/execution false, Agent Bus relay evidence UNKNOWN. No serving host/roles, relay, credentials, storage or worker changes in these source merges.
- Remaining actual proof: operator-trusted correct-host six-role loaded module + wheel / source + rollback escrow witness #669; Fabric independently off-target journal #1617/#942, offline independent A7 #943, exact same-original-client terminal ACK #609. Fabric #924 guards first node. No direct self_update and no OIDC/MFA deflection. Source CI/offline hash evidence is NOT the loaded server identity.

---

## 2026-10-20 — #669 v0.1.51 offline evidence canonical input guard (SOURCE ONLY)

Following SOURCE MERGED v0.1.50 #766, a separate bounded source child tightens the offline evidence chain's path semantics: all five candidate paths must be absolute, free of lexical `..` and have no symlinked lexical ancestors. A path alias cannot be construed as independently observed installed generation. Negative regressions exercise each of five linked-grandparent inputs, relative paths and inside-generation parent traversal. Failure Museum RMCP-F-0055. The result remains OFFLINE ONLY even for an exact match, with active source/wheel intentionally NULL. Correct-host loaded/process signer proof #669, Fabric off-target A6 #1617/#942, independent A7 #943 and original-client ACK #609 remain operationally WAIT. The central six roles on 0.1.38 are not changed.

---

## 2026-10-20 — #669 v0.1.50 offline RECORD extra-entry hardening (SOURCE ONLY)

Main v0.1.49, central original-client serving 0.1.38 with active source/wheel unknown and `self_update_ready=false`. Candidate source v0.1.50 tightens a narrow `offline_installed_record_preflight` consistency gap: previously any outside-package installed RECORD addition was ignored; bounded policy permits only known pip CLI/script and standard metadata extras, refuses foreign/traversal/duplicate entries and malformed optional hashes. A wheel/installed-RECORD match remains OFFLINE ONLY; no current-process/loaded-module attestation, host signer, original client ACK or A6/A7 recovery authority. Regression tests, Failure Museum RMCP-F-0054, exact-head CI and clean Ubuntu installer required. This does not authorize changing the six active services or creating another tunnel/update plane.

---

## 2026-10-20 — A6 source 0.1.49 MERGED / live WAIT

Runner-MCP #763 SOURCE MERGED v0.1.48, squash c5f88102f3d36ad0ffb968215594d9daf19f5328; PR exact-head validation 39380236274, clean Ubuntu 39380236331 and attribution 39380236370 ALL SUCCESS. Private A6 state/config paths reject linked ancestors and lexical traversal; RMCP-F-0052.

Runner-MCP #764 SOURCE MERGED v0.1.49, squash 585890997c6ec11147ef3b7d28101e0072f8d238; PR exact-head validation 39381025511, clean Ubuntu 39381025486 and attribution 39381025450 ALL SUCCESS. Full 11/11 A6 binding count with wrong fixed values no longer yields a PASS; RMCP-F-0053. Correct private configuration is not independent physical off-target A6 admission.

Original connected central Runner-MCP still 0.1.38, serving source/wheel null, self_update_ready=false, Doctor two FAIL, A6 0/11 and Agent Bus relay UNKNOWN. Six roles, hosts, worker processes, relay, credentials and disks unchanged. Missing correct-host signer/loaded wheel #669, Fabric independent off-target A6 #1617/#942, offline A7 #943 and same-client durable ACK #609; Fabric #924 alone guards first node. No OIDC/MFA or second update plane.

---
## 2026-10-20 — #509 A6 all-eleven binding value consistency (0.1.49 SOURCE ONLY)

Follow-up after SOURCE MERGED v0.1.48 linked-ancestor guard. Candidate v0.1.49 closes a second source-level false-green: previously `binding_count==11` and ready A6 roots were enough for Doctor `pass/ready_11_of_11`, including stale Fabric revisions or foreign fixed journal/probe values. New bounded private inspection checks exact sanctioned endpoint/roots/storage domains, probe ID/target/interval, matching 40-hex Fabric revisions and valid private bearer format. Full count with incorrect values or missing private evidence directory now returns NOT COMPLETE and `warn/unavailable`. No raw secret output, no credential edit or new runtime tool. Synthetic tests cover all eleven wrong fixed values, missing root and valid repaired config. Failure Museum RMCP-F-0053.

This is only SOURCE-LEVEL CONFIG CONSISTENCY, not independent physically off-target journal or live operation. Connected central runtime still 0.1.38 with A6 0/11 and `self_update_ready=false`. Fabric #1617/#942, #943, Runner-MCP #669 and same original-client ACK #609 must qualify independently before Fabric #924 can authorize one-node cutover. No host mutation and no OIDC/MFA reintroduction.

---

## 2026-10-20 — #509/#669 ancestor symlink private A6 qualification guard (0.1.48 SOURCE ONLY)

Source review found a previously uncovered synthetic redirection case: the fixed A6 state root and fixed private config directory were each resolved after verifying only their final lexical path was not a symlink. A symlink in a *parent* could still redirect private reads/updates to another tree. This is a SOURCE-OBSERVED security boundary, not evidence of a live exploit. Candidate source v0.1.48 rejects linked ancestors, relative paths and lexical ".." before resolving both paths and exercising existing fixed A6 key repair; tests verify no private config or environment writes under redirects. Failure Museum RMCP-F-0052, with distinct issue owner #509 and serving-trust dependency #669.

Physical acceptance remains unchanged: original central runtime v0.1.38, wheel/process current trust unverified, A6 0/11, self_update_ready=false, Fabric independent journal (#1617/#942), A7 offline rollback (#943) and exact original-client ACK (#609) are still WAIT. This code must pass exact-head CI and is NOT installed on the central host. No OIDC/MFA, second relay/update system, arbitrary filesystem tool or host action.

---

## 2026-10-20 — A6 source 0.1.47 and six-role witness tests MERGED / live WAIT

Runner-MCP PR [#760](https://github.com/Blacksp1d3r/runner-mcp/pull/760) SOURCE MERGED squash `0f3fa078e97458c8ae3982ec71251422b2e10151`, v0.1.47, exact tested head `11cf153ad19325113c947e0b3115fa2920172556`; validation #39371276604, clean Ubuntu #39371276607 and attribution #39371276627 ALL SUCCESS. `runtime_doctor.fabric_a6_binding_state` now reports `warn/not_configured_0_of_11` for both private roots and all keys intentionally absent, instead of prior misleading PASS. Structural binding READY is NOT off-target A6 journal readiness. No live install, restart, folder or token mutation.

Runner-MCP PR [#761](https://github.com/Blacksp1d3r/runner-mcp/pull/761) TEST-ONLY MERGED squash `f7c37c53197f6c06207c646db3af41e0b0454858`, exact tested head `abe615d89b997641859bc83f3a3a0898f0b9c615`; validation #39371812361 and attribution #39371812310 SUCCESS. Synthetic six-role signed witness parity and eleven wrong/missing/duplicated/stale role, host, nonce and expiry negative regressions remain `active_build_provenance_verified=false`. No operational worker role names asserted, no runtime tool change or shipping-version bump.

The v0.1.47 pushed source artifact is independently checked OFF-HOST only: GitHub Actions #39371598373 candidate SHA wheel `d0dd841c9da39d9d85c26221c207c488fe091aaf22dd459caedaa0767fb9bef6`, sdist `258e2cc5c99cecb9616f0e3a1d6b6275473882fed4db8f7f34a6b336f2ff3c69`, 123/123 RECORD file checks, 117/117 package module equality; no loaded-process/signer/restore proof. Current original first-party LIVE central Runner-MCP remains 0.1.38, source/wheel NULL, `self_update_ready=false`, A6 0/11 live historical PASS/no readiness, Fabric Agent Bus relay UNKNOWN; six roles untouched. Next real accepted operator proofs: #669 correct-host generation+witness, Fabric #1617/#942 independently off-target A6 and #943 A7 offline rollback, AIfordable #609 exact same-original-client terminal ACK. Fabric #924 alone may later admit one guarded target. GitHub required admission branch policy #757 remains independent.

---

## 2026-10-20 — #669 six-role signed witness negative regression (TEST ONLY)

Following Runner-MCP [#760](https://github.com/Blacksp1d3r/runner-mcp/pull/760) SOURCE MERGED v0.1.47, an independent bounded test-only child now checks a deliberately SYNTHETIC six-role Ed25519 offline serving-statement comparator: all six consistent roles STILL return `active_build_provenance_verified=false` with source/wheel null, and eleven missing/foreign/stale/duplicated role, signer-host/nonce/expiry and expected-list mismatches refuse without promoting a live identity. No real host role names are asserted and no worker/service is contacted; this reuses existing pure comparator, makes NO executable release or version bump, and requires exact-head CI before merge. Correct-host actual loaded process, trusted issuer/revocation, original-client ACK, Fabric #1617/#942 A6 and #943 A7 remain WAIT. Existing connected central v0.1.38 is not changed by this test branch.

---

## 2026-10-20 — #509/A6 Doctor false-green classification source candidate v0.1.47

The connected central live v0.1.38 Doctor reports `pass/not_configured_0_of_11` for safely absent private A6 roots and fixed keys. This conflates safe absence with update-readiness in green-status aggregators; no evidence of a real unsafe update. Bounded SOURCE-ONLY candidate v0.1.47 changes this row to `warn/not_configured_0_of_11`, retains structurally `ready_11_of_11` private binding PASS (NOT off-target A6 qualification), and denies malformed/bool/unknown fields as `warn/unavailable`. Fixed private 11-key repair code, host services, credential custody, actual installed 0.1.38 and all six active roles remain UNCHANGED. Full exact-head CI and independent Fabric A6 #1617/#942, A7 #943, host source/wheel witness #669 and same-original-client ACK #609 are still required. Failure Museum RMCP-F-0048. This is not installation permission.

---

## 2026-10-20 — first-node blocking gate reconciled, no service mutation

GitHub `main` source v0.1.46 (PR #756 merged; docs PR #758 merged); original connected central runtime v0.1.38, loaded source/wheel NULL and `self_update_ready=false`. Doctor 2 FAIL, A6 `pass/not_configured_0_of_11`: PASS means deliberately absent private state/config, NOT A6 readiness. Fabric bridge READY read-only but A6 prepare/probe false, relay layer UNKNOWN and execution/mutation disabled. Existing immutable baseline and independent A6/A7 recovery/original-requester ACK still unqualified. New [F30 first-node evidence gates](../docs/operations/F30_FIRST_NODE_ADMISSION_GATES.md) (linked from repository root) states the non-mutating prerequisites and narrow ownership. No host/relay/service/credential/disk/worker modification. #509 / #669 / Fabric #924/#942/#943 / AIfordable #609 remain the real operational owners. Subsequent source development may continue without pretending a source merge is installed or current host identity is attested.

---

## 2026-10-19 — F30 fixed Claude/Qwen worker process source read route merged / live WAIT

Runner-MCP [#756](https://github.com/Blacksp1d3r/runner-mcp/pull/756) source **v0.1.46 MERGED** `d15d5007a5e880fd4ad55f46cd0a0f1913479792` (from exact tested head `d4b31adfd991bec47ee6552f21909066931a730e`). Checks: Runner MCP validation #39319130336 SUCCESS (98 tool-name canonical baseline, unique next-release reservation, Ruff/pytest, built exact wheel, full clean demo), Clean Ubuntu #39319130367 SUCCESS, attribution #39319130494 SUCCESS. Fabric existing loopback agent [#1614](https://github.com/Blacksp1d3r/Runner-Fabric/pull/1614) earlier source merged `20c8cc44cda8a1bfe7916b85a0dde65201606e4e` with Foundation #39317011482 + attribution #39317011467 SUCCESS. These source merges must NEVER be read as current worker process or authenticated client result ACK.

New conditional authenticated read-only `fabric_worker_process_inspect(worker)` uses existing `FabricBridgeClient`, fixed Claude/Qwen only, no arbitrary host/PID/path/cmd/URL/credential, no second server or relay/tunnel. Only optional correct-host privately pinned process start ticks/UID permits a **non-authorizing** observation. Correct result `observed_unverified` is not imported wheel RECORD, source/wheel signer, per-subject issuer, original requester durable ACK or deployment permission; wrong host/missing observer/old Fabric peer gives WAIT. Existing github-runner relay transport (PID 1103700, /healthz 200, public GET 405) already physically observed PASS, do not repeat/rebuild.

**Operational state:** original connected central Runner-MCP v0.1.38 still installed and lacks trustworthy active source_revision/artifact_digest; Fabric Agent Bus status UNKNOWN/evidence-unavailable, A6 0/11, execution/mutation OFF. Distinct Claude AF-SVC-0011/aifordable-coder on AF-VM-0001 and Qwen AF-SVC-0019/qwenagent on AF-VM-0003 require existing authenticated correct-host route and separately protected A6/A7 independent recovery. Only Fabric #924 controls one host activation after Runner-MCP #669 current wheel/import trust and AIfordable #428/#585/#609 issuer/ACK evidence. No host install, model, credential, service or tunnel action in source task.

---

## 2026-10-19 — RELEASE ADMISSION MERGED, main 0.1.45; live operation remains WAIT

Runner-MCP source [PR #753](https://github.com/Blacksp1d3r/runner-mcp/pull/753) squash **MERGED** `8dbbd1263f32c868df259ad2c77b7306faf683c1`; verified `main` package v0.1.45. Exact final PR head `5fe81a7fb4ae503b9b911b7ce57d65eddaa2d9a5` with validation #39316596943 (release-admission, Ruff/pytest, built artifact, clean demo), Ubuntu #39316597003 and attribution #39316597250 **ALL PASS**. #743/#745/#750 previously merged unique source v0.1.42/43/44. A source-only GitHub next-patch/competing-ready-PR gate now exists and passed for this actual READY PR. **Actual required branch protection is NOT ATTESTED:** branch protection GET returned 403 to the integration; rulesets listing [] does not prove enforcement; merge_group qualification and automatic deployment are still missing. Stacked source PR #746/#748 carry stale version reservations and remain owned by their separate authors.

Live original-client connected central Runner-MCP is a separate earlier installation **0.1.38**, active wheel/source digest NULL, Doctor `source_baseline_drift` + `active_revision_unavailable` FAIL, `self_update_ready=false`. Fabric bridge readable but mutation/execution false, Agent Bus relay evidence UNKNOWN despite independently observed relay transport, Q7 central WAIT and no correct-worker task/result/same-client ACK. No worker, relay, host, production installer, credential, backup, restore or disk mutation occurred in the source merge. Next ordered gates: GitHub admin required check and freshness/serialized steward → correct-host active identity #669 → Fabric guarded A6/A7 recovery/one-target activation #924 → original requester durable ACK AIfordable #609 → actual worker-local bounded workspace preflight/prepare #747. Avoid repeating already completed operator relay or workspace preparation.

---

## 2026-10-19 — #662 release collision READY-admission receipt; enforcement and live rollout separate

Source #662 PR #753 v0.1.45, exact branch head `fc87cf46d55a1c4b37310682530c56bf6b3959f4` on current main `908f09fafad0ed1f9c8edeea5318f689e92cc483` v0.1.44: switched READY after #743/#745/#750 merged. First real READY `Release reservation admission` job #118276865364 PASS on workflow #39315811193. Exact-head prior draft validation/Ubuntu/attribution succeeded; fresh READY workflow is still subject to terminal full validation and any later docs-only head retest. Actual branch-protection API read 403 and ruleset listing []; REQUIRED status and up-to-date settings CANNOT be attested. The gate is advisory until independently configured; no merge queue/merge_group acceptance. The current central serving Runner-MCP is independently 0.1.38 with active source/wheel NULL, Doctor 2 FAIL, self_update_ready=false; Fabric relay-layer UNKNOWN, original requester ACK and physical A6/A7 blocked. NO live install/dispatch/backup/cloud secret.

Independent next gates: (1) exact-head terminal PR CI plus 12-hour review policy/actual branch rules; (2) repository administrator must enforce Release reservation admission + current-main revalidation / serialized release steward, and only separately qualify merge_group if queue enabled; (3) correct-host wheel/process/source identity #669, A6/A7 and same-original-client task/result/ACK; (4) only then guarded first-node activation. Documents-only changes do not reserve 0.1.46 or prove production readiness.

---

## 2026-10-19 — #669 signed serving statement source after distinct 0.1.42/0.1.43 releases

User-authorized single release sequence has merged pinned metadata PR #743 (0.1.42) and bounded release bytes PR #745 (0.1.43); draft PR #750 now reconciles this source with actual main as the next unique 0.1.44. Independently pinned offline Ed25519 signed statement comparator checks exact host, challenge, source, loaded version, wheel, generation and process role set, but returns current source/digest NULL and active_build_provenance_verified=false regardless of signed consistency. No trusted correct-host observer, nonce issuance, original requester ACK, host installation or Fabric A6/A7 recovery is gained from this source. Review exact new CI head before merge; keep historical self-update state and existing running central 0.1.38 unchanged.

---

## 2026-10-19 — #739 follow-on fixed asset bytes source 0.1.43 after #743 merge

Following user-authorized #743 takeover and merge (main `02970477d35b37c38fe67a4a645f2ad5c0ea7a11`, v0.1.42), this session reconciled stacked PR #745 to main as v0.1.43. It adds ONLY an inert fixed-ID release byte integrity helper, negative tests and runbook; no executable tool, client token, real download, owner-only directory, installer, scheduler or host operation. The embedded source helper requires separately trusted size/digest, never treats Github API as a signature authority, and denies unapproved redirects or forwarding Authorization. Real 33/33 importer, independent published signature, rootless custody, rollback and original-client Agent Bus ACK remain blocked. After qualified source-only merge, #750 draft v0.1.44 and #753 draft v0.1.45 follow with independent exact-head CI. No active central 0.1.38 update from this source work.

---

## 2026-10-19 — User-authorized takeover of Runner-MCP #743; source 0.1.42

This session is now accountable for #739 fixed, operator-interactive GitHub Release metadata read-only source PR #743 (previously handled by another account). Reconciled onto current merged main 0.1.41 preserving Claude/Qwen owner-local workspace #751, cross-project flow #752 and handover #754. Unique 0.1.42 candidate has bounded offline tests and explicit no-proxy/no-redirect, no asset download or credential storage. Exact new head CI/attribution/Ubuntu proof must pass before merge. After this source commit, stacked #745 is separately reconciled to 0.1.43; independent drafts #750 0.1.44 and #753 0.1.45 remain later. Live connected central 0.1.38 has unresolved current wheel/source provenance and original-client ACK; no host, token, relay, installer, download or deployment authorized by PR merge.

---

## 2026-10-19 — Source release conflict and new draft source gates (operator handover)

Runner-MCP source `main` is 0.1.41 at `575c565fb319f4b3a40b294765941e4452ceb05c`. #743 still open with duplicate 0.1.41; #745 stacked with 0.1.42. The approved provisional release sequence is unique #743→0.1.42; #745→0.1.43; #750→0.1.44; #753→0.1.45, dynamically recalculated on main changes. PR #750 draft **source branch** now merges main including #751/#752 and uses 0.1.44. PR #753 draft 0.1.45 implements no-proxy/no-redirect, twice sampled current GitHub own/competing PR evidence, deterministic priority and extensive negative CI tests; at its last exact tested head all three workflows were SUCCESS, while admission is deliberately SKIPPED as draft. GitHub branch-protection GET returned 403, so this is *not yet required or atomic* in real merges. A proper required status+up-to-date protected branch remains admin-owned; do not assume `merge_group` covered. Failure Museum entry RMCP-F-0047 is on the #753 source branch only. Live connected central Runner-MCP is independently still 0.1.38 with source/digest null and self_update_ready=false. Do not override historical self-update metadata, replay Fabric A6/A7 already proven subsets or launch any host worker activation from GitHub source alone. This handover records source state, not deployment.

---

## 2026-10-19 — #669 release collision and host/ACK authority split

Docs-only branch updates roadmap and [Runner-MCP local single-flow contract](https://github.com/Blacksp1d3r/runner-mcp/blob/main/docs/coordination/CONTROL_PLANE_SINGLE_FLOW.md) linked to canonical Fabric #924. Runtime/MCP control source release owner Runner-MCP; sole target mutation/campaign owner Fabric #924/A6/A7; host/relay/credential+original requester ACK owner AIfordable #428/#585; one-worker acceptance AIfordable #609. Source main 0.1.41 merged #751, collides with open #743 0.1.41 and stacked #745 0.1.42 plus draft #750 0.1.43. Coordinate branch owners rather than edit foreign PRs. A new deterministic release reservation CI child is still REQUIRED/NOT IMPLEMENTED. First-party central runtime still 0.1.38, serving provenance unverified, self_update_ready=false; no live host mutation authorized. Reuse earlier physical controlled update rollback evidence. Distinguish SOURCE_MERGED from installed/serving/ACK; after actual read-only host inventory follow only guarded Fabric single-target activation.

---

## 2026-10-19 — Runner-MCP PR #742 CI evidence and isolated wheel-record source path

Source candidate 0.1.40 is not deployed. On pre-cleanup exact-head run 39288993782, release version gate 0.1.40 PASS, tool catalogue 95 PASS, Ruff PASS, 3386 pytest PASS (8 warnings), registry PASS; CI ended FAIL only because five existing handover/roadmap lines had trailing spaces. This cleanup commit addresses whitespace, but requires NEW exact-head green checks before merge. New #669 source path checks offline signed manifest + existing receipt and generation layout + strict wheel/installed RECORD; negative tampering cases keep active identity NULL/unverified. Server adapter now additionally refuses a revision without paired wheel digest and loaded matching version; this structural check does not authenticate signer/process. Live central 0.1.38 still unverified, no host action. A6/A7 prior physical subset proofs are acknowledged from Fabric #942/#943, their final acceptance remains with Fabric.

---

## 2026-10-19 — RMCP-F-0046 checkout baseline read-only safety fix

PR #742 source-only 0.1.40 now also validates `clean_head` returns a clean mapping with canonical lowercase commit; malformed/corrupted provider results return unknown and do not enable self-update. Added 11 synthetic cases. This is a distinct static code failure family (RMCP-F-0046); no assertion of a live checkout provider defect. Preserve the running 0.1.38 last-self-update history and two Doctor FAIL results until a separate qualified active wheel/process generation and protected operator baseline exist. New exact-head GitHub Actions must be terminal green; currently hosted jobs have remained queued without runner allocation, cause unknown. No server or credential action.

---

## 2026-10-19 — Release version guard corrected / exact-head CI pending

2026-10-19 release-gate fix: PR #742 now carries unpublished source candidate 0.1.40 in pyproject/server/glama/__init__ (all four identities checked equal), plus CHANGELOG; prior shipping code on 0.1.39 would have failed scripts/check_release_version.py. The narrow RMCP-F-0045 revision-provider containment and negative regressions remain. Exact-head CI uses GitHub-hosted ubuntu-24.04; workflow jobs reported QUEUED with runner_id=null, not green or red. GitHub queue cause unverified; no proven October 19 global outage or quota fact. PR stays draft. First-party original client still serves 0.1.38 with historical checkout drift, unavailable active wheel/source revision, self_update_ready=false. Do not modify self-update history, activate or install any new source without qualified trusted correct-host provenance, operator approval, original-client ACK and Fabric A6/A7.

---

## 2026-10-19 — PR #742 current provenance Doctor lane; SOURCE CI PENDING

Current first-party read-only `runtime_status` and `runtime_doctor`: connected serving Runner MCP 0.1.38, source/history drift and active revision unavailable, `self_update_ready=false`; `build_identity` returns source/digest null. The two FAILs are correct and must not be hidden. GitHub PR #742 is open/draft on `fix/runtime-doctor-provenance-20261019`. Existing regression and child/task are preserved; new narrow `self_update.py` provider lookup/attribute exception containment and six synthetic negative tests were committed (e46da3e, e9d17f8). RMCP-F-0045 source-only bug; no proven live incident. Added independent signer/installed-byte/serving-generation attestation design; historical `self-update-state.json` stays unchanged. Previous head CI remained queued, new head CI terminal success NOT YET CONFIRMED; do not merge or deploy. Live host/source/receipt/role/ACK/A6/A7 admission is a separate operator/Fabric blocker. Never use generic remote shell to bypass missing witness.

---

## 2026-10-17 — #735 source merged, Black Agent Bus admission remains WAIT

Runner-MCP [PR #737](https://github.com/Blacksp1d3r/runner-mcp/pull/737) SOURCE MERGED `d2dce33c436794fb90ce78cb12d1a7f27b4243d3`, exact source head `c620db7c6417ae7a306862c8fd9292f7dc6e0f0b`, validation/Ruff/3326 pytest/artifact/demo #39061856248, clean Ubuntu #39061856254, attribution #39061856279 all SUCCESS. v0.1.38 is UNPUBLISHED/NOT INSTALLED; central active 0.1.27, new Black still non-serving staged 0.1.30. Read-only `agent-bus status` distinguishes missing owner-private base as `base_config_not_initialized` and gives local setup guidance; symlinks, bad owner/mode and partial private files deny safely. Valid base without relay remains `not configured`. No bearer generated, runtime installed, port opened or website deployed. Failure Museum RMCP-F-0044 source fixed after observed CI failure; no confirmed real credential exposure.

Physical Black stage `stage_complete=true` was already done by operator (Runner-MCP #723/Fabric #1562 CLOSED), but `service_activation=false`, `relay_enrollment=false`, `original_client_ack=false`. Owner-private real project selection/base setup, AIfordable #585 unique CAS-fenced issuer credential and Fabric #1563 target-specific durable result→original-client ACK remain WAIT; A6/A7 and all external services stay blocked. Runner-MCP #735 remains OPEN for approved stage-closeout UX/receipt compatibility plus physical setup proof; do NOT silently add a field to signed stage v1 marker, repeat original stage, copy another host's token, or confuse central heartbeat with Black.

---

## 2026-10-17 — LIVE RECONCILIATION: Black stage COMPLETE (non-serving); A2 enrollment WAIT

GitHub issue/state now supersedes older blocked entries below: Runner-MCP #716 and physical recovery #723 CLOSED, Runner-Fabric #1562 CLOSED after owner-attended one-time stage finalize. New owner-controlled target (asset/subject binding remains under private Infrastructure Authority), original source pin `f4f5e4fe2898e0eb9ae79ebed7a7ae844059df2a`; original operator output `stage_complete=true`, `service_activation=false`, `relay_enrollment=false`, `original_client_ack=false`. These source/host-local receipts do not independently prove live first-party Black runtime. No auto stage replay or generic shell.

New first-host diagnostic: its staged `runner-mcp agent-bus status` fails because owner-confirmed private base config dir, env and projects files are ALL ABSENT; bootstrap deliberately only stages. UX gap #735; separate owner-attended setup needs real repo/checkout and private authority. Fabric #1563 and AIfordable #585 remain WAIT for unique target credential, authenticated result/ACK/replay and reversible activation. Connected central MCP 0.1.27 (different physical host) has no proven active source/digest, self_update_ready=false, Fabric execution/mutation disabled.

Source prevention #732 PR #734 SOURCE MERGED `4ac5d0c85674f91ed882588cb1b323deefc73e11` from exact head `3f09078d6b0f5299b861d903e714aa242fafdcd3`, after 3/3 GREEN workflows; source 0.1.37 candidate still UNPUBLISHED/NOT INSTALLED. Failure Museum RMCP-F-0043 and visible dirty guard integrated. Do not repeat #733. Next safe source issue #735 may proceed separately now without version collision. No HDD format, site, production, credential or Claude mutation.

---

## 2026-10-17 — RMCP-F-0030 safe failed-stage diagnosis SOURCE MERGED; Black PHYSICAL STILL BLOCKED

Physical first new-Black operator-local bootstrap pinned to `a2d34dc80550ef744acf0ff927344b000a832dcc` failed `existing_installer_failed`; original stage prefix left intact. Python 3.12.3; venv help 0, system ensurepip 1 and staged pip 1, runner CLI/complete marker absent. Root cause remains **UNKNOWN** until operator-owned read-only Ubuntu package inventory; do not infer absent python3.12-venv solely from system ensurepip RC1. Canonical Failure Museum RMCP-F-0030 detailed issue [#716](https://github.com/Blacksp1d3r/runner-mcp/issues/716) remains OPEN.

Source #718/#719 **COMPLETED_SOURCE_ONLY**: new rootless `diagnose --manifest` is private-manifest/local-machine-bound pure `lstat` status of the originally pinned partial stage; no stage execution, auto retry/delete, credentials, SSH/tunnel, disk or service mutation. Tested exact source head `1b49e3052919efda1c61c857a52de2b94261ebdd`, PR #719 squash merged `e336735f1f249971a93e3666ee46387953cc377e`, Runner MCP validation #39045168201, Clean Ubuntu installer #39045168205 and attribution #39045168175 all SUCCESS. Candidate 0.1.30 is UNRELEASED/NOT INSTALLED. Central connected runtime 0.1.27 unaffected; Fabric mutation disabled, Agent Bus exact-Black receiver/ACK UNKNOWN, Claude Q7 not qualified. Physical stage [Fabric #1562](https://github.com/Blacksp1d3r/Runner-Fabric/issues/1562) BLOCKED and dependent [#1563](https://github.com/Blacksp1d3r/Runner-Fabric/issues/1563) BLOCKED. HDD reportedly ext4-mounted already, never reformat.

Next: operator on Black only checks installed distro venv packages read-only, then independent approval for bounded repair, newly pinned source and fresh stage identity; no repeat on original prefix and no false website/Claude readiness.

---

## 2026-10-17 — Real Black first-stage failure / RMCP-F-0030 / source diagnosis #718

New Black operator-reported single approved physical stage at prior source merge `a2d34dc80550ef744acf0ff927344b000a832dcc` returned **BLOCKED `existing_installer_failed`**. Local read-only report: Python 3.12.3; system venv help RC0 but ensurepip RC1; partial venv/bin Python symlink, venv pip RC1, runner CLI and stage completion marker ABSENT. This proves no completed stage; package root cause remains UNKNOWN (missing python3.12-venv is hypothesis, not confirmation). The original failed private stage MUST remain intact, never re-run automatically. No Agent Bus, site, disk or production action done. Root Failure Museum [#716](https://github.com/Blacksp1d3r/runner-mcp/issues/716) RMCP-F-0030. Fabric #1562 physical stage and #1563 original-client ACK remain blocked.

Bounded source child #718 adds only a read-only same-host, private-manifest-bound `diagnose` subcommand for fixed metadata and safe classifying incomplete stage layout without executing the partial venv, disclosing private fingerprint/paths, granting control, creating directories or performing recovery. Source candidate `0.1.30` unpublished/not deployed (connected control runtime 0.1.27). Exact branch PR/CI must be verified before source merge. Next physical safe step: independent operator read-only Ubuntu package checks, then explicitly approved new immutable generation and original first-party transport/ACK; do not alter already-reported ext4 HDD.

---

## 2026-10-17 — Black physical first-host source bootstrap #713 DONE, operator-local stage NEXT

Runner-MCP PR #714 **SOURCE MERGED** as `a2d34dc80550ef744acf0ff927344b000a832dcc`, tested source head `68e569d7964fe92abd8516a9cd5a6144f5f8fb97`, validation #39036840912 PASS, clean Ubuntu #39036840935 PASS, attribution #39036840862 PASS, zero outstanding review threads. The local, unprivileged `identity/plan/stage` program reuses the existing upstream installer in an isolated non-serving prefix and records `service_activation=false`, `relay_enrollment=false`, `original_client_ack=false`. Version metadata `0.1.29` is an **unpublished source candidate**, NOT deployed on the control host or on Black. CI/source completion is not host enrollment. The existing connected primary Runner-MCP still reports 0.1.27, unknown wheel provenance, `self_update_ready=false` and Fabric bridge mutation disabled; an intermittent snapshot `unavailable` recovered on bounded repeat but Agent Bus relay still UNKNOWN. Claude Q7 readiness WAIT.

Black remains only the owner-declared unverified AIfordable `AF-HOST` candidate and a separate unknown Fabric website-host candidate. An actual one-time *local attended* stage and private host-specific Agent Bus identity/credentials are required; then exact host service identity, command→result→original-client ACK and reversible activation must be shown through first-party Runner-MCP/Fabric. The reported ext4 HDD must not be wiped or reformatted. No live Black server/DNS/site/Claude mutation occurred in this session. Related issues: Runner-MCP #713, Fabric #1554/#1556/#924 and AIfordable #428/#584/#585.

---

## 2026-10-17 — New Black first-party bootstrap: LOCAL NON-SERVING STAGE PR #714

Operator explicitly requires routine host installs and website delivery via the first-party Runner-MCP → Runner Fabric route, no Desktop Commander/direct SSH shortcut. New Black declared as UNVERIFIED `AF-HOST-xxxx` in merged AIfordable #588 (main `0438726ca88249227e5fc8f2bcc1e480e2f486c8`) and candidate existing F17 topology in Runner-Fabric #1559. **No authenticated remote Black receiver exists yet.** Original connected central Runner-MCP 0.1.27 bridge handshakes READY but Fabric mutation/execution is disabled, relay layer unknown; no claimed real host enrollment, original-client command/result/ACK, running Claude dispatch or website deployment. Black large HDD was previously observed ext4-mounted outside first-party route; NEVER format it again.

Issue #713 / PR #714 builds the first REAL source child: operator-local `scripts/managed_host_bootstrap.py` with `identity`, read-only `plan`, and strictly confirmed `stage` that reuses existing `install.sh` in a separate non-serving private prefix; private manifest pins owner-approved host asset/runner subject, machine identity hash, immutable source commit and installer SHA256. Root, symlinks, mutable/dirty/wrong Git origin, wrong machine, reused stage and stale confirmation fail closed; after existing-installer stress check and pip/CLI smoke, a private marker explicitly records service/relay/ACK as FALSE. Tests include wrong-host/source, dirty checkout, bad manifest/custody, confirmation, failed/partial stage, manifest swap during stage. No new process/API/relay service/capability, no disk or production site changes. `docs/LOCAL_HOST_BOOTSTRAP.md` documents one-time local physical operator sequence.

First CI on early PR head failed expected release-version gate because `scripts/` executable changed without version change. Source candidate metadata updated consistently from 0.1.28 to **0.1.29** (not tagged, published, deployed or activated). Exact current PR head and CI must be rechecked before merge; no source green implies live. Remaining separate work after locally run stage: owner-configured existing Runner-MCP setup/Agent Bus private identity and Fabric release, independently verify receiver command→result→original-client ACK and rollback, only then website deployment and Claude qualifications. Do not re-upgrade current central live 0.1.27.

---

## 2026-10-17 — First physical Runner-MCP upgrade ACTIVE 0.1.27, rollback timer canceled

- ATTENDED one-node activation completed with existing isolated dependency-resolving installer (no new release/version or PR). Operator's original host console confirmed successful v0.1.27 stage with pip dependency check and active old launcher initially untouched; a fixed local cutover migrated ALL SIX managed cron component executable pins and launched new loopback MCP listener under a new process. Original 0.1.9 release and pre-cutover crontab escrow were retained. A temporary independent rollback timer was armed before cutover; operator explicitly STOPPED it after real connected-client verification and confirmed systemd timer state `inactive`.
- Operator's on-host `autostart status`: backend `cron`; server, topology-heartbeat, github-watcher, completion-watcher, agent-bus-worker, fabric-agent-qualification all installed/enabled/active=yes. Tunnel and fabric-live-overview absent/not managed, matching former topology. Loopback port 8000 listener present under NEW process ID. Report only role/status metadata in public docs; private machine paths remain off-repo.
- AFTER timer cancellation, the ORIGINAL already-connected ChatGPT MCP client independently returned `runtime_status.version=0.1.27` AND `installed_distribution_version=0.1.27`, `build_identity.build_version=0.1.27`, Fabric handshake `state=ready`, worker pool available 2/2, no active install/restart/update. This is first actual serving-client upgrade success, not merely CI/source and not a fleet rollout.
- Outstanding: independent *loaded* revision/digest/provenance is still unknown; `self_update_ready=false`; doctor FAILS `self_update_source_baseline=source_baseline_drift` and `self_update_runtime_activation=active_revision_unavailable`. Do not falsify self-update history, disable guard or interpret version string alone as signed wheel proof. Fabric A6 preparation/synthetic probe unavailable and mutation disabled; A7 independent physical restore and original-client durable result+ACK campaign not qualified. The temporary timer is inactive by explicit operator action: **no autonomous revert is currently armed**; preserve old release, cron escrow AND running new staging prefix (do not move/prune).
- Next: qualify stable active-release custody without moving currently serving executable, independent source/wheel receipt and honest self-update baseline repair, A6 journal and A7 physical recovery/ack before any multi-node fleet rollout. Full details/checkpoints: Runner-MCP #341, #669; Runner-Fabric #924/#942/#943. Older `live v0.1.9` text below is superseded by this dated verified checkpoint.

---

## 2026-10-17 — Fresh original-client A6/F30 read-only verification (NO host mutation)

Connected Runner-MCP still reports installed distribution `0.1.9`, `source_revision=null`, `artifact_digest=null`, `active_build_provenance_verified=false`, `self_update_ready=false`; no active update, pending restart or install recovery. `runtime_doctor` now reports two failures: `source_baseline_drift` and `active_revision_unavailable`. Its `fabric_a6_binding_state=pass/not_configured_0_of_11` is an optional diagnostic classification, **not** evidence that A6 is configured. Fabric bridge preflight is read-only READY, but `a6_prepare_available=false`, `synthetic_probe_status_available=false`, `mutation_enabled=false`; Fabric operational snapshot is degraded, relay evidence unknown and execution/mutation disabled. Both canonical Fabric remote/local update-readiness calls returned unstructured connector errors: classify as UNKNOWN, never APPROVED or a safe update path.

Immutable GitHub `main` package metadata remains `0.1.27`, adding required runtime `cryptography>=44,<51` compared with running 0.1.9 provenance-associated source. Existing `--no-deps --no-index` self-update cannot resolve this changed dependency contract regardless of repairing the revision-attestation gate. **Do not call self_update, A6 prepare/finalize or alternative update controls on the shared serving node.** Reuse the existing authorized attended dependency-resolving **isolated-prefix** installation flow (both separate install root and separate BIN_DIR), while preserving the actual old launcher/wheel and independent recovery. Only qualify a one-node controlled activation after real process/launcher/build provenance, independent restore and original-client result+ACK are proven. No new code release/version/updater PR is authorized in this lane until that actual upgrade is complete.

One read-only host sample showed elevated CPU load (1-minute 32.13 on 12 logical cores, CPU PSI some avg10 72.94%); this is transient telemetry, not proof of a process/root cause. No expensive host tests were run. A6 #942, A7 #943, Fleet #924, MCP #341/#669 and AIfordable #428 remain open and no physical A6 journal, rollback, activation or original-client ACK was claimed. This checkpoint is documentation/evidence only and respects the operator's freeze on further updater code/version churn.

## 2026-10-16 — OPERATOR PRIORITY: real Fleet upgrade; source-version development frozen

- Owner explicitly paused new version bumps, shipping code PRs and parallel updaters. Only the existing real installation/update lane is in scope until an attended actual first-node upgrade is safely qualified. The canonical topology is already known; do not restart host discovery.
- Original connected live Runner-MCP confirmed 0.1.9, active source revision and wheel SHA unavailable, `self_update_ready=false`, no pending recovery or restart. Historical self-update state says completed but is NOT actual wheel attestation. Exact deployed-source code at `e7cb9162d686b5992b3862a4b61f85980cbdfbd4` returns unavailable for current source in `installed_source_revision()`, making the activation-alignment check false while a prior install marker exists. Do not rewrite self-update history or bypass this guard.
- **Additional independently proven blocker:** immutable `pyproject.toml` on 0.1.9 versus proposed source 0.1.27 includes a NEW required runtime dependency `cryptography>=44,<51`; old runtime requirements had no cryptography. The existing self-update installs with `--no-deps --no-index` and exact dependency-contract preflight; by `docs/SELF_UPDATE_COMPATIBILITY.md` a changed runtime requirement mandates `bootstrap_required` / attended normal dependency-resolving installation. Merely making activation evidence available cannot make that in-place updater an eligible direct path.
- Exact candidate source (not deployed): merged source commit `265dc1fc0866e35df07b05f6bcf3addee4f8dafa`, v0.1.27, source green CI/clean Ubuntu; PR #709 GH artifact is explicitly prefixed `unapproved-` and must not be treated as independently signed release. Current source branch moving must not cause target SHA drift.
- Existing Fabric peer handshake READY read-only but A6/probe absent and mutation disabled; independent active process/launcher, preserved 0.1.9 package and rollback execution, and same-original-client response+ACK still require trusted private host evidence. Operator is away; all host-bound deployment actions WAIT. No broad remote control, worker billing, private paths, credentials, backups or services were touched. Original historic self-update job was reread without mutation and confirmed completed, `restart_required=true` historical but `restart_pending=false` now.
- Immediate next attended action: narrow READ-ONLY actual serving process/managed launcher and old generation escrow check; separately stage exact pinned target in a new isolated install prefix with normal dependency resolution; validate pip check, package/RECORD hashes, listener in isolation, original-client route and offline rollback; only afterward one bounded activation with independently confirmed client ACK. Keep #341/#669 and Fabric #924/#942/#943 OPEN as `BLOCKED_HOST_OPERATOR_DEPENDENCY_BOOTSTRAP_AND_RECOVERY`.

---

## 2026-10-16 — Fleet read-only diagnostics verified through actual MCP protocol; A6 symlink security restack running

- [PR #706](https://github.com/Blacksp1d3r/runner-mcp/pull/706) v0.1.25 optional CI guest status fallback SOURCE merged `262fd4e25a9a0ad63a02c5ad825f288998775656`; exact head `f40b8421dca8188a0467a1c2c195f20889ee01fe`, validation #38927006209, Ubuntu #38927006272, attribution #38927006246 all SUCCESS. Unknown guest remains explicitly unknown and cannot authorize work.
- [PR #707](https://github.com/Blacksp1d3r/runner-mcp/pull/707) v0.1.26 read-only Fabric GitHub/local update readiness bounded refusals SOURCE merged `000903bde5d6f81d9507fca95c0302f7364294e6`; exact head `bb407cc1b425b4b1929d0c43ba6b577ee2a6e5bf`, validation #38927767319, Ubuntu #38927767309, attribution #38927767311 all SUCCESS. Never interprets an error as a ready artifact.
- [PR #708](https://github.com/Blacksp1d3r/runner-mcp/pull/708) tests-only actual authenticated MCP initialize/tools/call integration merged `6e3e8e9dcffb9a6fe7b6fb4b7436612f1ad2fa1a`; exact head `54f682ddd584dd4ede1b9c05e72b62b9793fc7c6`, validation #38933713969 (Ruff/pytest, built artifact and demo all SUCCESS), attribution #38933714024 SUCCESS. No product version bump (still SOURCE v0.1.26); synthetic client test is NOT a live host/connection/provenance ACK.
- [PR #709](https://github.com/Blacksp1d3r/runner-mcp/pull/709) current-main A6 dangling-symlink fail-closed patch, source 0.1.27, squash MERGED `265dc1fc0866e35df07b05f6bcf3addee4f8dafa`, exact head `6f75e21b78badea7d0345c1125070809a5a17f83`. Validation #38934210559 Ruff/pytest/build/demo, Ubuntu #38934210595 and attribution #38934210533 all SUCCESS; old #655 CLOSED UNMERGED as superseded. Failure Museum RMCP-F-0026 now in the canonical diagnostic index with SOURCE_FIXED_LIVE_UNQUALIFIED; child state COMPLETE_SOURCE_ONLY.
- **Live truth unchanged:** original connected runtime 0.1.9, active source revision and wheel digest NULL, `self_update_ready=false`, runtime doctor `active_revision_unavailable`. Fabric bridge handshake ready but `mutation_enabled=false`, A6/probe unavailable. No 0.1.26 / 0.1.27 production installation, hosted timer deployment, physical restore, tunnel or server mutation. Next true gate is qualified host and loaded-wheel attestation (#669 / AIfordable #428) plus real single isolated canary with A6 #942 and A7 #943 original-client confirmed recovery. Operator explicitly deferred independent rollback-timer work to customer rollout; do not block useful pre-customer source development, and never bypass real installation safety.

---

## 2026-10-16 — #664 complete source-name baseline and #333 optional tunnel doctor both integrated

- [#702](https://github.com/Blacksp1d3r/runner-mcp/pull/702) tests-only guard of 14 presently registered tool callable signatures merged `aa1a80656a04c3b1d278228e20ea129988e622d0`, exact CI validation 38902202349 final rerun successful and attribution 38902202402 successful. RMCP-F-0040 targeted AST regression fix; RMCP-F-0041 one unconfirmed pre-existing fair scheduler test timing failure on an earlier CI attempt, then passed identical HEAD rerun (no scheduler change).
- [#703](https://github.com/Blacksp1d3r/runner-mcp/pull/703) source v0.1.24 opt-in bounded expected-tunnel evidence in actual `runtime_doctor` merged `d3929bbcdcf0d7fd547740ed80a2e4195b89dd36`; CI validation 38903795857, clean Ubuntu 38903796065, attribution 38903795921 all SUCCESS. Legacy default unchanged, no private evidence collector deployed, no secret/path/token probe, no host restart. Parent #333 OPEN for approved private observer and reboot-safe tunnel operation.
- #664 95-name source inventory guard originally PR #704 had exact-head tests green but merge conflict due to concurrent main handover edit; PR #704 closed unmerged. [#705](https://github.com/Blacksp1d3r/runner-mcp/pull/705) replayed fixture/tests onto clean main and merged `67770dd641c342c561e7631fe20f39057d2a019a` from exact tested head `7a9ac04f2efe107ee34006c1d471e9ecf6d9e36e`, validation 38905411566 Ruff/pytest/build/demo and attribution 38905411379 all SUCCESS. No Ubuntu run observed for tests-only PR. Failure Museum RMCP-F-0042 records shared markdown conflict; child COMPLETE_TEST_GUARD_ONLY.
- This pins 95 currently source-registered names, including conditional registrations, but does not prove historic v0.1.9 wheel input/output JSON schema or customer-permitted tool list, and never authorizes MCP dispatch. Parent #664 OPEN pending real released artifacts, authenticated serving inventory, legacy client versions and commercial support window.
- Latest SOURCE remains v0.1.24; original client last observed v0.1.9 and source/digest null. Rollbacktimer remains deferred until customer rollout. No live server, network tunnels, cron, credentials, paid workers or deployments modified.
- After all merges, update shared handover once on main; do not concurrently push same leading markdown sections to main while a PR modifies them (RMCP-F-0042).

---

## 2026-10-16 — #333 opt-in tunnel doctor source merged; #664 full tool-name guard CI

- [PR #703](https://github.com/Blacksp1d3r/runner-mcp/pull/703) source 0.1.24 merged `d3929bbcdcf0d7fd547740ed80a2e4195b89dd36` from exact CI-green head `dbb1143f7f9eff82bf676b9eaa94929f1ff2766c`; validation `38903795857`, independent Ubuntu `38903796065`, attribution `38903795921` SUCCESS. `runtime_doctor` can now receive an EXPLICIT opt-in expected-tunnel flag and separately authorized read-only typed evidence provider, reporting only fixed sanitized reason codes; legacy default unchanged. No private sensor/wrapper/health probe/tunnel secret or actual live installation. Child STATE COMPLETE_SOURCE_ONLY, #333 OPEN.
- #664 historical compatibility guard PR #702 source tests-only merged `aa1a80656a04c3b1d278228e20ea129988e622d0` and followed by separate draft tests-only PR #704 [full 95-name current source inventory](https://github.com/Blacksp1d3r/runner-mcp/pull/704), source 0.1.24 without bump. Latest source head `3dcfd21c907abd2e58b272f6987267fd000b199b`, validation `38904723679` Ruff/pytest and release artifact passed but five-minute demo still running, attribution `38904723800` successful; DO NOT MERGE until exact-head full validation green. These are current SOURCE AST contract/name baselines, not released historic wheel v0.1.9 or actual per-host tools/list output.
- Parent #664 still OPEN for full historical released wheel schemas, output/permission semantics, legacy client compatibility and operator LTS support decision. Rollback timer deferred to customers; live source 0.1.9 with null active SHA/digest unchanged. No host/credentials/tunnel changes.

---

## 2026-10-16 — #333 actual runtime_doctor tunnel evidence opt-in source child

- #664 tests-only PR #702 v0.1.23 sampled callable signature guard source merged `aa1a80656a04c3b1d278228e20ea129988e622d0`, final exact head `92d0e9ce8a423f87b61fb579d4545429c1288f59`, CI validation rerun 38902202349 SUCCESS including Ruff/pytest/demo/artifact and attribution 38902202402 SUCCESS. RMCP-F-0040 AST mutation fixed; unrelated fair-scheduler flaky assertion occurred once then passed rerun (RMCP-F-0041). Historic released wheel v0.1.9 is not proven compatible by source AST fixture.
- Independent #333 source-only candidate v0.1.24 on `chatgpt/333-explicit-tunnel-doctor-evidence-v0124`: actual runtime_doctor conditionally adds `connector_tunnel_readiness` via explicitly expected boolean and separately trusted read-only collector; defaults unchanged, fail-closed sanitized reason only. No tunnel state actually queried on existing live 0.1.9, no restart/credential access.
- Tests, TASK/STATE ready; exact-head CI and PR merge pending. Next parent #333 real private collector and managed restart operator action, not automatically authorized. Rollback timer deferred to customers.

---

## 2026-10-16 — #664 sampled existing MCP signatures safeguarded by CI, tests-only

- [PR #702](https://github.com/Blacksp1d3r/runner-mcp/pull/702) source test-only MERGED squash `aa1a80656a04c3b1d278228e20ea129988e622d0` from exact head `92d0e9ce8a423f87b61fb579d4545429c1288f59`. Validation `38902202349` FINAL attempt: Ruff/pytest 3160 passed, built release and clean five-minute demo SUCCESS; attribution `38902202402` SUCCESS. No Ubuntu installer PR workflow was observed for this tests-only change. Source distribution remains v0.1.23 (correct: no shipping runtime tool changes).
- A selected 14-tool AST baseline pinned existing registered MCP tool names, parameters/defaults and return annotations from source 0.1.23. CI detects drift. **This is not a v0.1.9 customer released wheel contract snapshot or generated runtime JSON schemas**, and does not establish full historical compatibility. Parent #664 remains open for real released artifacts, legacy N/N-1 client tests, output/error/permission semantics and commercial support policy.
- Failure Museum: RMCP-F-0040 bad broad textual mutation test corrected by targeted named-tool AST mutation; RMCP-F-0041 one unconfirmed pre-existing concurrent scheduler fairness timing failure in CI first attempt, same exact commit rerun passed without changing the scheduler. Do not claim a proven scheduler root cause or suppress security checks.
- No production, tunnel, user-host, keys, cron, rollback timer or service mutation. Active original-client Runner-MCP last observed 0.1.9 with null verified source/digest. Operator defers independent rollbacktimer to customer phase.
- Follow-up independent roadmap may proceed (e.g. operational tunnel readiness #333) without waiting for actual customer version rollout.

---

## 2026-10-16 — #664 legacy callable signature CI regression guard, source-only

- Following merged #665 source-only 0.1.23 classifiers/inventory and alert digest, started independent #664 tests-only branch `chatgpt/664-legacy-signature-regression-v0124`, base `53a002df136d010ebe460643a37ddcf86af58c6e`.
- Pinned sampled v0.1.23 server tool registration/callable AST signatures in `tests/fixtures/legacy_tool_callable_signatures_v0123.json`; guard checks current source names, required/default arguments and return annotations. No product code/version bump, no runtime activation.
- Scope caveat: not an actual historical 0.1.9 wheel schema/semantic compatibility test; parent #664 remains open for released train source/JSON schema and customer support/upgrade decisions. Tests/CI and PR pending.
- Rollback timer still deferred to customers, active MCP 0.1.9 unchanged.

---

## 2026-10-16 — #665 three source-only children through v0.1.23 merged; operational fleet proof still open

- [#699](https://github.com/Blacksp1d3r/runner-mcp/pull/699) 0.1.21 bounded tool-contract identity classification merged squash `70201f6ac138ce1fd1dfd3e91ed4f1f7c4b6fd08`. Exact head validation `38897275967`, Ubuntu `38897275912`, attribution `38897275777` all SUCCESS. Failure Museum RMCP-F-0038/RMCP-F-0039 fixed and complete (strict actual bool trust flags).
- [#700](https://github.com/Blacksp1d3r/runner-mcp/pull/700) 0.1.22 bounded tool inventory duplicate-ID/name/schema/revision preflight merged squash `26c135952b2786e498871c68b37dcdb1900a26ea`; exact HEAD CI validation `38898006036`, Ubuntu `38898006091`, attribution `38898006047` all SUCCESS.
- [#701](https://github.com/Blacksp1d3r/runner-mcp/pull/701) 0.1.23 typed alert digest/cooldown source merged squash `10501c1d28ef050ecfc61f7b341487e7ead47d2b`, exact head `88b8c81d15a664998b988ef02201f74875593090`, validation `38898938032` (Ruff/pytest, build, demo), Ubuntu `38898937966`, attribution `38898937757` all SUCCESS. Child TASK/STATE COMPLETE_SOURCE_ONLY. Pure local per-scope/tool/reason synthetic event aggregation, no clocks, external alerting, durable state or side effects.
- Operational gate: neither registry flag input nor SHA token / namespace / tool id is authenticating by itself. No dispatcher authorization, signed live process inventory, trusted customer host/tenant policy, Fabric customer inventory/notification delivery or ACK exists. READY classification or sanitized summary is not an operation permission. Parent #665 remains OPEN; legacy customer contract #664 remains separate.
- Actual original connected Runner-MCP still last verified **0.1.9** with null active source/digest; GitHub **0.1.23 is source only**. Fabric/A6 live rollout still unqualified. No host, tunnel, keys, cron, service update, paid worker or rollback timer changed. Operator explicitly deferred timer work to customer rollout.
- Next independent work: customer-compatible old tool contract fixtures #664 or authenticated inventory/alert transport with Fabric (requires qualified authority); do not add standalone synthetic validation layers without a real use path. Keep CI exact-head and public topology redacted.

---

## 2026-10-16 — #665 typed alert digest source candidate 0.1.23

- #699 / #700 bounded identity classifier/inventory collision source children have both merged and CI-green, main source 0.1.22. Latest squash #700 `26c135952b2786e498871c68b37dcdb1900a26ea`. No actual tool permission granted.
- New independent source child `chatgpt/665-typed-alert-dedupe-v0123` groups sanitized typed mismatch events by caller-provided opaque SHA256 scope, tool ID and reason with cooldown, no free-text/private details, no notification, persistence or network. The source timestamps/scope/claimed reason are **untrusted unless separately attested**.
- Tests/TASK/STATE created, CI/PR merge pending. Parent #665 still requires Fabric trusted inventory and customer alert delivery/ACK. Running original connected MCP remains 0.1.9 with null active revision/digest. Rollback timer postponed until customers. No host mutations.

---

## 2026-10-16 — #665 source children through 0.1.22 merged; actual live identity remains unqualified

- PR #699 source-only bounded tool metadata classifier merged squash `70201f6ac138ce1fd1dfd3e91ed4f1f7c4b6fd08` from exact tested head `7d14aa23dddfd8557c20e12471a0e8041ff171a2`. Full CI validation `38897275967`, clean Ubuntu `38897275912`, attribution `38897275777` all SUCCESS. Failure Museum RMCP-F-0038 Ruff test fixture and RMCP-F-0039 nonboolean truthy trust flag fixed / source-complete.
- PR #700 source-only bounded inventory collision guard merged squash `26c135952b2786e498871c68b37dcdb1900a26ea` from exact tested head `b7457faaf6e38307af2c749954764a2991278a3c`. Full CI validation `38898006036` Ruff/pytest/build/demo, clean Ubuntu `38898006091`, attribution `38898006047` all SUCCESS. New source v0.1.22, child state marked COMPLETE_SOURCE_ONLY.
- **Important:** typed comparison READY, unique tool metadata and consistent tool inventories are not authorization or real trust. Registry/operator custody and authenticated actually loaded serving process, caller+tenant/host policies, enabled tool admission and persistent alert deduplication/delivery are still absent. #665 OPEN; legacy #664 contracts separate. Never use these source helpers alone to promote a deployment or dispatch a tool.
- Original client still last observed 0.1.9, source_revision=null, artifact_digest=null. Source 0.1.22 not installed. No host, tunnel, secret, cron, model/worker activation or rollback-timer mutation. Rollback timer intentionally postponed until customer phase.
- Follow-up source lane candidates are pure schema contract compatibility tests / bounded duplicate alert classification while the external authenticated inventory/custody and A6/A7 remain separately gated. Avoid duplicating merged source children #699/#700.

---

## 2026-10-16 — #665 stable identity first child source merged, inventory collision child underway

- [PR #699](https://github.com/Blacksp1d3r/runner-mcp/pull/699) v0.1.21 source MERGED `70201f6ac138ce1fd1dfd3e91ed4f1f7c4b6fd08` from exact head `7d14aa23dddfd8557c20e12471a0e8041ff171a2`. CI validation `38897275967` Ruff/pytest/release/demo, clean Ubuntu `38897275912`, attribution `38897275777` all SUCCESS. RMCP-F-0038/0039 Failure Museum source-qualified.
- Independent new child `chatgpt/665-tool-registry-collision-preflight-v0122` source 0.1.22: compare bounded expected/observed tool inventories for duplicate stable IDs/names, invalid schema/revision, mismatched inventory. No authenticated process inventory/registry enrollment, and READY is never dispatch authority.
- Tests + TASK/STATE present. Exact HEAD PR/CI still needed; #665 remains OPEN for actual attestation, policy-bound dispatch and alerting; #664 customer legacy compatibility separately scoped.
- Original connected MCP remains 0.1.9, with null source/artifact digest, no installation change. Rollback timer postponed until customer deployment. No host/tunnel/key/paid worker actions.

---

## 2026-10-16 — #665 tool identity comparator source child started

- Confirmed source main at `7e3fba64a28b4ecd10786c253a5111affa45fda4` (0.1.20, after merged FASTER-13 #698). No duplicate #383 baseline work.
- New source-only child `chatgpt/665-tool-identity-classifier-v0121`: pure tool contract comparison against supplied independently trusted registry/authenticated inventory flags. Typed mismatch reasons and synthetic negative tests, no dispatch/side effects. Version candidate 0.1.21. Exact-head CI and PR merge pending.
- Critical trust caveat: boolean flags and namespace/ID/hash from a caller are NEVER a cryptographic trust anchor. Production identity still v0.1.9/null source/digest; no live alert or authenticated handshake.
- Follow-on issue #665 requires independently authenticated serving inventory/host policy, alerts and distinct customer legacy contracts #664. Rollback timer deferred to customer phase; no host actions.

---

## 2026-10-16 — functional source #681 and FASTER-13 #383 phase 1a landed

- PR #697 on #681 host read failure no hidden extra Fabric preflight merged source-only 0.1.19 `1bbb46ce9061e7f453532e5000fb2a0995ee7140`, exact source head `fb37db2084946f618904318f7fcbf7dcea0d497d`; validation `38886451977`, clean Ubuntu `38886451953`, attribution `38886452030` all SUCCESS. Failure Museum RMCP-F-0036 COMPLETE_SOURCE_ONLY. PRs #695 and #696 preceding likewise merged. Parent #681 still OPEN for live client evidence.
- Independent FASTER-13 parent #383 phase 1a PR #698 synthetic local JSON framing/polling baseline merged source 0.1.20 at `844062bec7602df5131f7157f1a8ff074a41653f`, exact checked source `79633aabd751a761d9b4b27ab45b7cde03f668a4`; validation `38891328157` Ruff+pytest/release/demo SUCCESS, independent Ubuntu `38891327629` SUCCESS, attribution `38891327767` SUCCESS. Benchmark emits p50/p95/p99 JSON encode/decode and deterministic 500ms polling-delay model with explicit synthetic-only label. CI real Ruff B023 loop closure fixed as RMCP-F-0037, now COMPLETE_SOURCE_ONLY. Child TASK/STATE completed.
- NO real TCP/MCP latency measurement, event push benchmark, end-to-end speedup claim, host changes or privileged worker dispatch. Next FASTER-13 Phase 1b needs isolated authorized local loopback fixture with session/auth and trace ID; the current protected 24/7 host is not an approved benchmark target.
- Original-client MCP remains version 0.1.9, no proven serving source SHA or artifact digest. The 0.1.20 SOURCE merge is not a live installation. Operator deferred independent rollback timer to customer phase. No tunnels/keys/cron/processes touched.
- Public GitHub handover and separate parent issues #681 and #383 are canonical. Other roadmap items may proceed without waiting for a source-only review queue or rollback timer. Production update still separately gated.

---

## 2026-10-16 — functional #681 source complete; FASTER-13 #383 benchmark child underway

- PR #697 (no hidden Fabric preflight after failed host read) merged at `1bbb46ce9061e7f453532e5000fb2a0995ee7140` from exact tested head `fb37db2084946f618904318f7fcbf7dcea0d497d`. CI Runner validation `38886451977`, independent Ubuntu `38886451953`, commit attribution `38886452030` all SUCCESS. Failure Museum RMCP-F-0036 now COMPLETE_SOURCE_ONLY.
- Three narrow #681 source remedies are merged: continuity unavailable 0.1.17, snapshot unavailable 0.1.18, host error first-edge/no hidden preflight 0.1.19. Original connected MCP remains 0.1.9 until separately authorized versioned rollout. #681 stays open for live peer/relay proof.
- New bounded FASTER-13 / #383 source-only candidate 0.1.20 `chatgpt/383-mcp-local-fastpath-synthetic-baseline`: synthetic local JSON serialization baseline and deterministic polling calculation. No claims of live MCP RTT, no actual host traffic or API execution. Child TASK/STATE and CLI+tests present. Exact-head CI pending.
- Operator defers independent rollback timer until customers and has private host access later if needed; no privileged host/secret/tunnel/cron changes now.

---

## 2026-10-16 — functional #681 no-followup host-inspection child

- #695 (source 0.1.17) and #696 (source 0.1.18) both merged with full exact-head green CI; #696 source squash `2ac39378f69262a5e3e75934d186629ed223d271` from `f5ee909c119c1ce77966b941e9c63efac760841e`, validation 38885682444, independent Ubuntu 38885682419, attribution 38885682491.
- New source-only branch `chatgpt/681-host-inspect-no-followup-preflight-v0119`: after a failed host read, no hidden additional preflight network traffic. Failure is explicitly bounded/unavailable; success unchanged. Candidate 0.1.19. Tests, child TASK/STATE, exact CI pending.
- Running original client last verified 0.1.9; remaining Fabric peer intermittent/relay unknown. No production, paid worker, secrets, tunnel, cron or rollback timer changes; operator defers timer work until customer phase.

---

## 2026-10-16 — functional #681 source progress through snapshot failure classification

- PR #695 v0.1.17 merged to main at `804be37993da563cdd6ed45872e50573a22b2a48` from exact CI green head `785204aea44be7c0f87a59c8641fd31bf1b55f85` (validation 38884916215, clean Ubuntu 38884916569, attribution 38884916186 all SUCCESS). Source-only bounded `fabric_continuity_status` unavailable now returns sanitized deny-by-default state; original client v0.1.9 unchanged.
- Distinct child branch `chatgpt/681-snapshot-bounded-unavailable-v0118` candidate v0.1.18 addresses other observed generic failure: Fabric operational snapshot bridge exceptions map to explicit bounded degraded/unavailable result without retry, secrets or extra preflight.
- Tests, TASK/STATE, source version manifests updated, newest exact-head CI still to be qualified. Parent #681 intermittent host-inspection/relay behavior and #590 runtime bridge evidence remain separate. Rollbacktimer intentionally deferred to customer phase; no host/credential/tunnel work.

---

## 2026-10-16 — functional roadmap resumed: #681 continuity failure observability

- Operator reprioritized away from rollback-timer implementation (customer phase). Read-only original client 0.1.9 showed Fabric host-inspect fresh and snapshot v1 degraded with unknown agent-bus.relay; `fabric_continuity_status` still generic internal error, while `runtime_doctor` explicitly indicated missing private continuity configuration. No server repair required today.
- New source-only bounded child on `chatgpt/681-continuity-bounded-unavailable-v0117` candidate 0.1.17 returns explicit sanitized deny-by-default unavailable state for controlled continuity errors in existing MCP tool, keeping successful payload and audit semantics. No retry/fallback/process change.
- Parent #681/#590 remain open for live verification after eventual authorized update. Child TASK/STATE + tests and exact HEAD CI needed. No private host/tunnel/cron/key changes.

---

## 2026-10-16 — OPERATOR CORRECTION: rollback timer deferred until customers

- Operator explicitly decides that independent rollback-timer work is NOT an immediate pre-customer priority; schedule it for customer rollout. Earlier handover references that suggest a mandatory timer gate before continued development are superseded **for priority and scope**, not an authorization to perform risky production changes.
- Operator can access privately owned servers when home and assist later with narrowly scoped local repair if a real operational blocker remains. Do not demand host access now, nor halt unrelated source/functional roadmap tasks for timer proof.
- Current live read-only MCP is 0.1.9 with unverified installed source/digest; source code is 0.1.16. Keep truthful version boundary; production promotion/activation still separately requires fit-for-purpose checks and explicit authority.
- Relevant issue updates: #669 (operator priority correction), #681 (deferral). No secrets, physical paths or host configuration copied to public repo.

---

## 2026-10-16 — #669 offline signed provenance source children through v0.1.16 merged; LIVE UNQUALIFIED

- PR #693 v0.1.15 source-only detached Ed25519 builder-manifest signature preflight merged `e85b15924790d22a90b9a54cef1b55d10379d785`, exact PR HEAD `eedc369f695cabbc4ef837a822d22cc33de3d44b`. CI attribution `38871536337`, validation `38871536393`, Ubuntu `38871536397` SUCCESS. RMCP-F-0034/RMCP-F-0035 source CI/security fixes resolved and recorded.
- PR #694 v0.1.16 source-only *signed offline candidate evidence chain* merged `ee019e491c53d1d2b239cc07faa15b9f4fcaed51`, exact tested head `95e2019f62df7ecc6766d78f3cba1ac1c1755959`. Validation `38872162974`, clean Ubuntu `38872162972`, attribution `38872163036` all SUCCESS. Bounded source child STATE marked COMPLETE_SOURCE_ONLY.
- Offline proof comprises Ed25519 detached signature with independently pinned public-key SHA256, externally pinned manifest digest, wheel/module candidate SHA256 and generation path checks. This is **not** operator enrollment/revocation/expiry or process attestation; a claimant controlling both signer key and pin has NO trusted origin.
- Original connected Runner-MCP remains **0.1.9**, `source_revision=null`, `artifact_digest=null`; runtime_status active_build_provenance_verified=false, self_update_ready=false. Fabric bridge preflight has `mutation_enabled=false` and `a6_prepare_available=false`; operational snapshot still generic error in this session and separately tracked #681. No host/tunnel/key/cron/deployment mutation.
- Next technical boundary remains protected root/trusted signer enrolment (source of out-of-band expected public-key pin, expiry/rotation/revocation and release purpose), sealed installer generation and loaded active executable/module witness, independently armed A6/A7 rollback and original-client same-route ACK. These require qualified private/operator authority and MUST NOT be bypassed or simulated by public GitHub source. Umbrella issue #669 stays OPEN/BLOCKED_EXTERNAL.
- Verified main source squash #694; later documentation commits do not imply post-merge CI status. Live evidence and protected custody win over old self-update history.

---


## 2026-10-16 — signed evidence chain source child 0.1.16 in progress

- #693 offline Ed25519 manifest-signature verifier source merged `e85b15924790d22a90b9a54cef1b55d10379d785`, CI exact head `eedc369f695cabbc4ef837a822d22cc33de3d44b` attribution 38871536337, validation 38871536393, clean Ubuntu 38871536397 all SUCCESS. No trusted signer enrolled.
- New bounded child branch `chatgpt/669-signed-evidence-chain-v0116` composes signature with offline candidate receipt/manifest/generation checks. Candidate 0.1.16; CI and merge not yet qualified. Live original MCP remains 0.1.9 with source and artifact digest null.
- Actual #669 acceptance still BLOCKED_EXTERNAL on protected key issuer/rotation/revocation, immutable installed generation, actual process import/executable witness and independent A6/A7 rollback + same-route client ACK. No privileged host or tunnel mutation.

---
## 2026-10-16 — #669 detached signer preflight source qualification, PR #693

- Source-only 0.1.15 Ed25519 detached verifier on branch `chatgpt/669-detached-signature-source-v0115` requires a public key whose SHA256 is independently pinned. It also validates exact builder-manifest v1 schema and duplicate-key rejection; signature over arbitrary JSON is not an accepted builder proof (RMCP-F-0035).
- Initial CI 38870971649 had a real Ruff RUF059 unused test variable; repaired and logged RMCP-F-0034. New exact-head CI must be fully green before source merge.
- There is NO actual operator-trusted signer enrolment/revocation, root/issuer policy, immutable installer or serving-generation witness. Running connected MCP still 0.1.9 with null source/digest. No host/tunnel/credential actions.

---


## 2026-10-16 — #669 detached Ed25519 builder proof source child

- Main at start: `ce1a4846ce28a13569baf45a3f7fe4abd77a0c0f`, source-only 0.1.14. All previous source children #689–#692 merged, tested and marked source-only complete.
- New source-only candidate v0.1.15 on `chatgpt/669-detached-signature-source-v0115` checks Ed25519 detached raw manifest signature against a public key fingerprint supplied independently. No operator key is enrolled, no trusted signer exists, no runtime process is attested by this code.
- `cryptography` declared explicitly. Exact-head CI and PR merge pending, no production activation. Original client still 0.1.9, null source/digest. Next real #669 operational gate is trusted key custody, key revocation/freshness, immutable installation, serving process proof, rollback and original client ACK.

---
## 2026-10-16 — #669 offline source children #689/#690/#691/#692 merged; live 0.1.9 remains UNATTESTED

- Offline source versions 0.1.11 through **0.1.14** integrated as bounded sequential children; latest source squash is PR #692 `a7e3bb30d008d655ae5b8c5fdc15813303f84935`, accepted from exact tested head `8e77d9796744a19c7ebcd6a2dfa759ed7248a3f5`. GitHub validation `38864199810`, clean Ubuntu `38864199752`, attribution `38864199758` all SUCCESS before merge.
- Candidate-only chain verifies external digest-pinned builder manifest, wheel, private receipt/Python module bytes, source/wheel identity consistency and generation directory structural containment. Fixed disconnected or symlinked/group-writable package evidence (RMCP-F-0032) and group-writable wheel/module candidate evidence (RMCP-F-0033). Child TASK/STATE files updated to `COMPLETE_SOURCE_ONLY`.
- **The installed/serving runner is still 0.1.9**, confirmed by original connector build_identity with `source_revision=null` and `artifact_digest=null`. This is correct fail-closed behavior, not evidence of a production upgrade. No private host/role/tunnel/key/deploy action performed.
- Next #669 phase is genuinely gated: independently protected builder manifest hash trust custody, installed generation sealing or equivalent protected install evidence, actually loaded executable/module lineage, A6/A7 independent rollback custody, and authenticated original-client ACK. A mutable local JSON receipt or a caller-selected hash must NEVER be promoted to active provenance. Operator/qualified private host authority is a prerequisite before any live mutation.
- Post-merge `main` CI beyond exact tested PR head remains separately unverified; check in next session without mistaking absent PR workflow on main for source test failure. Umbrella #669 stays OPEN.

---


## 2026-10-16 — #669 offline evidence consistency chain, source-only

- PR #691 offline versioned generation layout source merged at `c1407cc59be940451d4024b680ffa2c257ed1518` from exact-head `06437f5b91e2ce00108630a91bdb821e408963ad`, GitHub validation/Ubuntu/attribution all SUCCESS. The original connected server remains 0.1.9 with null active digest/revision.
- New distinct child branch `chatgpt/669-offline-evidence-chain-v0114` candidate 0.1.14 composes manifest, wheel, receipt/modules and generation layout as **offline checks only**. No independent trust root, signed receipt or active serving process proof; no production mutation.
- Source child needs exact-head CI, PR and handover. Umbrella #669 OPEN for trusted pin custody, installer/immutable generation and original-client ACK/A6/A7.

---

## 2026-10-16 — #669 source progress through generation layout PR #691

- Source-only PR #690 offline pinned builder-manifest preflight merged into main at `215218cd06786838ca3e7ea86ae770b07eec4a84` after exact-head CI success (validation 38861301736, Ubuntu 38861301729, attribution 38861301743). No trusted signer or active runtime claim.
- New independent PR #691, branch `chatgpt/669-immutable-generation-preflight-v0113`, candidate 0.1.13: structural generation directory name/source/wheel identity and path/permission checks; does not attest immutable bytes or serving process. CI requires exact head green before merge.
- Original connected MCP still 0.1.9 with source/digest null. Production/tunnels/keys untouched. #669 remains open for trusted builder source, installed byte proof, live serving process generation and A6/A7 rollback/original client.

---
## 2026-10-16 — #669 builder-manifest source child in progress (PR #690)

- PR #689 source-only candidate receipt stage was merged to main at `4a7a03fb9f0785a5d8fe20e4a3ba2176b2ff508a`. Current main before next child was `f563cb49e2f3fa8db81f3239c1f118e0922ddc44`.
- New dedicated #669 source child PR #690 on `chatgpt/669-pinned-builder-manifest-v0112` (candidate 0.1.12). Performs offline validation of a SHA-256 manifest pin obtained **externally under independent trust** and wheel bytes. It never marks an active process verified and is NOT an installer or signing authority.
- The manifest comparator now hashes and parses exactly the same read bytes, fails closed on duplicate keys/deep nesting. RMCP-F-0031; tests and exact-head GitHub CI still need terminal reconciliation.
- Connected server still 0.1.9, no trusted source SHA/digest. No approved immutable venv activation, A6/A7 journal/rollback or authenticated same-route ACK. Source changes do not qualify production rollout.

---

## 2026-10-16 — #669 offline receipt source child merged; serving runtime NOT attested

- Bounded child PR #689 merged via GitHub squash at `4a7a03fb9f0785a5d8fe20e4a3ba2176b2ff508a` from exact checked source head `b2f0b0138849195cc5eba94df4c8dcef80547148`. Validation 38860034267, independent clean Ubuntu 38860034274, attribution 38860034268 and 38860276351 all SUCCESS before merge. This is **0.1.11 SOURCE ONLY**, no published release/host activation.
- Child `roadmap/children/669-artifact-receipt/STATE.md` is now COMPLETE_SOURCE_ONLY. New file candidates compare offline wheel/module hashes and atomically create PRIVATE candidate receipt; they are NOT a trusted independent build-witness and never expose active provenance as verified.
- Original connected MCP still reports version 0.1.9 with null live source/digest; Fabric A6/A7 and independent serving-generation receipt remain unqualified. Do not equate main merge or 0.1.11 version declaration to an active upgrade.
- RMCP-F-0029 and RMCP-F-0030 record the path/competition defense and actual Ruff import-sort failure/fix. #669 remains open. Next qualified lane: independent trust-root/builder manifest, immutable environment and actual serving process witness, then safe release/rollback/ACK. Post-merge `main` CI must be separately reconciled.

---

## 2026-10-16 — #669 offline receipts, 0.1.11 source-only DRAFT PR #689

- Operator-approved source lane is `chatgpt/669-offline-artifact-receipt-preflight`, PR #689; `main` remains 0.1.10 (`ff165118...`); connected serving runtime last verified 0.1.9. No host/keys/tunnel mutation.
- Offline verifier compares wheel SHA-256 and complete Python-module manifest, rejects symlinks/unlisted native modules/malformed and nonprivate receipt, and ALWAYS returns `active_build_provenance_verified=false`, null active source/digest. Candidate receipt writer creates 0600 owner-only, create-once atomic file and distinguishes uncertain effects after publish. Neither component is wired into trusted installer/serving runtime.
- Previous validated source head `93b91686d9ed0f862a6021f02e41e2e1a3b88117` had CI validation, Ubuntu install and attribution SUCCESS. Subsequent source fixes add explicit absolute-path enforcement, `..` rejection, linked-ancestor rejection, real concurrent create-once race test, and associated regressions, recorded RMCP-F-0029. Latest code/test head `1a53ddc81f53e1755bfe845441ebb02df605a7af`; its CI still requires exact-HEAD qualification.
- Blockers: trusted independent build manifest/verification, immutable release environment, installer-generated evidence bound to wheel/modules and executable generation, actual serving-process verification and original ChatGPT same-route ACK. A6/A7 rollback authority separately qualified. Keep #669 open / PR #689 DRAFT, no production deployment.
- Next bounded action: reconcile exact PR head and its CI; fix genuine failing test if present. Then prototype verified builder receipt issuance under independent trust root; do NOT promote a self-declared receipt into runtime build identity.

---

## 2026-10-15 — live 0.1.9 confirmed; tunnel runtime identity remains unqualified

- Original connected client now reports loaded Runner-MCP **0.1.9** and its installed distribution 0.1.9. `fabric_bridge_preflight` returns `ready` with Fabric source `51c37f1eac65951e15a5122b89f368aa6e18c1f5`; `fabric_host_inspect` and `fabric_operational_snapshot` now return bounded results. Fabric relay status remains honestly `degraded=true` with `agent-bus.relay` unknown. This supplies live follow-up evidence for regression #681, but does not prove original-client ACK after a controlled version rollout.
- `runtime_doctor` returns 1 FAIL (`self_update_runtime_activation:active_revision_unavailable`) + 3 warnings. This is **intentional fail-closed #669 behavior**: `build_identity.source_revision` and `artifact_digest` are null because installed/loaded wheel provenance is not independently attested. Do not substitute historical `self-update-state.json` commit for the active process.
- `tunnel_topology_refresh` returned `blocked/runtime_identity_unavailable` on the same connected client. Source fix in progress on this child branch for v0.1.10: classify missing `tunnel-health.url`, unreadable local health endpoint, invalid JSON/schema, absent/invalid process instance ID **using exactly the existing loopback GET**, before any credential-bearing topology heartbeat. Do not assume missing local health means another host owns the tunnel. No tunnel, server or key mutation here.
- Fabric A6 binding remains `not_configured_0_of_11`, self-update is not qualified, and Q7 Claude host/listener is not admitted. Live host routes, independent rollback and installed artifact digest must be verified before new update. No mandatory external code reviews; exact HEAD CI and protected operational gates continue.

---

## 2026-10-15 — 0.1.9 code merged, active 0.1.8 unchanged; manual stage BLOCKED_EXTERNAL

- Original ChatGPT connector verified active Runner-MCP 0.1.8, healthy `fabric_bridge_preflight` with fixed Fabric revision `51c37f1eac65951e15a5122b89f368aa6e18c1f5`, two available test workers and an idle test queue. `fabric_host_inspect` still responds `fabric_inspection_unavailable`; `fabric_operational_snapshot` still fails via the original connector. The Fabric agent's direct local read-only functions succeeded in the earlier physical test, with the honest snapshot `degraded=true` (relay unknown). **The live regression #681 remains OPEN.**
- Source-only fix for absent optional peer tools and wrong component ID is merged as [Runner-MCP PR #683](https://github.com/Blacksp1d3r/runner-mcp/pull/683), squash `e7cb9162d686b5992b3862a4b61f85980cbdfbd4`, version **0.1.9**. Exact PR HEAD `b7e58d67a8e7164a38e1dbd1294c82f331e6ece5`; validation `38630452366`, independent clean Ubuntu install `38630452355` and attribution `38630452496` all SUCCESS. Four version registry files were independently checked against merged main.
- Runtime `self_update_ready=false`, active artifact digest/source attestation unavailable (#669), doctor 1 fail (active revision unavailable) + 3 warnings. Therefore **no stock self-update**. The unapproved source PR CI artifact is not an approved production release. Fabric A6/A7 #942/#943 are separate unqualified fleet gates.
- An operator-local **stage-only** Python helper is prepared outside GitHub and syntax-checked. It pins exact merged main commit 0.1.9, builds a wheel beside active 0.1.8, validates version, installed code checksums and six-role candidate cron bytes; it explicitly does not change the launcher, cron or tunnel. A separate offline root activator prototype is also syntax-checked to arm a persistent independent rollback timer before any six-role switch. **Neither helper was run on the private host; wheel receipt/physical timer do not yet exist.** Script source/artifact remains in the current private ChatGPT conversation, NOT the public repo.
- **BLOCKED_EXTERNAL next:** owner uses an authorized private computer and runs stage-only helper on designated host; compare receipt, exact active executable and signed source identity. Only then prepare operator-approved maintenance window, inspect persistent supervisor/rollback under root, activate six roles once, prove original-client host/snapshot, and disarm rollback after independent checks. If acceptance fails, allow independent rollback and do not close #681. No remote broad-shell replacement, token disclosure or paid model call authorized.
## 2026-10-14 — Runner-MCP 0.1.8 cutover plus Fabric bridge regression

- Operator completed controlled pinned Runner-MCP `0.1.8` standalone release activation with independent rollback timer, six autostart role-lock/executable checks (four direct Python CLIs, two Fabric children), and original connected client version/health verification. One systemd-owned tunnel retained; duplicate cron tunnel disabled. Rollback timer disabled after confirmed checks. No claim of physical rollback fault-injection.
- Managed local-custody Fabric update to `51c37f1eac65951e15a5122b89f368aa6e18c1f5` completed and both Fabric cron children restarted into new slot. Original Runner-MCP connector sees Fabric handshake `ready` at exact revision, with no active/queued test jobs and two configured test workers.
- Regression after Fabric restart: original connector host-inspect `fabric_inspection_unavailable` and operational-snapshot tool error, although same Fabric slot local host inspection succeeds and its snapshot returns `degraded=true`, relay UNKNOWN. See new bounded diagnostic #681, topology and RMCP-F-0028. Source analysis: full bridge's reconnect path may mistakenly demand optional A6/synthetic tools despite preflight allowing absence; exact live root cause requires isolated session/catalog evidence. Keep no replay after stale unknown-effect failure.
- Active Runner-MCP wheel revision/digest unverified by design (#669); doctor 1 fail + 3 warn. Fabric A6/A7 host-level independent rollback/notifier not verified (#942/#943). No bridge authorization weakening, unbounded shell, host mutation or new tunnel.
- Documentation branch `docs/topology-live-update-20261014`; GitHub merge/CI remains to qualify separately. Next: safe #681 bounded source test and original path acceptance; topology documentation alone is not the repair.
## 2026-10-10 late reconciliatie — issue #540 extern CLOSED, live #590 blijft OPEN

Na volledige broncode-merge van #651 en handover heeft een afzonderlijke actor/werklijn issue [#540](https://github.com/Blacksp1d3r/runner-mcp/issues/540) om 2026-10-10 21:10:33 UTC met `state_reason=completed` gesloten; issue-evenementen bevestigen de sluiting, maar de hier beschikbare first-party connected probes bewijzen nog **niet** dat de live geïnstalleerde MCP-server, clientcatalogus en antwoordaflevering overeenkomen. De Runner-MCP-communicatiechat **heropent of overschrijft #540 niet**. Eerder genoteerde #540 OPEN is nu historisch/verouderd; behandel #540 als CLOSED (source/other-owner decision), niet als operationeel bewijs voor #590.

Runner-MCP [#590](https://github.com/Blacksp1d3r/runner-mcp/issues/590) blijft OPEN: eerst een geautoriseerde private exacte actieve build/catalogus en één bekende geslaagde + één falende verzoek-ID door ingress/dispatcher/serveraudit/response-delivery/oorspronkelijke client; voor vervanging blijven Fabric A6 #942 en A7 #943 aparte live uitrolgates. Geen productie- of tunnelwijziging.

## 2026-10-10 evening — Runner-MCP #590 loopback bearer egress source fix PR #651 merged

[PR #651](https://github.com/Blacksp1d3r/runner-mcp/pull/651) MERGED squash `68093ab85bee293a8cc7616340d2893d5e4c24a0`, reviewed exact head `d588c72619fc277d8423b680f473c8d62e3c992a`. Commit attribution `38086367280` SUCCESS; full validation `38086367281` SUCCESS (Ruff, **2813 pytest**, built release artifact, clean demo). Fixed `LocalMCPClient._post` standard `urllib.request.urlopen` proxy/HTTP 30x bearer egress risk by using a fixed `ProxyHandler({})` + `_NoLocalMCPRedirects` opener through a single testable `_open_local_mcp_request` seam. Unit negatives cover hostile HTTP(S)/ALL_PROXY environment, redirects 301/302/303/307/308 to off-host and same-host destinations, single-call/no-redirect behavior, sensitive error redaction. Historical bridge tests now inject the bounded seam. Preserves #650 stale-session unknown-effect no-replay and exact build/schema requalification on subsequent separate explicit caller request.

Child `roadmap/children/590-local-mcp-transport-egress/{TASK,STATE}.md` COMPLETE_SOURCE_ONLY; Failure Museum RMCP-F-0024 SOURCE_FIXED_LIVE_UNQUALIFIED. **No real bearer exfiltration/compromise has been observed.** **No live host/tunnel/service/credential deployment was performed.**

Next actual #590/#540/#381 live acceptance remains **BLOCKED_EXTERNAL**: privately qualify active installed process build + registered client catalog + original one-good/one-failing opaque MCP request through admission/dispatcher/server audit/response-delivery/client; Fabric A6 #942 off-target journal and A7 #943 independent rollback/ACK required before any controlled fleet release. Fabric #1398/#1400 issuer/leases owned by Fabric chat; AIfordable #370 real dedicated service and Fabric #972 real Q7 also pending. NO_DISPATCH Claude/EnerCue #89. Avoid speculative restarts, tunnel changes and replays.

## 2026-10-10 end-of-session egress source audit — RMCP-F-0024 OPEN

Independent offline Python stdlib inspection verified that default `urllib.request.HTTPRedirectHandler.redirect_request` on 301/302/303 POST forwards the original `Authorization` header on the resulting GET (only content-length/content-type omitted). Default `urllib.request.build_opener` includes ProxyHandler plus HTTPRedirectHandler. Runner-MCP `LocalMCPClient._post` currently uses `urllib.request.urlopen` with the local Bearer attached; original loopback endpoint validation cannot alone prevent an inherited proxy or redirect egress. Central Failure Museum **RMCP-F-0024** recorded as `OPEN_SOURCE_RISK_NO_LIVE_LEAK_PROOF`; GitHub #590 comment filed. No network request, raw token, actual redirect, leak or process compromise observed. Next source child `roadmap/children/590-local-mcp-transport-egress/{TASK,STATE}.md` UNCLAIMED, model safe fixed no-proxy/no-redirect opener after Fabric source #1446, with synthetic hostile env/redirect regressions. This is *separate* from fully merged PR #650 no-replay fix and still requires A6/A7 before any installed rollout.

## 2026-10-10 late — #540 fixed unsafe stale MCP tool replay (PR #650 MERGED); live #590 still blocked

**Real Runner-MCP source security defect corrected:** [PR #650](https://github.com/Blacksp1d3r/runner-mcp/pull/650), exact reviewed head `154b9444a1ea67023588ce75fdc86628687e60ff`, attribution `38085233372` and review `38085481144` SUCCESS, full validation `38085233326` SUCCESS (Ruff + **2781 pytest** + release artifact + clean demo), squash MERGED `8608ddde46f228d045d64189f12e7464a1919fb9`. Source `LocalMCPClient._call_tool` had automatically resent the *same* old tools/call after a stale MCP HTTP 404 (including potentially mutating calls). HTTP 404 from an intermediary cannot prove the prior work had no effect. New code NEVER transparently replays: fixed `MCP_SESSION_STALE_EFFECT_UNKNOWN_RECONNECT_REQUIRED` exception; discards session/peer metadata, requires exact `tools/list` + `build_identity` requalification on the next **separate** explicit caller request (even if preflight was initially optional); failed reconnect preflight clears partially accepted session; mismatch blocks before any tool action. Source tests cover 6 tool types including writes, mismatched build and verified fresh explicit request. Child `roadmap/children/540-stale-session-no-replay/{TASK,STATE}.md` COMPLETE_SOURCE_ONLY; Failure Museum RMCP-F-0023.

**Fresh connected runtime read-only probe this session:** one `list_projects` returned six safe staging projects, but `project_status(runner-mcp)` returned the generic internal connector error; joined two-call script also failed generically without request lineage. That proves partial access, not first failing edge or active version. Old 12-check `runtime_doctor`, opaque `runtime_status`, and missing source Q7 preflight were previously observed; this current installed runtime/catalog/route STILL UNQUALIFIED. #590/#540 and Claude #381 remain OPEN. No live process/tunnel, service, credential or provider mutation; full A6/#942 off-target journal and A7/#943 disconnected rollback plus live exact process/catalog fingerprints and correlated request->delivery proof still required before protected rollout. Fabric #1398/#1400 owned by Fabric chat, AIfordable #370 and Fabric #972 own physical real Q7 proof. NO_DISPATCH/EnerCue #89.

**Next independent source security child identified (not yet implemented):** `roadmap/children/590-local-mcp-transport-egress/{TASK,STATE}.md`. Current `LocalMCPClient._post` uses default urllib `urlopen`, which may honor environment HTTP proxies or HTTP 3xx redirects after bearer authorization despite loopback-only configured endpoint. Fabric source [#1446](https://github.com/Blacksp1d3r/Runner-Fabric/pull/1446) already uses no-proxy/no-redirect opener for analogous Q7. The Runner-MCP child is UNCLAIMED pending post-#650 fresh base/owner scope and its own synthetic CI; this is a SOURCE risk, **not** a proven live bearer disclosure. Avoid modifying the same file until reconciling #650 merge. No automatic retries, proxy bypass, generic shell or live actions.

## 2026-10-10 late evening — #590/#540 in-process MCP transport and catalogue proofs DONE; production unknown

Runner-MCP [PR #648](https://github.com/Blacksp1d3r/runner-mcp/pull/648), exact head `403eedf2429fda7d4b84839aa70790a3a6e71ae5`, attribution `38075662830` SUCCESS, full `38075662792` SUCCESS (Ruff/2773 pytest/artifact/demo), squash MERGED `16f3dc9f118f7a02747a3050fe7409bc7fe3c32e`: real isolated authenticated MCP HTTP same-session good `list_projects` + synthetic degraded `runtime_status`, distinct X-Request-IDs and W3C child spans, JSON-RPC results and exactly matching non-secret audit record. Child `roadmap/children/590-mcp-response-audit-lineage/{TASK,STATE}.md` COMPLETE_SOURCE_ONLY. First red CI head failed only because test assumed the MCP list was nested under one JSON array; fixed before exact-green CI; Failure Museum RMCP-F-0022.

Runner-MCP [PR #649](https://github.com/Blacksp1d3r/runner-mcp/pull/649), exact head `8c0ad02ac315e28b7f09e69e09fe0846053f26ea`, attribution `38076184097` SUCCESS, full `38076184096` SUCCESS (Ruff/2774 pytest/artifact/demo), squash MERGED `2a8ca54272fe6cf1cc12a2f2aa7919caf8481359`: same authenticated isolated MCP session `tools/list` *actual advertised* names+inputSchema+outputSchema independently produce exact `build_identity.interface_schema_digest` hash. Child `roadmap/children/540-advertised-schema-digest/{TASK,STATE}.md` COMPLETE_SOURCE_ONLY.

**Live #590/#540 remain OPEN:** installed process/source SHA, client cached tool generation, true route, ingress/audit and response-delivery ACK unqualified. Earlier connected client: `list_projects` success six staging projects; `runtime_doctor` old 12-check WARN; `runtime_status` generic internal error; source-merged Q7 preflight not advertised. #648/#649 only exclude source inconsistency on synthetic in-process tests, not stale installed host/client or reply mismatch. Next requires operator-approved *private read-only* exact running-process build/tool schema plus one-good/one-failing opaque request correlated client→dispatcher→installed MCP audit→delivery→originating client; no guessed remote host/tunnel. Fabric #942 A6 off-target journal + #943 A7 independent rollback remain OPEN and block fleet live release. #642 host admission separately owned; Fabric #1398/#1400 externally owned, AIfordable #370 and Fabric #972 real Claude Q7 pending. #381 stays OPEN; Claude/EnerCue NO_DISPATCH. No host/tunnel/service, credential, or paid API mutation this turn.

## 2026-10-10 evening — #590 exact-request response/audit SOURCE proof #648 MERGED, live tunnel still OPEN

[PR #648](https://github.com/Blacksp1d3r/runner-mcp/pull/648), reviewed head `403eedf2429fda7d4b84839aa70790a3a6e71ae5`; attribution run `38075662830` SUCCESS, full validation `38075662792` SUCCESS (Ruff, 2773 pytest, built release artifact, clean demo), squash `16f3dc9f118f7a02747a3050fe7409bc7fe3c32e`. Source-only child `roadmap/children/590-mcp-response-audit-lineage/{TASK,STATE}.md` COMPLETE_SOURCE_ONLY. One authenticated in-process MCP session proves success `list_projects` and synthetic degraded `runtime_status` each yield distinct `X-Request-ID` and unique W3C spans, exact matching JSON-RPC answer class + audit entry, without leaking private-looking manager errors. Initial red test only misread the MCP project list item framing, fixed at exact-green HEAD; Failure Museum RMCP-F-0022 records it. No deployed host/service/tunnel/code rollout from this test.

**Remaining operational #590:** actual ChatGPT-connected release/host/client catalogue/return-route identity remains unqualified: previously observed `list_projects` structured success, older 12-check `runtime_doctor`, `runtime_status` opaque failure, source-merged #643 Q7 preflight absent from connected advertised tool set. Need owner-approved FIRST PARTY private read-only exact process build/catalogue/schema fingerprint and one known-good/one failing opaque-ID request mapped through authenticated client admission → dispatcher → installed server/audit → response-delivery ACK → client. No assumption that local TestClient proof equals live tunnel. Release A6 #942 and independent rollback A7 #943 remain OPEN; no unapproved deployment or guessed restart. Runner-MCP #540 session generation and #642 host permission must not be bypassed. Fabric #1398/#1400 delegated Fabric chat, AIfordable #370 physical worker and Fabric #972 real Q7 owner are external. #381/#590 OPEN; Claude/EnerCue NO_DISPATCH.

## 2026-10-10 late — Runner-MCP Q7 communication source repairs FINISHED; live rollout BLOCKED

Operator confirmed Fabric chat owns #1398/#1400; Runner-MCP chat owns Q7 communication side. [PR #646](https://github.com/Blacksp1d3r/runner-mcp/pull/646) source MERGED `a8833190b62e1ace6d88617951116cca541cf8ba` (exact head `e196f38208abf1704dd7c2d815679c03a656170c`, attribution + full `38073594605` SUCCESS, Ruff, 2768 pytest, artifact, demo): known first-party Q7 failures now return fixed safe `runner-mcp/coding-availability-qualification-unavailable/v1` with separately classified confirmed `not_started` vs uncertain `unknown` execution effect. Both result/dispatch/retry unverified/disallowed; previous handler threw one generic ValueError. [PR #647](https://github.com/Blacksp1d3r/runner-mcp/pull/647) source MERGED `d078781d28f98398359e4db163dd8c248a77264d` (exact head `ea6e27bb1b3dcfe256b561ff8955bf31c0cdd768`, attribution `38073911858`/`38074186402` SUCCESS, full `38073911864` SUCCESS, Ruff, 2772 pytest, artifact, demo): Q7 positive response requires `assignment_requests` to be exact integer 1, denies JSON true/1.0/string "1" numeric spoofing. New independent child TASK+STATE complete source only, diagnostics RMCP-F-0020 and RMCP-F-0021 tracked.

**Live communication still unqualified:** one connected read-only trio showed structured `list_projects` (six staging), older 12-check `runtime_doctor` WARN, opaque `runtime_status` error; source-merged #643 Q7 preflight absent from connected advertised catalogue. This indicates unresolved installed-version/catalogue/response-path identity; does not prove which host/client route is wrong. #590/#540/#642 need approved private exact installed build/tool-schema/per-request ingress↔response-delivery proof, safe Fabric A6/#942 and A7/#943 rollout, no broad remote shell or speculative restart. Fabric #1398/#1400 trusted issuer/lease/fence, AIfordable #370 right-host rootless worker, Fabric #972 actual authenticated Q7/Agent Bus ACK remain separate owner gates. #381 operational OPEN, Claude/EnerCue #89 NO_DISPATCH, no host/service/tunnel/credential/paid API calls.

## 2026-10-10 evening — Q7 communication fixes (#381); Fabric lease/fencing stays with other chat

User explicitly assigned Fabric #1400/#1398 to Fabric chat; Runner-MCP chat resolves independent Q7/MCP communication defects without changing shared host or Fabric authority. New [PR #646](https://github.com/Blacksp1d3r/runner-mcp/pull/646) MERGED as `a8833190b62e1ace6d88617951116cca541cf8ba`, exact HEAD `e196f38208abf1704dd7c2d815679c03a656170c`, attribution `38073594611`+review `38073697157` SUCCESS and full `38073594605` SUCCESS (Ruff, **2768 pytest**, release artifact, clean five-minute demo). Fix: Q7 known handler errors are now fixed sanitized typed results with `qualification_effect=not_started|unknown`, `result_verified=false`, `dispatch_authorized=false`, `retry_authorized=false`. Application-level failures no longer collapse to generic ValueError, while uncertain post-launch side-effects are NOT blindly retried. `roadmap/children/381-q7-communication-errors/STATE.md` COMPLETE_SOURCE_ONLY. Failure Museum RMCP-F-0020 records the source-only correction.

Separate [PR #647](https://github.com/Blacksp1d3r/runner-mcp/pull/647) exact HEAD `ea6e27bb1b3dcfe256b561ff8955bf31c0cdd768` adds stricter integer-type check for Q7 `assignment_requests`: Python `True == 1` and `1.0 == 1` could falsely count as exactly one worker assignment. Unit regressions now reject bool, float and string. Attribution `38073911858` SUCCESS; Ruff and **2772 pytest** PASS; artifact/demo in progress at this checkpoint; no merge until all exact-head green. Distinct child `roadmap/children/381-q7-assignment-count/{TASK,STATE}.md`, source only.

Live connected read-only MCP still returned structured six-project `list_projects`, legacy 12-check `runtime_doctor` WARN and opaque failing `runtime_status`. New source-merged `fabric_coding_availability_preflight` (#643) is absent in the connected tool catalogue. Thus installed process/catalogue/response route has **NOT** been qualified (#590/#540/#642). New #646 code cannot repair a failure before handler invocation or become live by source merge. Fabric A6/A7 protected fleet exact release + separate private per-request ingress→response-delivery proof is needed, without speculative tunnel/host restart. Fabric #1400/#1398 trusted durable issuer/lease/fence; AIfordable #370 actual right-host Claude user-service; Fabric #972 authenticated real Q7 return remain OPEN. Runner-MCP #381 stays operationally OPEN and Claude/EnerCue #89 NO_DISPATCH. No host/tunnel/services/credentials, paid provider or protected storage mutation.

## 2026-10-10 evening — Claude #381 fixed listener provenance PR #645 MERGED; trusted Fabric authority still blocks operational closure
Operator asked to actually finish [Runner-MCP #381](https://github.com/Blacksp1d3r/runner-mcp/issues/381). Source-only security slice [PR #645](https://github.com/Blacksp1d3r/runner-mcp/pull/645) implemented exact fixed rootless `systemd --user` MainPID-to-socket-inode corroboration: unknown/foreign/reuse-port/PID drift fails closed without successful service observation. Branch exact HEAD `446a1edc8129a51421a6ef1b6516f2a84e1ab93f`; exact-head attribution `38071120207` and review `38071261321` SUCCESS; full validation `38071120259` SUCCESS (Ruff, **2752 pytest PASS**, built release artifact, clean demo); squash MERGED `e29105cf6ed5baed42849dcdc8d706df97b182bc`. Original red first-head pytest was caused by double-escaped synthetic fixture newlines only (2744 other tests passed); fixed on exact green head. New independent `roadmap/children/381-fixed-service-listener-owner/{TASK,STATE}.md` SOURCE_COMPLETE. Failure Museum RMCP-F-0019 indexed with strict limits.

**External dependencies as of this review:** Runner-Fabric #1400 and #1398 OPEN — no trusted shared durable cross-host lease/fence and signed or authenticated lifecycle issuer/JIT executor; #1172 OPEN and #1422 design DRAFT. Fabric #1433/1446/1447/1448 source MERGED, but #1448's real HTTP is to isolated synthetic MCP peer only, NOT real installed AIfordable service. AIfordable #370 OPEN — packaged right-host rootless service start/status/stop/disabled/listener-gone receipt unverified. Fabric #972 OPEN — real same-route authenticated Q7/Agent Bus return path not proven. Runner-MCP #643 source-merged read-only Q7 preflight unavailable in current connected client's tool schema; live `build_identity` gave generic internal failure while `fabric_operational_snapshot` returned degraded=true, agent-bus relay evidence unavailable, `execution_enabled=false`, `mutation_enabled=false`. No installed host/catalogue/version proof.

**DO NOT CLOSE #381 or start Claude/EnerCue #89.** This PR does not create trust authority, live PID/host qualification or network endpoint. Local MainPID check remains non-atomic and may fail closed if worker delegates listener to another process; do not bypass by interpreting numeric port alone. Next required sequence: Fabric #1400/#1398 trustworthy, durable enrolled issuer+lease/fence with JIT checked right-host mapping -> operator-authorized AIfordable #370 correct-account fixed unit qualification and process/listener receipts -> Fabric #972 real authenticated Q7 synthetic return -> separately approved bounded Claude worker dispatch. No shell/host/service/tunnel/credential/protected storage/provider API change from this lane. #630/#634 belongs to other chat; never clobber its source.

## 2026-10-10 evening — Claude Q7 diagnostics source landed; execution still NO_DISPATCH

User priority: use the ALREADY installed Claude Pro subscription-backed worker, ideally for EnerCue P6A.1 #89. Do not install a second Claude or create a second scheduler; no Anthropic API/pay-as-you-go fallback, generic shell/host/admin, identity rewriting or automatic PR merge.

Actual connected read-only evidence from this chat on the github-runner Runner-MCP route:
- `build_identity`: `0.1.3`, source revision `a0fd964c4a6fe7e0a1506a513e9b2b4059c5453a`, fixed interface schema digest `711f96eb3d9cc5dcd2c6476f87ab70f34b69dc87c394b33d0d5b4ae8f308045f`; cannot conclude other distinct lab instance has the same code.
- One `fabric_coding_availability_qualify(subscription-auth-required, bfc5c3313a2d3fe2552ff95ea19f1415e4c1f5a9)` failed with opaque MCP error. This is **not proof Claude subscription OAuth failed** or a real Q7 round-trip, and its expected revision was a previously recorded AIfordable qualification revision, not independently verified current running source.
- `runtime_doctor` succeeded: `warn`, zero failed checks, three warnings: `fabric_continuity_status_configuration_unavailable`, `fabric_worker_qualification_readiness unavailable`, `migration_job_storage not_configured`. Explicit continuity warning is about fixed local source/CI continuity configuration (four required env binding keys), **not proven causal for Agent Bus worker routing**.
- Read-only `fabric_operational_snapshot` intermittently errors but then succeeded with `degraded=true`, `unknown_layers=[agent-bus.relay]`, `reason_code=evidence-unavailable`, `execution_enabled=false`, `mutation_enabled=false`; still NO_DISPATCH. `worker_status` test-worker capacity does NOT prove coding-worker readiness.
- AIfordable #370 evidence previously proved dedicated aifordable-coder subscription-only synthetic edit→proposal→Fabric registration (one changed path, safe retry, no paid API). Qualification listener deliberately stopped afterward; this is NOT persistent rootless worker admission. Runner-MCP #381 dedicated fixed actuator and Fabric #972 authenticated live loopback/lease/fence/return path remain open.

Delivered and **MERGED** source-only Runner-MCP PR [#643](https://github.com/Blacksp1d3r/runner-mcp/pull/643), squash `edbe8a78f82019635aff5b5795d6d126ceee99a6`, exact-head CI commit attribution `38066933996` SUCCESS and validation `38066934022` SUCCESS (Ruff, pytest, build/install, five-minute demo). Adds `fabric_coding_availability_preflight()`, zero-arg READ-ONLY safe local Q7 launch/config/operator-stop classification: `blocked/operator_stop_active`, `blocked/operator_safety_unqualified`, `wait/fabric_launcher_unqualified`, `wait/q7_private_configuration_incomplete`, or `ready-for-qualification/bounded_q7_preflight_passed`. Response always `qualification_executed=false`, `provider_session_checked=false`, `dispatch_authorized=false`. New tool does not exist on old active host until independently approved *same secure generation* fleet update; do not equate source merge with deployment.

Fabric [#1446](https://github.com/Blacksp1d3r/Runner-Fabric/pull/1446) squash `6b3081560968ccc41471815ef344450bc48b5fb6` merged exact-head Foundation/attribution SUCCESS, rejects HTTP redirects and environment proxies for bearer-authenticated worker loopback. No live host/tunnel was changed.

Next: independently qualify correct host dedicated account/service lifecycle #370/#381, real authenticated Q7 availability #972 and shared durable Fabric issuer/lease/fence #1398/#1400. Preserve A6 #942/A7 #943 independent safe fleet update gate and uniform Runner-MCP security code #1439. EnerCue #88/#89 stays unclaimed/no model task started until actual qualified same-route admission. Cross-project AGENT_EXCHANGE and diagnostics updated separately.

## 2026-10-10 — F30 common security code / host tool admission (SOURCE ONLY; live fleet still divergent)

Operator binding: every enrolled Runner-MCP installation must converge to ONE exact promoted source/artifact/tool-schema release. Host-specific permissions remain explicit local denials, not missing tool names; no separate code generations for small workers. Observed two intentionally distinct installed MCP instances 123 source commits apart and 63 vs 68 source tool declarations; present development main has 69. PyPI version remains 0.1.3 on both. Primary installed source was modified after process start, so loaded process identity remains UNVERIFIED. Connected `runtime_status` errors have unlocated failure edge (#590); do not claim that divergent sources caused them or invent a second tunnel.

Merged source-only PR [#641](https://github.com/Blacksp1d3r/runner-mcp/pull/641), squash `4e32a260d46bb28bbcfafbf3556e4ced80a486a7`: `host_tool_admission.py` evaluates fixed `HOST_TOOL_NOT_PERMITTED` unless exact registered tool names, active process release SHA/schema digest, expiring separately qualified host policy and explicit per-tool grant all agree. Tests prove same catalogue with denied primary OCR and potentially permitted lab OCR; stale runtime/unknown/expired/mismatched catalogue or shared high-risk tool is denied. Exact-head commit attribution `38065390605` and Runner MCP validation `38065390596` (Ruff, pytest, wheel build/install, five-minute clean demo) SUCCESS before merge.

**NOT YET ENABLED:** PR #641 is a pure admission decision, not wired into MCP dispatch. New child [#642](https://github.com/Blacksp1d3r/runner-mcp/issues/642) tracks trusted host binding, actual active process build/catalog identity, fixed audited tool-denial responses, negative/positive first-party live test and correct response-return lineage. Previous docs policy PR #640 remains OPEN after tool safety blocked merge; do not pretend it landed or bypass tool safety. No service, token, tunnel or host changes took place.

Fabric A7 #943 was re-opened after premature completed marking. Merged Fabric source-only #1443 offline fsynced idempotent watchdog, #1444 independent prior-wheel escrow with exact receipt binding, #1445 isolated end-to-end disconnected synthetic rollback. Real separate on-host watchdog, source/wheel/service restore actuator and physical A6 #942 off-target journal/ACK/rollback tests remain OPEN. Runner-MCP #341 owns fixed host execution; Fabric alone schedules fleet updates. Operational central database/verified backups and tenant/lease authority are not proven. Do NOT automatically roll live protected hosts until A6/A7 recovered-control-path proof and qualified canary are complete.

## 2026-10-10 afternoon — #638 real JSON Schema proposal regression LANDED; physical authority unchanged

Independent BPA-02-T source-test [PR #638](https://github.com/Blacksp1d3r/runner-mcp/pull/638), exact reviewed head `3c02f04167075e59f6d872359ce1b404b02c90cc`: attribution `38052880661` SUCCESS, validation `38052880714` Ruff/pytest + built artifact + clean five-minute demo all SUCCESS, Clean Ubuntu installer `38052880727` SUCCESS; squash MERGED `5231c6814d8bc80d9ddc7eba7a2e5fb44212e708`. `roadmap/children/bpa-02-schema-validation/{TASK,STATE}.md` and child index now mark COMPLETE_SOURCE_ONLY. Existing `tests/unit/test_repository_manifest_candidate.py` had self-tested with a bespoke miniature interpreter; now uses dev-only OSS `jsonschema>=4.23,<5` and real `Draft202012Validator.check_schema/validate` with synthetic fail-closed negative cases. No changes to proposal YAML/JSON schema or executable runtime configuration; Failure Museum RMCP-F-0018.

**Live authority remains BLOCKED.** #630/#634 still OPEN: no proven Git primary/single writer, physical isolated restore, independent storage receipt, correct Fabric lease/fence or operator approval; root `project.yml` remains absent. #590 installed build/tunnel request↔response lineage still unverified; #587/#588 physical backup/restore still unproven, preserve GitHub artifacts. #381 is exclusively under another active chat (that chat's #637 source changed main before this task; do not duplicate). Fabric #1428 and PR #618 remain separate owner/review lanes. No production host/tunnel/service/mount/credential/deletion/Claude action took place.

Next: #634 owner-approved private read-only Git/storage evidence and isolated restore in its own lane; #590 approved installed build/catalog plus opaque request↔response correlation. A docs/source CI pass never grants deployment or storage authority.

## 2026-10-10 — #381 operator-priority Claude source security PR #637 MERGED; live trust chain still BLOCKED
Runner-MCP #381 remains operationally OPEN and actively owned by this Claude lifecycle chat, distinct from the other chat's blueprint #630/#634 lane. After source baseline PR #628, independently implemented fixed lifecycle pre-action consistency: [PR #637](https://github.com/Blacksp1d3r/runner-mcp/pull/637), exact HEAD `e8e696d880729705c1e88a2055d60828fc66558a`, attribution `38052268180` SUCCESS, complete `38052268203` SUCCESS (Ruff, 2701 pytest passed, built artifact, clean demo), squash MERGED `16230a35698abf43d274cae27150ad0eeecce3b9`. New `roadmap/children/381-preaction-snapshot/{TASK,STATE}.md`: SOURCE COMPLETE, LIVE BLOCKED. Before action, START needs fixed service INACTIVE+listener ABSENT; STOP/RESTART needs ACTIVE+LOOPBACK_ONLY. Wrong/occupied port, duplicate action, transitional or failed service blocks before command. No new MCP endpoint/sudo/host install; no real PID ownership attestation, lease approval or production status from CI. Failure index RMCP-F-0017 and component failure register updated.

Cross-owner CURRENT: Fabric #1432 source-only typed exact intent preflight merged `2b108339aa0726ed6e541cf39114fd80952a2191`, always mutation_authorized=false. Fabric #1433 receipt correlation draft head `dd51a436fdf0d90b06d9599338801611bb28194a`, never execution-authorizing. AIfordable #555 rootless lifecycle evidence runbook merged `41326016bdddcdaf5cb05241de0774bebb12c4c7`. **Real** Fabric trusted issuer/lease/fence/JIT external #1172/#1400/#1398 remains open; canonical lifecycle design #1422 is still DRAFT; AIfordable #370 real fixed right-host rootless start/stop receipt remains open; Fabric #972 exact authenticated same-route availability and return proof remains open. Claude/EnerCue #89 NO_DISPATCH and no paid provider API fallback. Do not treat source CI or fixed listener presence as actual safe live worker readiness. No host/service/tunnel/storage/credential actions performed.

Next #381 owner-safe action once Fabric single-plane durable signed verifier available: bind only its exact enrolled target to fixed dedicated-host actuator, independently prove service/PID ownership + loopback and STOP gone with AIfordable owner, then Fabric #972 correlation/lease/fence synthetic admission. No generic cross-user systemctl or duplicated Fabric scheduler. Other independent #630/#634 and #587/#588 lanes not modified.

## 2026-10-10 afternoon — #590 mixed-result connected probe evidence MERGED (no #381 work)

[PR #636](https://github.com/Blacksp1d3r/runner-mcp/pull/636) exact head `e35513459760107e0e555f66313360b5f5884fbc`, attribution `38052251708` SUCCESS and full validation `38052251712` Ruff/pytest, built artifact, clean demo all SUCCESS; reviewed, squash MERGED `74faab4c1a5f1b9111cf0c847e2e931af91d2619`. New `docs/diagnostics/CONNECTOR_PROBE_MATRIX_2026-10-10.md` and canonical triage/Failure Museum updates record one connected session's bounded facts.

Structured responses: `list_projects` includes runner-mcp in six staging projects; `project_capabilities` generic adapter/project root available; `queue_status` zero queued/claimed/running and two available workers; `safety_status` operator stop inactive; `runtime_doctor` WARN with only 12 checks, 0 failures and 3 warnings. Generic tool errors for `build_identity`, `project_status`, `worker_status`, file metadata, project preflight and Fabric mirror/bridge/host readiness; some private Fabric preflights surfaced only generic nested `INVALID_ARGUMENT`. Same source `cfg.public_summary` supports list/status projection, so classification is **mixed-success unlocated ingress/dispatch/serialization/return-lineage**, NOT a proven bad Git project, total tunnel outage, correct installed generation or qualified physical storage.

#590 is **OPEN** for approved operator-private installed build/schema/client catalog fingerprint and single known-good vs failing request with opaque ingress/dispatch/delivery correlation; do not restart/update/rotate keys or invent host identity. #634 / #630 remain **OPEN/BLOCKED_EXTERNAL_AUTHORITY** for actual local Git primary, one-writer fencing and isolated restore. `project_root_available=true` does not qualify primary or independent archive. #587/#588 remain physically unproved; preserve provider artifacts. #381 work exclusively belongs to the separate active chat; no competing branch/runner/Claude tasks touched. No production mutation or private topology exposure.

Next safe external operator step: perform the authorized read-only first-divergent-edge correlation for #590 or approved private source authority admission for #634; independently assigned reviewers handle PR #618 and Fabric #1428. Avoid a new source-only code fix until the installed generation and failing edge are known.

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

## 2026-10-10 — Runner-MCP main after PR #626
#626 safety(#587): final independent archive mirror verification is **MERGED** via `5aba8423594290a7837208e53721234dfe0df778` (exact reviewed PR head `abd2c4eb05348b86b87e09f65acd5cf149d98972`). GitHub Actions attribution run `38038139765` and full validation `38038139723` all SUCCESS. #587 and #588 remain OPEN, 0 live independently mirrored release archives and 0 recovery proof. No deletion/cleanup/mount/service/production mutation.

#590 status split: doctor structured 0 fail / 3 warns, but status and identity generic tool error. Source currently re-raises raw manager exception text from `runtime_status`; diagnosed as plausible error-handling/sanitization gap, not yet proven root cause, recorded in issue #590. F34 repository mirror activation distinct and remains unconfigured.

AIfordable draft #553 CI red due 9 legacy test clocks (2026-10-08) versus storage authority registry review (2026-10-10); issue documented in PR comment. Fabric #1397 operator-qualified namespace/bootstrap pending. Physical path remains #537 -> #1397 -> #586 -> #587 two immutable copy receipts -> #588 genuine no-network reader/bootstrap recoveries -> provider artifact disposition only then.

## 2026-10-10 — Actual current Runner-MCP state after chat rollback
Prior #621/#622/#623/#624/#625 **already MERGED**; #625 exact-head `ea88bb010cfc866bdf0ee8e1de7299be8c4fd8e9`, attribution `38030008919` SUCCESS and full validation `38030008996` SUCCESS including clean demo; merge `2e274c5b4ed9bf14842803a832689f79cbb805c9`. Do not restore old pending-CI status as current.

Current source child of #587: draft [PR #626](https://github.com/Blacksp1d3r/runner-mcp/pull/626) `fix/587-final-mirror-reverification`, HEAD `abd2c4eb05348b86b87e09f65acd5cf149d98972`; attribution `38038139765` SUCCESS; validation `38038139723` IN_PROGRESS (check again before merge). Post-second-copy finalization revalidates safety, pinned pair, volume admission, secondary integrity of **both** protected archives and pins again. Four bounded tests; no live binding or copy.

Cross-project storage gate: AIfordable #553/`#537` draft red CI `38035068769`, failure = 9 stale 2026-10-08 topology test clocks versus canonical 2026-10-10 registry (1,352 passed). Root cause sent to owning PR comment. Fabric #1397 policy/read gates merged (#1426/#1427), live namespace/bootstrap still OPEN. Runner-MCP #587 and #588 OPEN, 0 actual second-disk protected copies or offline recovery proof. Never prune provider archives merely to free GitHub quota.

Read-only connector probe #590 partially works: doctor=warn 0 failed/3 warning, runtime_status and build_identity generic internal error, F34 mirror activation unconfigured. No host, service, tunnel, mounted media, job, credential, deployment or physical backup actions performed. Next = #626 full exact-head CI then dependent live authority/storage admission chain, or independent bounded diagnostic work.

## 2026-10-10 — latest protected-storage prerequisites and CI

Runner-Fabric #1426 (policy-only namespace admission) and #1427 (source-only trusted authority inspection) are now merged, but NO operator-qualified live provider or private dedicated namespace bootstrap exists. AIfordable #537 canonical fresh host/runtime/independent-volume machine authority remains OPEN. Thus Runner-MCP #587 and #588 remain OPEN: zero verified physically independent active+rollback mirror receipts, zero real offline restore proofs.

PR #624 protected set drift before copies and final verification exact head `b962dcaff11a78b2ae244fe14f59399555c41837`, attribution `38029722100` and validation `38029722174` both SUCCESS; squash merged `8460283b1fe34ffd2fe4be9426682ff3d1cf6f83`. PR #625 independent restore-qualification protected set drift guard was restacked on subsequent main (including #624) to head `ea88bb010cfc866bdf0ee8e1de7299be8c4fd8e9`; attribution `38030008919` SUCCESS, validation `38030008996` Ruff/pytest and artifact SUCCESS, clean demo IN_PROGRESS at last check. No merge until exact-head full green. No infrastructure changes, file copies, deletes, mounted-volume actions or test receipts presented as real.

## 2026-10-10 — #623 full storage re-admission MERGED (supersedes prior WAITING_CI)

Draft #623 head `80058882e30487d251ff347c5e34af3ecbb30c40`: attribution `38029219757` SUCCESS and full validation `38029219729` SUCCESS, including Ruff/pytest, release artifact, clean demo; squash merged `d755cce23a18130189335d8ad6775f80f19d8525`. Pre-copy admission in the source-only protected mirror orchestrator now rechecks full versioned #586 readiness before EVERY copy, not just `ready=True`; regression tests cover device/mount degradation after first copy and schema drift before first. Real independent storage remains NOT connected: AIfordable #537 and Fabric #1397 open, #587 and #588 live physical acceptance open. No backup copy, archive pruning, server/tunnel/runner mutation or restore performed.

## 2026-10-10 — HIGH PRIORITY backup safety gates integrated; PHYSICAL BACKUP STILL BLOCKED

User explicitly prioritized #587 (real independently mirrored protected releases) then #588 (actual restore proof) to unblock other projects. Both issues MUST remain OPEN until on-host authoritative physical evidence. Existing #586 zero-arg read-only separate-volume readiness already merged via #610; its live status was not available in this conversation (runtime/safety connector generic internal failure). Do not mistake source tests or device-number difference for genuine independent physical disk readiness.

#587 child PR #621 exact head `832cf4ea4157cfa32797038df297fd37831cf7f1`: attribution `38026327476` SUCCESS; validation `38026327510` SUCCESS (Ruff, pytest, release build, clean demo); squash merged `823b11160f7c0b671ae6d0b250ac1f24aae2015e`. Source-only `ProtectedReleaseMirror` orchestrator: backup action+stop/retention gate, exact two trusted distinct protected SHAs, complete exact #586 readiness schema, independent-device admission, verify primary custody before each copy, fixed-adapter exact mirror receipt, verify secondary each, success only both; partial copy cannot yield success; negative tests included. No MCP mutation endpoint or concrete private adapter/pins bound; **0 verified live copies**, source-only.

#588 child PR #622 exact head `d7d2eed1d97a4637769efd717a6c7b350652e62b`: attribution `38026689570` SUCCESS; validation `38026689559` SUCCESS (Ruff/pytest, release artifact, clean demo); squash merged `b62efbda768c7cf2f56eea22ec3764f18788e94c`. Source-only `ProtectedReleaseRestoreQualification` proof gate: requires two exact protected SHA-bound secondary archive receipts, real installed local-custody reader, offline disposable bootstrap preflight/apply/rollback, cleanup receipt, transaction unchanged and no live changes; synthetic negative tests. NOT wired to actual isolated first-party import/reader/bootstrap lifecycle; **0 independent-volume restore proofs**. Do not close #588.

Owner dependencies before ANY physical action: AIfordable #537 private machine-readable primary runtime -> independent physical storage volume + freshness authority; Runner-Fabric #1397 fixed release-archive namespace admission/bootstrap distinct from F34 repository mirror namespace. Cross-project owner priority comments posted. Only then do #586 live readiness under correct managed identity, bind real trusted protected active+rollback pins, invoke first-party `control_plane_bundle_mirror.py` immutable copy semantics with full verification for both and no overwrite/delete, then #588 via `control_plane_archive_import.py`, installed `FabricUpdateManager._validated_bootstrap`, and isolated no-network preflight/apply/rollback against disposable owner-private state with cleanup+no live transaction change. No generic shell/Desktop Commander/sudo/mount bypass; zero private paths/devices/credentials in public docs; do not delete provider archives. Keep #585/#587/#588 open. No host, tunnel, runner, credential, service, rollout, deletion or production update was changed in this session.

## 2026-10-09 — Final landing: A6 doctor #518 and F36 read-only relay #412 exact green MERGED

- Existing #519 source-baseline drift PR CLOSED WITHOUT MERGE because current main already has stronger, tested source/installed drift and unavailability checks, active runtime revision evidence and sanitized `runtime_doctor` source status. Never overwrite current main with stale #519. Separate queued-to-activation TOCTOU review remains open.
- A6 sanitized diagnostic PR #518 exact head `8c9683a16dcbccece78a0d08a6722fa19dee5cf2`: attribution `37984556255` SUCCESS, full validation `37984556225` SUCCESS (Ruff/pytest, artifact, clean demo), squash merge `62c6832338370190e9b9dcee69478fa288031c61`. Adds fixed A6 state-root classification / binding count to existing `runtime_doctor` with no private values; A6 root expression was checked identical to existing restart resolver; deferred onboarding env import avoids module startup circular dependency. No live self-update, agent restart or A6 campaign. #509 live acceptance remains separate.
- Existing F36 continuity relay PR #412 was selectively restacked in place to retain already merged MCP tool/managed Runner-Fabric operation. Adds only fixed no-argument `fabric_continuity_status` over existing Agent Bus bridge, explicit loopback MCP executor dispatch and adversarial field validation. Exact head `2c5e7c0233613ac8da76b4b734f2163efb8e1e2e`: attribution `37985552722` SUCCESS, full validation `37985552667` SUCCESS (Ruff/pytest, artifact, clean demo), squash merge `7ccb65a6ad5d734614e2384a309c126c5607d47b`. Issue #410 CLOSED as SOURCE completed, not proof of deployed Agent Bus route.
- Separate dormant self-update supervisor PR #438 reviewed: `ServerActivationProofMiddleware` may consume restart marker before downstream ASGI handler returns success; potential premature activation proof. Review posted on existing PR, no merge/host mutation.
- External ChatGPT connector/tunnel return-generation identity #590 STILL OPEN and unproven. No active tunnel/service, customer production, CI runner, credentials or runtime deployment changed. Next safe task: reconcile existing #438/#618 and other owned PRs with current main; do NOT activate supervisor without successful-readiness marker regression tests; runtime A6/F36 acceptance remains separately gated.

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

## 2026-10-09 — #619 exact-head GREEN and MERGED (supersedes WAITING_CI)

New bounded source-only PR #619 (`fix/windows-service-backend-admission-20261009`) exact head `b426692798092edf263d0182a205ae7ba9a6dc2b`, attribution run `37975695602` SUCCESS, full validation run `37975695551` SUCCESS (Ruff/pytest, built release artifact, clean demo), squash merge `bac86a97f1493ff943ef5f3d01228814e3ed61c0`. `ServiceManager._backend()` refuses default Linux SystemdUserBackend on Windows/unsupported host before instantiation; existing Linux and explicitly injected backends unchanged. Three regression cases passed. This does NOT implement Windows SCM, change actual Windows startup, grant remote authority, or activate any server. Broader #489 remains open for least-privilege SCM adapter and isolated Windows CI.

This session's other exact-green source merges: Faster shadow #460 `6a9ed29197ee7b58c8c6a672c313dfc4edccc160`, first platform contract #490 `816c7e5abd5ddbf91d0e580e6a7102bb0308faf0`. All are GitHub source changes only; no runtime/self-update/tunnel, CI enrollment, credentials, production/worker mutation. #590 remains OPEN, external response return route unqualified. Prior temporary WAITING_CI paragraphs below are superseded. Safe next independent work is review/reconcile existing owned open PRs (#526, #519, #518 etc.), not duplicate or merge without fresh head and ownership checks.

## 2026-10-09 — Faster-13 eventfd shadow + Windows host contract

#460 (shadow-only shared-memory/eventfd benchmark) exact-head attribution `37974721744` and full validation `37974721750` GREEN; squash merged `6a9ed29197ee7b58c8c6a672c313dfc4edccc160`. Added 5s response deadline and guaranteed worker cleanup on failure with positive and negative tests. Not a production transport or OCR throughput improvement.

#490 (host-platform capability contract) exact-head attribution `37975249864` and validation `37975249793` GREEN; squash merged `816c7e5abd5ddbf91d0e580e6a7102bb0308faf0`. Platform family `supported` is not Windows backend readiness: explicit `serviceAdapterImplemented` false for Windows, true for Linux implementation, false unsupported. Runtime Windows SCM not installed or qualified.

#619 implements a narrow further fail-closed guard on default service-manager backend selection for non-Linux. Latest head `b426692798092edf263d0182a205ae7ba9a6dc2b`, attribution `37975695602` GREEN, full validation `37975695551` IN_PROGRESS. No merge until exact-head green. Linux normal/injected test backends remain unchanged. Subsequent Windows SCM implementation requires separate least-privilege, isolated Windows CI and deployment approval. #489 remains broader owner.

#590 external tunnel return-path identity remains OPEN; #599 source freshness guard already closed. No live host/tunnel changes.

## 2026-10-09 — Final landing: #456 fully GREEN and MERGED

Supersedes earlier #456 WAITING_CI: PR #456 exact head `c2ff700ed4e87cd0a6dd400975a5c47c4016c2a8`, attribution `37962833940` SUCCESS, validation `37962833262` SUCCESS (Ruff/pytest, release artifact, clean demo), squash merge `fc034b094c633b51889e2a13cc86727e2b1941fe`. Together with exact-green merges #465 `365a7a1f32f82e01da75004b800ed2948516fa9e`, #467 `4bba36e877d96246c93eb8064d6bf0d4af72de05` and #613 `ae2eac3f4e38574d4405460e14f7b8cad122e4d4`, all four code PRs are integrated; no live server, CI selector, tunnel, credential or production transport mutation. New next-safe CI-aware action in following session: reconcile existing stacked PR #460 against merged #456 and newest main (do NOT duplicate PR), inspect CI and rebase only using exact branch name. #458 is a temporary hosted benchmark lab and explicitly DO NOT MERGE. #590 external connector response delivery still OPEN despite local JSON-RPC ID guard; remote health dispatcher/response-delivery snapshots remain unproven. #599 source-level auth freshness is closed. No OCR throughput claims from synthetic measurements.

## 2026-10-09 — Faster-13 shadow merges #467 and #465; #456 awaiting clean demo

Exact-head attribution and full validation SUCCESS: existing PR #467 Unix-envelope E2E head `f918a91c9824f747c1a3ad429cf28d9f8960dc91`, attribution `37962618491`, validation `37962618480`, squash merge `4bba36e877d96246c93eb8064d6bf0d4af72de05`; existing PR #465 compact-envelope head `9d1344beaef929acc9bac236a6c8d692dd48b988`, attribution `37962706609`, validation `37962706712`, squash merge `365a7a1f32f82e01da75004b800ed2948516fa9e`. #456 same-Linux-host Unix IPC head `c2ff700ed4e87cd0a6dd400975a5c47c4016c2a8`, attribution `37962833940` SUCCESS, validation `37962833262`: Ruff/pytest and built artifact SUCCESS, clean demo IN_PROGRESS at last check, state `WAITING_CI`. #460 is STACKED on #456 and must not merge first. #458 hosted synthetic lab DO NOT MERGE. These are measurements only: no actual OCR speedup, live worker load, runtime transport change, service or tunnel mutation. Prior #467 GraphQL diagnostic retracted: incorrect branch name caused failure; exact branch solved it. #590 external connector still OPEN despite #613 local bridge reply-ID hardening.

## 2026-10-09 — Local MCP reply-ID guard merged; three Faster shadow PRs in validation

PR #613 exact head `6b5dc2c2c646aba0fdc45a0ae9a08a6af83a8f97` passed attribution `37962077429` and full validation `37962077446`, merged `ae2eac3f4e38574d4405460e14f7b8cad122e4d4`; internal JSON/SSE replies without exact numeric JSON-RPC id are rejected. Externally intermittent connector/route issue #590 remains OPEN. Issue #599 source freshness was already merged via #609 and closed on reconciliation. Official upstream tunnel-client diagnostics define loopback-only dispatcher and response-delivery counters, documented in triage.

Existing shadow-only Faster PRs (no deployment) restacked to main, original PRs preserved: #467 head `f918a91c9824f747c1a3ad429cf28d9f8960dc91`, CI `37962618480`; #465 head `9d1344beaef929acc9bac236a6c8d692dd48b988`, CI `37962706712`; #456 head `c2ff700ed4e87cd0a6dd400975a5c47c4016c2a8`, CI `37962833262`. Attribution green for all; Ruff/pytest green for all, full demo pending at last check. `WAITING_CI`, no merge claim. #460 remains stacked behind #456; #458 temporary benchmark lab is DO NOT MERGE. No live service, worker, CI selector, tunnel, credentials or customer data touched.

## 2026-10-09 — Faster-13 synthetic benchmark integrated

PR #514 exact head `1f329ff57e1ef5b8262f813b4a72100aa410820a` passed attribution `37957744577` and full validation `37957744262`, then squash merged `46f9a8b86dc00586cfa24a2368e146f234345d2f`. Includes existing bounded shadow benchmark and seven CLI input rejection tests. No real OCR acceleration claim, local runtime/deploy or workload change. #383 broader Faster-13 remains open. The earlier WAITING_CI note below is superseded. Connector response tracing PR #608 and sanitized playbook PR #607 also merged; #590 external return-path still unqualified.

## 2026-10-09 — MCP connector response identity and Faster-13 benchmark

**Completed:** PR #607 sanitized operator playbook fully green merged `6dc5160c93815b223214302ffb50cebbb304e49d`. PR #608 existing HTTP middleware trace/request-ID negative and concurrent tests fully green merged `e0250205ee33cd39f5ffc501ff8fa86861679d30`. Tests prove local response identity, not external tunnel return path. User/operator observed enabled/active tunnel, readiness 200, zero service restarts; boot drill pending. #590 remains open for live first failing response edge, #540 generation fencing open, #333 reboot readiness open; no live reconfiguration.

**Active:** Existing Faster-13 #514 was cleanly restacked in-place onto current main, with seven fail-closed CLI argument tests. Latest head `1f329ff57e1ef5b8262f813b4a72100aa410820a`; exact-head attribution `37957744577` SUCCESS, Runner MCP validation `37957744262` Ruff/pytest and built artifact SUCCESS, clean demo IN_PROGRESS at last check; `WAITING_CI` overall. Earlier Ruff formatting failure `37957558080` repaired; no production benchmark was run. #383 remains open; no OCR throughput claim or production transport switch.

## 2026-10-08 — Diagnostic topology adoption in review

Tracking: #569.

A documentation-only diagnostic architecture is being added under `docs/diagnostics/` following the merged AIfordable cross-project standard. It maps 14 Runner-MCP components, their sources, state lineage, physical store classes, public tool/result lineage, tests and reusable failures. It does not change runtime behavior, MCP schemas, private configuration, services or the active Fleet/Bewind work.

Reusable failures already indexed include local-idle versus end-to-end-busy, source authorization independent of runtime health, healthy Fabric process versus missing peer capability, and stale client tool-catalogue state.

## 2026-10-08 — Bewind OCR source custody + scalable artifact cache merged; client refresh remains

Runner-MCP #541 / PR #542 merged as `9b0560d3b07bbd7cca548ce72d790ea5fe3f50bd`: workload-neutral private content-addressed worker artifact custody keyed by exact SHA-256 + size, with owner-only atomic storage, cache hit/miss semantics and fail-closed re-verification. No generic MCP/file-transfer/path/URL authority was added.

Runner-MCP #538 / PR #543 merged as `3af622efa95c694946814a7bc33b54e7870bff7f`: zero-argument canonical Bewind OCR source provisioner. It fetches only the fixed public eJustice sentinel `2026/02/03_1.pdf`, pins HTTPS authority, verifies exact SHA-256 `80a0fc4a561f26527aa7fb6dcc89209310f5af73a96e4e030f213faf76defa46` and size `2811759`, publishes it into content-addressed local custody, and writes a private file-backed source binding consumed by the existing staging tool. Exact cache hits avoid redownload. Normal/multi-host activation remains disabled.

Exact-head #538 validation was fully green before merge: attribution, compile, Ruff, 2323+ pytest suite, MCP Registry metadata, whitespace, built release artifact and clean demo.

Live self-update job `f1c924bb4680409caf2012da4970f6ce` completed to exact `3af622efa95c694946814a7bc33b54e7870bff7f`. Runtime status proves installed/source/active runtime revision aligned and no install recovery pending. One restart marker remains pending in the currently connected MCP process/session; the current ChatGPT tool catalog was loaded before the new zero-argument `bewind_ocr_qualification_source_provision` tool existed and does not expose it yet.

Scalability follow-up is Runner-Fabric #1249 (child of #986): content-addressed artifact publish/worker-cache replication with authorization manifests, one-publish/many-reference, backpressure, resumable replication, retention/leases and corruption refetch. #538 is the first consumer, not a Bewind-only transfer architecture.

Next exact action after connector/tool-catalog refresh:
1. confirm `bewind_ocr_qualification_source_provision`, `bewind_ocr_qualification_stage` and `bewind_ocr_qualification_run` are visible;
2. call source provision exactly once and require ready + canonical SHA/size + bindingReady=true + normalActivationEnabled=false;
3. call stage exactly once and require ready + same SHA/size + singleUse=true;
4. call run exactly once;
5. validate the bounded result through Bewind #101 and compare hashes/timing/CPU/load against the canonical route;
6. keep production/multi-host activation disabled until Runner-Fabric #1110 qualification is accepted.

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

## 2026-10-06 — Cross-project authority binding

Runner-MCP is bound to the AIfordable Infrastructure + Credential Authority. Do not maintain a separate full server/token map here. Resolve scoped current context before infrastructure mutation or credential repair; unknown/stale/conflicting context fails closed.

## 2026-10-06 — Mandatory topology preflight

Before connection or infrastructure troubleshooting, consult the canonical AIfordable infrastructure authority at `Blacksp1d3r/AIfordable/docs/INFRASTRUCTURE_AUTHORITY.md` and Runner Fabric's topology directory. Confirm the actual host, runtime and service identity before changing configuration. Unknown or conflicting topology fails closed. Historical correction: `github-runner` was the first Runner-MCP host; `aifordable-lab` was the first Runner-MCP + Runner Fabric combination.

## 2026-10-06 — #451 dedicated Bewind source credential in validation

Tracking: #451; unblocks Runner-Fabric #1112/#1110.

Runner-MCP #445 is merged via #452 as `1d4957ff0787e91378dc1a46215469623fc76947` and live on aifordable-lab with restart/recovery clear.

#451 adds one fixed private credential selector for the built-in `bewind` project. When `RUNNER_MCP_BEWIND_GITHUB_TOKEN` is present, only Bewind known-project preflight/source-preflight/prepare may use it. Other projects and mailbox remain on the existing global token. Missing dedicated credential explicitly preserves current global fallback; malformed dedicated credential fails closed. MCP callers still provide only project_id and no credential value is returned/audited.

Next: exact-head CI/merge/live update. Then the owner stores the already-created fine-grained Bewind read token in the dedicated private env binding; run bounded preflight -> prepare -> register to close Fabric #1112 without touching v3.

## 2026-10-06 — #445 fixed worker-qualification provisioner in validation

Tracking: #445; Fabric chain #1130 -> #1113 -> #1110. Active branch: `fabric/445-worker-qualification-provision-v2`.

Implemented:
- fixed MCP tool `fabric_worker_qualification_provision`;
- exact accepted capability `bewind-ocr-qualification-v1`;
- request fingerprint recomputed locally from worker/capability/generation/plan digest/expiry/Fabric revision;
- local private worker identity/capability/generation authority;
- active managed Runner-Fabric launcher must resolve inside the exact requested control-plane update slot;
- owner-only fixed qualification config is written under Runner-MCP private config and persisted into `runner-mcp.env`;
- the same in-memory private environment is shared with existing `fabric_disposable_target_qualify`, so provision -> qualify needs no runtime restart;
- sanitized result proves managed launcher + qualification state ready and keeps normal activation false;
- no OCR execution and no active Bewind v3 interaction.

Original PR #449 was restacked once because concurrent A6 work advanced main; v2 is based on current main `10df2c8b...`.

Next: exact-head CI/review/merge. Then update the live Runner-MCP runtime, configure only the host-owned private qualification template, execute Fabric #1130 bounded binding and continue #1113.

## 2026-10-06 — Known projects can materialize from trusted local source

Tracking: #401.

Runner-MCP can now consume an optional host-owned private known-project local-source map before falling back to GitHub. The MCP caller still supplies only project_id.

The local binding is schema-bound to:
- fixed catalog project identity;
- expected canonical repository identity;
- private owner-only local source directory;
- exact expected commit revision.

When present and valid, preparation clones locally with network disabled, checks out the exact revision, verifies a clean HEAD, normalizes the resulting origin to the canonical GitHub repository identity, atomically renames the temporary checkout into the existing trusted sibling destination and cleans partial state on failure.

Invalid or unsafe configured local authority fails closed rather than silently falling back to GitHub. Without a local binding, the prior GitHub preparation path is unchanged. The private binding is retained across config overwrite.

Live branch qualification included lint + unit PASS and a real bare local Git source materialization test.

## 2026-10-06 — Local Fabric update custody is self-staging

Tracking: #442, follows local-custody update source #404.

Runner-MCP now has a bounded exact-commit staging path for Runner Fabric control-plane update bundles. The caller supplies only the full commit revision. Runner-MCP owns the canonical Runner Fabric repository, fixed builder, private temporary checkout and existing local-bundles custody root.

The staging path:
- clones/fetches only the canonical Runner Fabric source using the existing private GitHub credential;
- verifies exact clean HEAD before build;
- invokes only scripts/build_control_plane_update_bundle.py;
- reuses FabricUpdateManager local bundle and bootstrap integrity validation;
- atomically publishes only a fully validated bundle to local custody;
- is idempotent for an already-valid exact bundle;
- cleans temporary source/credential state on failure;
- exposes no repository/path/token/argv authority to the caller.

This closes the gap between provider-neutral bundle creation and the existing fabric_local_update_readiness/fabric_local_update route.

## 2026-10-06 — F34 bounded mirror activation

Tracking: #431. Depends on Runner Fabric #1121 for one-time delegation of the fixed 8TB namespace.

Runner-MCP now has a zero-argument activation path that, after the fixed storage namespace is writable by the managed service identity:
- verifies the fixed inventory/mirror roots are private and writable;
- writes the canonical 11-repository desired-state snapshot into owner-only Runner-MCP private config;
- binds the existing GitHub credential into an owner-only Git configuration without exposing it in output/audit;
- persists the four F34 private runtime bindings atomically into runner-mcp.env;
- updates the same in-memory mirror environment used by readiness/preflight, so activate -> preflight works without an extra restart;
- never runs mirror reconcile/network work as part of activation.

Reconcile remains separately gated on repository-mirrors-preflight READY.

## 2026-10-06 — A6 now blocked by stale Fabric runtime plus private Runner-Fabric authorization

The ChatGPT runner-mcp-control schema now exposes both A6 qualification proxies. Runner-MCP #427/#428 also restored bounded recovery of the fixed qualification-only Fabric Agent MCP after genuine process loss; the live restart returned `state=restarted`, `pid_changed=true`, `healthy=true`.

A full Runner-MCP restart on `55fa3d1ba46d6d6bb41b2e43d3d94e97376cf309` ruled out cached downstream MCP session state. Fabric bridge calls still fail, including A6 prepare and older read-only Fabric operations.

Bounded source evidence for built-in `runner-fabric`:
- credential_configured=true;
- source_reachable=false;
- main_ref_available=false;
- reason_code=source-unreachable-or-unauthorized;
- runtime doctor still reports Runner-Fabric Actions read unavailable/unauthorized.

The managed Fabric slot is older than A6 (#1046/#1049). Local-custody readiness was checked for current Fabric main `7af6cbf887a214f70354726c99abe9d19712b32f`, A6 baseline `5b5e71ad9ed66a9f7cec35ddb48eb7535edf3d99`, prior managed-update baseline `a8cb6835d33269bfb96ea3d8e40bc505f91b107b`, and older live-qualified `a7492aeb2bc738a4de4d19d6e515d29b1482a1a0`; none is locally staged.

Do not create an untrusted bundle ingress, another updater, or a shell/Desktop Commander bypass. Immediate unblock is either least-privilege Runner-Fabric repository/Actions read for the existing private Runner-MCP credential or a separately trusted pre-staged local-custody bundle. After Fabric is updated to an A6-capable exact revision, resume only `prepare -> self_update -> fresh A3 probe -> finalize`.

## 2026-10-06 — Fleet A6 blocked only on client schema; access warning split to #417

Fresh reconciliation confirms the active runner-mcp-control catalog still lacks the two existing A6 qualification proxies. Live Runner-MCP remains operational on the previously qualified installed commit with no pending restart or install recovery. Do not rebuild the proxy or updater.

Runner-MCP #417 separately tracks the private Runner-Fabric source/Actions read warning. This is not A6 implementation work and must not weaken the fixed-repository, fixed-workflow, fail-closed update boundary.

## 2026-10-06 — customer update readiness counterpart planned

Tracking: #414; Runner Fabric #1063; AIfordable #401.

Runner-MCP is execution-only for the new customer-update safety lane. Planned first scope is read-only semantic readiness for disk capacity/margins, RAM/available memory/memory pressure/swap/OOM, CPU/thermal/storage/power/network/restart/build/schema/recovery and returning-node trust generation. No live customer mutation or fleet policy is activated.

## 2026-10-06 — A6 qualification proxy merged and live

Runner-MCP main/live: `e88e76badad428995c026cf5ac9988607fd52069`.

PR #411 added exactly two strict Runner-MCP -> Fabric A6 qualification proxies:
- `fabric_a6_update_qualification_prepare(candidate_commit)`
- `fabric_a6_update_qualification_finalize(correlation_id, job_id)`

Exact-head validation #1138 and attribution #655 were green before merge. Live self-update job `3d3339dcad1d44838eb99825286eca8a` completed successfully; runtime_status confirms exact installed commit, operational mode, no restart pending and no recovery pending.

The remaining blocker is ChatGPT connector schema refresh: this current session still exposes the older runner-mcp-control tool catalog and therefore cannot invoke the two newly added proxy tools even though the server runtime has them.

Do not add another proxy/updater. After tool schema refresh, execute the existing A6 prepare -> self_update -> finalize path and hand evidence back to Fabric #942.

## 2026-10-05 — Tunnel readiness proven through control-plane authentication; end-to-end gate remains

Canonical Runner-MCP main: 9a4f9d7a2916625617aa2ef144fc40679e549129.

Issue #333 remains open. Completed and green: #370 managed tunnel autostart, #371 managed process evidence, #372 fixed local MCP health evidence, and #373 fixed local control-plane successful-poll evidence.

Current bounded progression: COMPLETE config -> managed process active -> local MCP proven -> control-plane authenticated -> end_to_end_not_routable. Do not claim READY from config, process, local MCP health, or successful control-plane polling alone.

Upstream tunnel-client review confirms each process sends an opaque X-Tunnel-Client-Instance-Id, but the local runtime has no authoritative inventory of every other active instance using the same tunnel ID. Tunnel service uses a shared queue per tunnel; redundant clients are safe only for equivalent/stateless or session-aware shared backends. Runner-MCP targets localhost per host, so keep one active tunnel client per tunnel ID unless topology proves equivalent shared-backend behavior.

Remaining #333 gate: do not invent local uniqueness evidence or a second probe engine. Wait for Fabric A3/#939's existing qualification/synthetic-work-unit path to expose continuous durable end-to-end evidence. Consume only a bounded first-party result if/when available, and require topology/duplicate-runtime reconciliation before end_to_end_routable=true / READY.

No live autostart, tunnel restart, deployment, migration or runtime update was performed in these slices.
## 2026-10-05 — Tunnel readiness runtime boundary merged; managed autostart next

Canonical Runner-MCP main: `2a27fb0d8236e6c06f2fd0da3b04dfced558d471`.

Issue #333 remains open. Completed this session:
- #364 / `4aae2a21...`: maps secret-free tunnel restart-config evidence into the bounded readiness state machine;
- #366 / `69b958aa...`: complete private config no longer makes `doctor` claim PASS; without separate process evidence it stays WARN / `process_not_running`;
- #367 / `7e157688...`: local read-only `tunnel-status` exposes only restart_config/state/reason;
- #368 / `2a27fb0d...`: hidden fixed `tunnel-run` executes only installed `tunnel-client run` against Runner-MCP loopback, explicitly exports the existing private tunnel ID/runtime key, requests an ephemeral loopback health listener and writes the resolved health URL to the fixed private config path.
- #363 also merged in parallel as `7b2782f2...` for A3 bound traceparent propagation; the transient duplicate restack #365 was closed after reconciliation.

Security boundary:
- no generic process scan, shell, arbitrary executable, arbitrary endpoint/argv, credential output or paid dependency was added;
- tunnel-client profile management is not reimplemented; current upstream supports env-backed tunnel ID/runtime key, a fixed MCP server URL and private health URL-file evidence;
- no live runtime update, deployment, migration or tunnel restart was performed in this session.

Next safe #333 slice:
1. admit `tunnel` as one fixed optional Runner-MCP autostart component for systemd-user and managed-cron only when `inspect_tunnel_restart_config(...) == COMPLETE`;
2. invoke only the existing hidden `tunnel-run --port <bounded-port>` path;
3. expose managed active/inactive evidence through existing autostart status, then feed that bounded process evidence into tunnel readiness;
4. only after process evidence is proven, consume the fixed private tunnel health URL for local `readyz` evidence; control-plane authenticated and end-to-end routable remain separate later evidence;
5. keep duplicate-tunnel/fencing protection explicit before any READY/routable claim.

Runner-Fabric A3/#939 is active in parallel; do not duplicate its Fabric-side trace/result/ACK/failure-taxonomy work.

## 2026-10-05 — Fleet Update A2 Runner-MCP audit identity hardening merged

Canonical Runner-MCP main: `98bd8ca0de5ecdb2c16b70bbe3ff620b882e432c`.

A1 remains complete via #346 / `c37f60dc...`.

A2 progress:
- #348 / `c73298e6...` added component/version stamping and runtime-start to the existing durable audit log.
- #355 / `98bd8ca0...` replaced the partial shape with the full bounded BuildIdentity field set on every audit row: component_id, build_version, source_revision, artifact_digest, protocol_min/max and interface_schema_digest.
- Existing request_id/tool/project/actor/result/timestamp evidence remains intact; unproven provenance/protocol/interface fields remain explicit null.
- exact-head #355 validation: Runner MCP validation #1033 success; attribution #543 success; Ruff/pytest, release artifact and clean demo all green.

Do not claim #938 complete from Runner-MCP alone. Remaining cross-repo work belongs primarily in Fabric: request/connection stamping across first-party hops plus trustworthy installed provenance/protocol/interface evidence. Runner-MCP may need a later bounded slice to expose those facts, but must not invent checkout-derived provenance.

## 2026-10-05 — Fleet Update A2 Runner-MCP build identity merged

PR #348 merged as `c73298e601081bc85d7f850583356b9c1ee741b4`. Runner-MCP now reuses its existing durable audit log to stamp every record with `component_id=runner-mcp` and the installed package version, and emits a safe runtime-start event. No new logging service/dependency was introduced. Fabric #938 remains open because Agent Bus/Fabric and other first-party hops still need equivalent identity evidence with backward-compatible persisted schemas.

## 2026-10-05 — Fleet Update A1 characterization merged

PR #346 merged as `c37f60dc6001be5f269f88506a92934bc09bf7cb`. The integration regression reproduces the observed stale-client tool-catalog failure class: MCP protocol negotiation remains green while the cached peer lacks a newly available Fabric tool, so the failure layer is `interface_schema`, not transport/protocol. No production code or runtime authority changed. Track A may proceed to A2 only after post-merge validation remains green.

## 2026-10-05 — Fleet Update Track A added; A1 first

Runner-Fabric v2 review narrows Runner-MCP work to concrete control-path protection. #341 is the execution counterpart; Fabric #937–#943 define Track A. First implementation is the historical incompatibility reproduction only; no production mutation.

Code inspection confirms existing self-update already has baseline-wheel/install-time recovery but not an independent post-activation commit-confirmed supervisor. Reuse the installer; do not build another updater.

Zero-cost rule: no paid software dependencies before project revenue.

## 2026-10-04 — bounded Fabric operational snapshot proxy merged

PR #286 merged as `e6330820a2ee58a2ec5068830c2d9a1267f2297b` after Runner MCP validation and attribution were green. Runner MCP now allow-lists Fabric's zero-argument `operational_snapshot` and exposes `fabric_operational_snapshot`, validating exact schema, pending-count relationships, capacity/age bounds, read-only flags and private-detail restrictions. Runner MCP does not reconstruct relay/Fabric truth. Fabric #876 is merged as `98baf4e2532e591d534ba893a147773aa31f644f`; live usefulness still depends on Fabric providing an explicit canonical provider. Keep #269 open until provider wiring and live proof show upstream pending work while local test workers are idle.

## 2026-10-04 — operational snapshot proxy implementation in validation

Issue #269 is now implemented as a strict Runner-Fabric projection rather than a local reconstruction. PR #286 head `d43e472bb265a7314e59bb3109bcdddbab650e18` adds zero-argument `fabric_operational_snapshot`, allow-lists only Fabric's fixed `operational_snapshot` call, validates exact `runner.fabric/operational-snapshot/v1` fields/count relationships/capacity bounds/ages/read-only flags and reuses private-detail rejection. This preserves Fabric as orchestration truth. Commit attribution is green; Runner MCP validation is in progress. Dependency: Runner-Fabric #876 must first land the optional Agent-MCP source contract. Do not merge #286 before both sides are terminal green.

## 2026-10-04 — operational snapshot gap promoted to maintenance priority

Live operator evidence showed `queue_status` and `worker_status` at 0 queued / 0 claimed / 0 running with both test workers available while first-party client sessions still reported systems as busy. Restart state later converged clear, so local test-queue idleness is not sufficient end-to-end evidence. Issue #269 now tracks one bounded read-only `operational_snapshot`; Runner Fabric #867 owns the canonical cross-layer projection. Required attribution spans control relay, Agent Bus, Runner MCP, Fabric/Conductor/work-unit, worker capacity, durable result/outbox/replay and ACK state. Unknown/unobservable layers must remain unknown rather than false green. This is a correctness/operator need allowed under maintenance mode, not speculative feature growth.

## 2026-10-04 — alpha core complete; maintenance mode

Runner MCP is now in maintenance mode after completion of the technical alpha/MVP core and live recovery acceptance.

Current live evidence:
- runtime is operational with emergency stop inactive;
- self-update is ready, with no active update, restart marker or install-recovery transaction;
- #108 recovery qualification is complete: interrupted install state was detected, overlap failed closed, local emergency-stop-gated recovery restored the exact prior baseline, and a normal bounded self-update returned the runtime to exact main;
- first-party bounded Runner Fabric work-unit control is proven; Runner Fabric remains the orchestration/control-plane owner;
- canonical public release is v0.1.3 on PyPI, the official MCP Registry and GitHub Releases;
- Glama and AllMCPs discovery/ownership are established without introducing hosted runtime dependencies;
- #101 remains open only for a deliberately deferred technical launch post after `aifordable.com` is ready;
- #263 remains open only for third-party directory metadata corrections, including upstream MCP Find issue #26.

Maintenance policy:
- no speculative Runner MCP feature work;
- accept security fixes, correctness bugs, compatibility fixes and concrete operational needs;
- preserve the deny-by-default bounded authority model and local-only recovery boundaries;
- keep broad orchestration, scheduling, provider logic and higher-level automation in Runner Fabric;
- external discovery/marketing work is non-blocking and must not drive runtime/package changes.

## 2026-10-04 — local self-update recovery qualification harness live-ready

Canonical Runner MCP runtime/code checkpoint before the live recovery drill: `ba35f70eb9e3e489fc6936d2bc2f0fc425710c81`.

Completed:
- #110 is closed after first-party coarse Fabric run/get plus fail-closed cancel/operator-safety acceptance;
- issue #261 / PR #262 add a local-only `self-update-recovery-qualify <commit>` path for #108;
- the qualifier uses normal exact-main validation/staging/install, then deterministically interrupts after target wheel installation and before verification/finalization, preserving the existing recovery transaction and staged baseline;
- the qualification path is not exposed through MCP, mailbox or Agent Bus and adds no generic command/path/package/process authority;
- exact-head #262 validation, release artifact, clean demo and attribution are green;
- managed Runner MCP self-update to `ba35f70e...` completed and restart convergence is clear;
- Fabric runtime update remains idle; do not confuse Runner MCP #260 automatic-bundle acceptance with an active Fabric update.

Next:
1. use the next exact current-main documentation commit as the forward target for the live #108 drill;
2. locally run `self-update-recovery-qualify <exact-current-main>` under the qualified service-user runtime;
3. prove remote/normal self-update refuses overlap while recovery is pending;
4. locally activate the operator emergency stop and run `self-update-recovery` with its exact confirmation;
5. verify baseline restoration, clear recovery state and then perform a normal bounded self-update back to exact current main;
6. close #108 only after that live evidence is recorded.

## 2026-10-04 — exact-main self-update guard is live

Canonical Runner MCP live code checkpoint: `82e4b0f133bae3a709bb29a89a9be2d98122aef9`.

Completed:
- PR #258 / issue #257 now require normal self-update to target the exact fetched `origin/main` tip; a stale normal target fails closed instead of becoming an implicit downgrade;
- recovery keeps its dedicated older-baseline path and no generic ref/branch selector was introduced;
- the six affected recovery/install test doubles were adapted to the new main-tip sync path; exact-head and post-merge validation, release artifact, attribution and clean demo are green;
- live self-update to `82e4b0f1...` completed through Runner MCP itself; after controlled restart: `self_update_ready=true`, `restart_pending=false`, `pending_restart_count=0`, `install_recovery_pending=false`;
- issue #246 is closed after live proof that configured restart consumers converge without orphan optional markers;
- current already-open client session still exposes the older cached MCP tool catalog, so newly landed `fabric_update` / `fabric_host_inspect` schemas require a fresh first-party client session; do not bypass this with broad remote shell/Desktop Commander.

Next:
1. open a fresh first-party client session and verify the newly landed Runner MCP Fabric tools are visible;
2. re-reconcile Runner Fabric current `main` at that moment and choose only the exact current commit with a successful canonical `control-plane-update-bundle` artifact; do not reuse a formerly-current Fabric SHA merely because it was recorded in an older handoff;
3. perform the first bounded managed Fabric update through `fabric_update`, prove status and rollback readiness, then use `fabric_host_inspect` / coarse work-units for routine control;
4. keep #110 as the remaining first-party work-unit proof and #108 as the separate deliberate recovery/fault-injection proof.

## 2026-10-04 — managed Fabric update path landed and Runner MCP live runtime converged

Canonical Runner MCP main/live commit: `cb7804bf0dbd10e9e343520aefb7b5df0f45ccc4`.

Completed:
- PR #252 / issue #250 fixed stale optional self-update restart markers with explicit bounded reconciliation and fail-closed optional-component configuration;
- PR #255 / issue #253 bound server self-update restart to the actual local loopback serve host/port instead of inferring restart authority from the public/tunnel resource URL;
- live self-update to `cb7804bf...` completed through Runner MCP itself;
- server and configured GitHub-watcher restart markers both self-consumed; live status is `self_update_ready=true`, `restart_pending=false`, `pending_restart_count=0`, and no install recovery is pending;
- PR #256 / issue #251 added bounded managed Runner Fabric exact-commit update/status/rollback tools;
- Fabric updates accept only a full lowercase commit, require a successful canonical `control-plane-update-bundle` workflow from `main`, verify exact manifest/commit/file-set/SHA256 integrity before execution, strip GitHub authorization before artifact redirects, reject local/private redirect hosts, require an already-managed Fabric slot launcher, and invoke only fixed `BOOTSTRAP.py preflight|apply|rollback` actions;
- rollback is bound to the currently active managed commit only; no repository, URL, path, command, environment, package, artifact ID or executable authority is caller-supplied.

Next:
1. make sure the desired Runner Fabric `main` commit has a canonical control-plane update artifact without reintroducing a manual operator dependency;
2. start a fresh first-party client session so newly added MCP tool schemas reload;
3. use `fabric_update` for the first exact managed Fabric upgrade and prove bounded status/rollback readiness;
4. then use the already-landed `fabric_host_inspect`/work-unit route to continue retiring Desktop Commander from routine work.

## 2026-10-04 — bounded Runner Fabric host inspection bridge

Tracking: #247. Cross-repo dependency: Runner Fabric #760 / I5 #751.

Runner MCP now proxies one new fixed zero-argument Runner Fabric capability:
- `fabric_host_inspect()` -> loopback Fabric `host_inspect`;
- strict bridge allow-list now includes exactly `host_inspect` beside the existing work-unit tools;
- result must be `runner.fabric/host-inspection/v1` with `mutation_enabled=false`;
- top-level, host and browser shapes are validated fail-closed;
- nested output is size/node bounded and rejects keys that could expose paths, credentials, endpoints, argv, command or executable authority;
- the public plugin takes no arguments, so callers cannot select a path, command, executable, service, URL or environment;
- audit records only `fabric_host_inspect`, semantic `host:local` and outcome;
- Fabric work-unit behavior and authority are unchanged.

Next:
1. exact-head Runner MCP validation;
2. merge after Runner Fabric #760 is green/merged;
3. self-update the managed Runner MCP runtime;
4. update the managed Runner Fabric runtime;
5. prove `fabric_host_inspect` through the existing remote connector and use that proof instead of Desktop Commander for browser/runtime readiness.

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

## 2026-10-03 — Canonical service-user Agent Bus restart/replay acceptance completed

The dedicated `aifordable-runner` runtime on `runner:aifordable-lab` has now completed the live bounded Agent Bus acceptance that remained open in #125.

Evidence:
- Runner Fabric was activated through its managed slot/update path at exact qualification revision `a7492aeb2bc738a4de4d19d6e515d29b1482a1a0`;
- q591 executed through the AIfordable SQL relay while GitHub fallback was unavailable;
- the successful terminal relay acknowledgement was deliberately dropped only by the qualification-only Fabric path after durable commit;
- Runner MCP convergence observed `state=pending pending_results=1`;
- the ordinary Agent Bus worker was restarted;
- after restart the durable result replayed before new claims and convergence returned `state=clear pending_results=0`;
- the relay still returned q591 as the same completed/ok/reported terminal result;
- reused q591 identity with changed content failed closed and did not alter the original terminal record;
- prior live evidence already covers relay restart durability, stale-generation fencing, read-only GitHub-denied status/doctor and primary/fallback state.

Do not repeat:
- the old watcher-marker activation proof;
- stale-generation fault injection;
- relay-restart proof;
- manual outbox/relay-store edits;
- credential reconstruction.

Runner MCP itself required no new runtime authority for this proof; the existing wrapper/private-env boundary and convergence surface were sufficient.

Next:
1. reconcile/close #125 from the accumulated acceptance evidence;
2. keep Agent Bus as primary runtime control and GitHub mailbox as fallback/bootstrap only;
3. proceed with managed persistent worker lifecycle and higher-level Fabric live overview/operations rather than adding generic remote-shell authority.

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

## 2026-10-03 — Replacement-host Runner MCP live qualification checkpoint

Canonical runtime-code self-update target: `9dc9d2bfa09b25deff7a5186b9f12252c84cdd52` (reachable from `origin/main`; later documentation-only handover commits need not move this target).
Installed/source rollback baseline on `aifordable-lab`: `a71f68b3c6375c22d9a10a7cfea9e28c9692cc0d`.

Live facts proven on the dedicated `aifordable-runner` service user:
- `runner-mcp 0.1.3`; doctor previously reported 0 failures / 0 warnings.
- Local MCP server starts cleanly on `127.0.0.1:8000`; `/healthz` returns `{"status":"ok"}`.
- Direct MCP bridge `runtime_status` succeeds and reports `self_update_ready=true`, no active update, no restart pending and no install recovery pending.
- Bounded local `lint` and `unit` profiles both pass through the MCP bridge.
- GitHub mailbox -> watcher -> local MCP bridge -> bounded test runner is proven end-to-end by request `lint-55f906d7faec4d15`, job `dc43ca86f38244588b09ced284b70e34`, terminal `passed`, exit code 0.
- Self-update request `self-update-b3864011660143cb` was accepted end-to-end and created job `48a3cb362da249f0925b5cee18fdfe86` for exact target `fa2bedc3d9e9f8181fe2c27043a6d75c3dfe81fe`.
- That self-update job reached the target checkout, passed target `lint`, then failed target `unit` collection with exit code 2. v0.1.3 automatically restored the source checkout to baseline afterward, so a baseline HEAD after failure did not mean sync had never occurred.
- Runtime packaging preflight is healthy: pip is available and `setuptools.build_meta` imports successfully.
- A manual no-install/no-sync wheel build of the baseline project succeeds. Therefore do not re-investigate missing pytest/ruff, mailbox transport, MCP endpoint/auth, baseline registration, pip availability or build backend availability unless new evidence contradicts these facts.
- The MCP server is not yet installed as persistent autostart; for qualification it must currently stay alive in a foreground terminal.

Resolved root cause and correction:
- target lint job `bf7e0872202a4b4d91d15e3f9762e4df` passed;
- target unit job `eb64112264214b5cb88291ac4a04e540` failed during collection because pytest imported the previously installed baseline package from `.venv/site-packages` instead of the newly checked-out `src/` tree;
- PR #233 fixed validation with `pythonpath = ["src"]` in pytest configuration so self-update tests the active checkout;
- #233 merged to `main` as `9dc9d2bfa09b25deff7a5186b9f12252c84cdd52` after commit-attribution, Runner MCP validation, Clean Ubuntu installer proof, Ruff/pytest, demo smoke and release-artifact validation were green;
- current live host source remains safely restored to baseline `a71f68b3c6375c22d9a10a7cfea9e28c9692cc0d`; next runtime-code target is `9dc9d2bfa09b25deff7a5186b9f12252c84cdd52`.

Do not regress:
- Agent Bus remains the intended primary runtime control path; GitHub mailbox is qualification/fallback, not long-term authority.
- Do not install persistent autostart until the bounded live qualification path is understood and green.
- Do not manually replace the installed package or move the source checkout to the target to bypass self-update safety.
- Keep rollback baseline `a71f68b3c6375c22d9a10a7cfea9e28c9692cc0d` intact until the failed self-update is diagnosed.

## 2026-10-02 — Agent Bus live proof + replacement-host reconciliation

Canonical Runner MCP main at this checkpoint:
`c2ef4a348a126867f07777b162d913efa3a97edd`.

Important correction to older handoff sections below:
- live `runtime_status` and `runtime_doctor` over the AIfordable Agent Bus have completed successfully;
- one real bounded Runner Fabric work-unit completed over Agent Bus on `runner:aifordable-lab`;
- the work-unit reached terminal execution before a real HTTP 413 blocked completion delivery; the result remained durable in the local outbox and replayed successfully after the scoped AIfordable/nginx 64 KiB relay-body fix without work-unit re-execution;
- relay restart durability and stale-generation fencing are already proven;
- Runner Fabric repository tests prove a restarted worker/coordinator replays a pending terminal result after lost acknowledgement while executor call count remains exactly one, then converges the outbox to empty.

Runner MCP state now landed:
- #226 fixed runtime-smoke behavior for the service-user virtualenv symlink layout.
- #227 -> `70609a216e5b279a7a191a83f78eb0f876a15ae0`: deterministic dedicated service-user qualification guidance; do not weaken private home/config permissions or qualify an operator-account substitute.
- #229 -> `c2ef4a348a126867f07777b162d913efa3a97edd`: read-only `runner-mcp agent-bus convergence` status. It exposes only `not_initialized|clear|pending|invalid` plus pending-result count and performs no acknowledgement/deletion/mutation.
- Live service-user verification after the runtime-smoke fix reported doctor 0 failures / 0 warnings and autostart preflight ready.

Runner Fabric dependency now landed:
- Fabric #590 -> `98ea725a965ce4fbc94474df63738b2be296e3b0`: `agent-bus-qualify-isolated-work-unit`.
- The qualifier proves GitHub/source-control credential environment absent and fixed GitHub HTTPS probes blocked before using relay configuration, then submits only the synthetic qualification work-unit contract.
- It exposes no generic project/work-item/change-plan/provider/path/command authority and does not activate production Agent MCP.

Remaining #110/#125/#198-adjacent work is live-host specific:
1. regain local reachability to the `aifordable-lab` VM;
2. run `runner-mcp status`, `runner-mcp doctor`, `runner-mcp agent-bus status`, and `runner-mcp agent-bus convergence` in the dedicated service-user runtime;
3. require convergence to become `clear` before/after the next proof;
4. run Fabric #590's bounded work-unit while GitHub credentials are absent and GitHub network access is explicitly blocked;
5. perform one real Agent Bus worker-process restart/replay confirmation;
6. only after the Agent Bus primary path is green, register/qualify the separate GitHub runner fallback identity/pool and prove it can be disabled independently;
7. persistent activation remains gated until these proofs complete.

Do not regress:
- Agent Bus is primary runtime control; GitHub is fallback/CI/source integration only.
- Do not reconstruct a control credential on the runner.
- Do not inspect/delete private outbox files to manufacture convergence.
- Do not replace the qualification-only Agent MCP with production `agent-serve`.
- Do not add another Runner MCP bridge/recovery path for behavior already owned and proven by Runner Fabric.

Immediate resume:
1. use the AIfordable AF-22.6 live runbook/checkpoint;
2. resume at host reachability and service-user runtime checks;
3. use `runner-mcp agent-bus convergence` instead of manual private-state inspection;
4. complete the live isolated work-unit + worker restart proof;
5. only then proceed to fallback registration/drain/persistent activation.

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

## 2026-10-02 — Secondary-directory independence policy

- External MCP directories/marketplaces are explicitly optional discovery surfaces, not Runner MCP dependencies or launch gates.
- Canonical authority remains GitHub `Blacksp1d3r/runner-mcp`, PyPI `aifordable-runner-mcp` and MCP Registry `io.github.Blacksp1d3r/runner-mcp`.
- Glama hosting/gateway, Smithery-specific hosting/bundling, alternate package identities and provider-specific deployment modes must not be introduced merely to obtain a listing.
- If a directory changes requirements or cannot represent the self-hosted project unchanged, skip/drop that listing instead of redesigning Runner MCP.
- This rule is duplicated deliberately in `AGENTS.md` so every future AI/agent session receives it during mandatory bootstrap.

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

## 2026-09-27 — AI fault-containment regression proof merged

- PR #106 merged to `main` as `affc2c054b3072f480822675718baefedc2db619` after exact-head Runner MCP validation and commit-attribution policy both passed, with zero review-thread blockers.
- Cross-boundary security tests now prove that client/AI intent cannot select an unlisted executor capability, mutate an already approved plan, reuse approval across action classes, self-assert production mutation authority or override the external operator emergency stop.
- Read-only work remains available during the operator stop, preserving the proportional-security rule instead of turning every safety state into a blanket development block.
- No new runtime authority was introduced; this slice locks existing executor, approval and operator-safety boundaries with regression coverage.
- Open follow-up #101 tracks secondary discovery; #108 now tracks the remaining private-host proof for recovery-capable self-update. Canonical v0.1.2 publication is already complete, and neither lane should duplicate completed release/runtime work.

## 2026-09-27 — AI fault containment roadmap rule prepared

- Runner MCP now documents AI/client requests as intent rather than execution authority.
- Security gates are proportional to blast radius: contained read/test work stays automatic,
  controlled staging/mutation paths use deterministic policy/freshness/fencing, and protected
  production/credential/destructive actions require independent authority.
- Prompt-injected content cannot create capabilities, weaken policy or satisfy approval.
- This documentation change adds no new runtime authority.

## 2026-09-27 — v0.1.2 canonical distribution published

- Human-approved Publish Runner MCP run #2 completed successfully from exact main `83175f439c60346f92b5759a90993c3b8f5352f8`.
- PyPI published `aifordable-runner-mcp==0.1.2` successfully and the workflow verified that exact version became publicly visible.
- Official MCP Registry validation, GitHub OIDC authentication and publication all succeeded for `io.github.Blacksp1d3r/runner-mcp` version `0.1.2`.
- GitHub pre-release `v0.1.2` was created with wheel and sdist assets; tag `v0.1.2` points exactly to `83175f439c60346f92b5759a90993c3b8f5352f8`.
- Repository description and discovery topics are already live; README/distribution follow-up is moving canonical PyPI/Registry links and one consistent directory-submission packet into the first-party docs.
- Secondary discovery: Glama, Smithery, mcp.so and optional AllMCPs are the next channels. The current GitHub App cannot write to the external `chatmcp/mcpso` submission thread, so that submission needs a user-authenticated browser/CLI path rather than an integration bypass.
- Do not republish or overwrite PyPI 0.1.1. It remains historical evidence of the first PyPI-only attempt; 0.1.2 is the canonical cross-registry release.

## 2026-09-26 — v0.1.1 AIfordable PyPI identity integrated

- PR #102 merged to `main` as `d948945034e07616d673945467e9b2e44748fa10` after exact-head validation and commit-attribution checks were green with zero review threads.
- Post-merge `main` validation and attribution were green on the merge commit.
- Python distribution identity is now `aifordable-runner-mcp`; product/primary CLI remain Runner MCP / `runner-mcp`; `aifordable-runner-mcp` is also exposed as a launcher alias for uvx/Registry compatibility.
- Pending PyPI Trusted Publisher is configured for `aifordable-runner-mcp`, `Blacksp1d3r/runner-mcp`, `publish.yml`, environment `pypi`; GitHub `pypi` is main-only with required human review and no stored PyPI token.
- The previous umbrella brand is retired from current project materials; AIfordable is the current umbrella identity.
- Remaining release action is human-controlled: dispatch `Publish Runner MCP` from `main` with version `0.1.1`, approve the `pypi` environment deployment, then verify PyPI -> MCP Registry -> GitHub pre-release in that fail-closed order.

## 2026-09-26 — v0.1.1 PyPI identity reconciled

- Active branch: `release/v0.1.1-aifordable-pypi`.
- PyPI rejected the new project name `runner-mcp` as too similar to an existing project; no package was published under that name.
- The pending Trusted Publisher is now configured for `aifordable-runner-mcp`, repository `Blacksp1d3r/runner-mcp`, workflow `publish.yml`, environment `pypi`.
- The GitHub `pypi` environment is restricted to `main` and requires the repository owner as reviewer; no long-lived PyPI API token is used.
- This branch changes only distribution/branding metadata: PyPI package `aifordable-runner-mcp`, CLI/product name remains `runner-mcp` / Runner MCP, official MCP Registry identity remains `io.github.blacksp1d3r/runner-mcp`.
- Public umbrella branding is being reconciled to AIfordable; the previous umbrella brand is retired from current project materials. Runtime/security authority remains unchanged.
- Publication remains blocked until this branch is exact-head green, reviewed, merged to `main`, and the human-triggered `Publish Runner MCP` workflow is approved/run for version `0.1.1`.

## 2026-09-26 — v0.1.1 distribution/discovery release prepared

- Active branch: `release/v0.1.1-discovery`.
- This slice changes packaging, discovery, release automation and public positioning only; it adds no new Runner MCP runtime authority.
- Package/version metadata is prepared for `runner-mcp` 0.1.1 and official MCP Registry identity `io.github.blacksp1d3r/runner-mcp`.
- `server.json`, distribution metadata regression tests, PyPI Trusted Publishing guidance and a human-triggered publish workflow are included.
- Publication order is fail-closed: exact release validation and artifact build -> PyPI OIDC publication -> PyPI visibility proof -> MCP Registry GitHub-OIDC publication -> GitHub pre-release.
- External publication is NOT complete yet. The first PyPI release still requires the one-time pending Trusted Publisher configuration plus matching protected GitHub `pypi` environment; then the publish workflow must be explicitly run from merged `main`.
- README/launch copy now lead with the concrete problem: useful AI development/staging operations without making a general-purpose remote shell the normal interface.
## 2026-09-24 — v0.1.0 alpha released and public docs reconciled

- GitHub pre-release `v0.1.0` is published from exact validated release commit `f00ac3fd03df234cb186a4dfcd804136501c0cf7`; the published notes preserve the alpha limitations and validation provenance.
- Post-release docs PR #98 merged as `5647aa8839af90451189d2d943ce393edfacfe78`. Exact PR head `adc08c86628aed6256ba44271d0a55cd366ae3e8` passed run #514 / `36041142332`; merged-main run #515 / `36041352332` is fully green.
- README now links the current alpha, CHANGELOG records the dated 0.1.0 release, and launch-readiness no longer describes the first tag as pending.
- The immutable release reference remains the earlier exact green commit `f00ac3fd03df234cb186a4dfcd804136501c0cf7`; post-release documentation is intentionally later on `main`.
- GitHub repository metadata still needs the prepared public wording: description `Security-first self-hosted MCP for controlled AI development and staging operations without a general-purpose remote shell.`; topics `mcp`, `model-context-protocol`, `self-hosted`, `ai-tools`, `developer-tools`, `devops`, `staging`, `security`, `python`, `automation`.
- Runner Fabric remains a separate private/proprietary project and is not part of the Runner-MCP MIT release.
- Remaining broader-launch gates: clean-host install verification from published `v0.1.0`, repository metadata, then optional ecosystem/registry submission and human-controlled community timing.

## 2026-09-24 — release-track reconciliation after Task 41 integration

- Runner Fabric remains a separate private repository/project. Runner-MCP stays the small, auditable execution product intended for release and must not absorb Runner Fabric orchestration scope.
- PR #97 `feat: add reusable bounded text redaction` merged as `9ce5fe94f417e4e7f910c9945727f70cffd33ecb`.
- Exact PR head `91e0c1b1e737ad14a43b31750cfdfbf1bf582f24` passed validation run `36037258558` fully green: Ruff/pytest/whitespace, clean five-minute demo and built release artifact.
- Live reconciliation after the merge found no open Runner-MCP pull requests and no open Runner-MCP issues.
- This coordination update must itself receive exact-main green CI before any first alpha tag is considered.
- Task 10 private-host self-update/recovery proof remains unproven; release wording must keep that limitation explicit rather than implying live-host proof.
- The next release-track action after exact-main CI is a final alpha-candidate gate check. Tag/release, repository description/topics, registry submission and external posting remain explicit user-controlled actions.

## 2026-09-24 — Task 41 bounded redaction complete; Task 43 lock prerequisite found

- Task 41 implementation is COMPLETE on PR #97 pending final exact-head CI/integration.
- New shared bounded text-redaction primitive handles known secrets, known private paths and the existing bearer/password/token/GitHub-token patterns with explicit input/output byte limits and deterministic truncation.
- TestRunner now delegates its log scrubbing to the shared primitive; no journal reader or remote log authority was added.
- Direct implementation prep for Task 43 found a real safety prerequisite: `DeploymentManager._lock_for()` uses in-process `threading.Lock`, while Task 43 is a local CLI process and can therefore race deploy/rollback in the long-lived MCP process.
- Task 43 is blocked on Task 46 cross-process release-mutation lock review. Do not implement pruning until that boundary is resolved.
- Task 44 is now prerequisite-safe because Task 42 / PR #96 merged as `82ecef725d828b69e328f8f474553e01ef8548cb`.
- Task 47 is queued after Task 41 for a local/private service-journal reader with explicit per-service opt-in only; MCP/mailbox log exposure remains deferred.

## 2026-09-24 — Task 42 durable migration-job substrate review complete

- Task 42 review is COMPLETE on PR #96 pending integration.
- A dedicated persisted migration-job substrate is justified, but it must be additive first: the current MCP/bridge `apply_migrations` path remains synchronous until the substrate is independently proven.
- Future migration jobs must durably persist queued state before worker start, revalidate the exact approval-bound migration plan, call existing `DatabaseManager.apply_migrations()` at most once, and never replay queued/running work after restart.
- Restarted queued/running migration jobs become terminal `interrupted`; ambiguous success is reported for attention rather than guessed or retried.
- Deployment-triggered migrations remain synchronous inside deployment.
- Task 44 is queued for the private job substrate plus read-only completion scanner. Task 45 is separately blocked on Task 44 for any later remote asynchronous integration decision.
- Task 43 is prerequisite-safe after Task 40 / PR #95; Task 39 is already integrated on main via PR #94.

## 2026-09-24 — Task 39 adapter preset boundary refactor complete on PR #94

- Task 39 implementation is COMPLETE on PR #94 pending final exact-head CI/integration.
- Built-in pytest, Ruff and Alembic recipe materialization moved out of generic `config_manager.py` framework branches and behind typed adapter methods.
- Python adapter executable discovery remains project-local, rejects symlinked roots/virtualenvs/executables, requires executable access and verifies the resolved executable remains under the project root.
- The generic adapter has no built-in recipe authority. Unknown/ambiguous presets fail closed.
- The `custom` path remains explicit/local with the previous validation and no shell command string.
- Direct adapter/config-manager regression coverage and extension documentation were updated.
- No dynamic plugin loading, framework dependency, speculative adapter or new execution authority was added.
- Tasks 37 and 40 are already integrated on main; Task 43 remains blocked only on its explicit ownership/implementation claim, not on Task 40.

## 2026-09-24 — Task 40 retention pruning execute-boundary review complete

- Task 40 review is COMPLETE on `chatgpt/task40-retention-pruning-review` pending integration.
- Task 34 evidence is sufficient for one conservative next mutation only: local/manual pruning of exactly one old non-migration orphan release outside the entire retained rollback chain.
- The first executable slice must preserve current/direct rollback/reference closure and every migration-boundary release, acquire the deployment lock, recompute eligibility, bind a short-lived local plan, quarantine atomically, and use only symlink-safe fd-relative recursive deletion.
- Manual backups remain indefinite-retention/non-candidates. Backup pair pruning remains separately deferred because flat dump+metadata deletion needs its own durable crash-recovery transaction.
- Automatic/unattended pruning and all MCP/mailbox deletion authority remain deferred.
- Task 43 is queued but blocked until Task 40 is integrated.

## 2026-09-24 — Task 34 read-only retention preview implementation complete on PR #92

- Task 34 implementation is COMPLETE on PR #92 pending final exact-head CI/integration.
- New local CLI: `runner-mcp retention preview PROJECT`.
- Preview is advisory only and explicitly reports `deletion_authorized=false`; no release, backup or metadata deletion/rewrite path was added.
- Strict scanning fails closed on unsafe/symlink/broad-permission/malformed release or backup metadata, incomplete backup pairs and dump-size mismatch.
- Current release, direct rollback target, retained release references and migration-recovery references are protected; manual backups are never automatically eligible.
- Production/non-staging projects remain read-only; preview remains available while the emergency stop is active.
- Public output contains only bounded project/environment/ID/timestamp/kind/category state and does not expose filesystem paths, DSN, service units, health URLs, dump content or private configuration.
- Focused tests plus the full suite have passed during implementation; final exact-head PR CI remains authoritative before merge.
- Actual pruning/deletion remains deferred. A later execute-boundary review must separately resolve locking, crash-safe deletion, rollback-chain semantics and typed confirmation.
- PR #91 already merged as `11b9a4d4e508ac93cd436037563c09d08cfa43ab`, completing Tasks 33, 35 and 38.
- Task 37 restore-execution boundary review is proceeding independently on PR #93; Task 39 is now prerequisite-safe after Task 38 integration.

## 2026-09-24 — Tasks 32 and 36 alpha-readiness work landed

- Task 32 COMPLETE: PR #89 merged as `e629515f9c7e7a5d44506dfb82a48343870f94da`.
- Task 32 exact PR head `99c72037eff4ed54cf7e92f7a08b278b48af4e45` passed CI run 35967246877 fully green: Ruff, whitespace, 1267 pytest tests, built release artifact and clean demo.
- Audit conclusion: package/build/demo mechanics are suitable for an alpha candidate, but six public-documentation drift items had to be reconciled before any tag.
- Task 36 COMPLETE: PR #90 merged as `8c971016e4fc3cd821dc52d28334567c20835ff4`.
- Task 36 exact PR head `1b3567b5de1f5a4ac5a67db16c609db2edac25dd` passed CI run 35967550375 fully green: Ruff, whitespace, 1267 pytest tests, built release artifact and clean demo.
- CHANGELOG now treats 0.1.0 as an unreleased alpha candidate; restore/security wording, mailbox launch copy, README rendering, public-data hygiene wording and connectivity limitation are reconciled.
- Live GitHub still has no `v0.1.0` tag or GitHub release. Repository description/topics, tag/release, registry submission and external posts remain explicit user-controlled actions.
- Task 10 private-host live self-update/recovery proof remains externally BLOCKED and must not be overclaimed in release wording.
- Current bounded queue: Tasks 33–35. No release/publication action was performed.

## 2026-09-24 — Task 31 local read-only restore preflight landed

- Task 31 COMPLETE: PR #88 merged as `e54a0684bdc9da3a32d062e0e0e45261c1616020`.
- Exact PR head `fc08b60c6feed85824b6097bf1479e7e41a29844` passed CI run 35966414093 fully green: Ruff, whitespace, 1267 pytest tests, built release artifact and clean demo.
- Local CLI now supports `runner-mcp database restore-plan PROJECT BACKUP_ID` for a read-only PostgreSQL backup preflight.
- The preflight validates strict backup identity/shape, private regular-file modes, size, symlink-free storage and fixed trusted `pg_restore --list` parseability without reading the configured DSN or connecting to a database.
- The archive is opened once with no-follow semantics, streamed through SHA-256 privately, passed to `pg_restore` over stdin so the private dump path is not placed in argv, and revalidated/hash-checked after parse to detect content/permission races.
- Production projects report ineligible. Emergency stop does not block the read-only preflight.
- Database restore execution, pre-restore backup, restore approval authority, WAL/PITR, production recovery and MCP/bridge/mailbox restore exposure remain deferred.
- Current bounded queue: Tasks 32–34. Task 10 remains externally BLOCKED.

## 2026-09-24 — Task 30 retention-pruning boundary review landed

- Task 30 COMPLETE: PR #87 merged as `99d081cd242642bfa8346031a22079b7397869bc`.
- Exact PR head `0a6e09fe4e4cd403c6ee6c4cc66461694b019a2a` passed CI run 35958661041 fully green: Ruff, whitespace, 1237 pytest tests, built release artifact and clean demo.
- Review conclusion: existing age/count predicates are policy inputs, not destructive authorization. Manual backups have no automatic-deletion policy; current/rollback/reference/migration-recovery relationships require additional protection.
- Automatic deletion remains deferred. Task 34 is queued as the smallest safe follow-up: local read-only retention preview only.
- Current bounded queue: Tasks 31–34. Task 10 remains externally BLOCKED.
- No backup/release deletion, metadata rewrite, retention change, approval expansion or mailbox deletion authority was performed.

## 2026-09-24 — Task 29 privacy-safe connectivity guidance landed

- Task 29 COMPLETE: PR #86 merged as `b0f54cb14d73fba3b7c5b8655b5b051af779fd0a`.
- Exact PR head `7d4c264fbfac6881badbdf8f9bc69ea7a7ab12e8` passed CI run 35958283065 fully green: Ruff, whitespace, 1237 pytest tests, built release artifact and clean demo.
- `runner-mcp guide` now reports only a generic connectivity category and bounded next steps. Configured external hostnames/resource URLs/auth issuers/tokens/private paths are not printed.
- Public setup is now documented consistently as external HTTPS identity only; it does not bind publicly or configure TLS, DNS, firewall, proxy or tunnel state.
- Current Secure MCP Tunnel guidance is linked to canonical OpenAI documentation; Runner MCP remains loopback-first and vendor provisioning stays external.
- Current bounded queue: Tasks 30–32. Task 10 remains externally BLOCKED.
- No network exposure, TLS/DNS/firewall, tunnel, tag, release or publication action was performed.

## 2026-09-24 — Task 28 deployment/rollback completion delivery landed

- Task 28 COMPLETE: PR #85 merged as `131e168e02b7d5781441bbc8256e65de434e6166`.
- Exact PR head `87f1d0c8295b059b4504e2971c5ef89ed9dc8422` passed CI run 35951310986 fully green: Ruff, whitespace, 1235 pytest tests, built release artifact and clean demo.
- Completion delivery now scans configured deployment/rollback job metadata read-only and never instantiates `DeploymentJobRunner`.
- Strict validation requires exact lowercase 32-hex job identity, explicit deploy/rollback operation, safe project, known state, private regular metadata and timezone-aware terminal timestamp; malformed/duplicate/non-finite/oversized/unsafe metadata fails closed.
- Deploy and rollback events use source-scoped deterministic IDs and the existing bootstrap cutoff, local delivery ledger and remote marker idempotency.
- Notification bodies omit `Test profile: None` for non-test events and expose only validated project, allow-listed operation, state and event ID. Deployment result/error/commit/release/path metadata is not copied.
- Migration completion remains blocked pending a separately reviewed durable migration-job substrate.
- Current bounded queue: Tasks 29–31. Task 10 remains externally BLOCKED.
- No tag, release, publication, deployment, rollback, migration or external mutation was performed by this task.

## 2026-09-24 — Task 27 database restore/recovery review landed

- Task 27 COMPLETE: PR #84 merged as `f1e92bb2997ad8b9d26e978892319289e1b7e4f1`.
- Exact PR head `a90667259b7dea7d6dcddf1ead26fc982d4fb893` passed CI run 35949363983 fully green: Ruff, whitespace, 1211 pytest tests, built release artifact and clean demo.
- Review preserves the hard separation between code rollback, one-backup logical restore and WAL/PITR. Automatic/remote restore remains unavailable; production restore remains outside Runner MCP mutation authority.
- Task 31 queued as the smallest safe follow-up: local read-only restore preflight/plan only, with strict backup identity/privacy and fixed pg_restore parseability checks; no database mutation or MCP/mailbox restore action.
- Task 10 remains externally BLOCKED. Current bounded queue: Tasks 28–31.
- No tag, release, publication, deployment, migration, restore, deletion or external database action was performed.

## 2026-09-24 — Task 26 bounded service-journal review landed

- Task 26 COMPLETE: PR #83 merged as `b08a0b10afcce754440c37025230773da72c6c05`.
- Exact PR head `faa5126548021c9294e3a395c6b71344505e545d` passed CI run 35949004101 fully green: Ruff, whitespace, 1211 pytest tests, built release artifact and clean demo.
- Review conclusion: remote/MCP service-journal access stays deferred. Current alias/process boundaries are strong, but arbitrary application journal content needs an explicit per-service log-read opt-in and a reusable bounded text-redaction prerequisite before any local reader is justified.
- Task 30 was added from the roadmap's explicit deferred retention-pruning work to keep the public queue dependency-safe.
- Task 10 remains externally BLOCKED. Current bounded queue: Tasks 27–30.
- No tag, release, publication, deployment, migration, restore, log exposure or deletion was performed.

## 2026-09-24 — Task 25 private connectivity/TLS onboarding review landed

- Task 25 COMPLETE: PR #82 merged as `f2c1d6a135133033ab1e0059f9a92cfec3021d88`.
- Exact PR head `38b3143d53d49c58af896adfe96b943e34c2ee5a` passed CI run 35948648167 fully green: Ruff, whitespace, 1211 pytest tests, built release artifact and clean demo.
- Review confirms Runner MCP already preserves the required runtime safety boundary: setup does not mutate network exposure, serve/autostart remain loopback-first, non-loopback bind requires explicit override, and non-loopback HTTP is rejected/flagged.
- Demonstrated onboarding drift: `security/CONNECTIVITY.md` still describes Secure MCP Tunnel as a future connection, while current official OpenAI guidance and Runner MCP's own README/Quickstart describe it as available for supported products.
- Task 29 queued for documentation + privacy-safe guide reconciliation only; it must not configure TLS, DNS, firewall, reverse proxy or tunnel state.
- Task 10 remains externally BLOCKED. Current bounded queue: Tasks 26–29.
- No tag, release, publication, deployment, migration, restore or network mutation was performed.

## 2026-09-24 — Task 24 completion-delivery expansion review landed

- Task 24 COMPLETE: PR #81 merged as `d9f7d40f952ab39478d4a0286d317f160d6b46ce`.
- Exact PR head `22d5e9a7c7e5ab854b81d84b7b9997202837caf4` passed CI run 35915217076 fully green: Ruff, whitespace, 1211 pytest tests, built release artifact and clean demo.
- Review finding: persisted deployment and rollback jobs are safe candidates for one bounded read-only completion-delivery integration; migration completion is blocked because no dedicated persisted migration-job substrate exists.
- Task 28 queued from this evidence for deployment/rollback completion delivery only.
- Task 10 remains externally BLOCKED. Current bounded queue: Tasks 25–28.
- No tag, release, publication, deployment, migration or database action was performed.

## 2026-09-23 — Task 23 completion watcher diagnostics landed

- Task 23 COMPLETE: PR #80 merged as `873f905c64cdfbfc0ec6ac4b5091c04877b84d59`.
- Exact PR head `595bb6466e7eca50b4b21a9dbc8695a59b248c11` passed CI run 35914643900 fully green: Ruff, whitespace, 1211 pytest tests, built release artifact and clean demo.
- `CompletionNotifierRuntime.run_forever()` now emits only enum-rendered lifecycle, healthy/degraded cycle and bounded restart-failure diagnostics through an optional sink.
- Delivery/replay/idempotency behavior remains unchanged; tests inject repository/path/token/event/URL/exception literals and prove they cannot enter diagnostics.
- Task 10 remains externally BLOCKED. Current bounded queue: Tasks 24, 25 and 26.
- No tag, release, publication, deployment or migration was performed.

## 2026-09-23 — Task 22 cron supervisor diagnostics landed

- Task 22 COMPLETE: PR #79 merged as `1bfeb9e7e8991058fb82a31b6d93b94f77c5ba72`.
- Exact PR head `65e15a9654e131073d8e90dc90cfa5e0536b9781` passed CI run 35903803377 fully green: Ruff, whitespace, 1208 pytest tests, built release artifact and clean demo.
- `run_cron_component()` now emits only enum-rendered `cron_supervisor` diagnostics for lock-held, exec handoff and bounded start/restart failure states through an optional sink.
- Diagnostics contain no selected component, argv, executable/config path, environment value or raw exception text; adversarial tests inject sensitive literals and prove they cannot escape.
- Cron ownership, locking, command construction and execution authority were not changed.
- Task 10 remains externally BLOCKED. Current bounded queue: Tasks 23, 24 and 25.
- No tag, release, publication, deployment or migration was performed.

## 2026-09-23 — Task 21 managed autostart secure I/O landed

- Task 21 COMPLETE: PR #78 merged as `22e14fff99a4f02a30f2edf9abffd98a8b1792ea`.
- Exact PR head `01ee0c0bfeaeae8f3a07a47f4162d4f9560304ab` passed CI run 35903107229 fully green: Ruff, whitespace, 1207 pytest tests, built release artifact and clean demo.
- `autostart._write_managed_unit` now uses the shared private atomic-replace primitive while preserving the existing managed-marker ownership refusal.
- Regressions prove unmanaged unit content is preserved, successful writes end at 0600, fsync/replace failures keep the previous managed unit and emit only bounded errors, and a symlink swap cannot alter its referent.
- Cron, job metadata, ledgers, create-only writers, deployment activation/tar extraction and self-update were not changed.
- Queue refilled from explicit roadmap items: Tasks 22 and 23 remain CODE lanes; Tasks 24 and 25 are bounded CHAT REVIEW lanes for completion-delivery expansion and private connectivity/TLS onboarding.
- Task 10 remains externally BLOCKED on a usable private-host proof path. No tag, release, publication, deployment or migration was performed.

## 2026-09-23 — Task 20 bridge adversarial matrix landed

- Task 20 COMPLETE: PR #77 merged as `4bfd71d85cb5228ba328ee17fc60414c84c43e0a`.
- Exact PR head `666a399803db41bae4deae73fc4f205de5e97854` passed CI run 35895116909 fully green: Ruff, whitespace, 1203 pytest tests, built release artifact and clean demo.
- Test-only hardening: one minimal valid fixture now exists for every BridgeAction, every syntactically valid non-owned optional field is rejected per action, action case/hyphen/prefix variants fail closed, duplicate request_id and request-side NaN/Infinity fail closed, and uppercase self-update commit remains rejected.
- Every adversarial rejection is exercised through BridgeProcessor with fail-if-reached replay/result boundaries and an executor invocation counter, proving invalid requests do not reach execution.
- No production protocol, action enum, alias, normalization, identifier regex, replay state, executor mapping or capability changed.
- Current UNCLAIMED bounded public queue: Tasks 21, 22 and 23. Task 10 remains externally BLOCKED.
- No tag, release, publication, deployment or migration was performed.

## 2026-09-23 — Task 18 private atomic-replace hardening landed

- Task 18 COMPLETE: PR #76 merged as `5c4f5db350cdafa99066bdb091866b7d6979a7a9`.
- Exact PR head `97fcde693d6264171920c386d10e9e63403a9a9a` passed CI run 35894315537 fully green: Ruff, whitespace, 794 pytest tests, built release artifact and clean demo.
- Added one internal `secure_io.atomic_replace_private` overwrite primitive using a random same-directory temp, exact 0600 descriptor mode, file fsync before atomic replace, symlink refusal, ordinary-failure cleanup and bounded errors.
- `config_manager` and `approval_manager` now use the primitive while retaining their existing higher-level locks and serialization/state ordering.
- Completion notifier config/bootstrap private JSON state now uses the primitive while retaining size/schema checks and parent-creation behavior.
- Autostart, cron, high-churn job metadata, in-place ledgers, create-only writers, deployment activation/tar extraction and self-update were not changed.
- Queue refilled from existing review evidence: Tasks 20, 21, 22 and 23 are UNCLAIMED; Task 10 remains externally BLOCKED on a private-host proof path.
- No tag, release, publication, deployment or migration was performed.

## 2026-09-23 — Tasks 16/17 landed and session reconciled

- Canonical main checkpoint after PR #74: `3d7792ee088a10ca44126415394e74c8e3c29ce3`.
- Task 16 COMPLETE: adversarial protocol review merged via PR #72; no runtime capability-expansion defect demonstrated; bounded follow-up Task 20 queued for exhaustive fail-closed regression coverage.
- Task 17 COMPLETE: append-only audit writer hardening merged via PR #73. Exact final head `60466a72b1c8492eac54e4963b9d7ef4bb572977` passed CI run 35891213181 fully green.
- PR #74 merged the queue/agent handoff evidence for Tasks 16/17.
- Task 10 remains externally BLOCKED pending a usable private-host proof path.
- Next safe implementation work is Task 18 or Task 20 after live ownership reconciliation.
- No release/tag/publication was authorized or performed.

## 2026-09-23 — v0.1.0 public release docs prepared

- PR #57 merged: the changelog now has a dated v0.1.0 release-candidate section and Unreleased is reopened.
- `docs/RELEASE_NOTES_0.1.0.md` now covers the completed self-update hardening, bounded runtime visibility and the no-dependency bootstrap boundary.
- The release notes explicitly state that the newest private-host self-update recovery matrix has not yet been freshly re-proven.
- No tag, GitHub release or external publication has been created.
- After this handoff-only update lands, the resulting exact `main` commit must pass public CI and a final privacy review before it can be considered a tag candidate.
- The remaining non-public evidence item is the private-host live self-update proof; if it is not completed before release, the limitation must remain explicit.

## 2026-09-23 — Tasks 2–9 queue complete

Current public repository state:
- PR #53 merged as `0c46bbefb8fcad6ae5c7f87450e638c40492a41a`: Task 6 documentation/CLI contract audit complete; `runtime_doctor` is documented and the stale evergreen pre-tag test count is gone.
- PR #54 merged as `69e604935bfe0fef0dd61b48dfdde76fed8f46ba`: Task 7 dependency compatibility/bootstrap design complete; `docs/SELF_UPDATE_COMPATIBILITY.md` is the canonical boundary.
- PR #55 merged as `358f8f6345a7ff6f094eb6c8e4d7db4b9943aed7`: Task 9 release-candidate hygiene dry run complete.
- Tasks 2–9 are complete; no open Runner-MCP PR existed when this checkpoint was reconciled.
- No tag, release or external artifact has been created.

Next safe release-preparation work:
- finalize the v0.1.0 changelog and release-notes draft;
- validate the exact candidate commit and repeat public-repository privacy review before any tag;
- keep dependency/build/interpreter contract changes on the normal dependency-resolving bootstrap path;
- reconcile the remaining private-host self-update live proof, or explicitly retain that limitation in release notes.

Private runtime state:
- this batch did not re-probe the private host;
- older watcher recovery-attention observations remain historical/last-known, not current health evidence;
- never reset watcher replay/cursor/transaction state as a shortcut.

## 2026-09-22 — Task 8 checkpoint

- PR #52 merged as `d6821ddb0773b586b6a106b66b2e18154c90cc7a`.
- local release validation now has one fail-fast wrapper: `bash scripts/release-check.sh`;
- the wrapper covers compile, Ruff, pytest, branch/local whitespace, built-artifact smoke and clean-demo smoke while explicitly leaving GitHub CI authoritative;
- the clean demo no longer creates or deletes the repository's developer `.venv`; its project virtualenv lives under the temporary demo root;
- Task 6 audit has one demonstrated documentation drift ready for the next slice: `runtime_doctor` exists in the bridge protocol/executor/server but is omitted from README and the public bridge supported-action list;
- private watcher/recovery state was not re-probed in this batch.

## 2026-09-22 — current reconciliation checkpoint

Current public GitHub state:
- `main` includes PR #46 installer/operator robustness, PR #47 secure-I/O inventory, PR #48 self-update durability fsync hardening, PR #49 safe diagnostics contract, PR #50 CLI removal-confirmation deduplication and PR #51 reconciled self-update recovery visibility.
- PR #51 merged as `011fcbfec4e0b75a93820ca1c4c487111da6b495` after current-main CI passed Ruff, 773 pytest tests, whitespace validation, clean demo and built release artifact.
- stale PR #45 was closed unmerged after its functionality was rebuilt on current main in #51.
- there are no open Runner-MCP pull requests at this checkpoint.
- self-update transaction and installed-state markers now flush/fsync the file before replace and fsync the parent directory after replace.
- local `status` exposes install recovery only as `clear`, `REQUIRED` or `INVALID`; `doctor` warns/fails on pending/invalid recovery without exposing transaction details.
- watcher/notifier/supervisor diagnostics now have a category-only safe contract; production logging integration remains a separate later slice.
- ordinary REMOVE-style CLI confirmations share one narrow helper; emergency-stop, approval, watcher-recovery and self-update-recovery confirmations remain separate.

Agent-capacity policy:
- analysis/design-heavy Claude work is marked `CHAT REVIEW` and should be done in normal Claude chat rather than Claude Code;
- ChatGPT is the default implementer for CODE work unless explicitly reassigned;
- a Claude rate limit never blocks the critical path.

Private runtime state was not re-probed during this GitHub-only reconciliation. The prior handoff's degraded watcher/recovery-attention observation therefore remains historical/last-known, not a newly verified current fact.

## Controlled multi-project concurrency — 2026-09-21

Bounded fair multi-project concurrency is merged and validated. Runner MCP now separates mailbox acceptance from durable test execution, maintains fair logical per-project queues, returns immediate job IDs, exposes safe queue/worker/job state, and keeps same-project overlap opt-in only. High-risk mailbox actions remain excluded.

The authenticated MCP request limit was also raised from 60 to a still-bounded 600 requests per minute so concurrent mailbox workers and normal status polling do not hit a transport bottleneck before worker or queue capacity. Test-worker, project-lock and queue limits remain independent safety controls.

## Shared watcher migration proof — 2026-09-21

A private deployment has been migrated from the pilot poller to the shared `runner-mcp github-watcher run` runtime. The watcher was explicitly bootstrapped at the current request head, so historical mailbox entries were not replayed. After fresh requests and a package restart, the private cursor matched the request head, the replay ledger contained only completed records, and the heartbeat reported healthy with zero recovery attention.

Live protocol-v1 checks completed for `project_status`, `project_capabilities`, `list_test_profiles`, `queue_status` and `worker_status`. A real predefined test request was accepted asynchronously and later reached a terminal passed state through `job_status`. During that proof, the MCP SDK's multi-item encoding for list-returning tools exposed a compatibility gap; the loopback executor was hardened to accept bounded object-only multi-item list results while scalar tools remain fail-closed.

The legacy private poller is disabled in that deployment. Completion-notification transport remains an independent capacity concern and is not part of mailbox execution authority.

# Current state

Date: 2026-09-21

## Status

Runner MCP Phases 0 through 9 and Phase 3.9 launch-readiness are merged to main. Phase 3.7 formalizes the GitHub mailbox transport; Phase 3.8 adds bounded results and replay protection. Phases 3.8.1 through 3.8.7 add completion events, restart safety, the transport-neutral processor, hardened GitHub transport, incremental watcher coordination, the loopback MCP executor and private-config watcher runtime. Phase 3.8.8 adds bounded fair multi-project concurrency. The shared watcher runtime has now also been proven in a private deployment with explicit bootstrap, restart-safe cursor/replay recovery, bounded concurrent request handling, strict result publication and asynchronous test-job follow-up. GitHub remains the source-code surface, while Runner MCP remains the local execution and safety boundary.

Phase 0:
- repository structure defined;
- public infrastructure-data ban documented;
- security baseline drafted;
- threat model drafted;
- example project configuration added;
- public example safety tests added;
- manual privacy scan clean.

Phase 1 foundation:
- MCP server skeleton added;
- bearer-token verification hook added;
- health endpoint added;
- project registry added;
- `list_projects` added;
- `project_status` added;
- append-oriented audit logging added;
- per-request IDs added;
- bounded in-memory rate limiting added;
- health endpoint exempted from operator rate limiting;
- unauthenticated MCP requests verified to fail closed;
- project roots/repositories/services validated before use;
- DNS-rebinding protection bound to the private runtime MCP resource URL;
- authenticated MCP handshake and tool discovery verified end-to-end.

Phase 2 safe file access:
- `read_project_file` added with bounded line pagination;
- `list_project_files` added with bounded non-recursive listing;
- `file_metadata` added without exposing configured root paths;
- absolute paths, traversal, backslashes and symlinks rejected;
- secret paths such as environment files, keys and database artifacts blocked;
- binary/private-key content blocked;
- known literal secret values redacted;
- file-size, line-count and directory-entry limits enforced;
- MCP-level allowed/denied file reads and audit behavior tested end-to-end.

Phase 2.5 operator safety:
- external operator-stop file policy added;
- future operator actions fail closed until stop mechanism is configured;
- future operator actions remain read-only until retention values are explicitly confirmed;
- `safety_status` exposes safety state without returning private paths;
- code-release cleanup requires both count and age thresholds;
- default proposal is 20 releases and 90 days;
- PITR and pre-migration backup retention are separate controls;
- one approved code rollback may move back exactly one release;
- database restore always requires explicit approval;
- automatic production database restore is prohibited;
- operator-safety rules documented for later test/deploy/migration phases.

Phase 3 controlled test execution:
- private predefined test-profile schema added;
- MCP clients select only project and profile name, never a command string;
- executables must be absolute and are launched with `shell=False`;
- unsafe working-directory traversal and process-control environment variables are blocked;
- asynchronous jobs expose safe status, cancellation and paged scrubbed logs;
- per-project and global concurrency are bounded;
- test timeout and log-size limits are enforced;
- external operator stop terminates running test process groups;
- unfinished jobs are marked interrupted after Runner MCP restart;
- job metadata/logs use restrictive permissions;
- environment secrets, project paths and absolute command paths are scrubbed from logs;
- MCP lifecycle from `run_tests` through `test_status` and `get_test_log` is tested end-to-end;
- test-code trust boundary is documented; untrusted public-fork code remains excluded until stronger isolation exists.

Phase 3.5 onboarding:
- installable `runner-mcp` console command added;
- non-root `install.sh` added;
- interactive setup supports safe local mode and explicit public mode;
- generated private config uses restrictive filesystem permissions;
- inherited shell variables do not override setup-managed private runtime config;
- setup overwrite preserves the existing bearer credential unless `--rotate-token` is explicit;
- `status`, `doctor`, `emergency-stop` and `serve` commands added;
- project add/list/remove commands added without manual YAML editing;
- test-profile add/list/remove commands added;
- pytest and Ruff presets auto-detect project virtual environments;
- custom executable and project paths reject symlink components;
- project config updates are lock-protected and atomic;
- user-first README and QUICKSTART added.


Phase 3.7 GitHub mailbox bridge protocol:
- public infrastructure-neutral architecture and usage guidance added;
- versioned JSON requests are size-bounded and reject duplicate keys;
- request fields are strict and unknown fields fail closed;
- only list_projects, safety_status, project_status, project_capabilities, list_test_profiles and run_tests are allow-listed;
- no shell, executable, filesystem path, environment, service or arbitrary MCP tool may be supplied through the protocol;
- migration, deployment, rollback and restore remain outside the mailbox bridge and keep their existing approval boundaries;
- reusable public protocol logic is separated from private watcher credentials and infrastructure configuration.


Phase 3.8 bridge result envelope and replay protection:
- strict protocol-v1 result envelopes added for completed and failed operations;
- result payload size, nesting, collection count and string length are bounded;
- unknown result fields and duplicate JSON keys fail closed;
- sensitive result keys and absolute locations/URLs are conservatively redacted;
- failed results use bounded safe error codes instead of arbitrary raw process or exception output;
- canonical SHA-256 request fingerprints added;
- local replay ledger stores only request ID, fingerprint, allow-listed action and first-seen timestamp;
- duplicate identical requests are detected and must not execute again;
- reusing an existing request ID with changed content fails closed;
- corrupt, oversized, capacity-exhausted and symlinked replay-ledger states fail closed;
- replay ledger files are restricted to the service account;
- an initial umbrella project identity and a free public-launch-readiness plan were added without changing Runner MCP's product identity or security boundaries;
- public CI validates pull requests and main on a fresh standard GitHub-hosted runner with read-only repository permissions, pinned official actions and no private secrets; standard runners are free for this public repository.


Phase 3.9 public launch readiness:
- README now leads with a concise problem statement, architecture and safety boundary;
- the umbrella identity remains secondary; Runner MCP retains its own product/package identity;
- five-minute local evaluation demo added alongside the full Quickstart;
- root security-reporting policy added;
- public changelog and release checklist added;
- factual launch copy prepared without publishing external posts;
- privacy-safe bug and feature request forms added;
- pull-request template reinforces security invariants and public-repository hygiene;
- package metadata expanded for future public distribution;
- launch-readiness gate explicitly tracks what is complete and what still needs clean-environment/release verification;
- no marketing telemetry or paid runtime dependency added.

Service auto-start packaging — 2026-09-21:
- fixed local CLI management for the Runner MCP server, shared GitHub watcher and completion watcher;
- systemd user services remain preferred when a usable user bus exists;
- a managed cron backend is available for headless accounts without a usable user bus;
- the cron backend uses a marked private-user crontab block and per-component file locks; it executes only fixed Runner MCP argv and never accepts a shell command;
- unmanaged pre-existing Runner MCP cron entries make installation fail closed to prevent duplicate supervisors;
- the server remains loopback-only and no generic service/unit/cron command can be supplied by a remote client;
- optional watcher supervision requires private configuration plus explicit bootstrap state before installation;
- generated autostart state contains no credentials; foreign systemd units and unrelated cron entries are preserved;
- safe status reports only backend plus component installed/enabled/active state.

Test runtime hardening — 2026-09-21:
- local PostgreSQL validation exposed that the existing per-job `TMPDIR` could make Unix-domain socket paths exceed the platform limit when the private jobs root is long;
- Runner MCP now allocates a short, unique 0700 temporary directory below the fixed system temp root for each test job;
- the short temp path is included in private-path log scrubbing and removed after the job terminates;
- this is project-neutral and does not add environment passthrough or project-specific command authority.

Phase 3.8.1 task-completion feedback:
- strict terminal completion events added for succeeded, failed and cancelled outcomes;
- deterministic event IDs provide notification deduplication without exposing private source identifiers;
- completion source and operation are fail-closed bound;
- test completion requires a safe predefined profile identifier;
- attention state is derived from the terminal result;
- event parsing rejects unknown fields, duplicate keys, non-standard JSON constants and oversized payloads;
- completion payloads exclude paths, hosts, URLs, credentials, environment values, service names and raw logs;
- execution replay protection remains separate from notification deduplication;
- notification transport failure may be retried but must never rerun the completed task;
- public completion contract is transport-neutral; private destinations remain private configuration;
- built-in completion delivery now observes persisted terminal test jobs, uses deterministic event markers plus a private delivery ledger, and has a live exactly-once private proof; it no longer depends on repository-specific self-hosted Actions capacity.

Fail-closed mailbox recovery — 2026-09-21:
- exact claimed/completed requests missing a durable result can be locally resolved to terminal `RECOVERY_REQUIRED` without invoking the executor;
- a strictly valid unclaimed request can be locally abandoned to terminal `OPERATOR_ABORTED` without execution;
- a malformed historical request can be quarantined only when every sibling request in the current backlog already has a matching durable result and the request head remains unchanged;
- the raw recovery fetch is bounded and fixed-path; normal watcher processing remains strict protocol-v1 parsing;
- a live malformed legacy `sync_project` request was quarantined after 40 sibling requests were verified durable/completed, restoring heartbeat to healthy with zero replay;
- no replay-ledger reset, cursor reset command, request deletion or blind task retry exists in these recovery paths.

Phase 3.8.2 watcher resilience and restart recovery:
- replay entries now carry an explicit claimed/completed lifecycle;
- legacy replay entries without state are treated conservatively as claimed;
- completion is recorded only after a safe result is durable;
- restart classification distinguishes process, result-exists, ambiguous-claim and result-missing states;
- ambiguous or missing-result work is never automatically re-executed;
- public heartbeat exposes only healthy/backlog/degraded plus bounded counts and oldest-pending age;
- request IDs and infrastructure metadata are excluded from heartbeat output;
- stale thresholds and observation counts are bounded;
- duplicate pending observations fail closed;
- transient transport retries are bounded and limited to timeout/rate-limit/unavailable failures;
- authorization and invalid-response failures are not automatically retried;
- watcher resilience and task-completion notification remain separate concerns.

Phase 3.8.3 transport-neutral bridge processor:
- request parsing and replay claim are enforced before execution;
- completed duplicate requests never execute again;
- claimed duplicates become an ambiguous recovery state;
- executor interface exposes only the six mailbox-allow-listed actions;
- run_tests is represented as an explicit run_tests_to_completion(project, suite) operation;
- executor exceptions are converted to generic safe failure envelopes;
- unsafe executor output fails closed as UNSAFE_RESULT;
- only scrubbed/bounded serialized results reach the transport sink;
- durable result persistence precedes replay lifecycle completion;
- persistence/finalization failures require recovery and never authorize action replay;
- GitHub credentials, branches, endpoints and supervisor configuration remain outside the public processor.

Phase 3.8.4 hardened GitHub mailbox transport:
- fixed GitHub API host; no caller-supplied endpoint;
- safe repository/ref/token shape validation;
- fixed request/result/heartbeat mailbox locations;
- bounded API response and mailbox entry counts;
- strict GitHub JSON rejects duplicate keys and non-standard constants;
- wrapped base64 is accepted only after validation;
- request payload ID must match its filename;
- results are create-once and idempotent only for identical existing content;
- conflicting result content fails closed;
- all result read/write transport failures enter the BridgeProcessor persistence-recovery boundary;
- heartbeat publication is bounded and validated;
- HTTP/network failures are safely classified without raw response leakage;
- transport uses the Python standard library and adds no paid runtime dependency.

Phase 3.8.5 incremental watcher coordinator:
- bounded transient GitHub retries only for timeout/rate-limit/unavailable failures;
- fast-forward request discovery from a private local cursor;
- no historical replay on first start; bootstrap is explicit;
- cursor file is 0600, lock-protected and refuses symlinks;
- cursor advancement uses an expected previous SHA to detect concurrent watchers;
- existing durable results are reconciled without action execution;
- claimed or completed requests missing results never execute again automatically;
- persistence/finalization recovery leaves the cursor behind for safe reconciliation;
- malformed request changes fail closed and block cursor advancement;
- heartbeat publication stays independent of completed task execution;
- heartbeat delivery failure cannot cause an action replay;
- non-request commits advance the cursor without creating fake work.

Phase 3.8.6 loopback MCP bridge executor:
- local MCP endpoint is restricted to loopback HTTP(S) and the exact /mcp path;
- URL credentials, query strings and fragments are rejected;
- bearer token, MCP session ID and test job ID values are bounded/validated;
- MCP response bytes and JSON/SSE parsing are fail-closed;
- raw transport/server/tool errors are not exposed through bridge results;
- public executor exposes only the six mailbox bridge operations;
- generic MCP dispatch remains private and internally allow-listed;
- run_tests uses internal test_status polling only until terminal state;
- test logs are never fetched by the bridge executor;
- terminal run_tests output contains only project, suite and status;
- polling and total wait durations are bounded.

Phase 3.8.7 private-config watcher runtime and CLI:
- private GitHub repository/refs/token are stored only in the 0600 runtime environment;
- mailbox configure/status/remove use existing atomic private-config locking;
- status output never returns repository, refs or token;
- token entry uses a hidden prompt and there is no token CLI argument;
- setup overwrite preserves DB and mailbox secrets, including during bearer-token rotation;
- private replay/cursor files are derived inside the private config directory;
- explicit watcher bootstrap skips historical requests;
- one-cycle watcher output is limited to safe state/counts;
- continuous watcher polling and heartbeat cadence are separately bounded;
- heartbeat is slower than request polling by default and is refreshed on state transitions;
- heartbeat failure remains independent from completed action execution.

Phase 3.8.9 bounded operational bridge:
- the mailbox action enum now reaches existing configured service, backup, migration, deployment and rollback capabilities through explicit methods only;
- test-log retrieval is bounded to 100 lines per request and remains subject to test-runner redaction plus bridge-result scrubbing;
- service mutations accept only configured service aliases and preserve per-alias opt-in plus emergency-stop enforcement;
- backup creation uses only configured database state; no DSN/path/command input is accepted from the mailbox;
- migration/deploy/rollback plans can be requested and inspected remotely, but approval granting remains local/human-controlled;
- apply/deploy/rollback execution requires a valid pre-approved opaque approval ID and cannot bypass action/project/binding/expiry checks;
- deployment/rollback status accepts only validated opaque job IDs;
- restore/PITR, production mutations, arbitrary shell/argv/path/env/unit/tool input remain unavailable.

Phase 4 staging service management:
- private service aliases map to systemd-user units;
- service aliases default to read-only;
- start, stop and restart permissions are independently opt-in;
- MCP list/status output never exposes private unit names or health URLs;
- optional HTTP health checks return only safe health state;
- operator emergency stop blocks mutating service actions while status stays available;
- systemctl invocation uses fixed argument arrays with `shell=False`;
- raw systemctl failure output is not returned to MCP;
- no sudo or generic system-service control;
- CLI service-config add/list/remove avoids manual YAML editing;
- MCP list/status/restart/emergency-stop flow is integration tested.

Phase 5 PostgreSQL backup and migrations:
- private DB connection strings use dedicated `RUNNER_MCP_DB_*` variables;
- CLI database connection input is hidden and never echoed;
- setup overwrite preserves existing DB secrets;
- backup root/project directories and dump/metadata files have restrictive permissions;
- pg_dump receives the DSN via child environment and not command-line arguments;
- MCP exposes backup metadata only, never dump contents or private paths;
- migration status/apply use predefined argv arrays and `shell=False`;
- migration output is bounded and scrubbed for DSN/private paths/secrets;
- apply always creates a pre-migration backup and rechecks operator stop afterwards;
- migration failure keeps the backup and never performs automatic restore;
- database restore, PITR/WAL orchestration and retention pruning remain intentionally unimplemented.

Phase 6 staging deployment:
- staging-only deployment config with private release storage;
- clean Git HEAD is the only deployment source;
- client cannot supply arbitrary Git ref or build shell;
- Git hooks/fsmonitor disabled during preflight/archive operations;
- required tests run before release creation and source cleanliness is rechecked;
- repository symlinks are rejected from release archives;
- optional database migrations use the Phase 5 pre-migration backup flow;
- current-release activation uses an atomic symlink replacement;
- service restart requires a configured health check;
- activation failure auto-rolls code back one release only when no DB migration ran;
- post-migration activation failure requires manual recovery and never auto-restores DB;
- deployment jobs are asynchronous, private, persisted, and marked interrupted after restart;
- MCP plan/start/status lifecycle is integration tested;
- deployment config is manageable by CLI without exposing release paths.

Phase 7 controlled rollback:
- release history exposes safe metadata, retention protection and rollback eligibility;
- retention protection uses both minimum count and minimum age;
- release metadata identity/commit/timestamp/environment/permissions are fail-closed validated;
- rollback target is always the direct previous release from trusted metadata;
- unknown MCP tool arguments are globally rejected;
- current releases that applied DB migrations block code rollback;
- rollback runs as a persisted async job sharing the per-project deploy/rollback exclusion;
- successful rollback restarts and health-checks the configured service;
- failed rollback health reactivates the original current release when the stop is not active;
- no database restore, arbitrary target, production rollback or automatic cascade.

Phase 8 adapter foundation:
- built-in allow-listed adapter registry with no dynamic imports from config;
- generic adapter never guesses commands or automatic presets;
- Python adapter inspects safe local markers/tooling without returning paths;
- project adapter IDs are validated fail-closed;
- CLI and MCP can list adapters and inspect safe project capabilities;
- `auto` resolves only to existing allow-listed test/migration presets;
- named private/company project adapters remain outside the public repository.


Phase 9 human approval gates:
- migration, deployment and rollback require short-lived human approvals;
- MCP can request/inspect plans but cannot approve them;
- approval is local CLI only with explicit confirmation phrase;
- approvals are action/project/plan-bound, short-lived and single-use;
- migration approval binds a clean Git HEAD;
- deployment and rollback jobs are pinned to their approved commit/release targets;
- production project mutations are blocked; staging remains the only mutable environment;
- AIfordable-owned Agent Bus is the required primary runtime control path;
- GitHub mailbox is bootstrap/fallback only and must be independently disable-able;
- Desktop Commander remains break-glass only;
- optional third-party client tunnels do not become control authority.

## Validation

Current validation is green:
- Python 3.12 compile: green;
- Ruff: green;
- pytest: green in current CI; exact test counts are recorded with dated validation/release evidence rather than treated as durable status here;
- merged request-capacity change passed public CI including whitespace checks;
- live private bridge validation passed both Runner MCP lint and unit profiles;
- git diff whitespace check: green;
- HTTP auth/rate-limit tests: green;
- authenticated MCP handshake/tool-discovery test: green;
- unexpected Host rejection test: green;
- traversal/symlink/secret/binary/size/pagination file tests: green;
- MCP file-read allow/deny integration test: green;
- operator-stop/retention/rollback guard tests: green;
- startup fail-closed retention-confirmation tests: green;
- MCP safety-status integration test: green;
- controlled test-runner timeout/cancel/stop/concurrency/log-redaction tests: green;
- MCP test-job lifecycle integration test: green;
- test-profile schema and startup fail-closed tests: green;
- dependency check: green;
- non-root installer integration test: green;
- installed console command version/help smoke test: green;
- project-aware guide smoke test: green;
- GitHub mailbox bridge protocol validation tests on merged Phase 3.7: green;
- live private mailbox probe for the configured runner-mcp test-profile listing: green;
- isolated Phase 3.8 result-envelope/replay logic checks: green;
- full Phase 3.8 branch CI on the free standard runner for this public repository: green;
- operator-wrapper installer tests: green;
- onboarding/project/test-profile CLI tests: green;
- service manager permission/emergency-stop/subprocess tests: green;
- MCP service alias/status/restart integration test: green;
- service-config CLI/config-manager tests: green;
- PostgreSQL backup/metadata/permissions/secret-isolation tests: green;
- migration timeout/failure/pre-backup/redaction tests: green;
- MCP database backup/migration/emergency-stop lifecycle test: green;
- database-config and hidden-prompt CLI tests: green;
- staging release/git cleanliness/symlink/test/migration/health rollback tests: green;
- deployment job persistence/interruption/error-sanitization tests: green;
- deployment-config storage/validation/CLI tests: green;
- MCP asynchronous deployment plan/start/status/emergency-stop test: green;
- release listing/metadata-tamper/migration-boundary rollback tests: green;
- rollback job persistence/blocking tests: green;
- MCP one-step rollback/list/plan/status and arbitrary-target rejection test: green;
- adapter registry/inspection/symlink-safety tests: green;
- adapter auto-preset/config validation tests: green;
- CLI and MCP adapter capability tests: green;
- approval expiry/replay/action/project/fingerprint/permission tests: green;
- clean-Git high-risk source binding tests: green;
- production mutation gate tests: green;
- local approval CLI explicit-confirmation test: green;
- MCP approval request/consume migration/deploy/rollback flows: green;
- git diff whitespace check: green;
- private-address/path scan: clean.

## Deliberately not implemented yet

- arbitrary shell;
- production actions;
- database restore;
- PostgreSQL WAL/PITR orchestration;
- automated backup-retention pruning;
- production deployment;
- production rollback;
- arbitrary/multi-step automatic rollback target selection;
- automatic database restore;
- automatic release pruning.

## Next steps

The shared watcher migration, restart/reconciliation proof, exactly-once completion-notification proof, clean-Linux five-minute demo validation and non-root systemd user autostart packaging are complete. Keep obsolete pilot execution paths disabled, continue guided private-connectivity/TLS onboarding, and prepare the first tagged alpha only from an exact green commit.

Before activating real project test/service/database/deployment profiles, create the private runtime configuration and verify Linux-account, service-health and PostgreSQL recovery boundaries on the actual host.

Do not add real environment values to this repository.


## Safe project sync and adapter test presets — 2026-09-21
- Added a narrow `sync_project(project, commit)` mailbox capability for staging validation. The request accepts only an allow-listed project code and a full 40-character commit ID.
- Source sync requires a clean worktree, blocks submodules, validates that `origin` is exactly the configured GitHub repository, fetches with Git hooks disabled and terminal prompting off, verifies the commit is reachable from `origin/*`, and checks out the exact commit detached.
- Source sync refuses to run while that project's tests are queued or active. No branch, remote, filesystem path, executable, command, service or environment variable can be supplied by the mailbox.
- Python projects now expose fixed safe adapter presets `pytest` and `ruff` when the required executable is detected in `.venv/bin` or `venv/bin`. Configured profiles still take precedence.
- Adapter presets use fixed argv/cwd/env/timeout definitions. `custom` is deliberately excluded from implicit mailbox availability.
- Added protocol, executor, source-control and test-runner regression coverage for commit pinning, extra-field rejection, busy-project rejection, safe preset discovery/execution and custom-preset denial.
- This change does not enable migration, deployment, rollback, arbitrary shell or arbitrary Git ref execution through the mailbox.

Runtime observability bridge — 2026-09-21:
- added fixed read-only `runtime_status` and `runtime_doctor` MCP/bridge actions;
- output is intentionally host-neutral: version, safe capacity/configuration booleans and bounded check summaries only;
- private paths, endpoints, hostnames, environment values, service units and raw process output remain excluded;
- this is the first self-operations step toward removing routine dependence on general-purpose remote desktop tooling.

Shared Playwright runtime — 2026-09-21:
- Runner MCP E2E jobs previously replaced HOME and therefore could not see a shared Playwright/Chromium cache unless it was passed through manually;
- test profiles can now declare `runtime: playwright`;
- the browser cache comes only from private `RUNNER_MCP_PLAYWRIGHT_BROWSERS_PATH`, is locally validated and is scrubbed from logs;
- missing or unsafe browser runtime fails closed; PastEntrance does not need a project-code workaround for this boundary.

Runner MCP self-update — 2026-09-21:
- added fixed `self_update(commit)` and `self_update_status(job_id)` operations for the configured canonical Runner MCP project;
- commits are lowercase full object IDs and must be reachable from `origin/main`; direct MCP calls and mailbox calls enforce the same lowercase boundary;
- lint and unit profiles gate installation, and the source commit is rechecked immediately before the fixed local install;
- server, GitHub watcher and completion watcher use component-specific restart/reexec paths; callers cannot choose executables, commands, services or paths;
- private job/state/restart metadata is permission-restricted and restart recovery marks unfinished update jobs interrupted rather than replaying them;
- the current read-only `runtime_status` and `runtime_doctor` behavior is preserved, with self-update readiness/state added to runtime status;
- the local MCP bridge allow-list now explicitly includes both observability actions as well as the two self-update actions, closing the gap where protocol support existed but local dispatch could still reject runtime observability;
- arbitrary package-manager arguments, repositories, refs, paths, environment values, process controls and general remote-shell behavior remain excluded.


Self-update hardening follow-up — 2026-09-22:
- review of PR #37 found and fixed three integration gaps before merge: local MCP dispatch had not allow-listed runtime observability, the direct self-update capability normalized uppercase commits instead of rejecting them, and `self_update_status` was present in the enum/mapping but missing from strict request validation;
- the self-update source is now guarded across post-sync verification, lint, unit and install, closing the window where another source sync could change the checkout between validation steps;
- the project source guard was made re-entrant so the self-update orchestration can hold it while existing test-start/install paths safely re-enter it;
- PR #37 merged as `8570f842ffad5282bb28a89a77bcbcba5dd01bcd` after clean five-minute demo, built-artifact validation, Ruff and 704 pytest tests all passed.

Self-update activation recovery — 2026-09-22:
- follow-up work makes restart intent durable across fixed-component re-exec failure rather than consuming the marker before an unsuccessful activation;
- restart markers now cover server, GitHub watcher and completion watcher, are create-once and are batch-prepared so partial marker creation is rolled back;
- a new self-update is refused while any fixed activation marker remains pending;
- runtime status exposes only a boolean pending state and bounded fixed-component count, not paths/process identifiers;
- server self-reexec retries are bounded; watcher/notifier re-exec failure restores the marker so managed systemd/cron supervision can retry after process restart;
- failures after package installation are distinguished as activation failures with restart required, while pre-install failures remain ordinary self-update failures;
- package-install rollback remains a separate future hardening item; this slice improves activation recovery without claiming atomic package rollback.

Activation recovery merged — 2026-09-22:
- PR #40 merged as `1d160afdb9c0b6e0d3ebb3a74b88644b84eb348e`;
- validation was fully green: Ruff, 708 pytest tests, clean five-minute demo and built-release artifact;
- fixed-component restart intent now survives a failed re-exec, pending activation blocks overlapping self-updates, and runtime status reports only a bounded pending state/count;
- issue #7 (mailbox liveness/stale-request recovery) was closed as completed because its heartbeat, retry and fail-closed recovery scope is already implemented and live-proven;
- next self-update hardening target is package-install rollback/staging; current activation recovery does not claim atomic recovery from a failed in-place pip installation.


## 2026-09-22 — external review triage and low-risk cleanup

Claude's read-only review branch `claude/roadmap-review-suggestions-xxbhfo` was evaluated against the newer main baseline rather than merged wholesale. The review branch was based on `319259c7...`, before the commit-pinned self-update and recoverable activation work, so its exact test counts and some roadmap observations were already stale.

Accepted low-risk findings in this slice:
- gate the demo-smoke and release-artifact CI jobs on the main validate job so obviously invalid commits do not spend extra runner time;
- expose the validation workflow status from README and clarify that the operator wrapper is unnecessary for same-account installs;
- define status authority explicitly: roadmap for architectural phase status, handover for chronology, CI/release records for exact validation results;
- reconcile stale roadmap "Next" items that still described watcher migration, coordinator integration, completion proof and self-operation work that is already implemented;
- add direct unit coverage for the append-only audit logger and its 0600 file-permission contract.

Deferred rather than applied blindly:
- a shared `secure_io` rewrite: worthwhile, but the existing atomic/private-write call sites have different lifecycle and failure semantics, so this needs an inventory plus dedicated regression tests rather than a mechanical replacement;
- a generic audited-tool decorator: potentially useful, but audit payloads and failure categories differ by tool family and should not be homogenized without a separate design/test slice;
- watcher `logging`: operationally useful, but must first define a scrubbed, category-only logging contract so diagnostics cannot become a new private-data leak;
- large `server.py`/`cli.py` splits and adapter plug-in discovery: maintenance work, not current safety or self-update blockers;
- a full roadmap status table: not added because it would duplicate per-phase status and create another drift surface. The source-of-truth rule and stale-status cleanup address the underlying problem with less duplication.

The next functional priority remains the staged/rollback-capable self-update package-install strategy, plus live bootstrap/proof on the private host when that host can be upgraded through an available safe path.


Review cleanup merged — 2026-09-22:
- PR #41 merged as `0e66368ca1377359019de1d594833377892db7aa`;
- validation: Ruff and whitespace checks green, pytest 711 passed with one known third-party warning, clean demo green, built release artifact green;
- Claude's review branch remains unmerged by design; only independently revalidated low-risk findings were adopted;
- next functional target remains staged/rollback-capable self-update installation plus live private-host bootstrap/proof.


Self-update package-install recovery hardening — 2026-09-22:
- PR #43 stages the validated target as a private wheel instead of installing directly from the checkout;
- when a known installed baseline exists, a private recovery wheel is built before source sync while the project source guard remains held across baseline staging, target sync, lint/unit validation, target staging and package mutation;
- a strict private 0600 install-transaction marker is persisted before the in-place pip operation; pending recovery is exposed only as a bounded boolean and blocks overlapping self-updates;
- target installation must also pass a fresh-process Runner MCP import verification;
- a caught target install/import failure rolls back only when both baseline-package reinstall/import verification and exact baseline source restoration succeed; otherwise the transaction remains fail-closed as `install_recovery_required`;
- same-commit self-update requests still verify reachability through `origin/main` and then avoid unnecessary reinstall/restart;
- clean CI exposed that offline `--no-build-isolation` wheel staging requires the setuptools build backend to remain available at runtime, so `setuptools>=75` is now an explicit runtime dependency; this dependency-set change reinforces that the first private-host bootstrap must use the normal dependency-resolving installation path;
- the current design deliberately does not claim atomic in-place pip mutation. A process interruption can leave an install transaction pending; the next hardening slice is a bounded local recovery command before live package-install fault injection.


Package-install recovery merged — 2026-09-22:
- PR #43 merged as `2b7dac9fb3c9e5168c07c7967333995b646957de`;
- final validation was fully green: Ruff, whitespace, 742 pytest tests with one known third-party warning, clean five-minute demo and built release artifact;
- the source guard now remains held through installed-state persistence, restart-marker preparation and install-transaction finalization, closing a final post-install source-race window;
- the next hardening target is a bounded local operator recovery command for persisted install transactions; live package-interruption fault injection remains deferred until that local recovery path exists.


## 2026-09-22 — bounded local self-update install recovery

A local operator-only recovery path is being added for persisted rollback-capable self-update install transactions:
- `runner-mcp self-update-recovery` is local CLI only; it is not mapped into MCP or the GitHub mailbox;
- recovery requires the operator emergency stop to be active and exact confirmation `RECOVER SELF UPDATE`;
- only the private staged baseline wheel from the persisted transaction can be used;
- the installed package is reinstalled and import-verified, source is restored to the exact baseline commit reachable from `origin/main`, and installed-state metadata is reset to that same commit;
- the transaction is cleared only after all of those checks succeed; otherwise recovery remains pending and further self-update stays blocked;
- bootstrap/first-install transactions without a known baseline are deliberately not auto-recoverable;
- pending activation markers and install recovery are not allowed to overlap.


Local install recovery merged — 2026-09-22:
- PR #44 merged as `3ce122012d56ead3fbf75dfbf8fe770572f3ed47`;
- validation was fully green: Ruff, whitespace, 753 pytest tests with one known third-party warning, clean five-minute demo and built release artifact;
- persisted rollback-capable self-update transactions can now be recovered only through local `runner-mcp self-update-recovery`, with the operator emergency stop active and exact confirmation;
- the recovery path restores the private staged baseline package, fresh-process import validity, exact baseline source commit and installed-state metadata before clearing the transaction;
- bootstrap/no-baseline transactions and overlapping activation recovery remain fail-closed;
- no install-recovery action was added to MCP or the GitHub mailbox;
- next: bootstrap this merged baseline on the private host and prove same-commit, forward-update and deliberately interrupted/recovered package-install paths through the safe operating model.

## Coordination checkpoint — 2026-09-22

Canonical coordination now uses `SESSION_HANDOFF.md`, `AGENT_EXCHANGE.md` and `RESUME_PROMPT.md`. GitHub live state wins over stale handoff text.

Immediate priority:
1. reconcile the four private watcher recovery-attention items without replay/reset shortcuts;
2. confirm the pending read-only runtime-status probe;
3. reconcile and, if still green/current, merge PR #45;
4. bootstrap/prove the newest recovery-capable self-update baseline on the private host.

Current blocker: watcher heartbeat is degraded by four recovery-attention items, so cursor advancement is intentionally withheld. Desktop Commander is unavailable; use GitHub plus the bounded Runner-MCP bridge.


## Agent Bus architecture correction — 2026-09-29

A GitHub primary-rate-limit incident proved that the mailbox cannot remain operationally primary.
The required target is now explicit: AIfordable-owned durable relay + outbound-only Runner Fabric
Agent Bus. GitHub remains source/CI during migration and later optional mirror/bootstrap/fallback.
Runner MCP #125/#130 and Runner Fabric #356 track the implementation and live cutover.
