## 2026-10-24 — #587 physical archive namespace accepted; LIVE Runner-MCP #586 configuration still UNCONFIGURED

- Real original physical `github-runner` Fabric #1397 accepted **one** fixed `release-archives` child on the registered independent ext4 AF-VOL-0001: owner-run fixed protected bootstrap returned `FIXED_ARCHIVE_ACCEPTANCE=created-verified`, independent owner/mode/mount readback `gha-runner:gha-runner 0700` + correct UUID and `ORIGINAL_HOST_ARCHIVE_VERIFIED=PASS` / `NO_SERVICE_RESTART=TRUE`. AIfordable canonical single machine-registry AF-SB-0001 `qualified:true` merged via #671 after CI PASS, while the **whole** data volume's other backup/restore/F34 roles remain `qualification-pending`. Fabric #1397 CLOSED (namespace only), not 2/2 release archive copies.
- **NEW LIVE READ-ONLY MCP evidence after physical bootstrap:** existing connected original Runner-MCP 0.1.38 still returns `fabric_release_archive_mirror_readiness` `configurationState=unconfigured`, `reasonCode=storage-bindings-unconfigured`, `ready=false`, source/mount/mirror readiness flags all false, `mutationEnabled=false`. `runtime_status` reports provenance `active_build_provenance_verified=false`, `self_update_ready=false`; existing Fabric bridge preflight reports serving original Fabric revision `2ff81b...` and no A6 binding yet. This is a **missing original serving process owner-private binding**, not evidence that the new namespace is missing/wrong.
- Reuse already-merged #586 `fabric_release_archive_mirror_readiness.py` and its three **PRIVATE** env roles (`RUNNER_MCP_FABRIC_RELEASE_CUSTODY_ROOT`, `RUNNER_MCP_FABRIC_RELEASE_MIRROR_MOUNT_ROOT`, `RUNNER_MCP_FABRIC_RELEASE_MIRROR_ROOT`); never hardcode/invent caller-supplied source/custody paths or duplicate AIfordable topology. Physical scope already verified; independently identify/check the trusted current protected primary archive custody root, exact original service manager and currently installed module/venv/source before any config change. Only existing authorized owner-private config persistence, approved process recovery and no other service roles lost. Source-only PR merge cannot change the current serving process environment; no blind production update/restart.
- #587 remains **OPEN** pending actual live `ready=true` and two independently SHA256/provenance-verified immutable protected release archives stored/read back on that exact second device. #588 remains OPEN pending real disposable offline restore. No new relay, updater, controller, privilege path, mount, secret leak, protected-set copy or restore happened in this chat. Original operational receipt: [Runner-MCP #587 issue comment 6386724250](https://github.com/Blacksp1d3r/runner-mcp/issues/587#issuecomment-6386724250).

## 2026-10-24 — #669/#341 Fabric GitHub Release metadata preflight (SOURCE ONLY, target WAIT)

- Existing `FabricUpdateManager.release_assets_readiness(commit)` already validates exact immutable canonical Runner-Fabric GitHub prerelease tag/ref, source SHA, complete named asset set and published digest metadata. Existing MCP `fabric_update_readiness` still intentionally checks ONLY GitHub Actions artifacts; a GitHub Release is not an Actions update or install permission. New narrowly read-only `fabric_release_assets_readiness` exposure returns `source=github-release`, `mutation_authorized=false`, `download_performed=false`, bounded blocked reasons and audit; no source-mode fallback in `fabric_update`, no new updater, staging, privileged filesystem command or remote host authority. Synthetic tests cover admitted metadata, wrong tag/source, altered assets, old Actions path not called, and no bootstrap.
- A canonical *separate* Fabric GitHub Release asset bundle for exact source `ccb2aa334983df07a096028da4024bbe52245f0b` was published and verified in source owner Actions #40068489705. That package is not installed, independently custodied, or eligible for a control-path update. Original installed Fabric slots lack the new fixed archive bootstrap module. Existing Runner-MCP original runtime and A6/A7 independent recovery remain unqualified; AF-SB-0001 fixed archive namespace remains unqualified/missing. Do not interpret metadata `ready` as executable `artifact_ready` or promote production.
- Next: independently attest **original exact target** existing release importer and prior-good rollback/independent archive via current central topology. Stage only through already-approved, same-host first-party custody with full hash/identity/rollback and operator authority; never substitute a different server or copy source directly to live venv.

## 2026-10-23 — #669 original v0.1.38 GitHub wheel ↔ physical installed Python bytes MATCH (NOT loaded generation)

