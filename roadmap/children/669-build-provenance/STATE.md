## 2026-10-21 — serving instance epoch candidate v0.1.76 (#669 substep)

- Exact prior source 0.1.74 already merged: `runner-mcp agent-bus preflight`. Central 0.1.38 and lab 0.1.38 still serving separately; lab terminal CLI 0.1.3 is not the current lab service. Runner-Fabric #1694/#1695 merged pure source read-only fleet origin and sequential update policy. Do not repeat.
- This bounded source increment adds a per-`build_mcp` process epoch (32 opaque hex characters, fork-specific, no PID, paths or credentials) returned consistently by existing `runtime_status` and `serving_process_observation_preflight`; no new MCP tool and no private topology labels. Every response explicitly states `serving_instance_epoch_authenticated=false`. It helps detect restart / stale process / client route switching but does **NOT** prove source, wheel, host/route or ACK. Actual active artifact receipt remains #669 WAIT; never infer one from token or historical `self-update-state.json`.
- No distribution or instance installed; release qualification uses exact-head automated CI and merges without mandatory human reviews. Next #669: retain original wheel manifest/receipt at authorized initial install and compare against memory-loaded modules/actual serving process independently, then integrate with Fabric #924 authenticated route verifier and sequential A6/A7 supervised rollout.

## 2026-10-20 original-client 20:30 verification — still UNVERIFIED

- GitHub #509 CLOSED source-only 2026-10-20 17:20:58 UTC. Latest source v0.1.62 includes the already-written conditional fixed A6 11-key repair, but current connected v0.1.38 cannot prove it is loaded; A6 config remains 0/11.
- `build_identity`: version 0.1.38, revision NULL, wheel SHA NULL. `runtime_status` v0.1.38 installed v0.1.38, provenance FALSE, self_update_ready FALSE. Historical old self-update marker not trusted for current process. `runtime_doctor` two provenance FAIL; absent A6 looks PASS only in old Doctor and is NOT A6 readiness.
- Fabric read-only peer READY but A6 prepare/probe unavailable and mutation false; Agent Bus UNKNOWN, independent archive mirror not configured. `projects:6` is not six roles. Local Fabric `host:local` evidence does not certify correct six serving roles. External target inspections unavailable/UNKNOWN.
- No first-party read-only tool on the currently serving 0.1.38 surface returns a wheel SHA or an independent multi-role loaded-code witness. A wheel built elsewhere and an installed RECORD cannot establish the exact retained installed original wheel bytes. Require owner-controlled correct-host process/signer/pre-existing wheel escrow and nonce issued BEFORE any first installation. If unavailable classify WAIT, not inferred.
- Evidence and strict #509 conditional activation chain recorded in [handover/ISSUES_669_509_OPERATOR_GATES_20261020.md](../../handover/ISSUES_669_509_OPERATOR_GATES_20261020.md).
- No host, process, A6 private file, Fabric agent, relay, six serving roles, or update modified.

# #669 — serving-generation provenance

status: SOURCE_OFFLINE_GUARDS_MERGED / CORRECT_HOST_WITNESS_WAIT
owner: Runner-MCP source lane (#669); Fabric authority/activation separately #924
source_main_version: 0.1.62
latest_669_source_merge: 701f507ac00754c6e869448ed3158dcfb4eac539
live_connected_serving_version: 0.1.38
active_loaded_wheel_verified: false
active_source_revision_verified: false
self_update_ready: false
production_changes_performed: false

## Accepted source-only progress (2026-10-20)

- PR #781 v0.1.63 MERGED `8d0405490c73bc324a522e66e5e596649d169371`, exact tested head `a9b9df31aa8e79e29cf85183e75e6ba25dca1215`, validation #39479195410, Ubuntu #39479195458, attribution #39479195285 ALL SUCCESS. Strict six independently pinned synthetic role-to-process-instance hashes compared through existing signed witness preflight; always OFFLINE match, no active wheel attestation. RMCP-F-0067/0068; live 0.1.38 unchanged; source-closed #509 not runnable as trusted current installed code.

- #509 v0.1.58 PR #776 merged `22b3efc6a35375c9033f5aa71a8f9930fcf64843` with 11-key private env hardlink guard and exact-head full CI green; this is not a #669 independent live witness, or a host update.
- #739 v0.1.56 #746 and v0.1.57 #748 source merged with 33/33 offline Q7 asset consistency, not a signed trusted host import.

- v0.1.54 PR #770 fixed existing Fabric bridge A6 local read-only preflight; SOURCE MERGED, central 0.1.38 cannot yet call.
- v0.1.55 PR #773 current connected process only three-module roster/version observer, locked 100 tools; SOURCE MERGED exact-head full CI all green, active source/wheel still unverified.
- **Bootstrap-loop #669/#924:** trusted correct-host witness on original 0.1.38 and protected previous generation must be independently qualified before safe update; do not rely on newly merged but not installed observers, and do not bypass A6/A7/ACK.


- v0.1.52 #769 manager readiness denied when active generation unverified, 12-mode negative tests, CI all green.
- v0.1.53 #771 standalone receipt refuses linked parent, relative and `..` aliases across all three evidence inputs, nine negative tests, CI all green.
- Fabric source #1625/#1626/#1627/#1628 merged; source-only A6 root/journal/A7 baseline hardening does not meet physically separate storage or autonomous rollback qualification.

- Source 0.1.47 #760 false-green A6 Doctor classification; #761 six-SYNTHETIC-role witness denial tests.
- Source 0.1.48/0.1.49 #763/#764 private A6 parent-path and semantic fixed-key checks.
- Source 0.1.50 #766 installed-RECORD foreign/duplicate path denial (exact-head CI validation 39390108398, Ubuntu 39390108426, attribution 39390108361 PASS).
- Source 0.1.51 #767 offline evidence path canonicality (exact-head CI validation 39390980634, Ubuntu 39390980640, attribution 39390980656 PASS).
- Independent GitHub wheel/RECORD checks to 0.1.49 are OFF-HOST artifact consistency only. No trusted correct-host imported-code observation can yet be concluded.
- All source preflights intentionally keep `active_build_provenance_verified=false`, source revision and artifact digest NULL, even when their own offline signatures/bytes match.

## Not done: physical trust and activation

Original-client central v0.1.38 still reports source/digest unavailable, self_update_ready false, two Doctor failures. Historical `self-update-state.json` is rollback/transaction history, not current wheel identity. A6 private state 0/11, Fabric independent off-target journal #1617/#942 and A7 offline rollback #943 still unqualified. Original requester terminal result/ACK Fabric #1556/#1563 and AIfordable relay #585 not proved. Correct-host observer must bind actual loaded six process generations and launcher targets to owner-trusted pinned wheel/RECORD/source, a fresh bounded challenge and immutable rollback copy, then return public-safe categorical receipt without leaked host paths or secret material. Only Fabric #924 can later authorize one-node guarded activation after all gates; never bypass with generic shell or blind restart.

## Historical context

The earlier 2026-10-13 child branch proposing source 0.1.7 (review-waiting) is superseded by merges into main. Do not restart or reapply historical PRs or claim that the old branch describes current shipping source.
