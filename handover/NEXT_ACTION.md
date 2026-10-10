# NEXT ACTION

## 2026-10-10 12:52 CEST — #381 verified priority and precise remaining authority gap

1. [Runner-MCP #381](https://github.com/Blacksp1d3r/runner-mcp/issues/381) OPEN. Original issue description updated to fit one-Fabric-control-plane ADR: no ordinary same-user `aifordable` service alias to another identity/host. Source #628 MERGED, green exact CI; dedicated coding actuator exists only as a library without any exposed live control endpoint/installed dedicated-host helper.
2. New [Fabric PR #1430](https://github.com/Blacksp1d3r/Runner-Fabric/pull/1430) MERGED, green exact-head CI. **Readiness review only**, `dispatch_authorized=false` even if all synthetic flags true. Does not unblock Claude dispatch.
3. **First actionable dependency:** Fabric #1172/draft #1422 must supply centrally authenticated/fenced trusted worker lifecycle issuer/verifier and fixed pre-registered host binding. Runner-MCP owner then attaches the helper only under the correct dedicated rootless identity; never treat a local `lambda:True`, user/host input, or mere socket-listening state as authorization.
4. AIfordable #370 owner separately proves actual packaged rootless STATUS/START/STOP, only fixed localhost listener and its removal after stop with independently verified service ownership, no production enable. Fabric #972 owner then performs real authenticated availability, lease/fence, correlation/return-path and bounded synthetic no-billing work. Until both: Claude/EnerCue #89 **NO_DISPATCH**.
5. Client read-only snapshot and `list_services(aifordable)` failed internally in this check; no installed-runtime identity proof, and no service/tunnel/host mutation warranted. Other owner's #630 blueprint and #587/#588 physical backup work remain independent. See updated #381 body, handover and child roadmap.


## 2026-10-10 — Shared repository blueprint BPA-01 landed; BPA-02/BPA-03 still gated
[Runner-MCP #630](https://github.com/Blacksp1d3r/runner-mcp/issues/630) is OPEN. BPA-01 docs-only [PR #631](https://github.com/Blacksp1d3r/runner-mcp/pull/631), exact HEAD `f23c12079b2a2cdbb15b6ce2a2fa24c9b68c66f9`, attribution `38045941135` SUCCESS, full validation `38045941103` Ruff/pytest + artifact + clean demo all SUCCESS, reviewed and MERGED `20c19970d14b9402ce6a2393477f3056602498bd`. Final `roadmap/children/bpa-01/STATE.md` marked COMPLETE. `AGENTS.md` now references Library master v1.2 and repository blueprint v1.0; `docs/standards/REPOSITORY_BLUEPRINT_COMPATIBILITY.md` explicitly maps legacy structure and gaps. No mass rename, manifest/authority fabrication or runtime change.

Next #630 BPA-02: independently qualify symbolic project manifest schema and canonical local Git/storage authority before asserting local-first or creating `project.yml`; status BLOCKED/REVIEW_REQUIRED where not proven. BPA-03: map old issue/roadmap children while requiring TASK+STATE on new children, without duplicating canonical truth or clobbering active claims. Separate Fabric-owned automatic scaffolding remains unimplemented, not authorized here. Claude #381 source PR #628 landed but operational issue OPEN pending Fabric/AIfordable trusted lifecycle; #590 source #627/#629 merged but installed catalog/return-route unqualified; #587/#588 still no real 2/2 independent mirror or offline recovery, retain provider artifacts. Other AI owners' work untouched.


## NEXT CRITICAL: 2026-10-10 — Claude #381 source landed, live qualification is the blocker

- #381 remains USER TOP PRIORITY. Source PR #628 exact head `e88e880c1c8db307d94c558250d12ee119c35e48` full CI `38045484330` SUCCESS (2,659 pytest, Ruff, built artifact, clean demo), attribution `38045484328` SUCCESS; squash merged `4981fa648aa127e5d2e0538b9eefec170f816466`. GitHub erroneously auto-closed #381, which was deliberately **REOPENED**; verify still OPEN before next work.
- Source module `src/runner_mcp/fixed_coding_worker_actuator.py` is fail-closed and NOT installed/wired; no live Claude dispatch. Exact local account/unit only; no cross-user sudo or generic service selector. Architecture and complete TASK+STATE in `docs/architecture/FIXED_CODING_WORKER_ACTUATOR.md` and `roadmap/children/381-claude-worker-lifecycle.md`.
- **Next external prerequisite:** Fabric #1172 / draft PR #1422 (single control plane) must expose a genuine trusted, signed/fenced/leased/idempotent intent verifier bound to the correct pre-registered worker and local helper identity. Do NOT invent authority with a caller-supplied boolean, deploy an unverified local endpoint, or create a second scheduler.
- Then AIfordable #370 correct host under rootless `aifordable-coder`: packaged unit install/preflight, fixed STATUS/START/STOP, listener loopback-only 8030, listener disappears after stop and service remains disabled on boot; operator-private evidence only. Then Fabric #972 authenticated availability and exact lease/fence/correlation proof, read-only/synthetic bounded work, then EnerCue #89 isolated task. Claude work remains NO_DISPATCH until all gates.
- #587/#588 backup proof remains independent and OPEN; never delete GitHub artifacts merely because #381 source merged.


## HIGH PRIORITY 2026-10-10 — #381 Claude fixed host-local lifecycle (user requested)

Owner: Runner-MCP #381. Source draft [PR #628](https://github.com/Blacksp1d3r/runner-mcp/pull/628), branch `feat/381-fixed-rootless-coder-actuator`, expected current head `e7b0c4866fcbf1767e9ea73ad048c8ec89d7ae48`. Check actual current GitHub HEAD first. CI attribution `38045392637` and validation `38045392668` initially QUEUED. Previous head failed Ruff UP022 (fixed), no merge before full exact-head green.

Next implementer: (1) validate #628 Ruff/pytest, release artifact and clean demo; fix exact CI defects in #628 only; (2) review/merge bounded source-only capability only with all checks green; (3) keep #381 OPEN: missing trusted Fabric #1172/#1422 lease/intent binding, fixed dedicated-user first-party execution endpoint on correct host, AIfordable #370 real start/status/stop/disabled proof and Fabric #972 loopback+return qualification. (4) EnerCue #89/other real Claude tasks remain NO_DISPATCH until Fabric single-plane READY. Existing same-user ServiceManager must never be widened to sudo/UID/unit selector or fake alias on github-runner; no API fallback; do not reinstall Claude.

Canonical task tree: `roadmap/children/381-claude-worker-lifecycle.md`; architecture `docs/architecture/FIXED_CODING_WORKER_ACTUATOR.md`. After #381 safe readiness, resume independent #587/#588 backup work in its owning lanes.


## Independent Runner-MCP #590 lane — SOURCE COMPLETE, LIVE BLOCKED (10 October 2026)\n\nPR #629 exact head `53614092bafac8e528b4905fc962da72ffde4621`, attribution `38045401691` and full CI `38045401730` all SUCCESS, source MERGED `7deb63cd8d623a74389c9f582d6e2d1ec688b2eb`. `build_identity` returns fixed unavailable status rather than provider exception when no trustworthy identity exists. Issue #590 remains OPEN: 12-check client doctor and failed `runtime_status` are still unexplained at the actual installed generation, with no private request/response correlation. **Do not deploy/restart/reset tunnel** based on this merge. Next legitimate step is approved, safe, private read-only installed-build/schema/catalog and ingress/response lineage verification. \n\n## Latest coordination: 2026-10-10 — Fabric #1428 remains OWNER_IN_PROGRESS, WAITING_CI_FIX

Runner-Fabric #1397 dedicated owner has draft [#1428](https://github.com/Blacksp1d3r/Runner-Fabric/pull/1428), exact head `e3521f49ba996b378fdc132b8a922cc04b2bebcf`, attribution `38042060760` SUCCESS; Foundation `38042060585` FAILED only Ruff `C408` (unnecessary `dict()` in `tests/test_storage_binding_evidence_gate.py:9`), while tests and doctor SUCCESS. Diagnosis sent to Fabric owner in PR comment #6096292386; DO NOT duplicate edit or rerun its lane here. Require owner's new exact HEAD and green CI, then separately prove real private binding + physical namespace. No archives mirrored/restored/retired.


## Latest: 2026-10-10 — #627 merged, live connector and real backup evidence remain BLOCKED

- #590 source security [PR #627](https://github.com/Blacksp1d3r/runner-mcp/pull/627) exact head `e70e11702504c3fe161900ced4afceff8c7df084`, attribution `38042225385` and full validation `38042225393` ALL SUCCESS, squash `e06fe5b7f44c92ae22d4fa291a142b6b67803db3` MERGED. Previous pending-CI section below is superseded.
- The actual connected runtime is NOT proven to run this code. Current main doctor necessarily includes three checks absent from observed 12-check connected doctor, while status/identity tool calls fail. To progress #590, require bounded *operator-private read-only* proof of installed source/protocol/client catalog and request-response lineage; no speculative tunnel or service restart. See docs/diagnostics/CONNECTOR_READONLY_TRIAGE.md.
- AIfordable #553 MERGED with green CI but storage binding remains unqualified. Fabric #1397 still OPEN for authorized dedicated release archive namespace/bootstrap. Runner-MCP #587/#588 OPEN, 0 real independent mirror and offline restore receipts. Physical proof remains prerequisite to GitHub artifact deletion.
- Next safe source lane: inspect #590 build identity error-unavailable handling or another independent roadmap child only after checking no agent already owns it. Do not falsely claim a source merge repairs the live connector.
- Refer to the top of `handover/SESSION_HANDOFF.md` and `roadmap/DEPENDENCIES.md` for exact SHAs, owners, tests and dependency sequence.


## Latest: 2026-10-10 — #627 source-only diagnostic CI / storage authority model merged

- Runner-MCP PR [#627](https://github.com/Blacksp1d3r/runner-mcp/pull/627): source-only bounded status failure response, exact HEAD `e70e11702504c3fe161900ced4afceff8c7df084`. Commit attribution `38042225385` SUCCESS, full validation `38042225393` Ruff/pytest and artifact SUCCESS, five-minute clean demo pending at latest snapshot. **Do not merge until exact-head full terminal CI**. #590 remains OPEN for live installed-build/route correlation.
- AIfordable #553 **MERGED** at `486896fe0feac1ffbda51a8b8c3ca002f1161eb5`, CI `38038298136` SUCCESS, but storage binding still `qualified:false`. Fabric #1397 cannot skip trusted fixed namespace/bootstrap, and physical #587/#588 remain unverified.
- Connected doctor result structurally differs from current source: three mandatory diagnostic names missing, while `runtime_status` and `build_identity` failed. Classify installed/catalog/route generation as unknown. No tunnel/server restart or provider artifact deletion.
- See top of `handover/SESSION_HANDOFF.md` for exact dependencies, PR/head, test evidence and next actions. **This 2026-10-10 section supersedes older queued/success examples, including the 2026-10-03 instruction to restart watchers.**


## Latest: 2026-10-10 — supersedes the 2026-10-03 live-restart notes below

1. **Do not replay October 3 launcher/restart suggestions without authorized current state.** Installed runtime is not proven by this chat: `runtime_status` and `build_identity` returned generic errors, `runtime_doctor` returned WARN (0 failures, 3 warnings). See #590 and latest `handover/SESSION_HANDOFF.md`.
2. Protected backup #587 code gates #621–#626 are MERGED with full exact-head green CI; latest #626 squash `5aba8423594290a7837208e53721234dfe0df778`. Both #587 and #588 remain OPEN for **physical proof**, not more synthetic/source-only merge.
3. Current dependency chain: AIfordable #537/PR #553 fix isolated topology test clocks and qualify live storage authority (binding currently unqualified) -> Fabric #1397 qualified dedicated archive namespace/bootstrap -> Runner-MCP #586 live read-only readiness -> #587 2/2 physical active+rollback archive mirror and receipts -> #588 actual offline independent restore and cleanup -> provider artifact disposition review. No deletion/mount/sudo/tunnel or operator action until prior gates genuinely passed.
4. AIfordable #553 exact previous head `fea120cb18ab87d8ece7627b539ff27a981bd5a7`, CI `38035068769` FAILED 9 topology tests (1,352 passed), owner notified to fix test date 2026-10-08 versus registry date 2026-10-10 while keeping fail-closed future-dated rejection.
5. Safe independent source task: review #590 per-tool status/identity error handling. Issue has bounded code-path hypothesis and tests proposal; don't treat it as confirmed tunnel failure. Check upstream current PR/CI before opening duplicate branch.
6. Master v1.2: verify GitHub state and CI at exact head before all merges; update all canonical handovers and Failure Index at material changes.

---

Updated: 2026-10-03

## Goal

Consume only the two remaining source-supported watcher restart markers, then continue directly with Runner Fabric / Agent Bus live qualification.

## Current invariant state

- Installed runtime-code commit: `9dc9d2bfa09b25deff7a5186b9f12252c84cdd52`.
- Successful self-update job: `c6602347fe0646ffa9e20a0f638a2967`.
- Runner MCP operational; emergency stop inactive; install recovery clear.
- Doctor: 0 failures / 0 warnings.
- Agent Bus convergence: `state=clear pending_results=0`.
- `last_installed_commit=9dc9d2bfa09b25deff7a5186b9f12252c84cdd52`.
- `install_recovery_pending=false`.
- `restart_pending=true`, `pending_restart_count=2`.
- Remaining markers: `github-watcher` and `completion-watcher` at the installed commit; `server` is clear.
- Source contract: each long-running watcher invokes `run_restart_if_requested`, which safely removes its validated marker and re-execs the fixed component; failed re-exec restores the marker.

## Next engineering action

1. Resume/start `runner-mcp github-watcher run` under the dedicated service-user runtime; allow one normal cycle to reach its restart check.
2. Resume/start `runner-mcp completion-watcher run` under the same runtime; allow one normal cycle to reach its restart check.
3. Confirm only `restart_pending=false` and `pending_restart_count=0`.
4. Run Runner Fabric #590 isolated Agent Bus work-unit qualification with GitHub/source-control credentials absent and GitHub HTTPS probes denied.
5. Prove one worker-process restart/replay with no duplicate execution and convergence back to `clear`.
6. Only after that qualify/register the separate GitHub fallback identity/pool, independent drain/disable, then persistent activation.

## Do not repeat

Do not repeat MCP health/server startup checks, mailbox end-to-end proof, lint/unit qualification, pip/setuptools checks, baseline wheel staging, origin/fetch/target reachability, queue/worker idle checks, stale site-packages investigation, or the self-update proof. Do not manually unlink restart markers.
