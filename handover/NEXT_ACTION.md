<!-- doc-memory:archive-pointer -->
> **Actief bestand.** Oudere gedateerde secties staan ongewijzigd in `handover/NEXT_ACTION.archive-*.md` (manifest met SHA-256 per sectie ernaast). Lees die niet standaard; zoek gericht, bv. `grep -n "#1234"`.
>
> **Nog open werk waarvan de historie in het archief staat** (open issue/PR op het moment van archiveren; status volgt GitHub):
> - #739 F30 Black: private GitHub Release bytes importer with one-time read-only auth and immutable offline  — laatst 2026-10-19 in `handover/NEXT_ACTION.archive-2026-10.md`
> - #735 First-host bootstrap: explicit local setup prerequisite and safe Agent Bus not-initialized status — laatst 2026-10-17 in `handover/NEXT_ACTION.archive-2026-10.md`
> - #669 fix(build identity): attesteer actieve wheel en bronrevisie, geen oude self-updatecommit als actuele — laatst 2026-10-19 in `handover/NEXT_ACTION.archive-2026-10.md`
> - #642 F30: enforce qualified host-local tool denial at MCP dispatch without changing the shared catalogue — laatst 2026-10-11 in `handover/NEXT_ACTION.archive-2026-10.md`
> - #634 BPA-02B: qualify local Git/storage authority before root project manifest — laatst 2026-10-10 in `handover/NEXT_ACTION.archive-2026-10.md`
> - #630 Repository blueprint: incremental legacy compatibility adoption — laatst 2026-10-10 in `handover/NEXT_ACTION.archive-2026-10.md`
> - #590 Connector: runtime_status and runtime_doctor fail internally before runtime evidence — laatst 2026-10-11 in `handover/NEXT_ACTION.archive-2026-10.md`
> - #587 I5/F34: mirror only the protected Runner Fabric release set to independent custody — laatst 2026-10-10 in `handover/NEXT_ACTION.archive-2026-10.md`
> - #381 Bounded service alias for AIfordable subscription coding worker lifecycle — laatst 2026-10-10 in `handover/NEXT_ACTION.archive-2026-10.md`
> - #341 Fleet Update executor slice: bounded version, reconnect and recovery proof — laatst 2026-10-23 in `handover/NEXT_ACTION.archive-2026-10.md`
<!-- /doc-memory:archive-pointer -->

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
