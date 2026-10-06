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
