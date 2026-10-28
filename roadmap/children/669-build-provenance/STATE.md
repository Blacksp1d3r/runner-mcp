## 2026-10-28 — #669 geselecteerde werkelijk geladen code-objecten zichtbaar op bestaande MCP runtime_status (SOURCE 0.1.128 MERGED, ORIGINEEL LIVE WAIT)

- [PR #913](https://github.com/Blacksp1d3r/runner-mcp/pull/913) **MERGED** `a8b1aec7edcd310ad65654bc871edc986ecf0e18`, exact final head `be4d07a3b5e4c4e72979623f94a8e3a842c0ddaa`, source **0.1.127**. Exact-head validation [40744887726](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/40744887726), clean Ubuntu [40744889789](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/40744889789), attribution [40744887706](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/40744887706) all **SUCCESS**. Existing zero-argument `serving_process_observation_preflight` now measures bounded SHA-256 of *currently in-memory* function/method CodeType objects selected from `runner_mcp.server` and `runner_mcp.build_identity`. Recursive filename normalization; no source file reads, host paths, secrets, signer or OS mutation. Tests PASS: on-disk changed without reload → same in-memory digest; genuine loaded function code changed at same package version → different digest; real imported package in disposable test process → nonempty digest. **Only two selected modules, not all 131 .py, not wheel provenance.**
- [PR #914](https://github.com/Blacksp1d3r/runner-mcp/pull/914) **MERGED** `1c4c80e2b3e15329605ef4afed3b42e37f4c96c6`, exact final head `54799d69e7d4128c76bd45725a38925aa4579d3b`, source **0.1.128**. Exact-head validation [40745892238](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/40745892238), clean Ubuntu [40745892301](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/40745892301), attribution [40745892960](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/40745892960) all **SUCCESS**. Existing *authenticated* `runtime_status` (already in connected connector inventory) now returns same selected in-process code digest / code+module counts via pre-existing observer; existing real MCP HTTP wire test verifies measurement and **still** `active_build_provenance_verified=false`, source/artifact NULL, `self_update_ready=false`. No second tool/observer/relay/manager.
- **Next physical accepted proof is NOT done:** original AIfordable AF-HOST-0001 / AF-SVC-0001 `github-runner`, owner `gha-runner`, :8000 latest witnessed **0.1.88**, PID3217524/startticks107811168, release slot `2973f907...`. Earlier independent **131/131 .py on-disk** wheel/source match PASS reused, not repeated. Source 0.1.127/128 **NOT INSTALLED on original**. Live imported *complete* code generation, historical trusted on-host wheel file SHA, independent qualified signer/nonce original six-role process witness, Fabric #942 off-target target-loss A6 journal, #943 actual no-NIC boot-persistent autonomous rollback, and NEW same-campaign original-client terminal result+durable ACK remain **NOT TESTED / WAIT**. The new hash is unsigned/partial and not authorizing. `#341` physical update and `#662` automatic live promotion stay BLOCKED; no production changes or topology serving-version rewrite.
- **Coordination:** Runner-MCP A owns #669/#341/#662; Fabric independently owns #942/#943; B/#381/#747 and C/#844 untouched. #669, Fabric #942/#943, AIfordable #585 updated. Original connector's missing direct `serving_process_observation_preflight` action was handled by reusing existing `runtime_status` **in source**, without assuming old 0.1.88 connection currently serves 0.1.128. Fail closed at original host.

## 2026-10-27 — #669 unmanaged six-role cron conflict denial (v0.1.93 SOURCE / CI gate)

- Existing `_has_unmanaged_runner_mcp_entries` detected many direct `serve` and watcher commands but **missed an unmanaged `autostart cron-run server`**, allowing a stale second server cron outside the single managed block to survive a new install. This release adds exact `cron-run <canonical-role>` token recognition using the original `CRON_COMPONENTS` registry (all existing roles, no second inventory), rejecting such outside managed entries before a crontab write. The existing read-only `cron_status` now refuses to report a healthy uniquely managed role in the presence of an unmanaged Runner-MCP supervisor outside its block; commented history is ignored. No shell, new manager, new watcher or host operations.
- Regression cases cover all canonical role names with an old unmanaged command, duplicate server rows before/after the managed block, unchanged cron content/no lock creation on refusal, and legitimate commented history. **SOURCE ONLY:** last independent physical original `github-runner` `gha-runner` :8000 proof remains v0.1.88; GitHub source v0.1.93 is not installed or serving. Five other real cron role generations/source/wheels, an independent six-role witness, Black A7 real rollback and A6 original-client ACK remain WAIT. Prior A7 archival evidence is not repeated.

## 2026-10-27 — #669 private cron lock writer inode safety (v0.1.92 SOURCE, PR #840)

- The existing cron read-only status path was hardened in 0.1.89/0.1.90, but the separate original `run_cron_component` **writer** still used O_CREAT then `fchmod` before checking its opened inode. Candidate 0.1.92 requires O_NOFOLLOW/O_NONBLOCK, and validates regular file, actual UID owner, exactly one hardlink and private permissions by `fstat` BEFORE changing rights or invoking an existing component. Symlink, hardlink, FIFO, directory and unsafe mode fail closed without unrelated file mutation. Existing correctly private locks and absent lock creation remain functional; no second supervisor or registry.
- PR #839 consumed and merged v0.1.91. This branch was safely reset with a guarded lease to that merged `main`, preserving PR #839's original fix/handovers and moving this independent source fix to next release v0.1.92. Exact final-head release CI is mandatory before merge. **SOURCE ONLY**, not installed: physical original `github-runner` :8000 last attested v0.1.88, other five cron role imported wheels/generation, A6/A7 full recovery and fresh authentic client ACK all still WAIT. No host, cron, updater, relay or backup changes.

## 2026-10-27 — #669 cron source-role observation bound to exact local release/config (0.1.90 SOURCE)

- The **existing** `cron_status` from merged v0.1.89 accepted structurally valid managed cron commands with a foreign `--config-dir` or prior release executable as `installed`. Candidate v0.1.90 now matches the exact resolved configured root and accepts an optional expected immutable CLI entrypoint; the normal CLI's status and tunnel readiness call sites supply their own current `runner-mcp` entrypoint. Older paths, mixed release entries and foreign configs are NOT silently current. No cron, lock or host mutation; regression checks expected command, stale release and foreign private config.
- **Scope remains configuration only:** even an exact managed launcher is NOT proof that its process ran, loaded a particular wheel, emitted a scheduled completion receipt or belongs to the authenticated target host. Original `github-runner` :8000 physical v0.1.88 proof still latest; GitHub v0.1.90 is SOURCE ONLY until original-host admission. Other five live roles, signed build/provenance, A6/A7 independent rollback and original-client ACK remain WAIT. No backups/restarts/services/tunnels/credentials created.

## 2026-10-27 — #669 cron status no longer writes lock files (source v0.1.89, CI gate)

- New Runner-MCP v0.1.89 source candidate corrects the EXISTING `cron_autostart.component_active/cron_status` read-only path. It previously called `_open_component_lock`, which uses O_CREAT and chmod(0600), meaning a mere status inquiry could mutate existing private lock storage. The observer now only opens an already-existing same-owner private regular lock O_RDONLY | O_NONBLOCK | O_NOFOLLOW; missing file reports lock currently unheld without creating it; symlink/FIFO/hardlink/unsafe mode fails closed. Actual `run_cron_component` still exclusively owns creation/locking and launcher behavior. New tests prove no write/permission change and no fabricated scheduled-job liveness.
- **Correct scope:** missing/available lock is a CURRENT lock observation, NOT durable execution receipt or installed wheel/source/generation evidence. The physical original :8000 v0.1.88 witness is unchanged; code v0.1.89 on GitHub is NOT installed on `github-runner`. Five other cron role generations, authenticated six-role witness, A6/A7 autonomous original recovery and same-issuer client ACK remain WAIT. No new service/tunnel/updater/backups or host work.

## 2026-10-27 — ORIGINAL :8000 v0.1.88 confirmed; multi-role provenance still WAIT

- **Last distinct original-host physical witness (2026-10-26):** `github-runner` / `gha-runner`, loopback port 8000 PID `3217524`, pinned manual install v0.1.88 and six managed cron entries changed. Four previous-generation processes stopped; retained v0.1.38 rollback. Main server's live v0.1.88 process proof is accepted and **not** to be reinstalled or reconfirmed using obsolete PID `520762` as if still live. [#669 physical receipt](https://github.com/Blacksp1d3r/runner-mcp/issues/669#issuecomment-6427575625).
- **2026-10-27 first-party connected read-only observation:** `runtime_status.version=0.1.88`, `installed_distribution_version=0.1.88`; `reply_source_host_verified=false`, `active_build_provenance_verified=false`, `active_artifact_revision=null`, `active_artifact_digest=null`, `loaded_module_wheel_identity_verified=false`, `six_role_process_roster_verified=false`, `self_update_ready=false`, no active update, restart or installation recovery. Because reply host is not authenticated, this observation is NOT new original-host process/pid/source proof. `build_identity` and `runtime_doctor` currently return separate internal-tool errors; classify those **UNKNOWN**, not server-down.
- **Missing qualification:** five separate remaining cron roles' actual execution/loaded generation (schedule/receipt where short-lived), source+wheel linkage of each serving generation, and authenticated signed multi-role witness. A6 off-target append-only journal (#942) and autonomous independent fixed six-role rollback in existing persistent Black isolated guest (#943/#1650) remain separate WAIT. Already accepted normalized original runtime copy and six-role archive/isolated content restore (AF-SB-0002) **must not be repeated**. Historical entries below are dated snapshots, NOT current runtime truth. No host, release, cron, server or credential changed by this documentation update.

## 2026-10-21 — v0.1.77 local epoch response integrity MERGED, LIVE WAIT

- After #794 v0.1.75 and #796 v0.1.76 MERGED, the existing `runtime_status` aggregator still allowed a status manager to overwrite `serving_instance_epoch` and `serving_instance_epoch_authenticated`. This can produce misleading process correlation even if the loaded distribution version is correct.
- v0.1.77 merged source uses only the actual current `build_mcp` closure epoch as trusted local input to the existing `fail_closed_runtime_provenance` response finalizer; manager values, including optimistic `authenticated=true`, cannot override it. Tests include mismatched/stale status managers and malformed epochs; no invented host identity, wheel attestation, or role authority.
- Parent #669 live current wheel SHA / source / six-role original-client provenance remain WAIT. Central v0.1.38 is not upgraded; A6 0/11, Fabric A7/A6 and ACK prerequisites remain separate.

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

# #669 — serving-generation provenance (historical 2026-10-20 status, superseded)

status: SOURCE_OFFLINE_GUARDS_MERGED / CORRECT_HOST_WITNESS_WAIT
owner: Runner-MCP source lane (#669); Fabric authority/activation separately #924
source_main_version: 0.1.77
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
