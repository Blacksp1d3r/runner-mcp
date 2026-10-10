# NEXT ACTION

## Latest coordination: 2026-10-10 — Fabric #1428 remains OWNER_IN_PROGRESS, WAITING_CI_FIX

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