- **NEW ORIGINAL-HOST VERIFIED RESULT — PASS, no host change:** On original physical `github-runner` as actual `gha-runner` with original Runner-MCP PID520762/startticks36045221 and Fabric PID1784445/startticks72680080 guards, an independent calculation from the **actually installed 112 `runner_mcp/**/*.py` module bytes** produced exact canonical path/NUL/SHA256/LF digest `d49f2420f76ab3154e827b56393b509275fd386531ab97b923e43a2ee6bd4999`, identical to the independently verified existing GitHub Actions historical 0.1.38 wheel candidate. Physical sanitized receipt: `HISTORICAL_0_1_38_MATCH=PASS`, `MODULES_COMPARED=112`, `LOADED_MODULES_VERIFIED=FALSE`, `RESTORE_TESTED=FALSE`, `NO_CHANGES=TRUE` ([#669 authoritative operator result](https://github.com/Blacksp1d3r/runner-mcp/issues/669#issuecomment-6374329377)). **DO NOT repeat** 112-to-112 RECORD or this artifact byte-match inspection. This supersedes the older recovery-candidate-only pending comparison below, but **does not** prove imported six-process code, exact original wheel archive used during historical installation, or original live source/wheel attestation.
- **Existing historical artifact provenance:** Successful exact-source GitHub Actions run `39062118181`, artifact `12111995907`, source commit `d2dce33c436794fb90ce78cb12d1a7f27b4243d3`, wheel SHA256 `316c90dd66f139623e5f12efb59b1f7a7a84876e68de477c218ff98c13115adf`, outer GitHub artifact SHA256 `651e1ca9d2eaef0e83214c5fc2aec3fdf0cccd3eb61dd03606ce82357c3dedf0`. An **isolated** Python 3.13 `pip --no-index --no-deps` installation and metadata smoke test of the candidate succeeded outside the physical production host; not a full dependency/cron/Fabric/Agent Bus recovery. GitHub verified artifact expiry `2026-11-16T19:22:59Z`; preserve ONLY using existing qualified private custody before it expires.
- **Storage still DENIED:** Original registered `AF-VOL-0001` independent volume mount/UUID/ample free space pass, current owner venv 86 MiB, but existing registered `AF-SB-0001` archive namespace is **MISSING**, parent is **NOT WRITABLE** to `gha-runner` and binding `qualified=false`; first-party readiness `storage-bindings-unconfigured`. Existing Fabric namespace admission is policy-only and cannot create folder/write/authorize user; no sudo mkdir, fallback to another project's directory, new mirror/updater or privileged host mutation. [#669 namespace receipt](https://github.com/Blacksp1d3r/runner-mcp/issues/669#issuecomment-6374278037).
- **Next genuinely missing physical gates (not another source version increment):** existing AIfordable/Fabric authority must admit the exact registered owner-private archive namespace/binding; independently preserve the matching historical wheel and exact original venv dependency+six cron role launch bindings; qualify a separate networkless full offline return including proper executables, dependencies, current Fabric peer and Agent Bus, then independent original target A6/A7 and controlled rollback. Source-only GitHub current v0.1.85 remains **not installed**; original first-party is 0.1.38 with active revision/digest NULL and `self_update_ready=false`. No live issuer activation, Black SQL request/terminal digest/original-client ACK or Claude/Qwen dispatch is proven; #669 OPEN.

---
## 2026-10-23 — #669 HISTORICAL 0.1.38 WHEEL CANDIDATE FOUND; SAME-HOST BYTE MATCH AND OFFLINE RESTORE STILL WAIT

- **NEW EXISTING historical artifact (qualified CANDIDATE ONLY):** Other parallel #669 work located an unexpired original [GitHub Actions success run 39062118181](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/39062118181), artifact ID `12111995907`, for pinned 0.1.38 source commit `d2dce33c436794fb90ce78cb12d1a7f27b4243d3`. The artifact was downloaded and checked **outside the original host**: archive SHA256 `651e1ca9d2eaef0e83214c5fc2aec3fdf0cccd3eb61dd03606ce82357c3dedf0`; inner original wheel SHA256 `316c90dd66f139623e5f12efb59b1f7a7a84876e68de477c218ff98c13115adf`, 112 Python member paths with complete internal RECORD checks and 0.1.38 metadata. The expected canonical sorted `relative-name/NUL/sha256-hex/LF` digest for these **112 Python files** is `d49f2420f76ab3154e827b56393b509275fd386531ab97b923e43a2ee6bd4999` (see [#669 artifact investigation](https://github.com/Blacksp1d3r/runner-mcp/issues/669#issuecomment-6374237217)). This validates that archived **candidate**, NOT which bytes the original server loaded or whether the exact installed distribution matches; GitHub retention may expire.
- **Original physical snapshot-size/volume READ-ONLY PASS:** Separate correct-host owner inspection measured original running parent venv: `VENV_FILES=3556`, `VENV_SIZE_MIB=86`, `VENV_UNREADABLE=0`. Existing registered separate archive volume `AF-VOL-0001` mounted with UUID identity and distinct device PASS, available ~6931 GiB; **`RELEASE_ARCHIVE_NAMESPACE=NOT_VERIFIED`**, no snapshot taken, no storage write authority (see [#669 physical observation](https://github.com/Blacksp1d3r/runner-mcp/issues/669#issuecomment-6374215878)). The first-party archive readiness remains unconfigured; preserve AIfordable registered volume/service/namespace ownership and never write to an unqualified volume namespace or other projects.
- **One NEW bounded read-only acceptance, not redo of RECORD:** Have the authorized SAME ORIGINAL `github-runner`/`gha-runner` owner, with unchanged six process generations/venv guard, calculate the **canonical aggregate of installed 112 Python modules** using the artifact's exact sorted filename + `NUL` + lowercase content-SHA256 + `LF` convention and compare to the fixed digest above, without copying wheel to original host or revalidating already-PASS installed RECORD against itself. MATCH proves installed Python files correspond to historical candidate; does NOT prove in-memory loaded modules or preserved rollback. MISMATCH/unknown STOP and record discrepancy.
- **After a MATCH:** preserve the existing unexpired wheel in the **already-authorized protected release custody** through existing Fabric #924/#943 authority only when the exact private archive namespace and independent restore route have been qualified; replay a network-disabled disposable offline restore of the original runtime and six startup bindings, with old and target generations protected. Runtime #669 may assert active revision/wheel only after independent in-memory import/process witness AND original-client same-generation confirmation. No self-update, pip, cron restart, issuer activation, new relay/updater, unapproved archive namespace modification, or false live acceptance.

---
## 2026-10-23 — #669 original 0.1.38 rollback wheel custody NEGATIVE (bounded original-host scope), recovery still WAIT

- **NEW PHYSICAL READ-ONLY OPERATOR EVIDENCE (NO HOST CHANGE):** On verified original physical `github-runner` as `gha-runner`, after preserving all six already-attributed active cron/Fabric process generations, existing `self-update-install-artifacts` locations returned `BASELINE_WHEELS=0`, `BASELINE_VERSION_0_1_38=0`, `TARGET_WHEELS=0`, `TARGET_VERSION_0_1_38=0`, `UNVERIFIED_ENTRIES=0`, `INSTALLATION_CHANGED=FALSE`, `NO_CHANGES=TRUE`. An earlier 112-Python-RECORD comparison proved installed parent distribution v0.1.38 internally consistent. Absence in these **two scoped locations** is NOT proof no qualified backup exists anywhere. Do not repeat either completed scan; exact receipts in [Runner-MCP #669](https://github.com/Blacksp1d3r/runner-mcp/issues/669#issuecomment-6374115324) and [Fabric #924](https://github.com/Blacksp1d3r/Runner-Fabric/issues/924#issuecomment-6374117938).
- **SOURCE VERDICT / no false recovery claim:** Existing `src/runner_mcp/self_update.py:_run_job` stages rollback baseline wheel from a Git clean-head that must match recorded baseline commit; original runtime Doctor still FAILS `source_baseline_drift` + `active_revision_unavailable`, `self_update_ready=false`. Existing `src/runner_mcp/self_update_install.py:install_recovery_state` returning `clear` and public `install_recovery_pending=false` mean **no outstanding install transaction**, NOT the presence of restorable old wheel. Its `verify_runtime()` runs a NEW subprocess import, not attestation of in-memory imports of the six already-serving processes. The actual first-party current loaded+installed is v0.1.38, active source revision/digest NULL, verified false; GitHub v0.1.85 PR #818 is SOURCE ONLY, NOT installed.
- **Separate independent recovery deficiencies:** First-party `fabric_release_archive_mirror_readiness` remains `unconfigured/storage-bindings-unconfigured`, primary/mirror distinct device not proven. It is an archive-storage gate, not proof of any retained original Runner-MCP 0.1.38 wheel. `fabric_continuity_status=unavailable`, external submission disabled. Physical off-target Fabric #1617/#942 A6 original journal/target-outage readback, #943 networkless A7 six-role rollback and #924 original-host installed wheel/source/recovery receipt remain WAIT. Existing original machine issuer authenticates fixed GET but Black SQL POST→claim→terminal digest→same-original issuer ACK still NOT TESTED.
- **SHORT NEXT ACTION, existing owners:** Fabric #924/#943 must inspect only explicitly approved existing independent recovery custody (do not broad-search secrets). If no trusted original exact 0.1.38 immutable wheel remains, first qualify an owner-private byte-verified snapshot of the **exact currently installed original runtime environment(s)**, interpreter/dependency closure and six previously verified launch bindings using the EXISTING update/recovery custody. A copied venv alone is NOT rollback evidence: independently rehearse offline restore to real expected executable/venv/startup layout in an isolated authorized non-serving copy, reject altered module/permissions/absolute-shebang assumptions, and preserve previous good original without touching active services. A6/A7 real recovery, monitored promotion and original-client receipt are separate subsequent physical gates. Do NOT create a second updater/relay, synthesize an old wheel SHA from Git history, treat a fresh Python import as already-serving proof, relocate credentials, run pip/install, restart cron roles or enable missing services.
- **Ownership and status:** Runner-MCP #669 remains **OPEN** (software provenance/loaded generation unverified), Fabric #924/#943 own release/rollback, AIfordable #585 existing private issuer. Source audit recorded [#669](https://github.com/Blacksp1d3r/runner-mcp/issues/669#issuecomment-6374211387) and [Fabric #924](https://github.com/Blacksp1d3r/Runner-Fabric/issues/924#issuecomment-6374212668). No production change.

---
## 2026-10-23 — #669 original Agent Bus command PID PROVEN; six declared cron roles now attributable, imported code WAIT

- **NEW PHYSICAL ORIGINAL-HOST PASS / NO CHANGES:** Original `github-runner` as service owner `gha-runner`, guarded original Runner-MCP PID520762/startticks36045221, original Fabric Agent PID1784445/startticks72680080 (child of 520762), and original Agent Bus cron-lock-holder PID340238/startticks6855214. Exact operator sanitized output: `ORIGINAL_GENERATIONS=VERIFIED`, `AGENT_BUS_COMMAND=MATCH`, `AGENT_BUS_MANAGER=CRON`, `EXECUTABLE_IMAGE_SAME_AS_SERVER=False`, `LOADED_MODULES_VERIFIED=FALSE`, `NO_CHANGES=TRUE`. PID340238 executes actual existing Fabric CLI `agent-bus-run`. Existing Runner-MCP source `src/runner_mcp/agent_bus_worker.py` delegates to Fabric CLI, so different executable inode from Runner-MCP server is **not** evidence of a failure or wrong server; it is **not** trusted executable/wheel provenance either.
- **SIX DECLARED CRON ROLES NOW PROCESS-ATTRIBUTABLE, NOT SAME BUILD:** server PID520762, topology heartbeat PID520763, GitHub watcher PID520758, completion watcher PID520760, Agent Bus PID340238 (Fabric CLI, older process generation), Fabric qualification agent PID1784445 (actual `agent-serve-qualification` and verified owner of original loopback port 9020). The Fabric process is proven serving despite not holding the optional Fabric cron-exclusive lock; do not start duplicate agent. Tunnel/live overview are not configured in this cron block and are NOT part of this six-role acceptance. All six have role/process evidence; this is NOT proof their Python modules, exact executable release, source revision or wheel hashes agree. Re-running original cron/lock census, 112 parent Runner-MCP RECORD, 407 prior Fabric RECORD, prior old doctor, original credential GET or PID340238 `agent-bus-run` command check would duplicate already completed work.
- **#669 STILL OPEN / exact remaining acceptance:** original-client connected v0.1.38, `active_build_provenance_verified=false`, trusted active source and artifact digest NULL, `self_update_ready=false`; installed on-disk distribution RECORD matched prior but current in-memory imports for each role remain UNVERIFIED, original immutable wheel/build receipt and protected previous-good release for all roles unproven. Separately preserve A6 `0/11`, physical A6/A7 rollback/recovery and original Black SQL terminal result/ACK as independent gates, not interchangeable with process census. Next owner-correct-host **bounded read-only** six-role runtime executable/interpreter/installed slot and imported-generation attestation, followed by independent wheel archive/receipt custody checks and Fabric #924 recovery; no CLI restart/update, token relocation, second relay or fabricated digest. See [#669 exact process proof](https://github.com/Blacksp1d3r/runner-mcp/issues/669#issuecomment-6373441403), [Fabric #924](https://github.com/Blacksp1d3r/Runner-Fabric/issues/924#issuecomment-6373442745).

---

## 2026-10-23 — #669 original github-runner cron roster PARTIALLY VERIFIED; loaded generation WAIT

- **Read-only physical observed owner/correct host:** original `github-runner` / `gha-runner` verified Fabric listener. Actual operator output `ORIGINAL_PROCESS=VERIFIED`, `MANAGER_CRON=MANAGED_BLOCK`, `NO_CHANGES=TRUE`. Existing cron block declares six: `server`, `topology-heartbeat`, `github-watcher`, `completion-watcher`, `agent-bus-worker`, `fabric-agent-qualification`. `tunnel` and `fabric-live-overview` are **not listed** in this cron block, not demonstrated stopped or supposed to be installed under a different manager. Eight optional `systemctl --user` units were previously NOT_LOADED: they are not evidence of absence of the existing cron-owned execution.
- **Four directly matched original cron processes:** server PID `520762` startticks `36045221`; topology-heartbeat PID `520763` ticks `36045221`; github-watcher PID `520758` ticks `36045220`; completion-watcher PID `520760` ticks `36045221`. They matched the inspected private config root; `OTHER_CONFIG_ROLE_PROCESSES=0`, `UNKNOWN_CONFIG_ROLE_PROCESSES=0` within the **bounded argv-signature filter only**. Role signatures for agent-bus-worker and Fabric qualification showed `PROCESSES=0` under that limited matcher, **not** authoritative proof either service stopped.
- **Independent cross-lane role indications already physically proven:** existing owner-private `agent-bus-worker` cron flock held by same-owner PID `340238`, startticks `6855214` (Runner-MCP #669/#341 issue evidence); this is the previously missed Agent Bus process. Original Fabric peer PID `1784445`, startticks `72680080`, parent server PID `520762`, has been independently physically verified, though `fabric-agent-qualification` cron flock not observed. Do not restart or create a second Fabric agent because its cron lock was not held. The Agent Bus holder started earlier than the four matched original Runner-MCP cron processes: **homogeneous active generation cannot be presumed**.
- **Crucial unproven criteria for #669:** exact executable/imported-module/installed-wheel+source revision witness for **each** of the six real serving roles, historic immutable wheel/archive SHA with independent build/source trust, retained previous-good generation, off-target A6, networkless A7 and original requester→Black terminal digest→durable ACK. Existing original Runner-MCP parent installed `0.1.38` and its **112** Python files match installed RECORD (PASS); previous Fabric slot **407** RECORD files and old CLI doctor PASS. Do NOT repeat those checks as proxy for loaded modules. Current first-party build_identity revision/digest NULL, runtime doctor two FAIL and `self_update_ready=false`. GitHub source PR #818 0.1.85 is merged but **NOT** installed.
- **Next exact narrow original-host read-only gate:** under an unchanged physical original PID/UID/starttick guard, attribute **already known** agent-bus holder PID `340238` and Fabric listener PID `1784445` (plus four prior process PIDs) through `/proc` owner, process start, parent/cgroup, safe executable classification and **boolean** role markers. Never output argv/env/private paths/secrets; never invoke `cron_status()`, which can `O_CREAT` locks, or any operation that restarts/edits cron/services. If changed, STOP/reconcile, no mutation. Independent physical runtime import generation will remain UNATTESTED until trusted verification and supervised update.
- **Coordination:** Runner-MCP #669 physical build-identity; Runner-MCP #341 fixed client; Runner-Fabric #924 current-host release/recovery; AIfordable #585 existing original issuer. Maintain original physical `github-runner` distinct from `aifordable-lab`, Black and Blacky. See [#669 physical cron report](https://github.com/Blacksp1d3r/runner-mcp/issues/669#issuecomment-6373235047), [#669 same-owner lock](https://github.com/Blacksp1d3r/runner-mcp/issues/669#issuecomment-6373202580), [#341 owner-auth evidence](https://github.com/Blacksp1d3r/runner-mcp/issues/341). #669 OPEN, no host mutation, no SQL POST/ACK and no model dispatch.

---

## 2026-10-23 — #341 exact original publisher config-root mismatch, guarded sibling source correction

- **PHYSICAL ORIGINAL-HOST NEW READ-ONLY EVIDENCE:** On original physical `github-runner` as `gha-runner`, using original Fabric PID `1784445` / parent `520762` / startticks `72680080` guard, operator returned `PUBLISHER_PROCESS=VERIFIED`, `PARENT_CONFIG_SOURCE=CLI`, `PARENT_CONFIG_KIND=RUNNER_MCP`, `PARENT_CONFIG_PRIVATE=PASS`, `ISSUER_IN_PARENT_CONFIG=MISSING`, `NO_CHANGES=TRUE`. Previously independently owner-proven original machine issuer credential exists in its separate **Runner-Fabric owner-private sibling namespace** and really authenticated as the already registered original SQL `runner:control` with `AUTHENTICATED_NO_COMMAND` over fixed HTTPS GET. These are observations from the same original host, not `aifordable-lab`, Black or Blacky.
- **Root cause confined:** prior source-only #813 optional loader looked only in the original Runner-MCP CLI-selected config directory, whereas the REAL qualified original issuer file is already held separately in the local Runner-Fabric namespace. No token copy, symlink, alternate machine identity, new config registry or issuer rotation is permitted. Serving original Runner-MCP is still `0.1.38`, unverified artifact and self-update OFF: **this source correction is NOT installed/active**.
- **Bounded source-only repair (proposed on this branch):** extend the EXISTING `fabric_agent_qualification.py` optional machine-issuer loader to accept exactly one 0600 owner-held file in EITHER the existing Runner-MCP config directory OR the owner-private Runner-Fabric sibling directory, **only** when the Runner-MCP directory is the owner's standard `~/.config/runner-mcp`. Reject ambiguous dual files, directory or file symlinks, unsafe modes/UIDs/hard-links, non-machine issuer role, wrong canonical TLS origin and invalid credentials; no arbitrary path overrides or silent copied tokens. Preserve the existing optional absence/no-publisher default and existing fixed Fabric worker/issuer tools. Synthetic tests cover forwarding without copying, collision, unsafe custody and custom-config exclusion.
- **Operational gate unchanged:** this source-only patch and GitHub CI are NOT proof of active Fabric issuer opt-in or a usable rollback/update. Existing previous-slot 407 RECORD and old CLI doctor were already operator-PASS and must not be repeated. Fabric #924 owns same-host current manager/launcher/source/rollback admission; Runner-MCP #341/#669 owns safe installed provenance; AIfordable #585 owns canonical credential authority. No SQL Black POST/claim/result/digest/original ACK yet and no automated Claude/Qwen invocation. Do not restart six services or deploy from GitHub without physically qualified recovery.

## 2026-10-23 — #341 exact original-parent issuer-location mismatch VERIFIED (read-only, not fixed)

- **ORIGINAL PHYSICAL READ-ONLY PASS, exact host/owner:** On original `github-runner` as `gha-runner`, the operator verified the same serving Fabric process generation and its actual Runner-MCP parent role. Sanitized evidence: `ORIGINAL_PROCESS=VERIFIED`, `PARENT_ROLE=RUNNER_MCP`, `CONFIG_SELECTION=EXPLICIT`, `CONFIG_ROOT=OWNER_PRIVATE`, `PARENT_ISSUER_FILE=ABSENT_IN_PARENT_CONFIG`, `LIVE_ISSUER_ACTIVATION=NOT_PROVEN`, `NO_CHANGES=TRUE`. The original parent uses an explicitly selected private Runner-MCP config root; **the exact optional `af585-control-issuer.env` is absent there**. Do not expose its root path or parent argv/env in Git.
- **Distinguish CREDENTIAL AUTH PASS from RUNTIME BINDING WAIT:** A separately held, owner-private credential file on the *same original physical host* was previously validated and produced `RELAY_ISSUER_GET=AUTHENTICATED_NO_COMMAND` to the existing AIfordable SQL relay as registered original machine publisher `runner:control`. Its successful authenticated GET does not place that file in the parent process's separate config directory or register the optional Fabric tools. The earlier missing-file observation and the authenticated existing file concern two distinct private locations, **not two servers**. Do not mint, rotate, duplicate, copy, move, symlink or retest the credential to bridge this gap without existing private authority and a qualified approved action.
- **IMPLEMENTATION already present in source, but NOT INSTALLED:** Runner-MCP PR #813 (v0.1.84) reads the exact `<private active config_dir>/af585-control-issuer.env`, validates private owner/0600/single-link, fixed three-key mode/HTTPS origin and forwards only that optional credential to the existing Fabric Agent. The original live connected central Runner-MCP still reports version `0.1.38`, source/wheel unknown, `self_update_ready=false`, A6 `0/11`. Original Fabric 2ff... source already has the fixed Black three-tool surface but the active process's issuer settings/methods remain unarmed. Fabric PR #1730 fixes its rollback failure path in GitHub SOURCE only, not the physical original installation. Prior original Fabric previous-slot receipt/407 RECORD and doctor PASS: do not repeat; they are not physical rollback proof.
- **OWNERS and NEXT:** AIfordable #585 reconciles the *existing* original-host machine-secret custody and expected private parent root in its existing Infrastructure/Credential Authority. Fabric #924 validates the same physical server's exact existing launcher/service/PID/installed wheel and prior-good recovery, and coordinates any explicitly admitted existing managed activation. Runner-MCP #669 still lacks six-role active source/wheel attestation and offline A6/A7; do not blind-update the six primary roles. Only after proven issuer methods and rollback admit one fixed original `qual:black:runtime:v1` read-only SQL POST to `runner:black`, capture claim/worker generation/terminal payload+SHA256/same original machine-issuer durable ACK and reread. No SQL POST/claim/result/ACK or Claude/Qwen original-client dispatch yet; #341/#669 remain OPEN. No new updater, relay, controller, login, MFA/OIDC.
- Cross-project issue evidence: [Runner-MCP #341](https://github.com/Blacksp1d3r/runner-mcp/issues/341#issuecomment-6372069337), [Fabric #924](https://github.com/Blacksp1d3r/Runner-Fabric/issues/924#issuecomment-6372070341), [AIfordable #585](https://github.com/Blacksp1d3r/AIfordable/issues/585#issuecomment-6372071427).

---

## 2026-10-23 — #341 ORIGINAL machine issuer AUTH GET PASS; Fabric rollback fix SOURCE MERGED, not installed

- **PHYSICAL ORIGINAL-HOST AUTH PASS (new, no mutation):** The operator on verified physical `github-runner` as service owner `gha-runner` guarded the original serving Fabric process generation and used its *existing independently custodied* machine-issuer file over TLS, with no proxy/redirect, against the single fixed original SQL-relay GET. The returned `RELAY_ISSUER_GET=AUTHENTICATED_NO_COMMAND`, `NO_CHANGES=TRUE` is an authentication-accepted HTTP 404 for absent SQL command, **not** an unauthorized 401/403. The existing relay enforces original principal `runner:control` ahead of row lookup. Authenticated machine issuer credential custody and real acceptance at the **original** host are therefore proven. AIfordable #585 already carries private custody metadata in existing CRED-013 through merged #653/#654; do not copy its secret or repeat file/shape/GET validation. A separately custodied lab file is a different deployment.
- **FABRIC rollback SOURCE repaired, not physically present:** Fabric [PR #1730](https://github.com/Blacksp1d3r/Runner-Fabric/pull/1730) merged source at `d111ba8d5a8c6145fb1cf4e2927daa941eb827bc`, exact-head Foundation and attribution CI PASS. Existing `rollback_update` now retains the pre-switch launcher and reverts it when prior CLI doctor or post-switch rollback fails. Previous original physical Fabric slot/receipt and 407 installed RECORD hashes PASS, followed by independent prior-slot doctor PASS; **no actual service rollback or new rollback code installation occurred**. Fabric #924 still owns guarded current/previous launcher, imported wheel/RECORD, recovery and qualified managed deployment. This corrects the *older* note immediately below saying source rollback fix remained blocked; that note is historical.
- **REMAINING actual issuer bridge blocker:** Original *serving* Fabric Agent previous readout has machine-issuer mode/origin/credential OFF, therefore fixed `control_center_black_submit/status/ack` methods are not live; Runner-MCP connected installed v0.1.38 cannot load merged source-only optional private-file forwarding PR #813/v0.1.84. A proven confidential file and a successfully authenticated manual GET **do not mean the live process consumes that file**. Next is only *read-only exact original-host* parent Runner-MCP config-dir/launcher/active PID and release-slot/import mapping, with no sensitive argv/secret, before any protected six-role live upgrade. Follow existing Infrastructure Authority and Fabric #924; no blind restart or credential relocation.
- **No Black work yet:** Original `qual:black:runtime:v1` POST → SQL row → positive physical `runner:black` worker claim/generation → terminal payload+SHA256 → same-original-issuer durable ACK + readback is NOT TESTED. Existing bridge says READY but mutation and execution disabled; original connected Runner-MCP 0.1.38 active provenance unverified, self-update disabled, A6 0/11. After an independently qualified existing activation, do ONE bounded fixed Black status probe, then separately Claude and Qwen. No MFA/login/OIDC, extra issuer, updater, scheduler, tunnel or relay.
- **Ownership / evidence:** [Runner-MCP #341](https://github.com/Blacksp1d3r/runner-mcp/issues/341), [#669](https://github.com/Blacksp1d3r/runner-mcp/issues/669), [Fabric #924](https://github.com/Blacksp1d3r/Runner-Fabric/issues/924), [AIfordable #585](https://github.com/Blacksp1d3r/AIfordable/issues/585). Keep existing topology, role registry, decision log and Failure Museum; no duplicate resource registry.

---

## 2026-10-23 — #341 original-control-host previous-slot doctor PASS (READ-ONLY ONLY)

- **PHYSICAL PASS / no mutation:** On the independently verified *original control host* and original service account, the operator ran the existing bounded previous-slot doctor with process-generation and managed-slot guards. Actual output: `ORIGINAL_PROCESS=VERIFIED`, `PREVIOUS_SLOT=BOUNDED`, `PREVIOUS_DOCTOR=PASS`, `NO_CHANGES=TRUE`. Existing separate same-host previous-slot receipt and installed RECORD (407 Python files) were already verified; **do not repeat** either check. Full private host/PID/slot details belong only to existing Infrastructure Authority and canonical cross-project issue evidence.
- **NOT a rollback/activation proof:** The prior CLI can perform `doctor`, but service relaunch, tunnel-independent A7 auto-revert and active launcher recovery were NOT exercised. Fabric #924 documents an unresolved existing `rollback_update` failure path (launcher switched before doctor; unsuccessful doctor does not restore the formerly active link); an attempted source fix was safety-blocked. Do not claim the bug fixed, invoke physical rollback or install/update protected roles.
- **Existing publisher still WAIT:** `runner:control` exists in the original SQL relay registry, but independently qualified secret custody on the *original* publisher host and its active Fabric machine-issuer opt-in are not established. A credential on the separate lab host is not authorization to copy it. AIfordable #585 owns private issuer custody and relay; Fabric #924 owns correct-host rollback and issuer activation.
- **Runtime distinction:** Original authenticated central Runner-MCP still serves 0.1.38 with source/wheel provenance UNVERIFIED and `self_update_ready=false`; Fabric bridge is read-only READY, Agent Bus relay UNKNOWN/execution disabled. A6 live 0/11. Runner-MCP v0.1.84 (#813) is SOURCE MERGED ONLY; original `qual:black:runtime:v1` requester→worker claim→terminal result/digest→same-issuer durable ACK is **NOT TESTED**. #341/#669 remain OPEN; Claude and Qwen dispatch NOT YET ACCEPTED.
- **Next safe steps:** Resolve Fabric #924's existing rollback failure-path source repair without bypassing prior platform safety denial; independently establish original-host credential custody through AIfordable #585 private authority; then only after exact host+source/launcher/wheel/rollback admission issue ONE existing fixed read-only Black status command with durable ACK. Preserve original six-role control plane and recovery. No new relay, updater, credential, MFA/OIDC or other infrastructure.

---

## 2026-10-23 — #341 original machine issuer: receipt shape verified; private binding and actual Black ACK WAIT

**Evidence cut-off: 2026-10-23 (operator-local reports and current authenticated read-only MCP). Supersedes stale 2026-10-22 claims that the existing relay lacks `runner:control`.**

- **PASS, existing SQL identity only:** the separately authorized `runner:control` is already registered in the original relay identity provider with valid hash/generation/expiry. Its real authenticated fixed-request read-only GET returned expected JSON 404 (no queued request). Do **not** enroll a duplicate, reuse a worker token, rotate a credential speculatively or treat a relay identity record as proof that Fabric has the plaintext.
- **PASS, exact original Fabric *process mapping* by owner-local read-only check:** listener/owner/parent/managed slot matched the connected Fabric peer's source revision `2ff81b299e8d0b3f156d666ddc9719b97657664e`; owner-protected runtime-slot receipt schema `runner.fabric/control-plane-runtime-slot/v2`, receipt-field set, source match, `projectWheelSha256` and `bundleSumsSha256` SHA-256 *shape* passed. The earlier `WHEEL_DIGEST_PRESENT=False` came from probing a nonexistent `wheelSha256` key; it was a diagnostic false negative, **not** missing receipt digest. This does **not** independently rehash wheel/bundle bytes, attest imported Python modules/RECORD, validate the rollback launcher, or grant mutation authority.
- **BLOCKED, issuer custody/activation:** the existing right-host optional `af585-control-issuer.env` file was absent in the single qualified parent Runner-MCP config location; active Fabric issuer mode/origin/credential are absent. This does **not** prove absence from every independently authorized custodian. Source fix Runner-MCP [#813](https://github.com/Blacksp1d3r/runner-mcp/pull/813) (v0.1.84 optional secure-file forwarding) is merged **source only**; connected live Runner-MCP still serves `0.1.38`, `active_build_provenance_verified=false`, `active_artifact_revision/digest=null`, `self_update_ready=false`. A distinct older lab serving Fabric slot must never be equated to this original listener.
- **PASS, limited Black boundary only:** Black's original worker local `runtime_status` returned `ok`; fixed external issuer route rejected anonymous with JSON 401 and worker-role credential with JSON 403. **NOT TESTED:** original machine publisher POST for `qual:black:runtime:v1` → SQL persistence → target `runner:black` positive claim/worker generation → terminal original payload + SHA-256 digest → same authenticated issuer durable ACK and post-ACK readback. Fabric `fabric_bridge_preflight=ready` is not dispatch; `agent-bus.relay=UNKNOWN` and execution is disabled.
- **Next gated work:** via the existing AIfordable private Infrastructure/Credential Authority and Fabric #924, verify **on the exact original target** private credential custody, live launcher/RECORD/module vs receipt and independently viable previous release/rollback; continue only with a qualified existing bounded activation path. If any gate fails, read-only WAIT. When real existing issuer mode and correct serving proxy tools are demonstrated, issue **one** predefined read-only Black status request and preserve durable same-original-actor ACK. Follow with real Claude, then Qwen work. Human login/MFA/OIDC is deferred. No new relay, updater, tunnel, generic host/shell route, duplicate registry or blind central six-role restart.

Canonical owners: [Runner-MCP #341](https://github.com/Blacksp1d3r/runner-mcp/issues/341) (bounded publisher proxy/receipt), [#669](https://github.com/Blacksp1d3r/runner-mcp/issues/669) (serving provenance), [Fabric #924](https://github.com/Blacksp1d3r/Runner-Fabric/issues/924) (correct-host activation, dispatch/ACK), [AIfordable #585](https://github.com/Blacksp1d3r/AIfordable/issues/585) (private issuer custody and existing relay). Real host coordinates, PID/ports, environment secrets, credential bytes and private custody pointers belong only in the existing authorized private infrastructure authority and owner evidence, **not** this public Git tree.

---

## 2026-10-22 — #341 v0.1.83 ACK readback MERGED; physical machine chain still WAIT

- **Source DONE:** Runner-MCP [PR #810](https://github.com/Blacksp1d3r/runner-mcp/pull/810) v0.1.83 **MERGED** as `6ed9ad1a4edc124b2e39d1e82b086cde78bca243` after exact-head release reservation, Ruff/pytest, built wheel, clean Ubuntu installation, demo and commit attribution SUCCESS. This is the existing fixed Black ACK verifier, not another control or updater: the separate original-requester post-ACK SQL readback now must retain the exact terminal `result_payload` as well as original actor/auth strength, fixed request/target, fingerprint, version, positive worker generation, result code/digest and persisted ACK. Regression rejects changed payload with unchanged reported digest. Source merge **does not** deploy central runtime.
- **Physical AIfordable relay DONE:** existing original canonical relay/backend and existing TLS Nginx were safely activated by AIfordable #585; independent real physical Black HTTPS GET of the one fixed machine-issuer route now returns **401 application/json** without credential instead of historical 404 HTML. This establishes true route availability/authentication rejection, **not** successful command dispatch. Original physical Black worker `runner:black` already did one genuine local `runtime_status` using the existing Fabric Agent Bus worker→local MCP, `result_code=ok`, version 0.1.30. Do not reinstall Black.
- **Physical Fabric Agent source DONE:** first-party `fabric_bridge_preflight` now reads `state=ready` and **serving** Fabric source `2ff81b299e8d0b3f156d666ddc9719b97657664e`, after its already existing managed local update and safe agent restart. This is not the same as `mutation_enabled=true`; downstream fixed machine issuer tools still depend on private qualified opt-in issuer credentials.
- **Still BLOCKED:** canonical private relay identity inventory includes the Black worker and existing primary identities but **`runner:control` is absent**. The actually connected central Runner-MCP **still serves 0.1.38** with `active_build_provenance_verified=false`, `self_update_ready=false`; Fabric Agent Bus relay remains `UNKNOWN`, execution disabled, A6 original 0/11. Runner-MCP v0.1.83 is **GitHub source only**. No original-authorized `qual:black:runtime:v1` SQL insert, physical claim, terminal digest or separately authenticated original-requester durable ACK has yet been demonstrated. Neither a real backend HTTP 401 nor local Black `ok` is full chain acceptance.
- **Exactly next:** AIfordable #585 confirms privately and registers only the distinct existing-provider `runner:control` **original issuer** on the original host (never reuse worker credential); Fabric #924 qualifies the already-installed machine issuer opt-in; Runner-MCP #341/#669 coordinates a qualified serving version through the one existing proven and rollback-capable updater, **not** blind six-role replacement. Issue exactly one prebound read-only `runtime_status` to `runner:black` using the existing SQL relay; observe real positive claim/generation, terminal result/fingerprint/SHA digest, same original issuer ACK and retained readback. Only then Claude, then Qwen real lab tasks. Human login/MFA/OIDC remains deferred; no new relay, tunnel, general shell, host choice, updater, or security subsystem.

## 2026-10-22 — Runner-MCP #341 v0.1.82 source: fixed Black MACHINE issuer evidence

- Owner priority: machine-native Black real status/ACK, then one real Claude and Qwen task; human login/MFA/OIDC later. New v0.1.82 extends the **existing** Black status/ACK validator to accept true `machine` requester `runner:control` ONLY when original `qual:black:runtime:v1` is present, preserving old `mfa` mode and same original actor/claim/fingerprint/result digest/ACK.
- AIfordable #636 already source merged/staging; overlapping #637 + Fabric #1714 source must be reconciled into one active SQL publisher route, with independent owner-approved issuer identity. No two relay queues, no new tunnel/updater or arbitrary host/operation. Existing central 0.1.38 remains serving, physical original Black claim/result/durable ACK is unverified; A6/A7 original-host tests and six-role cutover remain WAIT. No live mutation from this source PR.

## 2026-10-22 — OPERATORBESLUIT: basis vóór menselijke MFA/login (uitgesteld)

**Prioriteit 1–4:** bestaande Runner-MCP/Fabric/AIfordable machineverbinding herstellen; één bestaande strikt vaste `runner:black`/`runtime_status` echte opdracht → worker-claim → resultaat → originele ACK; daarna één echte Claude-taak en één echte Qwen-taak via de juiste labworkers. **Pas na werkende basis:** menselijke login, Control Center-accounts, MFA/OIDC en aanvullende toegangsbeheerprojecten uitvoeren als apart *later* roadmaponderdeel. Niemand hoeft zich nu in een nog niet bestaand inlogscherm aan te melden.

De #804/#806 drie vaste tools en Fabric #1710 gebruiken in broncode de huidige MFA-operator-route; de betrokken projecten moeten de **bestaande** machine-to-machine autorisatie in de bestaande relay/bridge gebruiken voor de beperkte labtest, zonder publieke anonieme uitgeversroute of promotie van een worker-credential naar controllerrechten. Ontbrekende machine-uitgeversaansluiting is een concreet basisfunctioneel gat, geen verplichting om nu menselijke login/MFA te ontwikkelen. Geen extra relay, updater, algemene host/URL/shell-machtiging, nieuwe service of ongebruikte beveiligingsfunctionaliteit. Behoud originele opdracht/resultaat/ACK-correlatie, bevoegdheidsscheiding en veilige updatebarrières; raak de zes bestaande productieprocessen niet blind aan.

Dit besluit vervangt in de huidige werkplanning verouderde regels 'eerst MFA-issuer instellen' en 'eerst security klaar' als ontwikkelstop; het beweert **niet** dat de live centrale 0.1.38 is geüpgraded of Black/Claude/Qwen operationeel zijn.

## 2026-10-22 — #341 Black Control Center v0.1.81 SOURCE MERGED; isolated physical ACK WAIT

- Runner-MCP [PR #806](https://github.com/Blacksp1d3r/runner-mcp/pull/806) **SOURCE MERGED** `2fd8dcacc4c357663457d6651a93d572c31fe36a`, exact tested head `f5f63fdc60fa7abd19a0e47064bdb7bd68969510`. Runner MCP validation [#39756255817](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/39756255817), clean Ubuntu [#39756255754](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/39756255754), commit attribution [#39756257158](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/39756257158): all SUCCESS. Guard rejects unclaimed terminal worker generation; requires unchanged original issuer/request/target/fingerprint/worker claim/result through post-ACK readback. RMCP-F-0073 includes regression and early CI test-text correction.
- Cross-project source now aligns: Runner-MCP #804/#806; Fabric #1706/#1708/#1710/#1711; AIfordable #632 SOURCE MERGED `a9bf1519ded257fdc73850fafad831b95a6e08b5`. Existing Control Relay and genuine original MFA bearer must be reused. This is NOT a statement that active installations have been updated.
- Same original connected Runner-MCP `runtime_status` still 0.1.38 with unverified wheel/source and `self_update_ready=false`; read-only `fabric_operational_snapshot` reports `execution_enabled=false`, `mutation_enabled=false`, `unknown_layers=["agent-bus.relay"]`. Physical isolated Black v0.1.30 earlier confirmed 3 native services healthy and worker auth-only PASS, **not** an original requester result/ACK. No production six-role update, Black reinstallation, relay/credential/tunnel changes, or live dispatch.
- Operational NEXT: AIfordable #585 privately verifies actual original CONTROL_RUNNERS MFA issuer and currently served API revision; Fabric #924/#1556/#1563 qualifies the existing isolated first-party route and sends ONE prebound `runtime_status` to `runner:black`, records positive worker generation/claim/result digest and separately authenticated same-original-client durable ACK. Any missing authority remains WAIT. #341 and #669 remain OPEN for physical acceptance and separate six-role/A6/A7 provenance.

## 2026-10-22 — #341 Black original issuer: Fabric source connected, physical ACK WAIT; v0.1.81 guard candidate

- Fabric original issuer bridge **SOURCE MERGED** [#1706](https://github.com/Blacksp1d3r/Runner-Fabric/pull/1706), duplicate adapter removed [#1708](https://github.com/Blacksp1d3r/Runner-Fabric/pull/1708), bounded Agent MCP methods **SOURCE MERGED** [#1710](https://github.com/Blacksp1d3r/Runner-Fabric/pull/1710), docs [#1711](https://github.com/Blacksp1d3r/Runner-Fabric/pull/1711). Previous handover below incorrectly says Fabric Agent MCP methods were absent: **now superseded at source level only**. Exact fixed methods `control_center_black_submit/status/ack` match merged Runner-MCP #804 source.
- AIfordable #585 [PR #632](https://github.com/Blacksp1d3r/AIfordable/pull/632) SOURCE MERGED as `a9bf1519ded257fdc73850fafad831b95a6e08b5` (active deployment and MFA issuer still unverified): existing `/control-relay/commands` MFA-operator API adds canonical digest and explicit durable ACK; no deployed real issuer bearer independently observed. Existing connected central Runner-MCP remains **0.1.38**, bridge handshake READY but has no new exposed #804 methods, source/wheel unverified; physical `runner:black` original issuer result+digest+ACK **WAIT**. Do not install/upgrade/restart protected central six roles.
- Runner-MCP source-only v0.1.81 candidate strengthens #804's result verification: no terminal data without positively claimed worker generation, post-ACK original worker generation/requester/fingerprint must remain unchanged. Failure Museum **RMCP-F-0073**, synthetic regression tests and exact-head CI required, no relay/client duplication or runtime mutation.
- Operational sequence after upstream merge: AIfordable authenticates existing original CONTROL_RUNNERS MFA issuer and existing relay, Fabric deploys only approved isolated adapter/tool path, then one original authenticated `runtime_status` with fresh request ID to exact `runner:black` -> target claim -> retained result/digest -> same-issuer explicit ACK and verified readback. Heartbeat, source CI or HTTP 200 never substitute for this receipt.

## 2026-10-22 — #341 Control Center Black fixed issuer proxy SOURCE MERGED; live ACK WAIT

- PR [#804](https://github.com/Blacksp1d3r/runner-mcp/pull/804) SOURCE MERGED commit `ea641e691796556cd9f612b01946d7ab45951d5e` from exact tested head `202b0141c0f28e03cd9a4f2ce0479f17008c7483`; Runner MCP validation [#39747583227](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/39747583227), clean Ubuntu [#39747583162](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/39747583162), commit attribution [#39747583241](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/39747583241) all SUCCESS. Source version 0.1.80 only, NOT deployed or live-verified.
- Bounded optional tool delegation `control_center_black_submit/status/ack` operates only via original authenticated Fabric bridge to fixed `runner:black`/`runtime_status`. Three matching Fabric Agent MCP issuer tools remain **ABSENT** in existing Fabric source/runtime. AIfordable operator API PR [#632](https://github.com/Blacksp1d3r/AIfordable/pull/632) remains upstream dependency for REST result digest and explicit original-client ACK; Fabric must reuse #1701 existing receipt-bound commandclient and genuine original `CONTROL_RUNNERS` MFA bearer, not legacy internal worker route or credentials.
- Earlier CI discovered required tool catalogue baseline count drift (100→103) and noncanonical import order; both fixed before tested merge. Failure Museum RMCP-F-0072 updated. Actual Black result/digest/ACK still UNKNOWN/WAIT. The protected central 0.1.38 six roles, original wheel, A6 0/11 and isolated Black 0.1.30 remain untouched. #341 and #669 stay OPEN for true physical proof.

## 2026-10-22 — #341 fixed Black Control Center issuer proxy SOURCE CANDIDATE (live ACK WAIT)

- Runner-MCP candidate v0.1.80 adds optional `control_center_black_submit/status/ack` tools for ONLY `runner:black`/`runtime_status`, using existing authenticated `FabricBridgeClient` and no direct relay, arbitrary endpoint, host, operation, shell or second updater. Strict typed validator binds returned request ID, fixed target, fingerprint, MFA original requester, version, terminal digest and explicit post-ACK readback; wrong target/replay/foreign identity fail closed.
- **Missing upstream capabilities:** Fabric Agent MCP does not yet publish these three bounded methods backed by its EXISTING `ControlRelayCommandClient`. Its client historically uses incompatible internal relay issuer route; AIfordable #585 PR #632 proposes adding digest/ACK to EXISTING MFA operator REST `/control-relay/commands`; Fabric must adapt real operator bearer/HTTP201/schemas. Fabric PR #1701 receipt-bound status is already MERGED and must be reused.
- Work is source-only pending exact-head CI; cannot send a real Black request with central serving v0.1.38. Physical original-client result/durable ACK remains WAIT, as does #669 correct-host provenance. Three Black services and six protected central roles remain untouched. Root cause RMCP-F-0072; child `roadmap/children/341-control-center-black-runtime/`. Do not close #341 or claim live until AIfordable, Fabric and one actual original-client MFA command -> Black result -> verified explicit ACK are independently qualified.

## 2026-10-22 — #669 correct-host dependency update: isolated node LOCAL_STABLE_PASS, original-client ACK WAIT

- Independently recorded physical evidence from [Fabric #1563](https://github.com/Blacksp1d3r/Runner-Fabric/issues/1563) / [#924](https://github.com/Blacksp1d3r/Runner-Fabric/issues/924): isolated test node with pre-existing v0.1.30 package has exactly three approved native services installed, enabled and running; independent owner-local status and health checks PASS without restarts. AIfordable [#585](https://github.com/Blacksp1d3r/AIfordable/issues/585) already records unique relay identity and auth-only admission PASS. **Do not repeat setup, credentials, relay provisioning, autostart install, or local health checks.** This is a DIFFERENT physical host/process generation from central v0.1.38. Its three services are NOT the protected central six real process roles. No original-client result/digest ACK yet.
- Original authenticated central read-only check: loaded/installed 0.1.38; wheel SHA and active source null; `active_build_provenance_verified=false`, `self_update_ready=false`, Doctor provenance FAIL x2, A6 safely absent 0/11. `fabric_operational_snapshot` reports `agent-bus.relay` UNKNOWN/evidence-unavailable, `execution_enabled=false`, `mutation_enabled=false`; `fabric_continuity_status` unavailable/reconciliation required; bounded external target preflight/inspect error (UNKNOWN, not a proven remote host failure). The original connected client cannot yet attest or dispatch to the isolated node.
- NEXT external execution belongs to Fabric #1556/#1563 with AIfordable #585 existing authenticated issuer/relay: ONE harmless predefined read-only target-bound request with original request ID, exact target generation/lease, claim, persisted result/digest and ACK received by the SAME original initiating client. With `execution_enabled=false`, do not forge a probe, use unmanaged shell/Actions, or create a second issuer/relay. After positive proof, wrong-target/replay/lost-ACK negatives. Heartbeat and local HTTP 200 do not count as command completion.
- After original-client ACK, #669 separately requires PRIMARY pre-existing v0.1.38 original wheel bytes/installed RECORD plus actual loaded six-role launcher/process witness and independently retained earlier generation; Fabric #1617/#942 physical off-target A6 target-loss journal, #943 disconnected six-role A7. GitHub source v0.1.79/#802 only corrected offline candidate receipt durability; it is not installed/current build identity.
- Read-only canonical GitHub Releases query currently returned only v0.1.0, v0.1.2, v0.1.3. Source v0.1.79, rebuilt GitHub wheel, historical release asset or matching package version is NOT proof of the original physically loaded v0.1.38 wheel. Correct-host protected custody must supply independent evidence or stay UNKNOWN.

## 2026-10-22 — #669 v0.1.79 receipt publication safety SOURCE MERGED, live evidence WAIT

- [PR #802](https://github.com/Blacksp1d3r/runner-mcp/pull/802) SOURCE MERGED `32633535c2806b4011c425c74d36f10d84c723f6` from exact tested head `6a7eb52eec91636f66d6bfa3bc846c5b39775691`; validation [#39721158312](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/39721158312), clean Ubuntu [#39721158304](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/39721158304), attribution [#39721158317](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/39721158317) all SUCCESS. RMCP-F-0071 source corrected: post-byte-validation directory fsync failure preserves the original create-once receipt as publication uncertain; prevalidation write failure still cleans its own receipt.
- Post-source-merge live original client still `0.1.38`; source revision and wheel SHA NULL, active provenance FALSE, self_update_ready FALSE. Independent release archive mirror still UNCONFIGURED (`storage-bindings-unconfigured`, no cross-device proof). No host install, restart, private A6 binding, storage, relay, tunnel or update attempted. #669 remains OPEN; Fabric #924 correct-host six-process original wheel/RECORD identity, #1617/#942 physically independent journal, #943 offline rollback and #1556/#1563 original-client result+ACK still WAIT. Treat GitHub source 0.1.79 as SOURCE ONLY, not the server.

## 2026-10-22 — #669 offline receipt durability correction v0.1.79 SOURCE CANDIDATE

- RMCP-F-0071 discovered by source analysis: post-validation parent-directory fsync failure previously deleted potentially durable candidate receipt, losing evidence after an ambiguous publication. Narrow fix retains/create-once receipt, classifies `WheelReceiptPublicationUncertain`; early file-sync/byte mismatch cleans unvalidated receipt. Exact-head test/CI pending.
- Independent correct-host 0.1.38 wheel/RECORD/process/six-role evidence and previous-good generation plus Fabric A6/A7/original-client result ACK still WAIT. No live deployment/change. #669 stays OPEN.

## 2026-10-22 — #669 v0.1.78 SOURCE MERGED; independent live wheel/route still WAIT

- **Source reconciled**: PR [#800](https://github.com/Blacksp1d3r/runner-mcp/pull/800) merged 2026-10-21T20:34:26Z as `0daa8e7fd2c6edcb53c17d7f024efbb1e3d9e7c4`; exact PR HEAD `acf9e5e7b480e422ff1b6f2d64b27f4515a41732`, validation + clean Ubuntu installer + attribution SUCCESS. Source `pyproject.toml=0.1.78`. Earlier #794, #796, #797 and docs #798 are merged and MUST NOT be repeated. Supersedes the earlier “v0.1.78 candidate/pending” language below.
- **What exists**: `artifact_receipt_capture.py` can write one private 0600 candidate receipt of retained original wheel SHA-256 + installed `runner_mcp` Python-module checksums, requiring offline byte agreement. It does **not** independently authenticate the claimed source commit, attest process-imported wheel, protect an earlier generation, bind six real process roles, or yield A6/A7/update admission. #800 intentionally has not connected an installer hook or changed live services.
- **Fresh original-client primary** on 2026-10-22: loaded=installed `0.1.38`; `build_identity.source_revision=null`, `artifact_digest=null`, `active_build_provenance_verified=false`, `self_update_ready=false`; Runtime Doctor two provenance FAIL (`source_baseline_drift`, `active_revision_unavailable`), A6 `pass/not_configured_0_of_11` (safe absence, not qualified); Fabric bridge `ready` but `a6_prepare_available=false`, `synthetic_probe_status_available=false`, `mutation_enabled=false`. Reading local `host:local` inspection does not independently attest another host or wheel. Fabric #1697 pure fleet read projection is source merged, not a physical host scan.
- **Next executable dependencies (do not add another updater/relay)**: (1) Fabric #924 via authorized correct-host route independently inventories the *actual six launchers/process instances* and previously serving 0.1.38 original wheel bytes, installed RECORD and current loaded module evidence, retaining independently validated previous-good wheel; UNKNOWN remains WAIT. (2) Connect the existing #800 receipt emitter only within the already-authorized installer/generation custody (no generic path API); qualify its independent trusted source/bytes witness and original-client epoch. (3) Fabric #1617/#942 physical independent A6 journal, #943 disconnected A7 six-role rollback, #1556/#1563 terminal original-client result+ACK before #924 one-target staged update. None is complete merely because source CI passed.
- **Operational boundary**: no production install, six-role restart, A6 binding creation, storage formatting, Agent Bus dispatch, tunnel, secrets, OIDC/MFA or forced self-update in this session. #509 remains closed SOURCE-ONLY; #669 stays OPEN. Live baseline must not be relabeled as current GitHub main.

## 2026-10-21 — #669 v0.1.77 source MERGED; active 0.1.38 still UNVERIFIED

- Merged #794 v0.1.75 already forces locally scoped status and unverified active wheel; merged #796 v0.1.76 adds a process epoch to the two existing read-only tools. **Source-merged #797** fixes a remaining false origin-correlation path: the three legacy status-manager dictionaries can overwrite the epoch or mark it authenticated after the current process initially reports it. The final runtime normalizer now receives the current in-memory `build_mcp` epoch separately and overrides all manager claims. Extra negative tests cover stale/foreign/untyped epochs and invented authentication flags; no new tool or host mutation.
- Latest **original authenticated live primary remains 0.1.38** with no independently trusted currently loaded wheel/hash/source; A6 0/11, Doctor two provenance failures and `self_update_ready=false`. Source version 0.1.77 is not installed or cleared for primary production promotion. Real wheel+loaded six process identities, physical Fabric #1617/#942 journal, #943 offline return, #1556/#1563 original-client ACK and #924 one-host sequencing remain WAIT.
- GitHub PR [#797](https://github.com/Blacksp1d3r/runner-mcp/pull/797) MERGED `697f0b1efdb7b600c59fd7e6a15a1e35dfd4e703`; exact tested head `16f878af44bc4989dc773024477e116bde8cc8b4`, full CI validation #39668526638, clean Ubuntu #39668526305, attribution #39668526195 all SUCCESS. No central service mutation. No second updater/relay, tunnel, credential or arbitrary folder manager.

## 2026-10-21 — F30 Black #739 one owner-authorized offline Q7 importer path

- Existing black v0.1.30 isolated rootless stage and unique relay identity/HTTPS authentication are operator-observed PASS, but Fabric worker and exact original requester result ACK remain WAIT. #739 source milestones: #782 v0.1.64 audited 29 wheel ZIP/RECORD; #783 v0.1.65 fixed 33-body 0700 one-time custody; #784 v0.1.66 signed roster + fixed GitHub release + verified 33 downloads all merged; v0.1.67 standalone zipapp first-host packaging CANDIDATE. Authenticated independent publisher key/roster enrollment and real same-host asset import require separate correct-host operator action. A6 0/11 and A7 real six-role networkless rollback remain required before any central Runner-MCP production update. No second relay/installer/updater or OIDC/MFA work.

## 2026-10-20 — #669 independently pinned six-role offline source proof MERGED, #509 closed SOURCE / live A6 WAIT

- [PR #781](https://github.com/Blacksp1d3r/runner-mcp/pull/781) v0.1.63 MERGED `8d0405490c73bc324a522e66e5e596649d169371` (exact tested head `a9b9df31aa8e79e29cf85183e75e6ba25dca1215`). Existing Ed25519 signed offline statement check now has a strictly six-role process-identity-pin wrapper; each role must match a **separately supplied independent** unique process-instance SHA-256 pin; 5-role/swapped/substituted/duplicate/stale-wheel/host/nonce all refuse. ALWAYS `active_build_provenance_verified=false`, source/digest NULL and no update authority.
- CI exact-head validation/Ruff/pytest/demo/artifact [#39479195410](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/39479195410), clean Ubuntu [#39479195458](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/39479195458), attribution [#39479195285](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/39479195285) ALL SUCCESS. First negative test used `None` as both omitted and invalid data; corrected via sentinel, RMCP-F-0067/0068 SOURCE_MERGED.
- **LIVE original first-party** stays v0.1.38 loaded + dist, wheel SHA/source revision NULL, two provenance Doctor failures, A6 `0/11` safe unconfigured, self_update_ready=false. Six *managed projects* are NOT an attested six-process role roster. `#509` CLOSED **source only**; v0.1.63 contains its existing fixed 11-key conditional restore but old live 0.1.38 does not prove it is loaded. Never restart Fabric qualification agent or modify those private bindings before correct-host owner/Fabric #1617/#942 physically independent A6 state has been qualified.
- [#669/#509 evidence gates](https://github.com/Blacksp1d3r/runner-mcp/blob/main/handover/ISSUES_669_509_OPERATOR_GATES_20261020.md): independent actual serving old-wheel SHA/source+installed RECORD and all six loaded process/launcher maps + independently protected previous-good wheel missing; Fabric #943 offline six-role revert, #1556/#1563 original-client result+durable ACK and #924 one guarded cutover WAIT. No live install, restart, A6 changes, second updater/relay/tunnel/folder manager or OIDC/MFA.

---

## 2026-10-20 20:30 Europe/Brussels — #669 live identity WAIT / #509 CLOSED source but live A6 0/11

- Original authenticated serving Runner-MCP `0.1.38` and installed dist `0.1.38`, source revision NULL, **wheel SHA NULL**, independently verified provenance FALSE, self_update_ready FALSE, Doctor source_baseline_drift + active_revision_unavailable FAIL. Historical 2026-10-07 self-update commit != loaded wheel; `projects=6` is NOT six serving roles.
- #509 issue CLOSED for source 2026-10-20 17:20:58Z, existing fixed 11-key conditional repair remains in GitHub main `0.1.62` (not currently installed or proven loaded). Original client's A6 `pass/not_configured_0_of_11` = safe absence, NOT A6 qualification; bridge read-only READY, prepare/probe FALSE, mutation FALSE, Agent Bus UNKNOWN and archive mirror unconfigured. Do not restart agent on the strength of closed issue.
- #669 remains OPEN: independent owner-controlled correct-host current old wheel bytes+trusted SHA/RECORD, exact six-role loaded process/launcher map, fresh signed nonce and protected prior-gen escrow are missing; current old v0.1.38 MCP tools cannot attest them. GitHub wheel SHA or `importlib.metadata` alone does not establish active digest.
- Physical off-target A6 Fabric #1617/#942, #943 real disconnected six-role A7, Fabric #1556/#1563 original result/durable ACK and #924 one-target promotion still WAIT. No service/host/storage/credential/tunnel/relay mutation in this check.
- **Canonical original-client evidence**: [#669/#509 independent correct-host gates](https://github.com/Blacksp1d3r/runner-mcp/blob/main/handover/ISSUES_669_509_OPERATOR_GATES_20261020.md); issue #669 and closed #509 updated; Fabric #1617 notified.

---

## 2026-10-20 — #615 atomic quarantine existing PR #618 MERGED; production still WAIT

- Original draft [PR #618](https://github.com/Blacksp1d3r/runner-mcp/pull/618) was preserved and reconciled with main #531 safe noncreating inspection using a lease-guarded two-parent integration; exact tested head `bcf57059aa7a345f4966f043ff7a5f4c607071e6` merged squash `6cbd6880aaacef020747c5350fcb885d1047c67b`, source version **0.1.62**.
- Existing stable owner-private lock inode, atomic temporary file+fsync+replace+directory fsync, concurrency and restart tests retained; read-only inspection never creates lock or data and refuses orphaned/untrusted hardlinks. First CI negative legacy UTF-8 test fixture repaired without loosening lock invariants; RMCP-F-0064/#0065 SOURCE_MERGED.
- Exact-head validation [#39473776219](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/39473776219), clean Ubuntu [#39473776085](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/39473776085) and attribution [#39473776100](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/39473776100) all SUCCESS. This is a source-only state guard, not power-loss qualification or authorization to advance watcher cursor.
- #531/#615 remain OPEN for actual operator evidence; #616 quarantined cursor and #617 separately authorized replay are not active. Central six-role original serving v0.1.38 remains unchanged; #669/#509 correct-host physical A6 and Fabric #1617/#942/#943/#924 still WAIT.

---

## 2026-10-20 — #531 source v0.1.61 MERGED, operational watcher WAIT

- [PR #780](https://github.com/Blacksp1d3r/runner-mcp/pull/780) v0.1.61 SOURCE MERGED `07ff88dfa34586fbfcc515b666b5482e43594fb5`; exact-head validation #39470630553, clean Ubuntu #39470630582 and attribution #39470630605 ALL SUCCESS. Missing quarantine inspection now reads noncreating (O_RDONLY, private path checks); writer/actual watcher unchanged, Failure Museum RMCP-F-0063.
- Parent #531 OPEN: draft crash-atomic #615 / PR #618 exists but remains unmerged/stale and must be reconciled, followed by #616 safe cursor and #617 authorized replay. Source main 0.1.61 != original serving 0.1.38; six roles/A6/A7 and original-client ACK gates unchanged.
- [Canonical #531 handover](https://github.com/Blacksp1d3r/runner-mcp/blob/main/handover/RECOVERY_531_READONLY_20261020.md).

---

## 2026-10-20 — #664/#665 autonomous source v0.1.60 MERGED; connected 0.1.38 still WAIT

- #664 PR #778 merged `55c26eaef2d7f08a1f84c1c79df03898fd413842` v0.1.59 (pure legacy tools/list input/output schema compatibility check, failure RMCP-F-0061 fixed, exact-head CI all green).
- #665 PR #779 merged `2188fd3f89d05ae6c50d0fbe5a3216de0dc5a740` v0.1.60 (pure tool mismatch cooldown reset after source-observed READY, failure RMCP-F-0062, exact-head CI all green).
- Source-only: no historic customer-wheel attestation, real serving identity, live dispatch, notifications, result/ACK or host update. Parent #664/#665 OPEN. #669/#509 and Fabric #1617/#942/#943/#924 physical evidence still WAIT, existing six roles untouched.
- Canonical handover: [#664/#665 source guard acceptance](https://github.com/Blacksp1d3r/runner-mcp/blob/main/handover/COMPATIBILITY_664_665_20261020.md).

---

## 2026-10-20 — #509 v0.1.58 source MERGED / #669 six-role live attestation WAIT

- Runner-MCP [PR #776](https://github.com/Blacksp1d3r/runner-mcp/pull/776) source MERGED as `22b3efc6a35375c9033f5aa71a8f9930fcf64843`, version **0.1.58**. Existing fixed 11-key A6 private repair and diagnostic now reject multiply linked private `runner-mcp.env`; two synthetic no-write hardlink negative cases. Exact PR head `efaa513dc7424eaff74f851ec3be22e6326c3a19`: release reservation, Ruff/pytest, full validation + demo + built artifact [39464803945](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/39464803945), clean Ubuntu [39464803996](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/39464803996), attribution [39464804237](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/39464804237) ALL SUCCESS. Failure Museum RMCP-F-0060 source mitigated; NOT a live rollout.
- #669 provenance source guards from earlier merges remain fail-closed. Independent read-only original-client check: live six-role central MCP remains `0.1.38` installed and serving, `active_build_provenance_verified=false`, source revision + wheel digest NULL, `self_update_ready=false`; Doctor FAIL 2 (`source_baseline_drift`, `active_revision_unavailable`). Existing Fabric bridge READY read-only revision `51c37f1eac65951e15a5122b89f368aa6e18c1f5`; A6 prepare/probe false, local fixed A6 keys 0/11. Release mirror state `storage-bindings-unconfigured`; does NOT prove off-target A6.
- [#739](https://github.com/Blacksp1d3r/runner-mcp/issues/739) source PR #746 0.1.56 (`6cf550b4f1087a2996d8c810c375a8636412f4ec`) and PR #748 0.1.57 (`53e6c1af05b58624cb5ccb5a5f3a43f770af4899`) **MERGED**, exact-head CI green; source-only in-memory 33/33 independently pinned roster and complete Q7 bundle checks. No trusted signer or host import; parent still OPEN. RMCP-F-0059 release reservation race recovered without force.
- Fabric #1617 (source PR #1637 merged), #942 and #943 must still establish **actual independent** A6 journal storage with surviving target-loss readback and autonomous disconnected six-role A7 revert. Runner-MCP #669 needs an independently signed, correct-host serving six-role loaded wheel/source witness and protected *old* generation before any cutover; #509 existing private 11-key repair can run only after both physical owner-private roots qualify. Fabric #1556/#1563 require original-client terminal result+durable ACK, AIfordable #585 relay continuity. Only Fabric #924 may authorize ONE guarded update. Do not create a new relay/updater, use OIDC/MFA, execute an unsafe restart or mutate the six active services.
- Exact owner/gate checklist: [handover/ISSUES_669_509_OPERATOR_GATES_20261020.md](https://github.com/Blacksp1d3r/runner-mcp/blob/main/handover/ISSUES_669_509_OPERATOR_GATES_20261020.md).

---

## 2026-10-20 — owner-confirmed MCP boundary and cockpit integration (docs only)

AIfordable remains the **business/customer/registration/infrastructure desired-state cockpit**; Runner-Fabric owns the **technical F10/F17 Cockpit and sole technical orchestration**; Runner-MCP remains the **bounded authenticated execution/bridge** product, not a competing scheduler, updater or relay. The AIfordable-owned relay is an existing transport with Fabric work/result/ACK semantics. Preserve current MCP and A6/A7 recovery paths, fixed host/worker/work-unit workspace capability bounds, and existing six serving roles. Reference: https://github.com/Blacksp1d3r/AIfordable/blob/main/docs/CROSS_PRODUCT_ROLE_BOUNDARIES.md. No release, live host change, 0.1.38 promotion, or Agent Bus/Claude/Qwen approval claimed; #669/#509 and Fabric #924 remain gated.

---

## 2026-10-20 — checkpoint: #725 source test hardening complete, update gates stay WAIT

- [x] Source PR #744 (520+ synthetic stateless GitHub App tokens, wrappers and truncation) merged `67ebbff96dd6708fff927663c01bf0563258550b`, exact-head validation #39455822522 and attribution #39455821986 SUCCESS. No source version increment and no host mutation.
- [ ] #725 downstream consumer boundary review; no production incident claimed.
- [ ] #669 correct-host six-role serving-wheel/source identity and previous-generation escrow; #509 A6 bindings through existing fixed routine; Fabric #1617/#942 independent off-target A6, #943 actual offline rollback, #924 single-node controlled cutover and Fabric #1556 original-client result/ACK plus Fabric #1563 Black admission and AIfordable #585 relay continuity; AIfordable #609 is a separate Claude/Qwen workspace child. Live 0.1.38 remains not update-ready.
- [ ] #739 source PRs #746/#748 remain unmerged and version-stale; reconcile serially with next independently available version and full exact-head CI. These pure source checks never authorize a live import or update.

---

## 2026-10-20 — source 0.1.55 MERGED; original central 0.1.38 still WAIT

Runner-MCP [#770](https://github.com/Blacksp1d3r/runner-mcp/pull/770) SOURCE MERGED 0.1.54 (`247c3803ac8050c41c96eea93197fab0f3951129`): existing authenticated Fabric bridge fixed zero-input A6 local storage read. This only reads existing A6 journal and never proves physical independence or update authority.

Runner-MCP [#773](https://github.com/Blacksp1d3r/runner-mcp/pull/773) SOURCE MERGED 0.1.55 (`701f507ac00754c6e869448ed3158dcfb4eac539`, tested PR head `fe00e88e771d2d2876b9f1829972438f1e106435`): zero-arg `serving_process_observation_preflight` observes only three already-imported Python modules on the serving MCP process and its loaded-vs-installed-version comparison. 100 registered tools in the exact lock file; release admission, full Ruff/pytest, built wheel, clean Ubuntu proof #39451435006, five-minute demo #39451433529 and attribution #39451434036 ALL SUCCESS. Never emits paths, PIDs, tokens, source SHA or wheel digest; `activeBuildProvenanceVerified=false`, update/dispatch false for all results. Failure Museum RMCP-F-0058 SOURCE_MERGED_LIVE_UNVERIFIED.

**Critical bootstrap dependency:** live first-party central remains 0.1.38 with no actual imported wheel/source attestation, A6 0/11, `self_update_ready=false` and existing six roles. New 0.1.54/0.1.55 tools are SOURCE, not callable from old 0.1.38, and cannot be prerequisites that only self-certify a future upgrade. Correct-host independent owner-controlled pre-admission witness for the old installed/loaded baseline and immutable previous release escrow must be established through existing authorized Fabric/host operator authority under #669/#924; absent that stay WAIT. Fabric #1617/#942 independently off-target physical A6, #943 disconnected actual A7 rollback, original-client result + durable ACK #609 remain separate blockers. No second relay/updater, unsafe backdoor or OIDC/MFA reintroduction.

---


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

## 2026-10-19 — #662/#669 actual source release-lane reconciliation (not installed)

- Version collision still active: merged main 0.1.41 (#751), owner #743 still open 0.1.41 and not mergeable, stacked #745 open 0.1.42. The single release steward must reconcile #743→0.1.42, then #745→0.1.43 (only if main remains otherwise unchanged); no other worker may skip them. Draft #750 signed serving-statement input preflight has NOW been merged forward **in its own branch** to source main 0.1.41, retaining #751/#752, with proposed v0.1.44; exact-current-head CI still pending. Draft #753 next-patch release admission source candidate v0.1.45 has all 3 workflows SUCCESS (exact head `6a2c880de56947f1247d6ecd27e8ade492d55e19`); source check SKIPPED correctly while draft. Neither is merged to main or running on a host.
- Source #753 implements fail-closed normal next-patch, GitHub API checked own source/competing READY PRs twice, deterministic lowest PR priority, wrong head/base/version/refusal and no-proxy/no-redirect bearer GET. **A real atomic check-to-merge lock is NOT implemented**; GitHub branch-protection GET returned 403 so required-check and up-to-date merge policy must be separately configured and independently verified by an authorized administrator. Do NOT enable merge queue with this workflow until `merge_group` admission is added/qualified. Source Failure Museum `RMCP-F-0047` currently lives on draft #753.
- Central first-party installed Runner-MCP 0.1.38 still returns active source/wheel null and self_update_ready=false; AIfordable relay/worker original-client ACK and Fabric A6/A7 operator-guarded single-target deployment remain external proof gates. No live deploy, new tunnel, credential or filesystem action performed.

---

## 2026-10-19 — Single Runner-MCP release steward; coordinate Fabric and Agent Bus

Runner-MCP-specific [CONTROL_PLANE_SINGLE_FLOW](https://github.com/Blacksp1d3r/runner-mcp/blob/main/docs/coordination/CONTROL_PLANE_SINGLE_FLOW.md) aligns source #669/#341/#747, worker #609, Infra Authority #428, relay/ACK #585 with Fabric #924/A6 #942/A7 #943. Main 0.1.41 merged workspace #751 (`601afc95`), but existing #743 ALSO 0.1.41, #745 stacked 0.1.42 and #750 0.1.43 draft: **real duplicate release reservation** not prevented by existing `scripts/check_release_version.py`. Proposed order if main stays unchanged: respective owners reconcile #743→0.1.42, #745→0.1.43, #750→0.1.44; recompute on main advance and require exact-head release/version/pytest/Ruff/build/demo/Ubuntu/attribution before any merge. A deterministic collision-and-sequential-patch CI gate is new, scoped source child **NOT YET IMPLEMENTED**; do not hijack another team's version/branch. Source work parallel; Fabric owns one-at-a-time host activation/recovery lease and AIfordable owns correct-host identity, existing relay and original requester digest ACK. Central live 0.1.38 active source/wheel unverified, `self_update_ready=false`, Fabric mutations disabled, so **no** remote workspace prepare, host update, credentials or old self-update marker edit. Prior A6/A7 physical subset proof is retained. Planned sequence R(unique source release) ∥ H(identity/relay) → P(proven live generation) → A(Fabric guarded recovery) → U(one host) → K(requester ACK) → W(local worker workspace) → D(dispatch).

---

## 2026-10-19 — Release version guard corrected / exact-head CI pending

2026-10-19 #669/#341 update: PR #742 source candidate 0.1.40 corrects required release-version gate (all four shipping version fields synchronized, changelog), adds fail-closed missing revision-provider metadata containment and six synthetic negative tests. Exact-head automated GitHub-hosted CI pending; no physical server update or attested active source. First-party serving 0.1.38 remains two Doctor FAILs, self_update_ready=false; independent correct-host provenance/manual-baseline/ACK plus Fabric A6/A7 remain external admission blockers.

---

## 2026-10-19 — #669 runtime_doctor provenance child PR #742 IN PROGRESS

First-party read-only MCP 0.1.38 returns `self_update_ready=false`, historical source checkout != historical installed self-update commit, unverified active source and artifact digest, two Doctor FAILs. This is a **correct refusal**. Source-only PR #742 has negative tests and a narrow provider-metadata exception containment fix (RMCP-F-0045, synthetic bug; no live incident claim). Independent trusted serving-generation/host witness and separately accepted manual-install baseline still unavailable. Detailed gate design: `docs/diagnostics/components/01-runtime-self-update/SERVING_GENERATION_ATTESTATION.md`; reuse existing #669 offline validators. Exact PR-head CI pending, no merge or deployment authority. Source merge is separate from physical #669/#341/#590, Fabric A6/A7 #942/#943 and original-client ACK.

---

## 2026-10-17 — #735 source merged, Black Agent Bus admission remains WAIT

Runner-MCP [PR #737](https://github.com/Blacksp1d3r/runner-mcp/pull/737) SOURCE MERGED `d2dce33c436794fb90ce78cb12d1a7f27b4243d3`, exact source head `c620db7c6417ae7a306862c8fd9292f7dc6e0f0b`, validation/Ruff/3326 pytest/artifact/demo #39061856248, clean Ubuntu #39061856254, attribution #39061856279 all SUCCESS. v0.1.38 is UNPUBLISHED/NOT INSTALLED; central active 0.1.27, new Black still non-serving staged 0.1.30. Read-only `agent-bus status` distinguishes missing owner-private base as `base_config_not_initialized` and gives local setup guidance; symlinks, bad owner/mode and partial private files deny safely. Valid base without relay remains `not configured`. No bearer generated, runtime installed, port opened or website deployed. Failure Museum RMCP-F-0044 source fixed after observed CI failure; no confirmed real credential exposure.

Physical Black stage `stage_complete=true` was already done by operator (Runner-MCP #723/Fabric #1562 CLOSED), but `service_activation=false`, `relay_enrollment=false`, `original_client_ack=false`. Owner-private real project selection/base setup, AIfordable #585 unique CAS-fenced issuer credential and Fabric #1563 target-specific durable result→original-client ACK remain WAIT; A6/A7 and all external services stay blocked. Runner-MCP #735 remains OPEN for approved stage-closeout UX/receipt compatibility plus physical setup proof; do NOT silently add a field to signed stage v1 marker, repeat original stage, copy another host's token, or confuse central heartbeat with Black.

---

## 2026-10-17 — Black non-serving stage PHYSICALLY DONE; source #732 fix merged; A2 Agent Bus WAIT

- Operator-attended FIRST-HOST Black recovery `runner-mcp/local-host-stage-result/v1` at staged pinned 0.1.30 returned `stage_complete=true`, `service_activation=false`, `relay_enrollment=false`, `original_client_ack=false`. Owner/physical stage #723, failure #716 and Fabric #1562 CLOSED (supersedes outdated blocked snapshots below). This receipt is NOT an authenticated first-party host enrollment nor proof of remote service.
- Black local `runner-mcp agent-bus status` reported private config unavailable. Owner read-only inventory proved local base config directory/env/projects absent: missing FIRST-HOST setup, NOT failed stage or down relay. Source UX issue #735 open; never auto-generate bearer or falsely reuse other host configuration.
- Independent preventive recovery checkout fix #732 was merged via PR #734 from reconciled main: 0.1.37 unpublished candidate; bytecode-free direct CLI + real subprocess tests, visible dirty guard and Failure Museum RMCP-F-0043. Exact-head validation #39060829601, clean Ubuntu #39060829552, attribution #39060856703 SUCCESS; PR #734 squash merged `4ac5d0c85674f91ed882588cb1b323deefc73e11`; candidate not installed. Superseded conflicting #733 CLOSED unmerged.
- Next executable now that #734 is merged: #735 source-only NOT_INITIALIZED status, safe staged next-step/runbook, synthetic denials; then owner-attended local setup ONLY after real project path/UID approval, separate AIfordable issuer CAS identity, target-bound command→result→original-client ACK under Fabric #1563. Central serving 0.1.27 unrelated and Fabric mutation/execution disabled. No Black site, HDD, DNS, tunnel or Claude activation.

---

## 2026-10-17 — Fabric Releases exact metadata gate source complete; local importer remains WAIT

- `COMPLETE / SOURCE_ONLY`: Runner-MCP PR #729 merged `de7a0d7b5d51a27949cb6868125a4636411178e5` from head `75004ae076e3d3c77779a7c0a0bef3e16c5d4c02`, all attribution #39059117322 / clean Ubuntu #39059117379 / validation #39059117347 terminal SUCCESS. Candidate version `0.1.35` is **NOT an installed runtime or published public package**. New `release_assets_readiness` validates exact fixed Fabric GitHub Release tag+commit ref, prerelease source and bounded unique 33-style asset name/digest metadata. Returns `mutation_authorized=false, download_performed=false`. Existing Actions/local update consumer preserved.
- `WAIT / NEXT SOURCE DEPENDENCY`: protected first-party Release **file-body** downloader, exact 33/33 SHA256 manifest verification, unique private local-custody atomic importer, wrong-domain/redirect/token stripping and Q7 source pin negative tests. Preserve original updater, no cross-host private tokens. Then separately authorized same-host Fabric Q7 target staging, release archive, rollback, original-client 3x NON-RUN ACK/lease/fence.
- `COMPLETE / SOURCE_ONLY` security #730/#731: existing GitHub token-mask regex could leave synthetic `ghs_` suffixes after separators; candidate `0.1.36` head `4414524ce926ea7cea5949c29f8e663432a13531`, exact-head validation #39059688875, clean Ubuntu #39059688876 and attribution #39059688921 all SUCCESS, squash merged `022b9e24e15e116c639aef8e6227f74e531aae4b`. Failure Museum RMCP-F-0031 indexed; no authentic credential leak or host deployment established. No actual customer credential incident claimed.
- `BLOCKED / PHYSICAL`: lab older installed Fabric and coder worker have not changed; central loopback can't provide actual target proof. Independent mirror unconfigured; GitHub release is distribution, not an independent backup. No disk formatting or unapproved backend release activation.

## 2026-10-17 — RMCP-F-0030 source diagnostic complete, physical Black recovery WAIT

First new Black non-serving physical bootstrap FAILED (`existing_installer_failed`, original staged venv pip RC1). Canonical failure #716 remains OPEN/UNKNOWN_ROOT_CAUSE. RMCP source #718 `diagnose` read-only synthetic-verified and merged PR #719 `e336735f1f249971a93e3666ee46387953cc377e`, tested head `1b49e3052919efda1c61c857a52de2b94261ebdd`, CI validation #39045168201, Ubuntu #39045168205 and attribution #39045168175 SUCCESS. Candidate 0.1.30 source UNRELEASED/NOT DEPLOYED; no source merge repairs OS. Next physical safe evidence: on Black inspect Ubuntu Python-venv/pip-wheel package installation (read-only), independently verify exact root cause, approve a new isolated pinned stage generation (never original failed prefix), then Fabric #1562 and #1563 genuine authenticated ACK/recovery. No HDD format, site release or Claude activation.

---

## 2026-10-17 — #718 local failed-stage diagnostics, no Black retry

Operator's first new Black physical stage returned `existing_installer_failed`: venv exists but observed venv pip exited 1 and Runner-MCP executable/completion marker absent. Canonical Failure Museum RMCP-F-0030 = #716; physical owner Fabric #1562 BLOCKED; downstream Agent Bus #1563 BLOCKED. Fix source-only #718 adds **read-only, same-host, manifest-bound `diagnose`** with no attempt to execute the partial venv or infer pip root cause. Candidate source metadata `0.1.30` pending exact-head CI/merge, NOT installed/published. Physical recovery still requires read-only Ubuntu distro/venv diagnosis and separately approved new-stage custody; never silently retry or erase partial stage.

---

## 2026-10-17 — F30 Black one-time local bootstrap SOURCE COMPLETE

Bounded issue #713/PR #714 local first-host non-serving installer source MERGED `a2d34dc80550ef744acf0ff927344b000a832dcc`; tested head `68e569d7964fe92abd8516a9cd5a6144f5f8fb97` with exact CI validation #39036840912, clean Ubuntu #39036840935, attribution #39036840862 all SUCCESS. The new script reuses original `install.sh`, no fresh generic remote agent and no deployment authority. Physical stage not yet executed; 0.1.29 is unpublished source only.

Next dependency: operator-local Black machine/source/installer pin and rootless stage → existing first-party Runner-MCP/Agent Bus owner-private config and exact local process/host attestation → relay request/result/original-client ACK and recovery evidence → managed protected site release (AIfordable #584, Runner-Fabric #1554/#924). No package transfer via unmanaged host-control route, no format of previously ext4-mounted HDD, no claimed Claude dispatch.

---

## 2026-10-17 — #713 new Black physically attended first-party bootstrap source

Child #713 / PR #714: implement operator-local NON-SERVING, existing `install.sh` based exact-source first stage, guarded machine-id digest and canonical `AF-HOST`/runner-subject manifest, explicit plan SHA acceptance, no privileged/root operations or automatic credential/relay enrollment. Tests and local instructions source-only. Repo shipping-version policy requires synchronized source-only candidate 0.1.29 (not published/deployed). First CI blocked as expected on version gate; updated branch must independently pass all exact-head CI before merge.

Post-source dependencies (separate children and physical approval): valid fixed Black asset owner/host receipt in AIfordable #428 -> operator-local source-stage from reviewed exact commit -> private configured Runner-MCP + existing Agent Bus worker/Fabric slots -> authenticated receiver and actual per-request original-client ACK via AIfordable #585/Fabric #1556 -> independent rollback and host update #924/#942/#943 -> immutable AIfordable public-web release #584 and existing Cockpit #936. No other route; Black HDD already mounted, do not reformat. Claude dispatch remains separate WAIT.

---

## 2026-10-17 — First physical Runner-MCP upgrade ACTIVE 0.1.27, rollback timer canceled

- F30 PHYSICAL FIRST-NODE upgrade step now **DONE on attended host**: normal isolated installer with dependency resolution, six managed cron pins switched, and current original-client MCP responses after temporary fallback timer cancellation confirm 0.1.27. Retained old executable and crontab. Do NOT repeat installation or claim fleet complete; previous 0.1.9 runtime observations are historical.
- Still **OPEN/BLOCKED FOR FUTURE AUTOMATIC UPDATES**: independently verified current wheel/source signature and serving generation #669, correct-host attestation, self-update baseline/activation drift, physical independent A6 off-target journal #942 and A7 rollback + original-client ACK #943, scoped fleet rollout #924. `self_update_ready=false`, two doctor failures, Fabric bridge read-only/mutation disabled. Temporary one-off rollback timer canceled by operator, NOT a persistent A7 supervisor.
- Next highest-value work is preserving active 0.1.27 and old 0.1.9 escrow, read-only independent provenance/custody and safe supported baseline repair; defer any further deployment until separately qualified. Do not delete/move active staged venv merely due to staging directory name, as cron pins reference that path.

---

## 2026-10-17 — Fresh original-client A6/F30 read-only verification (NO host mutation)

Connected Runner-MCP still reports installed distribution `0.1.9`, `source_revision=null`, `artifact_digest=null`, `active_build_provenance_verified=false`, `self_update_ready=false`; no active update, pending restart or install recovery. `runtime_doctor` now reports two failures: `source_baseline_drift` and `active_revision_unavailable`. Its `fabric_a6_binding_state=pass/not_configured_0_of_11` is an optional diagnostic classification, **not** evidence that A6 is configured. Fabric bridge preflight is read-only READY, but `a6_prepare_available=false`, `synthetic_probe_status_available=false`, `mutation_enabled=false`; Fabric operational snapshot is degraded, relay evidence unknown and execution/mutation disabled. Both canonical Fabric remote/local update-readiness calls returned unstructured connector errors: classify as UNKNOWN, never APPROVED or a safe update path.

Immutable GitHub `main` package metadata remains `0.1.27`, adding required runtime `cryptography>=44,<51` compared with running 0.1.9 provenance-associated source. Existing `--no-deps --no-index` self-update cannot resolve this changed dependency contract regardless of repairing the revision-attestation gate. **Do not call self_update, A6 prepare/finalize or alternative update controls on the shared serving node.** Reuse the existing authorized attended dependency-resolving **isolated-prefix** installation flow (both separate install root and separate BIN_DIR), while preserving the actual old launcher/wheel and independent recovery. Only qualify a one-node controlled activation after real process/launcher/build provenance, independent restore and original-client result+ACK are proven. No new code release/version/updater PR is authorized in this lane until that actual upgrade is complete.

One read-only host sample showed elevated CPU load (1-minute 32.13 on 12 logical cores, CPU PSI some avg10 72.94%); this is transient telemetry, not proof of a process/root cause. No expensive host tests were run. A6 #942, A7 #943, Fleet #924, MCP #341/#669 and AIfordable #428 remain open and no physical A6 journal, rollback, activation or original-client ACK was claimed. This checkpoint is documentation/evidence only and respects the operator's freeze on further updater code/version churn.

## 2026-10-16 — F30 priority override: ACTUAL installed upgrade, source version lane paused

- No further release-version increases, update code PRs or new updater implementation until an actual qualified update of the existing live control path is achieved. Reuse already merged source v0.1.27 and existing installer; don't duplicate completed #706–#709.
- FIRST proven source gate: original connected v0.1.9 lacks active build SHA/digest; self-update historical marker exists while active revision deliberately unavailable, so self_update_ready=false. Second independent gate: v0.1.9 -> v0.1.27 adds required cryptography runtime package; exact dependency contract differs, so docs/SELF_UPDATE_COMPATIBILITY.md mandates attended dependency-resolving bootstrap instead of no-deps self_update. Neither a forced marker edit nor a new release version solves this.
- Host operator currently unavailable. Execute bounded read-only actual serving process/launcher evidence and baseline escrow when present, then one separate isolated exact-source package/bootstrap check, then independent recovery and real-client ACK before the single-node cutover. Fabric A6/probe is absent on active peer, mutation disabled; live control update remains WAIT, no false green. Target pin may be source merge `265dc1fc0866e35df07b05f6bcf3addee4f8dafa`, not an unapproved CI artifact.
- Completion means same original authenticated client sees the new loaded build/tool catalogue, real result + ACK and independently recoverable prior service, not just a successful wheel build/CI merge or cron running. Keep Runner-MCP #341/#669 and Fabric #924/#942/#943 open; GitHub issue receipts authoritative.

---

## 2026-10-16 — Fleet diagnostic source tests land; next actual update admission

- Runner-MCP #590 source read-only errors #706 (0.1.25) and #707 (0.1.26) MERGED, full exact-head CI+installer+attribution GREEN. Their actual MCP tool-response shapes are covered by merged tests-only #708, exact CI validation #38933713969 + attribution #38933714024 GREEN. These are diagnostic/original-client **synthetic MCP** tests, not independent active-server identity or release permission.
- A6 #509 dangling-symlink state-root security patch #709 v0.1.27 MERGED `265dc1fc0866e35df07b05f6bcf3addee4f8dafa`, exact HEAD validation #38934210559, Ubuntu #38934210595, attribution #38934210533 all SUCCESS; original historical #655 closed unmerged superseded. Failure Museum RMCP-F-0026 SOURCE_FIXED_LIVE_UNQUALIFIED, no duplicate A6 repairer.
- Operational F30/Runner-Fabric #924 STILL BLOCKED: serving Runner-MCP 0.1.9, active build revision/wheel digest unavailable, self_update_ready=false; live Fabric read-only handshake succeeds but A6/probe absent and mutation_enabled=false. Cross-host attestation #669/AIfordable #428 plus A6 journal #942 / A7 physical ACK+revert #943 are true release gates. Preserve source/CI progress without remote unqualified update or independent rollback timer deployment; operator has deferred timer work until customer phase. Windows offline 1 TB target is not yet a qualified independent recovery copy.

---

## 2026-10-16 — #664 legacy source tool-name retention test guard completed

- Tests-only #702 freezes sampled 14 legacy callable signatures; #705 freezes all 95 existing v0.1.24 source-registered MCP tool names via AST, including optional registrations; both MERGED after exact-head CI green. #705 squash `67770dd641c342c561e7631fe20f39057d2a019a`, validation `38905411566`, attribution `38905411379` success.
- Conflicted #704 closed unmerged after separate main handover update overlapped its markdown changes; regression unchanged in clean branch #705, Failure Museum RMCP-F-0042. Do not duplicate or retry #704.
- These are current SOURCE baselines, not released 0.1.9 JSON schema/authorization/response semantic compatibility evidence. Parent #664 still open for exact released legacy package snapshots, N/N-1 and named-v2 client contract tests plus operator commercial support schedule.
- Functional #333 source-only v0.1.24 opt-in expected tunnel doctor merge #703 CI green; not wired to a trusted private host sensor, no tunnel autostart or actual remote ACK. Rollback timer deferred until customer rollout.
- No production/credential/tunnel/host mutation. Source-only completion does not authorize a release.

---

## 2026-10-16 — #333 opt-in expected connector tunnel diagnosis, source candidate v0.1.24

- Following source-only #664 sampled legacy signature regression guard PR #702 MERGED tests-only (no version bump, current main source 0.1.23), new independent #333 child makes existing typed tunnel readiness evidence visible in actual `runtime_doctor` when operator explicitly marks tunnel expected.
- `tunnel_expected=False` default changes no old tool response; opt-in read-only evidence provider returns only stable reason codes with warn when process missing, authentication/routability unknown or collector absent. No probe, secret read, process scan or start/restart.
- Private host authorized evidence collector/reboot-safe launcher and same-original-client live proof remain separate. Rollbacktimer still deferred until customer phase.
- Source candidate 0.1.24, exact-head CI required. Parent #333 stays OPEN.

---

## 2026-10-16 — #664 sampled legacy MCP contract signature CI guard (tests-only)

- A new independent test-only child `roadmap/children/664-legacy-callable-signature/` pins a grounded subset of present 0.1.23 MCP tool names, registrations, parameter/default and return annotations. On drift the actual source AST test fails CI. No shipping tool code/version change.
- This is deliberately **not** a historic v0.1.9 customer wheel/runtime input/output schema snapshot. Source-only baseline must not be used to assert full N/N-1 support or actual client compatibility. Parent #664 stays open for authenticated released wheel catalogue capture, generated JSON schema/semantic regression, commercial supported release trains and original-client proof.
- No host or customer action, rollback timer deferred. Full exact-head CI necessary.

---

## 2026-10-16 — #665 tool identity three source children integrated through v0.1.23

- #699 v0.1.21 pure stable tool contract classifier (including RMCP-F-0038/0039 fixed); #700 v0.1.22 bounded duplicate tool ID/name and mismatch preflight; #701 v0.1.23 pure sanitized typed mismatch alert digest/cooldown all SOURCE MERGED with exact PR HEAD full validation, clean Ubuntu and attribution SUCCESS.
- Latest #701 squash `10501c1d28ef050ecfc61f7b341487e7ead47d2b`; tested HEAD `88b8c81d15a664998b988ef02201f74875593090` CI validation `38898938032`, Ubuntu `38898937966`, attribution `38898937757` SUCCESS. Source child STATE COMPLETE_SOURCE_ONLY.
- Still MISSING and NOT claimed: authenticated actually-serving source/build/tool schemas, independently protected fleet customer scope and host/tenant policy, actual tool dispatch enforcement, durable alert dedupe and real delivery/ACK. Synthetic trust flags, hashes, namespaces and IDs do not themselves confer authority. Parent #665 remains OPEN.
- Older customer versions #664 need explicit release contract compatibility fixtures and operator commercial support window before rollout; avoid making new tool availability break legacy clients. Actual connected MCP still 0.1.9, source 0.1.23 not installed. Rollback timer deferred until customers.
- No private host changes, tunnels, credentials, services, workers, model billing or deploy in this source session.

---

## 2026-10-16 — #665 bounded mismatch alert digest source child 0.1.23

- #699 v0.1.21 contract classifier and #700 v0.1.22 duplicate tool inventory rejection source merged with exact-head CI SUCCESS.
- New distinct child `roadmap/children/665-tool-alert-dedupe/`: pure grouped, deterministic per-opaque-scope/tool/reason alert summaries, cooldown and bounded event limits, no network/notifications or persistent state. Synthetic timestamps and scope digests require independently trusted upstream evidence.
- This is not alert delivery, real issue confirmation or runtime authority. Fabric fleet inventory, customer grouping, authenticated serving process and rate-limited notification/ACK remain parent #665 dependencies. No host, keys, tunnels or customer-phase rollback timer actions.
- Candidate v0.1.23. Exact-head CI mandatory.

---

## 2026-10-16 — #665 tool identity comparator and collision preflight source MERGED

- [#699](https://github.com/Blacksp1d3r/runner-mcp/pull/699) pure tool contract metadata classification (v0.1.21) source merged after exact HEAD validation/Ubuntu/attribution pass. RMCP-F-0038 Ruff fixture and RMCP-F-0039 strict bool trust flags source-fixed and green.
- [#700](https://github.com/Blacksp1d3r/runner-mcp/pull/700) pure bounded inventory collision/name/schema consistency (v0.1.22) merged squash `26c135952b2786e498871c68b37dcdb1900a26ea` after exact head `b7457faaf6e38307af2c749954764a2991278a3c` validation `38898006036`, Ubuntu `38898006091`, attribution `38898006047` all SUCCESS.
- No active server handshake, dispatch policy or alert emission authority comes from these helpers. Main 0.1.22 is SOURCE ONLY; client 0.1.9 still has null verified active SHA/digest. Remaining #665: independently witnessed live registry + signed version/schema identity, real caller/host/tenant dispatch checks and bounded alert dedupe; legacy #664 remains distinct.
- No host, tunnels, keys, cron, paid worker dispatch or customer-phase rollback timer mutation.

---

## 2026-10-16 — #665 inventory collisions, source candidate 0.1.22

- PR #699 v0.1.21 pure tool identity contract comparator MERGED `70201f6ac138ce1fd1dfd3e91ed4f1f7c4b6fd08` after full exact-head CI GREEN. RMCP-F-0038 test lint and RMCP-F-0039 nonbool trust flags fixed and marked COMPLETE_SOURCE_ONLY.
- New bounded child `roadmap/children/665-tool-inventory-collisions/`: source-only structural per-inventory stable ID/name collision detection and bounded expected-vs-witness contract list matching, with synthetic negative tests.
- This is NOT authenticated actual-serving inventory or tool dispatch/permission enforcement. Separate root registry/provenance policy and caller+host fencing remain gates. Legacy compatibility #664 and operational source v0.1.9 unaffected.
- Candidate 0.1.22. Exact-head CI required. No privileged host, credentials, tunnels or delayed rollback timer work.

---

## 2026-10-16 — #665 stable tool identity source-only comparator, v0.1.21

- FASTER-13 #383 phase 1a source 0.1.20 merged, real loopback RTT remains separate authorized measurement.
- New bounded child `roadmap/children/665-tool-identity-classifier/` classifies trusted expected-vs-authenticated observed tool contract records before any dispatch; typed reasons for unknown/disabled/version/schema/stale/transport/untrusted identity. Stable namespace `com.aifordable.runner-mcp` and stable ID are metadata only, NOT authentication.
- No MCP catalogue/dispatcher, tool permissions, source lineage, host, network or alert delivery modified. READY is comparison-only and never authorizes a call. Future parent #665 work still requires independently witnessed active serving build/registry/freshness/caller+tenant policy and rate-limited alerts. Legacy #664 remains separate.
- Source candidate 0.1.21, exact-head CI required. No production update, rollback timer remains deferred.

---

## 2026-10-16 — FASTER-13 #383 reproducible local JSON baseline, source-only

- #681 functional source PRs #695/#696/#697 all merged, exact-head CI green; #697 squash `1bbb46ce9061e7f453532e5000fb2a0995ee7140`, Failure Museum RMCP-F-0036 complete. Connected live MCP 0.1.9 remains unchanged, and peer intermittent #681 remains open.
- Independent performance child `roadmap/children/383-local-fastpath-benchmark/` candidate source 0.1.20: pure local synthetic JSON-RPC JSON encode/decode times for 128B/4KiB/64KiB payload, p50/p95/p99, message bytes, throughput; deterministic 500ms polling detection model, no network/work/probe.
- This is NOT measured actual MCP latency/CPU, push delivery or faster code execution. Next phase needs separately authorized isolated same-host loopback MCP RTT with trace/correlation matching before optimizing HTTP pooling vs UDS/event notifications. Keep original security/session/replay/fencing.
- Rollback timer deferred to customer rollout per operator. No production/tunnel/host actions.

---

## 2026-10-16 — #681 host inspection failure without implicit network preflight

- Two functional source fixes merged: #695 continuity unavailable (0.1.17) and #696 operational snapshot unavailable (0.1.18) with exact-head CI success. Live original MCP still 0.1.9 until separate update.
- New bounded child `roadmap/children/681-host-inspect-no-followup/`, source candidate 0.1.19, avoids automatic extra Fabric preflight RPC after a failed read-only host inspection. The independently invocable explicit preflight remains unchanged.
- Host inspection failure returns limited `runner-mcp/fabric-host-inspection-error/v1` state unavailable, with only fixed reason category and mutation_enabled false. No retry, new probe, remote host mutation, sensitive exception text or client authorization bypass. Parent #681 intermittent peer issue stays open. Rollback timer intentionally postponed until customer rollout.

---

## 2026-10-16 — #681 functional Fabric snapshot error observability

- #695 continuity-status bounded source change v0.1.17 merged (commit `804be37993da563cdd6ed45872e50573a22b2a48`) after exact CI success. Live original-client 0.1.9 has no new response until a separately authorized rollout.
- New independent source-only child `roadmap/children/681-snapshot-unavailable/` candidate 0.1.18 returns a finite, safe unavailable response for Fabric operational snapshot failures instead of throwing generic internal MCP error; preserving successful snapshot schema and denied audit.
- No additional preflight/network request, no retry on uncertain-effect transport, no secrets/host data, no process/tunnel/rollback changes. Parent #681 remains open for actual intermittent client stability; rollback timer deferred until customer phase.

---

## 2026-10-16 — #681 continuity status expected failure returns bounded unavailability

- Existing live first-party `fabric_continuity_status` errors on unavailable private continuity configuration, while runtime_doctor reports `fabric_continuity_status_configuration_unavailable`. Generic MCP tool error hides the *real first failed condition*.
- New bounded source-only child `roadmap/children/681-continuity-unavailable`, 0.1.17 candidate, leaves the existing read-only launcher/status validation and audit unchanged on success. Expected `FabricContinuityStatusError` returns nonsecret deny-by-default `runner-mcp/fabric-continuity-unavailable/v1`, no external submission/work/mutation.
- Strict reason allowlist, no exception text/endpoint/secret disclosure, no fallback/retry and no host change. Exact-head CI required; live 0.1.9 will not gain this behavior before a separate qualified update. Operator postpones rollback timer until customer phase.
- Parent #681 intermittent host/snapshot instability remains independently open; this addresses specifically continuity-status observability, not the whole bridge.

---

## 2026-10-16 — #669 signature+candidate source chain complete, operational trust authority next

- Source-only PR #693 (0.1.15, Ed25519 detached signed canonical builder schema) and #694 (0.1.16, compose signed proof with manifest/wheel/installed-module/receipt/generation consistency) MERGED after exact-head attribution, full validation and independent Ubuntu CI PASS. Latest source squash #694 `ee019e491c53d1d2b239cc07faa15b9f4fcaed51`. Subchildren STATE marked COMPLETE_SOURCE_ONLY.
- Live v0.1.9 has NULL independently verified active source and digest, intentionally fail closed; offline signatures are not a trusted release, sealing or active build attestation.
- Next dependency chain: independent privileged signer public-key pin custody+rotation/revocation/expiry, manifest issued by approved trusted builder, protected atomic installed generation witness, active process executable/import lineage, six-role independent rollback and A6/A7 original-client ACK. These are not software-only steps and require private custody authorization. #669 remains OPEN/BLOCKED_EXTERNAL.
- Existing #681 original connector snapshot regression is separately owned; latest read-only generic error does not authorize production tunnel or service intervention. No source reimplementation of merged #689–#694.

---


## 2026-10-16 — #669 signed offline candidate chain (source-only 0.1.16)

- #693 Ed25519 detached signature source-only 0.1.15 merged at `e85b15924790d22a90b9a54cef1b55d10379d785` after exact-head validation/Ubuntu/attribution PASS. No independent signer enrollment or live attestation.
- New child `roadmap/children/669-signed-evidence/` composes offline signer and manifest pin/wheel/module receipt/generation consistency, with synthetic tamper negative tests. It NEVER publishes active source/digest or sets active_build_provenance_verified=true.
- After this bounded source child, operator-protected signing identity authority, revocation/expiry, generation/installer sealing, process-executable identity and A6/A7 + original-client ACK remain actual gates. Source merge does not permit production update.

---

## 2026-10-16 — #669 independent builder-key source verification child

- Existing offline receipt, builder digest pin, generation layout and evidence chain (#689–#692) source-merged; connected host 0.1.9 remains intentionally unverified.
- New bounded child `roadmap/children/669-detached-signature/` (candidate source v0.1.15) adds read-only Ed25519 manifest-signature checks conditioned on an OUT-OF-BAND trusted key fingerprint. Strict negatives test changed manifest/key/signature, linked and writable evidence and invalid lengths. No operator trust root is provisioned by this source code.
- Next after exact source CI: operator/privileged independent builder-key enrollment, revocation and signed manifest issuance, then sealed installation with loaded-process generation + A6/A7 rollback/original client ACK. No live service changes by source-only work.

---
## 2026-10-16 — #669 source-only chain complete, trusted serving attestation BLOCKED

- Source children #689 (0.1.11 offline receipt), #690 (0.1.12 externally pinned builder manifest), #691 (0.1.13 generation layout), and #692 (0.1.14 offline evidence consistency) ALL MERGED with exact PR HEAD CI success.
- Last source merge #692 `a7e3bb30d008d655ae5b8c5fdc15813303f84935`; current live MCP remains 0.1.9 with null installed/serving source/digest. Offline source completion does NOT close umbrella #669.
- Operational dependencies next: (1) independently authorized builder SHA pin custody, (2) immutable/sealed installation receipt bound to exact wheel and loaded package, (3) actual process/import generation evidence, (4) independent A6/A7 rollback evidence and authenticated original-client ACK. These cannot be skipped, faked via self-update history, or inferred from module filenames/modes.
- No privileged host mutation, secrets, tunnels or expensive worker dispatch from this source session. STOP at external trust-custody gate rather than creating a false positive active identity.

---


## 2026-10-16 — #669 offline evidence chain, source candidate 0.1.14

- #689, #690, #691 all source merged. The prior versioned generation layout is structural only and does not attest immutable installed bytes.
- New bounded child on `chatgpt/669-offline-evidence-chain-v0114` composes offline evidence and ensures the declared builder source revision and wheel digest match the receipt and generation leaf. Self-controlled pins never establish independent trust; active runtime always unverified.
- Dependencies after this source child: independently trusted pin custody, immutable installer evidence, actual loaded process generation and original-client acknowledgement, authorized A6/A7 rollback. No host changes.

---

## 2026-10-16 — #669 versioned generation layout guard, source-only PR #691

- Offline preflight PR #689 merged 0.1.11; externally pinned builder-manifest PR #690 merged 0.1.12, neither proves installed/serving provenance.
- New source-only PR #691 candidate 0.1.13 checks versioned release generation lexical name, absolute path, linked ancestors, mode/owner with negative synthetic tests. No claim of immutability or loaded server proof.
- Child roadmap/children/669-generation-layout/TASK.md + STATE.md. CI gates required. Follow-up independent builder authority + actual immutable installer and serving-generation witness remain blocked on custody/rollback.

---
## 2026-10-16 — #669 pinned builder-manifest source child 0.1.12

- Offline receipt stage #689 merged as source-only 0.1.11; actual serving runtime remains 0.1.9 with unknown source/digest.
- New child [PR #690](https://github.com/Blacksp1d3r/runner-mcp/pull/690) validates independently pinned manifest SHA-256 and wheel SHA-256, source revision, distribution version and interface digest. Manifest and digest supplied by the same untrusted source **do not establish authenticity**.
- Negative regression vectors include same-version replaced wheel, forged manifest, extra/duplicate keys, symlink artifacts, malformed schema/version/source, and excessive JSON nesting. Failure Museum RMCP-F-0031 tracks hash/parse TOCTOU and duplicate keys.
- Source-only (0.1.12 candidate), no production activation; exact-head CI gates before merge. Next dependent work: approved builder authority and trustworthy pin distribution, immutable release venv, installer custody receipt, active serving process witness and A6/A7 rollback/ACK.

---

## 2026-10-16 — #669 phase-2 offline receipt verification child

- Source implementation [PR #689](https://github.com/Blacksp1d3r/runner-mcp/pull/689) for 0.1.11 candidate: offline wheel+installed-module digest comparator, owner-only atomic create-once candidate receipt writer, negative tests for path/permission/symlink/native module/manifest/fsync/crash/race, and integrated offline demonstration.
- Previous exact-head `93b91686...` validated in CI. Later traversal/race defense requires fresh CI; Failure Museum RMCP-F-0029 records the cause and regression. No merge while newest head unverified.
- NEXT (depends on #669 acceptance): authenticate builder manifest using a trusted independent root, write an actual installer-owned receipt tied to immutable venv generation, then attest loaded serving process with original-client ACK. Source-only receipt bytes do not authorize active identity or production rollout. Fabric A6/A7 ownership separate. No duplicate child/new PR.

---

## 2026-10-10 evening — Runner-MCP #590 loopback bearer egress source fix PR #651 merged

[PR #651](https://github.com/Blacksp1d3r/runner-mcp/pull/651) MERGED squash `68093ab85bee293a8cc7616340d2893d5e4c24a0`, reviewed exact head `d588c72619fc277d8423b680f473c8d62e3c992a`. Commit attribution `38086367280` SUCCESS; full validation `38086367281` SUCCESS (Ruff, **2813 pytest**, built release artifact, clean demo). Fixed `LocalMCPClient._post` standard `urllib.request.urlopen` proxy/HTTP 30x bearer egress risk by using a fixed `ProxyHandler({})` + `_NoLocalMCPRedirects` opener through a single testable `_open_local_mcp_request` seam. Unit negatives cover hostile HTTP(S)/ALL_PROXY environment, redirects 301/302/303/307/308 to off-host and same-host destinations, single-call/no-redirect behavior, sensitive error redaction. Historical bridge tests now inject the bounded seam. Preserves #650 stale-session unknown-effect no-replay and exact build/schema requalification on subsequent separate explicit caller request.

Child `roadmap/children/590-local-mcp-transport-egress/{TASK,STATE}.md` COMPLETE_SOURCE_ONLY; Failure Museum RMCP-F-0024 SOURCE_FIXED_LIVE_UNQUALIFIED. **No real bearer exfiltration/compromise has been observed.** **No live host/tunnel/service/credential deployment was performed.**

Next actual #590/#540/#381 live acceptance remains **BLOCKED_EXTERNAL**: privately qualify active installed process build + registered client catalog + original one-good/one-failing opaque MCP request through admission/dispatcher/server audit/response-delivery/client; Fabric A6 #942 off-target journal and A7 #943 independent rollback/ACK required before any controlled fleet release. Fabric #1398/#1400 issuer/leases owned by Fabric chat; AIfordable #370 real dedicated service and Fabric #972 real Q7 also pending. NO_DISPATCH Claude/EnerCue #89. Avoid speculative restarts, tunnel changes and replays.

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

## 2026-10-10 — #626 final mirror verification security slice DONE, live backups still gated
Runner-MCP PR #626 exact head `abd2c4eb05348b86b87e09f65acd5cf149d98972` passed attribution `38038139765` and full validation `38038139723`; squash merged `5aba8423594290a7837208e53721234dfe0df778`. Performed source-only final BACKUP operator/pins/independent-volume + dual-secondary verification with four regressions. #587/#588 open for physical 2/2 verified copies and offline restorability; no artifact deletion authority.

AIfordable #553 CI fail from obsolete 2026-10-08 test clock versus registry dated 2026-10-10 remains separate owner. Fabric #1397 dedicated archive namespace still needs trusted live provider/bootstrap. Next safe independent Runner-MCP lane #590 error-channel sanitization with HTTP tests; code audit finds `ValueError(str(exc))` on manager failure, while `runtime_doctor` returns WARN. Do not claim proven root cause without safe runtime evidence.

## 2026-10-10 — Source-only protected mirror finalization child active
PR [#626](https://github.com/Blacksp1d3r/runner-mcp/pull/626) (DRAFT, `fix/587-final-mirror-reverification`, head `abd2c4eb05348b86b87e09f65acd5cf149d98972`) closes a source-only TOCTOU gap after both mirror copies: final operator stop, protected pair, full #586 admission and both secondary custody checks, followed by second pin check. Four negative regression tests; attribution `38038139765` SUCCESS, validation `38038139723` IN_PROGRESS at first check. Require exact-head 100% green (Ruff/pytest + clean demo + artifact + attribution), then review and merge; **do not close #587** without actual 2/2 verified second-volume copies.

Priority live critical chain: AIfordable #537 / draft PR #553 (CI `38035068769` 9 topology-test date-fixture failures, 1352 pass; owning project to fix without bypass) -> Fabric #1397 dedicated host-owned archive namespace/bootstrap after trusted qualified mapping -> #586 live read-only volume proof -> #587 fixed first-party two-revision physical mirror -> #588 real offline disposable reader/bootstrap restore with cleanup proof -> only then consider GitHub artifacts retired. Existing source PR #621–#625 already integrated; no duplicate PRs or physical/archive cleanup.

Secondary independent lane #590: mixed connector availability, `runtime_doctor` structured WARN but `runtime_status` + `build_identity` generic transport errors. Diagnose by bounded tool lineage; avoid tunnel restarts or inference about healthy worker counts. PR #618 remains draft open; CI test/build/demo green on queried exact head, separate external registry acceptance required.

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

## 2026-10-09 — Faster-13 staged synthetic PRs reconciled

Existing #514 baseline is merged. Three unique existing, bounded shadow-only follow-ups were restacked without duplicating PRs: #467 Unix envelope E2E (head `f918a91c9824f747c1a3ad429cf28d9f8960dc91`, validation `37962618480`), #465 compact envelope (head `9d1344beaef929acc9bac236a6c8d692dd48b988`, validation `37962706712`), and #456 Unix IPC (head `c2ff700ed4e87cd0a6dd400975a5c47c4016c2a8`, validation `37962833262`, target base corrected to main after #514). At last review all three had Ruff/pytest green and demos still in progress; do not merge until respective exact-head full terminal success. #460 remains stacked behind #456; #458 is a temporary measurement lane explicitly DO NOT MERGE. A previous #467 branch-update blocker was caused by incorrectly guessed branch name; with exact GitHub PR head branch the ref update succeeded. No real OCR/production throughput claim, no routing or live host changes.

## 2026-10-09 — Local MCP JSON-RPC response identity guard landed

PR #613 head `6b5dc2c2c646aba0fdc45a0ae9a08a6af83a8f97`: commit attribution `37962077429` SUCCESS and full validation `37962077446` SUCCESS, squash merged `ae2eac3f4e38574d4405460e14f7b8cad122e4d4`. Internal `LocalMCPClient._post` now refuses replies with absent, mismatched, wrong-type JSON-RPC IDs; nine regression variants cover normal JSON and SSE. This does not prove external ChatGPT tunnel response delivery; issue #590 stays OPEN. #599 freshness source safeguard already merged via #609 and issue closed. Upstream `tunnel-client` local dispatcher/response-delivery component counters are documented as next safe first-failing-edge evidence, not a replacement for per-request identity proof.

## 2026-10-09 — #599 stale poll-authentication evidence reconciled

Issue #599 is **COMPLETE** on source: existing PR #609 exact head `04d0f493db9ba0ea00c4aa10e403e3823785e30b` passed validation `37957581774` and attribution `37958136637`, squash merged `ee29a791bb8dab96275ae3efc9987c6548a57bdd`. Current source rejects malformed, stale (>90s), or over-future (>5s) control-plane last_success; clock is injectable for deterministic tests, threshold grounded in documented 30s long-poll default. The issue was explicitly closed after source reconciliation. This does **not** prove the external connector route; #590 stays open. Independent internal LocalMCPClient JSON-RPC response-ID check is underway as draft PR #613, with no live tunnel changes. Do not recreate #599.

## 2026-10-09 — CI, tunnel and independent archive source gates landed

- Runner-MCP #584: #388 bounded local CLI **SOURCE COMPLETE** (`13a60429...`), #387 operator-dispatched cache-free qualifier **SOURCE COMPLETE** (`08bd1f96...`); live disposable guest, protected labels/network and no production secrets remain **BLOCKED**. Public hosted standard CI is free; no automatic replacement of current check selectors. Preserve exact required check names.
- Tunnel #599: conservative authenticated-poll freshness (`ee29a791...`) **MERGED / issue closed**, 30s documented default long-poll, 5s guardrail, 90s bounded age / 5s future skew; customized longer/backpressure not a tunnel-outage claim. External #590 remains **BLOCKED / UNLOCATED**, no production tunnel mutation.
- I5 independent protected release archive #586: zero-argument READ-ONLY semantic volume gate (`3077381b...`) **MERGED / issue closed**. No mirror-copy/restore performed; #585 parent still OPEN. Next hard dependencies AIfordable #537 and Runner-Fabric #1397 plus real operator volume/machine binding. #587 backup mutation and #588 restore qualification **BLOCKED** until those gates. Distinct filesystem `st_dev` is not physical disk identity or off-site DR.
- Other agents' Faster-13 / connector trace merges preserved; no requalification or duplicate branch.

## 2026-10-09 — Faster-13 local MCP baseline landed

Existing PR #514 was restacked (not duplicated) and exact-head green with validation `37957744262` and attribution `37957744577`, then squash merged `46f9a8b86dc00586cfa24a2368e146f234345d2f`. It adds shadow-only bounded local MCP communication benchmarking and fail-closed CLI argument tests. **Does not imply real Bewind OCR speedup**, and does not authorize a faster production transport or close broader Faster #383. Next performance steps require reproducible qualified workload segments and connection/session lifecycle evidence; no live workloads measured here.

## 2026-10-09 — Connector response lineage and tunnel authentication freshness

- #590: local HTTP response trace isolation COMPLETE via PR #608 / `e0250205ee33cd39f5ffc501ff8fa86861679d30`, with exact-head attribution #37956025846 SUCCESS and validation #37956026036 SUCCESS. This covers request-ID isolation, traceparent inheritance and malformed context; external tunnel return association remains **BLOCKED on first failing-edge evidence**, not confirmed healthy.
- #333: tunnel service enabled/active/readiness 200 observed by operator, but no coordinated post-reboot qualification. Preserve the running service.
- #540: stale runtime/tool catalog generation binding remains separately open; do not create a second generation mechanism under #590.
- #599: code inspection confirms control-plane `last_success` accepts any nonempty string regardless of timestamp validity or age. Next code child must derive actual poll cadence/clock source before enforcing an age bound, test invalid/stale/future/fresh and not confuse a past successful poll with current authentication. No active tunnel mutation.
- Sanitized operations playbook PR #607 merged `6dc5160c93815b223214302ffb50cebbb304e49d`; superseded #603 closed unmerged. Privacy: historical Git refs are not erased merely by closing PR.

## 2026-10-09 — Corrected CI runner priority, enrollment integrity

Tracking: #584; source hardening #604/#605 merged and exact-head green, after earlier #600/#601/#602. Documentation #589 merged and current. Runner-MCP PUBLIC standard hosted PR CI is free; migration to isolated self-hosted is **optional**, not a paid-minute emergency.

- CI-0 validated GitHub inventory, registration marker/path and filesystem writable-mode guards: source COMPLETE; no live executor claimed.
- CI-1 local bounded enrollment CLI #388 + independent elevated credential: PR_OPEN / not live. Do not merge or execute ahead of security review.
- CI-2 self-hosted qualification workflow #387: PR_OPEN, real disposable VM/cache/process isolation proof BLOCKED.
- CI-3 selector migration after CI-2 acceptance: NOT STARTED. Maintain required checks and hosted fallback.
- CI-4 monitor actual private Actions artifact/package storage in project-owning issues, not inferred from public hosted minutes: ONGOING cross-project.

## 2026-10-08 — DIAG component topology, data lineage and failure registry

Tracking: #569. Cross-project authority: Blacksp1d3r/AIfordable#485; canonical standard merged through AIfordable PR #486.

Runner-MCP is decomposed into 14 stable diagnostic components covering runtime/self-update, project/source, tests, mailbox/watchers, Fabric bridge, qualification/bootstrap, deploy/migrate/backup, safety/approval/retention, CI runners, service lifecycle, tunnel/connectivity, diagnostics/audit, artifact/mirror custody and the MCP server/client interface.

Each component owns ROADMAP/SOURCES/DATA_LINEAGE/FAILURES. Global maps cover physical store classes, public field/action lineage, implementation paths, test/evidence surfaces and reusable failures. Existing failure-record and safe-diagnostics contracts are reused rather than duplicated.

Troubleshooting rule: identify the public symptom/tool, walk upstream to the earliest divergent source/state/policy/interface edge, and only then repair. Process health, runtime health, peer capability, source authorization and client catalogue freshness remain independent states. Public docs never copy private infrastructure or credential details.

## 2026-10-06 — fixed Fabric worker-qualification provisioning executor in validation

Tracking: #445; orchestration owner: Blacksp1d3r/Runner-Fabric#1130/#1113/#1110.

Runner-MCP now has a bounded local provisioning slice for Fabric-authorized worker qualification. Fabric remains authoritative; Runner-MCP only verifies the request against host-owned private worker authority, exact generation/expiry/fingerprint and the exact managed Runner-Fabric runtime slot, then writes the existing disposable-target qualification config into one fixed owner-only local namespace.

The public MCP tool exposes only semantic worker/capability identity, generation, plan digest, expiry, exact Fabric revision and request fingerprint. No caller-selected shell, argv, path, host/IP, service, endpoint, Incus object, environment map or credential is accepted. Normal workload activation remains false.

After this lands and is live, Fabric #1130 may bind the fixed executor, then #1113 may run the real external-worker qualification. No Bewind OCR or v3 mutation is part of #445.

## Customer/on-prem update readiness counterpart

Tracking: #414. Orchestration/policy owner: Blacksp1d3r/Runner-Fabric#1063. Customer/product semantics: Blacksp1d3r/AIfordable#401.

Runner-MCP may later expose only bounded local primitives required by Fabric: read-only semantic disk/RAM/memory-pressure/swap/OOM/CPU/thermal/storage/power/network/restart/build/schema/recovery readiness; returning-node trust-generation state; exact release staging/activation/rollback only after separate authorization; and bounded failover/failback hooks only for fixed target adapters.

Runner-MCP does not choose customers, cohorts, rollout order, canaries, soak windows or failure cause. Missing/unsupported health remains explicit unknown. Insufficient RAM/storage or unsafe resource pressure blocks before mutation. No arbitrary path, shell, package manager, endpoint, service selector, raw hardware log or customer data is exposed.

## Fleet Update Track A — control-path protection

Canonical umbrella: Blacksp1d3r/Runner-Fabric#924. Reviewed design: Runner-Fabric `roadmap/FLEET_UPDATE_PLANE_BUILD_VS_BORROW.md` v2. Runner-MCP execution issue: #341. Fabric Track A: #937–#943.

Runner-MCP owns the concrete bounded execution and local safety pieces, not fleet orchestration. Near-term order:
1. reproduce the historical stale/incompatible peer failure in automated tests;
2. expose build identity and version-stamped logs;
3. propagate correlation context and support the synthetic end-to-end probe;
4. exchange/enforce protocol range plus interface/tool-schema compatibility;
5. implement CI evidence for N/N-1 first-party skew;
6. emit bounded journal evidence needed by Fabric;
7. reuse the existing staged baseline/self-update recovery machinery while adding support for a separate local commit-confirmed supervisor that can revert after activation without network/Fabric.

Important existing capability: install-time rollback already stages a baseline wheel and can restore it when installation/runtime verification fails. The missing mechanism is post-activation independent recovery: successful updates currently clear the install transaction/artifacts and restart is scheduled by Runner-MCP itself.

Economic constraint until AIfordable has revenue: **incremental software spend is EUR 0**. Use existing code and free/open-source dependencies only. No paid SaaS, commercial update manager, paid Fleet tier, Mender Enterprise or other paid runtime dependency. Hardware, connectivity and electricity are accepted owner costs; software cost remains time only until revenue supports a new explicit decision.

Status update — 2026-10-05:
- Step 1/A1 COMPLETE via #346 / `c37f60dc...`.
- Step 2/A2 ACTIVE. Initial component/version audit stamping #348 / `c73298e6...`; full aligned BuildIdentity fields on every existing audit row #355 / `98bd8ca0...`.
- A2 is not complete until installed provenance, protocol range/interface digest and cross-hop request reconstruction are proven.
- Next Runner-MCP contribution is to expose/propagate the provenance/protocol/interface facts needed by Fabric A2/A4 without broadening remote authority.

# Runner MCP roadmap

This public roadmap is intentionally infrastructure-neutral. Real deployment details belong only in private configuration.


Handoff policy: `roadmap/ROADMAP.md` is the canonical architectural roadmap; `roadmap/DEPENDENCIES.md` is the canonical cross-stream build/integration order when parallel work exists. GitHub live state wins if either document lags.

Status policy: this roadmap is the architectural source of truth for implemented and remaining phases. `handover/CURRENT_STATE.md` is chronological evidence of completed work, while GitHub CI and release records are authoritative for exact validation results such as test counts.

## Maintenance mode — alpha/MVP core complete

Runner MCP's technical alpha/MVP core is complete and the project is in maintenance mode.

Maintenance-mode rules:

- do not add speculative features merely to keep the roadmap moving;
- accept security fixes, correctness bugs, compatibility work and concrete operator needs;
- preserve the small deny-by-default transport/execution boundary rather than growing into a general remote-control platform;
- keep orchestration, scheduling, provider/API behavior, change planning, higher-level autonomy and fleet-scale control in Runner Fabric;
- deferred items in later phases are not launch blockers and should be revisited only when a real use case justifies them;
- discovery/marketing work is non-blocking and must not cause provider-specific runtime, package, auth or hosting changes.

The canonical public alpha release is v0.1.3. Live acceptance covers bounded first-party control, self-update/restart convergence and deliberate interrupted-install recovery. Remaining open issues are external/owner-controlled follow-up rather than core runtime blockers.

## Cross-cutting — end-to-end operational snapshot

Tracking: #269; cross-repo source of orchestration truth: Runner Fabric #867.

A concrete operator-correctness gap was observed on 2026-10-04: the local Runner MCP test queue could correctly report `0 queued / 0 claimed / 0 running` with all test workers available while the first-party client still reported that systems were busy. Therefore local test-queue idleness must never be presented as end-to-end idleness.

Runner MCP will expose one coarse, read-only, bounded `operational_snapshot` over the existing canonical control path:

`client -> control relay -> Agent Bus -> Runner MCP -> Runner Fabric -> worker/work-unit -> durable result -> acknowledgement`.

The snapshot must, where canonical evidence exists, distinguish queued, claimed/inflight, running, waiting-for-result, waiting-for-ack/replay and retrying work; expose oldest-pending and last-activity age; show bounded worker capacity/saturation and primary/fallback/degraded transport state; and return explicit `unknown` / `not_configured` instead of false green when a layer cannot be observed.

Runner MCP must not create a second queue, scheduler or orchestration state store. Runner Fabric remains the owner of orchestration truth; Runner MCP performs only bounded validation/projection. The tool exposes no payloads, prompts, file names, host paths, endpoints, credentials, raw logs, arbitrary queue browsing, shell, process or network authority.

Acceptance requires a synthetic and live-observable case where the local test queue is idle while upstream relay/Agent-Bus/Fabric work is pending to report the system as non-idle and attribute the correct layer; a truly idle path must converge to clear across all observable layers. One coarse snapshot call is preferred over many small status calls.

## Cross-cutting — AI fault containment with proportional security gates

Runner MCP assumes that an AI/client can misunderstand instructions, hallucinate, follow prompt
injection, call the wrong tool, or otherwise request an unsafe action. The model/client is never
the final authority.

The execution boundary must therefore preserve fast autonomous work where mistakes are contained
while applying stronger deterministic checks only as blast radius increases.

### Operating zones

- **Green / contained:** read-only inspection, safe file reads, predefined tests, bounded logs and
  other actions confined to declared project/runtime limits should remain automatic and must not
  require human approval merely because an AI requested them.
- **Controlled:** staging mutation, known managed service/release actions, migrations and equivalent
  bounded operations require deterministic policy, fresh-state validation, exact plan/target
  binding and replay/fencing protection. Human approval is required only where policy says so.
- **Protected:** production mutation, database restore/destructive recovery, credential/security
  policy changes, emergency-stop changes and equivalent high-blast-radius actions require
  independent operator authority and are not enabled merely by client or agent text.

### Security invariants

- AI/client text expresses intent only; deterministic Runner MCP code decides whether a predefined
  capability exists and is authorized.
- Forbidden capabilities must be absent, disabled or technically unreachable, not merely described
  to the model as "do not call this".
- Tools accept bounded semantic identifiers, not arbitrary shell, executable, host path, endpoint,
  environment, service/process or credential input.
- Mutations revalidate current state immediately before execution and remain bound to the exact
  approved plan/target/revision.
- Approval cannot be self-asserted by the requesting AI/client and must be independently derived.
- Repository/document/tool output is untrusted data and cannot grant capability, weaken policy or
  satisfy approval through prompt injection.
- The caller cannot modify the emergency-stop, approval, audit, authentication or policy boundary
  that governs the caller's own action.
- Executors receive the minimum OS/network/credential authority needed for the bounded operation.
- Mutations verify postconditions and preserve recovery/rollback semantics where applicable.
- **Security friction is proportional to blast radius:** safe read/edit/test loops should remain
  fast and automatic; expensive/human gates belong at trust boundaries, not on every development
  step.

This cross-cutting rule strengthens the existing deny-by-default design. It does not add any new
production, shell, credential or restore authority.

## Cross-cutting — optional Runner Fabric coarse work-unit transport

The transport foundation is implemented on `main` via PR #111. Runner MCP may expose exactly three
coarse Runner Fabric tools when private loopback configuration is present:
`fabric_run_work_unit`, `fabric_get_work_unit` and `fabric_cancel_work_unit`.

This integration preserves the product boundary:

- Runner MCP owns MCP authentication/transport, bounded request/response validation, rate limiting,
  existing operator/safety gates and bounded audit;
- Runner Fabric owns orchestration, work-unit policy/state, capability/fencing decisions, change
  plans, validation/repair, commit/push, provider/API-budget behavior, idempotency and recovery;
- the bridge is absent when unconfigured and may not introduce generic shell, Git, GitHub,
  filesystem, provider or arbitrary polling primitives;
- endpoint/token/provider/private-host details remain private and may not escape through tool
  output, audit detail or exceptions;
- transport sessions are isolated per calling thread and response identity/revision/state
  relationships fail closed.

Live activation and end-to-end proof are complete. Issue #110 is closed after a real first-party
client invocation traversed `client -> Runner MCP fabric_run_work_unit -> private Fabric MCP ->
trusted work-unit service`, followed by bounded get/cancel/operator-safety reconciliation. The
former upstream Runner Fabric durability/Agent-Bus qualification gate is also complete. The merged
transport layer must not be rebuilt.

Agent Bus remains the normal runtime-control path, direct GitHub choreography is fallback/bootstrap,
and broad remote-host tools are break-glass only. No plugin/client convenience may add generic shell,
Git/GitHub, filesystem, provider or credential authority.

## Phase 0 — repository and design

Establish repository structure, security baseline, threat model, configuration model, handover notes, dependency policy, and public-repository hygiene controls.

## Phase 1 — minimal MCP server

Implement Streamable HTTP, authentication, health endpoint, project registry, structured audit logging, request identification, basic rate limiting, `list_projects`, and `project_status`.

## Phase 2 — safe file access

Add allow-listed project file reads, metadata, pagination, path traversal protection, symlink escape protection, secret deny-lists, and file-size limits.

## Phase 2.5 — operator safety and rollback policy

Before enabling mutating tools:

- require an external operator emergency-stop mechanism;
- keep future operator actions read-only until retention policy is explicitly confirmed;
- retain code releases using both a minimum count and minimum age;
- retain pre-migration backups separately from code releases;
- treat database point-in-time recovery as a separate retention control;
- allow only one code rollback step per approved action;
- prohibit automatic production database restores;
- require explicit human approval before any database restore;
- require recovery/preflight metadata before migration, deploy, or rollback.

## Phase 3 — controlled test runner

Implemented design:

- predefined test profiles only;
- absolute executable paths and argument arrays with `shell=False`;
- project-relative working directories;
- bounded concurrency, timeout and log size;
- asynchronous jobs with status and paged logs;
- explicit cancellation;
- external operator-stop observation;
- process-group cleanup;
- scrubbed secrets and private paths in logs;
- persisted safe job metadata and interrupted-job recovery;
- restricted environment passthrough;
- short per-job private `TMPDIR` paths for local IPC/socket based test runtimes, with 0700 permissions and terminal cleanup;
- declarative `playwright` test runtime support that injects only a privately configured shared browser cache into the isolated job environment;
- no automatic execution of untrusted public-fork code without stronger sandboxing.

## Phase 3.5 — packaging and onboarding

Make the safe core usable without reading or editing source code:

- `runner-mcp setup` interactive private configuration;
- local/public setup modes with safe local defaults;
- explicit retention confirmation;
- `status`, `doctor` and emergency-stop commands;
- project add/list/remove commands;
- test-profile add/list/remove commands;
- pytest and Ruff profile presets;
- explicit token rotation only;
- non-root `install.sh`;
- user-first README and Quickstart;
- private config permission checks and atomic project-config updates.
- install/runtime preflight must verify the exact Python interpreter, venv support, pip usability/version, packaging backend availability, dependency compatibility and post-install import/bytecode integrity before enabling the installed command; known-bad or incompatible environments fail closed before service activation.
- clean-install validation must cover a minimal Ubuntu-like host where `python3-venv` may be absent and must exercise the real installed CLI after dependency resolution, including detection/recovery guidance for corrupted or incompatible `.pyc`/marshal state.

Service auto-start packaging is implemented with a preferred non-root systemd-user backend plus a managed cron fallback for headless accounts without a usable user bus. Both keep fixed components, explicit watcher bootstrap, duplicate-supervisor protection and foreign-state protection. Privacy-safe guided connectivity is implemented; external tunnel/TLS/reverse-proxy provisioning remains operator-managed. Task 33 reviewed optional graphical administration and keeps it deferred for the first alpha; any later first slice must be a separate loopback-only read-only dashboard over explicitly allow-listed safe summaries, with no new mutation authority.

## Phase 3.6 — community usability and extension path

Make the existing safe core easier to adopt, understand and extend without changing its trust boundaries:

- project-aware runner-mcp guide command with safe next-step suggestions;
- separate operator/service-account wrapper without secret duplication;
- dedicated user-to-developer extension guide;
- contribution rules that preserve deny-by-default behavior;
- configuration-first extension model;
- built-in adapter extension path before core changes;
- documentation must use placeholders and stay free of real infrastructure values;
- onboarding documents must stay synchronized with implemented features.

Still planned:

- optional graphical administration remains post-alpha/deferred after the Task 33 boundary review; revisit only on concrete operator need, starting read-only/local-only;
- framework adapters only when concrete reusable use cases justify them.

Privacy-safe private-tunnel/TLS/reverse-proxy guidance is implemented. Runner MCP deliberately does not provision external tunnel/TLS/DNS/firewall/proxy state itself.

## Phase 3.7 — GitHub mailbox bridge protocol

Formalize the proven GitHub to Runner MCP transport without turning it into a remote shell:

- public, infrastructure-neutral mailbox protocol documentation;
- strict versioned JSON request model;
- fixed allow-list for project inspection and predefined test execution;
- unknown fields, duplicate keys and oversized requests fail closed;
- no client-supplied shell, executable, path, environment, service or arbitrary MCP tool name;
- migration, deployment and rollback execution are available only through their existing approval IDs; restore remains outside the mailbox allow-list;
- watcher implementation stays private until deployment-specific parts are separated from reusable protocol logic.

Current status:

- the private watcher migration is complete through the shared runtime described in Phases 3.8.3–3.8.7;
- deployment-specific credentials and infrastructure details remain private.

## Phase 3.8 — bridge result envelope and replay protection

Harden the GitHub mailbox transport in both directions:

- strict, versioned result envelope;
- bounded result size, nesting, collection count and string length;
- fail-closed unknown fields and duplicate JSON keys;
- conservative redaction of credentials, environment metadata, paths, hosts, URLs, executables, commands and service-unit details;
- safe error codes instead of raw exception/process output;
- canonical SHA-256 request fingerprints;
- local replay ledger that stores no project/profile/path/credential/result content;
- duplicate request IDs never execute twice;
- request-ID reuse with changed content fails closed;
- corrupt, oversized, capacity-exhausted or symlinked replay ledgers fail closed;
- ledger file permissions restricted to the service account.

Current status:

- the shared validator, result envelope and replay lifecycle are integrated into the public watcher runtime and proven through the later 3.8.x phases.

## Phase 3.8.1 — task-completion feedback

Make asynchronous work observable to the operator without expanding execution authority.

Implemented public contract:

- strict terminal completion events: succeeded, failed or cancelled;
- deterministic event IDs derived from a private source identifier, giving transports a stable deduplication key without exposing the source identifier itself;
- fail-closed source/operation binding for test, migration, deployment and rollback job classes;
- test completion requires a predefined profile; unrelated job classes cannot attach one;
- project/profile/event identifiers use safe bounded shapes;
- attention state is derived from terminal status rather than trusted from a sender;
- duplicate JSON keys, unknown fields, non-standard JSON constants and oversized events fail closed;
- completion payloads contain no paths, hosts, URLs, credentials, service names, environment values or raw logs;
- notification delivery is explicitly separate from task execution: delivery retries may never rerun the operational action;
- mailbox permissions and action allow-lists are unchanged.

Implemented notification runtime and private proof:

- an optional private GitHub-issue notifier observes strict persisted terminal test, deployment/rollback and migration jobs without calling any execution path;
- notifier bootstrap deliberately skips historical completions;
- deterministic event IDs are used both in a private 0600 delivery ledger and as remote notification markers;
- existing remote markers are reconciled instead of posted again;
- notification failures remain retryable independently from task execution;
- one fresh predefined test job was proven end to end to produce exactly one user-facing notification, and a repeated notification cycle produced no duplicate;
- the built-in notifier no longer requires a repository-specific self-hosted Actions runner.

Next:

- keep heartbeat/stale-request recovery separate from notification delivery;
- map any future asynchronous Runner MCP job class to the same completion-delivery runtime only when its persisted terminal metadata can be consumed without widening execution authority.

## Phase 3.8.2 — watcher resilience and restart recovery

Make the private mailbox transport observable and restart-safe without widening the mailbox action allow-list.

Implemented public foundation:

- replay ledger lifecycle now distinguishes `claimed` from `completed`;
- legacy replay entries without a lifecycle state are treated conservatively as `claimed`;
- a request is marked completed only after its safe result is durable;
- restart recovery distinguishes processable, already-resulted, ambiguous-claim and missing-result states;
- ambiguous claimed work is never rerun automatically;
- a completed ledger entry with a missing transport result is never rerun automatically;
- sanitized heartbeat states are limited to `healthy`, `backlog` and `degraded`;
- heartbeat output exposes only bounded counts and oldest-pending age, never request contents or infrastructure metadata;
- stale/backlog thresholds are bounded;
- duplicate heartbeat observations fail closed;
- transient transport retry is bounded to timeout/rate-limit/unavailable failures;
- authorization and invalid-response failures are not automatically retried;
- transport retry policy never authorizes operational action replay;
- local operator recovery can resolve an already-claimed missing-result request by publishing a terminal safe `RECOVERY_REQUIRED` result without invoking the executor;
- the recovery command requires an existing exact replay record, refuses an existing durable result, preserves the cursor, and finalizes a claimed ledger entry only after the safe failure result is durable;
- a strictly valid request that has never been claimed can be explicitly abandoned by a local operator, producing an `OPERATOR_ABORTED` result without invoking the executor;
- a malformed historical request can be quarantined only when it is in the current backlog, has no result, every sibling request has a matching durable result, and the request head remains unchanged through final verification;
- malformed-request quarantine fetches only bounded bytes from the fixed mailbox path and does not weaken normal protocol parsing;
- no recovery path exposes a generic replay, ledger-reset or cursor-reset control;
- a normal watcher cycle performs subsequent reconciliation where applicable.

Operational proof covers migrated claim -> execute -> persist -> complete ordering, sanitized heartbeat publication, restart-safe reconciliation and one live malformed legacy-request quarantine with zero replay. Explicit operator recovery paths have regression coverage for persistence failure, protocol validity, exact confirmation and cursor/head races.

Next:

- keep notification delivery and heartbeat/stale recovery independent;
- extend operator recovery only when a new fail-closed state has a provable non-replay resolution; never add a generic replay/reset switch.

## Phase 3.8.3 — transport-neutral bridge processor

Move reusable watcher orchestration into the public package without publishing deployment-specific transport details.

Implemented foundation:

- strict request parsing happens before replay claim or execution;
- replay claim happens before any Runner MCP action;
- duplicate completed requests return without execution;
- duplicate claimed requests become an ambiguous recovery state and are not executed;
- executor interface contains only the six mailbox-allow-listed actions;
- no arbitrary MCP tool name, shell, executable, path, environment or service name is accepted by the processor;
- `run_tests` uses an explicit `run_tests_to_completion(project, suite)` executor method;
- executor exceptions become generic safe failure envelopes without raw exception text;
- unsupported/unsafe executor output becomes a bounded `UNSAFE_RESULT` failure;
- results are scrubbed/serialized before the transport-specific result sink sees them;
- durable result persistence happens before replay lifecycle completion;
- result-persistence failure leaves the request claimed and returns safe recovery material rather than rerunning the task;
- replay-finalization failure after durable persistence is reported as recovery-required rather than triggering execution again.

Still transport-specific/private:

- mailbox repository/branch selection;
- credentials;
- polling/webhook mechanics;
- result-file naming/location;
- notification destination;
- supervisor/service configuration.

Current status:

- the processor is integrated with the hardened GitHub transport and watcher coordinator in Phases 3.8.4–3.8.7; the private pilot migration and end-to-end proof are complete.

## Phase 3.8.4 — hardened GitHub mailbox transport

Provide a reusable GitHub transport without putting deployment-specific credentials or infrastructure details in the public repository.

Implemented foundation:

- fixed GitHub API host; callers cannot supply an arbitrary endpoint;
- repository and branch/ref identifiers are strictly validated;
- request, result and heartbeat locations are fixed below the mailbox root;
- GitHub credentials remain runtime-only and are never serialized into mailbox data;
- API responses are size-bounded;
- duplicate JSON keys and non-standard JSON constants from GitHub fail closed;
- wrapped GitHub base64 content is accepted only after strict validation;
- request payload identity must match its mailbox filename;
- result publication is create-once and idempotent only when existing content is identical;
- conflicting existing result content fails closed;
- result transport failures map into the BridgeProcessor persistence-recovery boundary;
- heartbeat create/update uses bounded validated public heartbeat JSON only;
- HTTP authorization, rate-limit, timeout, conflict and availability failures are classified without returning raw GitHub response content;
- no GitHub SDK or paid external service is required.

Current status:

- the generic coordinator and private-runtime integration are implemented in Phases 3.8.5–3.8.7;
- credentials, repository/ref selection and supervisor configuration remain private.

## Phase 3.8.5 — incremental watcher coordinator

Combine the public GitHub transport, bridge processor, replay lifecycle and heartbeat contract into a restart-safe watcher loop.

Implemented foundation:

- transient GitHub transport retries are bounded to 2 and 5 seconds after the original attempt;
- authorization and invalid-response failures are never automatically retried;
- request discovery uses a strict fast-forward compare from a private local cursor instead of rescanning historical mailbox contents;
- compare input is limited to validated 40-hex commit SHAs;
- request-file deletes, renames, nested paths, malformed IDs and oversized compare sets fail closed;
- first use is explicitly uninitialized and executes nothing;
- explicit bootstrap records the current request head and deliberately skips historical requests;
- local cursor uses restrictive permissions, file locking, symlink refusal and optimistic expected-SHA advancement;
- an existing durable result is reconciled into the replay ledger without executing the action;
- claimed requests without a result are never automatically rerun;
- completed requests with a missing result are never automatically rerun;
- persistence/finalization failures keep the cursor behind so the next cycle reconciles safely;
- malformed requests block cursor advancement instead of being silently skipped;
- heartbeat publication stays independent from operational task success;
- heartbeat delivery failure never rewinds an already-advanced cursor or reruns an action;
- non-request commits can advance the cursor without executing work.

Current status:

- the coordinator is combined with the loopback MCP executor and private runtime in Phases 3.8.6–3.8.7; restart/reconciliation proof is complete;
- completion delivery remains an independent idempotent subsystem.

## Phase 3.8.6 — loopback MCP bridge executor

Move the remaining pilot-specific MCP handshake and test polling into reusable public code without exposing a generic remote-control interface.

Implemented foundation:

- local MCP endpoint is restricted to HTTP(S) loopback hosts and the exact `/mcp` path;
- credentials in endpoint URLs, query strings and fragments are rejected;
- bearer token, session ID and test job ID shapes are bounded and validated;
- MCP response bytes are bounded;
- JSON and SSE payloads reject duplicate keys, non-standard constants, malformed UTF-8 and ambiguous multi-event responses;
- transport, JSON-RPC and tool failures become generic `BridgeExecutionAdapterError` values without raw server details;
- the public executor exposes exactly the six bridge operations;
- generic MCP tool dispatch stays private and internally allow-listed;
- internal `test_status` polling is used only to finish a previously allow-listed `run_tests` request;
- test logs are never fetched by the bridge executor;
- terminal test output is reduced to project, suite and status;
- polling interval and overall wait time are bounded.

Current status:

- private-config watcher migration and restart/reconciliation proof are complete in Phase 3.8.7;
- clean-environment demo validation and completion notification proof are also complete; remaining connectivity/onboarding work is tracked separately.

## Phase 3.8.7 — private-config watcher runtime and CLI

Wire the public GitHub transport, replay ledger, cursor, watcher and loopback MCP executor together without putting deployment-specific values into the repository.

Implemented foundation:

- GitHub repository, request ref, result ref and token live only in the private 0600 runtime environment;
- mailbox configuration is validated before atomic persistence;
- mailbox status reveals only configured/not-configured state;
- the GitHub token is entered through a hidden prompt and is not accepted as a CLI argument;
- mailbox removal deletes only the four mailbox environment values;
- setup overwrite preserves database and mailbox secrets even when rotating the Runner MCP bearer token;
- replay ledger and cursor files are derived inside the private configuration directory;
- `github-watcher bootstrap` explicitly starts at the current request head and skips historical requests;
- `github-watcher once` processes one bounded incremental cycle and prints only safe counts/state;
- `github-watcher run` provides continuous polling with bounded intervals;
- request polling and heartbeat publication have separate cadences;
- heartbeat defaults to a slower cadence and is also published on watcher-state transitions;
- heartbeat delivery remains independent from operational task execution.

Private deployment proof:

- the pilot poller has been replaced by the shared `runner-mcp github-watcher run` runtime in a private deployment;
- explicit bootstrap started at the current request head without historical replay;
- fresh protocol-v1 inspection requests, queue/worker observability and asynchronous test execution were proven end to end;
- restart/reconciliation preserved the cursor and replay ledger without duplicate execution;
- the legacy pilot poller is disabled in that deployment;
- completion-notification transport remains a separate capacity concern.

Current status:

- the independent exactly-once completion-notification proof and clean-environment demo validation are complete;
- remaining private-connectivity/TLS onboarding stays in the onboarding/launch phases.

## Phase 3.8.8 — controlled multi-project concurrency

Remove global serialization from routine bridge and test work without widening execution authority.

Implemented foundation:

- bounded mailbox request workers with a separate maximum in-flight batch;
- request acceptance separated from long-running test execution;
- persistent logical queues per project with fair round-robin scheduling;
- bounded global test-worker capacity and bounded global/per-project queue capacity;
- conservative defaults: two test workers globally and one active test per project;
- explicit per-project `max_parallel_tests` plus per-profile `parallel_safe` opt-in;
- queued, claimed and running lifecycle states before terminal test results;
- safe queue/worker/job observability and queued/running cancellation;
- malformed or recovery-required mailbox requests do not block independent work in the same batch, while cursor advancement remains fail-closed;
- GitHub result writes keep only a short serialized critical section;
- loopback MCP clients are thread-local so concurrent watcher workers do not share mutable MCP session state;
- existing shell, path, environment, service-name and arbitrary-tool injection boundaries remain unchanged;
- migration, deployment, rollback and restore remain outside the mailbox allow-list;
- authenticated MCP request capacity defaults to a bounded 600 requests/minute so status polling and mailbox concurrency do not become a new global bottleneck;
- request rate, test-worker capacity and queue capacity remain separate independently enforced controls.

Capacity can later grow by increasing bounded worker settings or adding execution capacity behind the same request/job protocol. Protocol clients do not need to change.

See `docs/CONCURRENCY.md` for defaults, scheduling, observability and Runner MCP versus GitHub Actions guidance.

## Phase 3.8.9 — bounded operational bridge

Extend the GitHub mailbox from inspection/tests into existing Runner MCP operational capabilities without introducing a generic remote shell or bypassing local safety controls.

Implemented foundation:

- bounded scrubbed test-log pages through `job_log`;
- configured service alias listing/status/start/stop/restart, never arbitrary systemd unit names;
- backup listing and on-demand configured PostgreSQL backups;
- read-only migration status, deployment plans, release lists and rollback plans;
- approval-plan request/status through opaque IDs;
- migration/deployment/rollback execution only with an already-approved short-lived approval ID;
- deployment and rollback job status through validated opaque job IDs;
- per-action strict argument schemas, bounded list/log ranges and fixed loopback MCP tool mapping;
- database restore, PITR, production actions, shell/argv/path/env injection and approval granting remain outside the mailbox authority.

This phase is specifically intended to remove routine dependence on general-purpose remote-control software. GitHub remains a transport; Runner MCP remains the local authorization and execution boundary.

Next:

- prove the expanded operational bridge live against one read-only operation and one low-risk configured mutation on the upgraded private runtime;
- preserve separate human approval for migration/deploy/rollback.

Runner MCP read-only observability and commit-pinned self-operations are implemented separately in Phases 3.8.10–3.8.11 rather than exposing package-manager or process-control primitives.

## Phase 3.8.9a — shared Playwright test runtime

Make browser-based E2E profiles work inside Runner MCP's isolated test environment without weakening HOME/TMPDIR isolation.

Implemented foundation:

- test profiles can declare a fixed runtime of `default` or `playwright`;
- the Playwright runtime receives only `PLAYWRIGHT_BROWSERS_PATH`, sourced from private Runner MCP configuration;
- the configured browser-cache path must be absolute, exist as a directory and not itself be a symlink;
- the browser-cache path is treated as a private path for log scrubbing;
- missing browser runtime fails closed before test execution;
- no arbitrary browser path can be supplied through the mailbox or test request.

This is intended for shared Chromium/Playwright installations on persistent self-hosted runners while preserving per-job HOME/TMPDIR isolation.

## Phase 3.8.10 — runtime observability bridge

Expose Runner MCP's own health/configuration state through fixed, read-only bridge actions so routine diagnosis no longer needs general-purpose remote access.

Implemented foundation:

- `runtime_status` returns package version, safety mode, emergency-stop state, bounded worker/queue capacities and whether test/database/deployment/approval subsystems are configured;
- `runtime_doctor` returns only bounded PASS/WARN/FAIL-style checks and generic details;
- no private paths, URLs, hostnames, credentials, service units, environment values or raw process output are returned;
- both actions are fixed no-argument protocol-v1 actions and map only to local MCP tools;
- result publication still uses the existing bridge scrubber, replay ledger and create-once result lifecycle.

Next:

- prove the runtime observability actions live after the private runtime is upgraded.

Mutating self-operations remain separate from read-only diagnosis and are implemented as commit-pinned operations in Phase 3.8.11.

## Phase 3.8.11 — commit-pinned Runner MCP self-update

Remove routine dependence on general-purpose remote-control software without introducing generic package or process control.

Implemented foundation:

- `self_update(commit)` accepts only one full lowercase 40-character commit ID for the configured canonical Runner MCP repository;
- the target commit must be reachable from `origin/main`, and source synchronization remains clean-worktree, exact-commit and staging/test gated;
- existing fixed `lint` and `unit` profiles must both pass before installation;
- validated update source is staged as a private wheel before installation; wheel building and installation use the active Python runtime with fixed offline/no-dependency pip arguments, no shell and no caller-supplied path/argv/environment;
- when a previously installed commit is known, its clean source is staged as a private recovery wheel before source synchronization, while the per-project source guard remains held across recovery staging, target sync, lint/unit validation, target staging and installation;
- a private 0600 install-transaction marker is durable before the in-place package mutation; runtime status exposes only a bounded `install_recovery_pending` boolean and overlapping self-updates fail closed while it exists;
- target package installation is verified in a fresh Python process before it is accepted;
- a caught target install/import failure automatically reinstalls and verifies the recovery wheel and restores the exact prior source commit when both package and source rollback can be proven; successful automatic recovery is reported as `install_rolled_back` without scheduling activation;
- a first/bootstrap install failure, process interruption during package mutation, failed rollback, or unfinalized transaction remains `install_recovery_required` and blocks further self-update instead of pretending the environment is intact;
- a persisted rollback-capable install transaction can be recovered only through the local `runner-mcp self-update-recovery` operator command; it requires the emergency stop to be active, reuses only the privately staged baseline wheel, restores the exact baseline commit from `origin/main`, re-verifies the installed runtime and clears the transaction only after package/source/state recovery is proven;
- the local recovery path refuses first/bootstrap transactions without a known baseline and refuses to overlap pending activation recovery; no recovery action is exposed through the mailbox or MCP tool surface;
- local `status` exposes only `clear`, `REQUIRED` or `INVALID` install-recovery state, while `doctor` warns on a valid pending transaction and fails on corrupt/unsafe transaction state without exposing commits or artifact paths;
- same-commit requests still verify the exact commit against `origin/main`, but then complete without package mutation or restart;
- the build backend required by the deliberate `--no-build-isolation` wheel path is an explicit runtime dependency rather than an implicit build-environment assumption;
- update jobs and installed-commit state are persisted privately with restrictive permissions;
- server, GitHub watcher and completion watcher activate new code through fixed component-specific self-reexec flows;
- activation creates fixed create-once restart markers for all three components; a failed component re-exec restores its marker instead of silently consuming the restart request;
- runtime status exposes only whether activation remains pending and the bounded number of fixed pending components; another self-update is blocked until those markers are cleared;
- server activation uses bounded retries, while watcher/notifier failures preserve their marker so existing systemd/cron supervision can safely retry on restart;
- `self_update_status(job_id)` exposes only bounded persisted state;
- read-only `runtime_status` keeps the broader observability fields and adds self-update readiness/state; `runtime_doctor` remains separate;
- the loopback bridge explicitly allow-lists `runtime_status`, `runtime_doctor`, `self_update` and `self_update_status`;
- protocol validation treats `self_update_status` as an exact job-id-only action, and direct/self-update entry points reject uppercase or abbreviated commit identifiers;
- arbitrary repository/ref selection, package-manager arguments, install paths, process commands, service identifiers and restart commands remain unavailable.

Next live-proof lane (tracked by #108):

- bootstrap the current recovery-capable baseline once on the private Runner MCP host through the normal dependency-resolving path;
- prove same-commit/no-op and one forward commit-pinned self-update through the bounded operating model;
- deliberately fail/retry one activation and fault-inject one package-install interruption only after the recovery-capable baseline is confirmed, proving that durable recovery state blocks overlap and can be cleared only by the existing bounded/local recovery path;
- keep dependency-set changes explicit because self-update intentionally never resolves or installs dependencies; a dependency-set change still requires an explicit compatible bootstrap path;
- do not describe in-place pip mutation as atomic: the transaction marker makes interruption detectable and fail-closed, while automatic rollback is claimed only for caught failures where both package and source restoration are verified;
- publish only scrubbed categorical evidence and public commit/workflow references; no private host identity, paths, services or credentials.

## Phase 3.9 — public launch readiness

Prepare Runner MCP for free, responsible discovery without changing its security boundaries.

Implemented launch-readiness foundation:

- Runner MCP remains the product identity under the AIfordable umbrella;
- README leads with the problem, safety boundary and architecture;
- Quickstart remains the full guided path while a separate five-minute local demo provides a shorter evaluation path;
- root security-reporting policy added;
- public changelog and release checklist added;
- reusable factual launch copy prepared for GitHub and developer communities;
- privacy-safe GitHub bug/feature forms and a security-focused pull-request template added;
- package metadata improved for future distribution;
- discovery metrics remain platform-level; no application marketing telemetry is added;
- no paid advertising, paid hosted CI or paid hosted infrastructure is a hidden dependency; standard free CI for this public repository is acceptable when it carries no private secrets.
- clean Ubuntu 24.04 / Python 3.12 CI now exercises the documented five-minute demo end to end, including installation, setup, doctor, predefined test-profile configuration, emergency stop and loopback health check;

Canonical publication completed:

- PyPI package `aifordable-runner-mcp==0.1.3` is published;
- official MCP Registry identity `io.github.Blacksp1d3r/runner-mcp` version `0.1.3` is published;
- GitHub pre-release `v0.1.3` is aligned with exact release commit `0aa013c279128e22fbd53be32c35bced3ae26834` and carries wheel + sdist assets;
- protected publish workflow run `36962568072` completed PyPI, official Registry and GitHub pre-release publication successfully;
- public GitHub description/topics and first-party canonical discovery links are live;
- mcp.so community submission is complete;
- secondary directories must reuse the canonical identity/install/auth metadata rather than inventing alternatives.

Remaining discovery work is intentionally non-blocking:

- Glama listing discovery, maintainer claim and metadata verification are complete; Glama hosting/release/Gateway remain intentionally unused;
- Smithery is deliberately skipped unless it exposes a repository-only path that preserves the canonical self-hosted architecture unchanged;
- AllMCPs listing ownership is verified through the free README path; no paid boost/featured placement is justified;
- stale third-party directory metadata is tracked separately in #263 and must not trigger package/runtime changes;
- one technical launch post remains deliberately deferred until `aifordable.com` is ready enough to serve as the public umbrella/landing page.

## Phase 4 — staging service management

Implemented core design:

- private service aliases mapped to systemd-user units;
- no arbitrary unit names supplied by MCP clients;
- safe alias listing without unit/health-URL disclosure;
- status and optional HTTP health checks;
- independent opt-in for start, stop and restart;
- all mutating actions pass the operator safety guard;
- emergency stop leaves status available but blocks service mutations;
- subprocess execution uses a fixed systemctl argument array with `shell=False`;
- no sudo or generic system-service control.

Task 41 provides the shared bounded text-redaction primitive. Task 47 is now integrated as a local/private `service-log` reader with explicit per-service `allow_log_read` opt-in, fixed bounded `journalctl` tailing and no MCP/mailbox/Agent-Bus log action. Any remote disclosure remains separately deferred to Task 51 review.

## Phase 5 — backups and migrations

Implemented core design:

- PostgreSQL-only database configuration with private `RUNNER_MCP_DB_*` credentials;
- DSN entered through hidden CLI prompt and kept out of project YAML;
- private backup root/project directories and 0600 dump/metadata files;
- `pg_dump` custom-format backups with DSN in child environment, never argv;
- safe backup metadata listing without dump paths or contents;
- predefined migration status/apply profiles with `shell=False`;
- bounded and scrubbed migration output;
- pre-migration backup required before migration apply;
- safety guard rechecked after backup and before migration;
- failed migration keeps the recovery point and never auto-restores;
- Task 44 adds the strict private durable migration-job substrate and `MIGRATION_JOB` completion source; Task 49 is now integrated as an additive `start_migration_job` / `migration_job_status` contract with distinct `migration_async` human approval while preserving synchronous `apply_migrations` and deployment-triggered migrations;
- local read-only restore preflight validates one private PostgreSQL archive without database connection or restore authority;
- local CLI retention preview strictly validates private release/backup state and reports protected or potentially eligible records without deleting or rewriting data;
- CLI database and migration configuration without manual YAML editing.

Not implemented yet:

- database restore execution remains deferred after Task 37: the current architecture does not prove a separately prepared empty recovery target, complete database-writer quiescence, application cutover, `pre_restore` retention semantics or semantic post-restore verification;
- WAL archiving/PITR orchestration and verification;
- automatic/unattended retention pruning;
- backup pruning remains deferred pending a separate crash-safe pair-deletion contract;
- local one-release pruning is implemented by Task 43 after Task 48 added the shared cross-process release lock: local CLI only, one freshly eligible non-migration orphan per short-lived plan, typed confirmation, durable quarantine transaction and fd-safe deletion; backups and automatic pruning remain deferred.

## Phase 6 — staging release engine

Implemented core design:

- staging-only deployment configuration;
- clean Git HEAD as the only deploy source;
- no client-supplied branch/ref/commit or arbitrary build shell;
- fixed Git argv with hooks/fsmonitor disabled;
- safe Git archive extraction with repository symlinks rejected;
- private release root, releases directory and runtime HOME;
- required test profiles before release creation;
- source HEAD/cleanliness rechecked after tests and before migrations;
- optional Phase 5 migration orchestration;
- atomic `current` symlink activation;
- configured service restart plus mandatory health check;
- one automatic code rollback after failed activation only when no migration was applied;
- no automatic rollback after database migration;
- persisted asynchronous deployment jobs and restart-interruption handling;
- MCP `plan_deploy`, `deploy_staging`, and `deployment_status`;
- CLI deployment configuration without manual YAML editing.

Still deferred:

- production deployment;
- framework-specific build/adapters;
- release pruning;
- manual historical rollback selection (Phase 7).

## Phase 7 — rollback engine

Implemented core design:

- safe release metadata listing with current/previous/commit/timestamp state;
- retention-protection reporting using both minimum count and minimum age;
- local advisory retention preview protects current/direct rollback/reference/migration-recovery relationships and never treats manual backups as automatically eligible;
- fail-closed release metadata validation and permission checks;
- direct previous release is the only rollback target;
- global strict MCP input validation rejects unknown arguments;
- rollback blocked when current release crossed a database migration boundary;
- asynchronous persisted rollback jobs;
- deploy and rollback jobs mutually exclude each other per project;
- atomic one-step release switch plus service restart and health verification;
- failed rollback health reactivates the original current release when safe;
- no database restore and no automatic multi-step cascade.

Still deferred:

- automatic release pruning remains deferred; Task 43 implements only one local/manual non-migration orphan release outside the retained rollback chain per confirmed plan;
- arbitrary historical target selection remains deferred after the Task 35 boundary review; older history is reached only through fresh direct-previous one-step approvals with health revalidation;
- production rollback;
- database restore/recovery workflow.

## Phase 8 — multi-project adapters

Implemented core design after Tasks 38–39:

- built-in `generic` and `python` adapters are deny-by-default and expose only bounded capability metadata;
- execution layers are project-generic after configuration is resolved;
- no dynamic adapter/plugin loading from project configuration is allowed;
- built-in non-custom test/migration presets are materialized through typed fixed adapter recipes rather than framework-specific branches in generic configuration code;
- Python-specific project-local executable discovery and fixed pytest/Ruff/Alembic argv construction live behind the Python adapter boundary;
- `custom` remains the explicit local-operator path with existing executable validation and no shell command string;
- unknown or ambiguous built-in presets fail closed.

New projects should normally require configuration/adapters rather than core changes. Additional framework adapters remain separate reviewed additions rather than dynamic plugins.

## Phase 9 — approval and risk gates

Implemented:

- short-lived persisted approval plans for migration, deploy and rollback;
- approval request/status available through MCP, but approval itself only through local CLI;
- explicit local confirmation phrase;
- approval bound to action, project and cryptographic plan fingerprint;
- single-use consumption and replay prevention;
- default ten-minute TTL with strict 60–1800 second bounds;
- deployment approval pinned to clean Git commit;
- migration approval requires and binds a clean Git HEAD;
- rollback approval pinned to current and direct previous release;
- runtime race checks reject changed deploy/rollback targets;
- mutating project actions restricted to `staging`;
- production remains read-only.

Connectivity decision:

- prefer OpenAI Secure MCP Tunnel for private ChatGPT/OpenAI connectivity where supported;
- keep Runner MCP private/loopback and use outbound HTTPS rather than opening inbound firewall ports;
- a hosted multi-user relay comparable to commercial remote MCP services is optional future infrastructure, not part of the MVP.

## Phase 10 — optional restricted command templates

Only if concrete use cases remain unmet, add tightly allow-listed executable templates under a sandboxed account. No free-form root shell.

## MVP completion

The MVP is complete when one pilot project can be inspected, tested, backed up, migrated, deployed to staging, health-checked, and rolled back without a general remote-shell dependency, while all actions remain auditable and secrets stay inaccessible.


## Cross-project Infrastructure Authority invariant

Runner-MCP consumes the canonical AIfordable Infrastructure + Credential Authority and does not own a separate fleet/server truth. Bounded operations must resolve scoped customer/site/host/runtime/service identity/credential binding and freshness before infrastructure mutation. Stable asset IDs are technical identity; env-var names and Linux usernames are implementation bindings, not host identity. Unknown, stale or conflicting context fails closed.

Authority: `Blacksp1d3r/AIfordable/docs/INFRASTRUCTURE_AUTHORITY.md`.
