# #747 — Fixed owner-local coding workspace through Runner-MCP

## Goal
Expose two bounded MCP tools: `coding_workspace_preflight(worker_id)` and `coding_workspace_prepare(worker_id, work_unit_id)`, without exposing generic mkdir, host/guest target, absolute paths, sudo, Incus, Git credentials or shell arguments.

## Evidence and scope
- User already created per-worker private roots with `jobs` and `patches` subdirectories and verified adequate free disk (physical measurement remains private).
- Source-only capability operates on the **same filesystem and UID as the actually serving Runner-MCP process**, never on another host inferred from topology.
- Exactly one trusted private per-runtime binding: `RUNNER_MCP_CODING_WORKSPACE_WORKER` (claude|qwen), `_OWNER` (local non-root account), and `_ROOT` (pre-existing local root). Every key must be set, with correct effective user.
- Caller controls **only** one known worker alias and opaque bounded work-unit ID. Result contains no private path/username. Each call creates only `jobs/<work-unit>` and `patches/<work-unit>`, 0700, existing-owner only.
- Root and parent traversal use no-follow directory descriptors; symlinks/foreign UID/unsafe modes/incomplete layout/incomplete config blocked. Repeated same task is idempotent. Bounded ≤128 task slots, no deletion/overwrite, recovery_required on uncertain partial failure.
- Registered through existing authenticated MCP tool catalogue and request audit. The separate Agent Bus issuer/lease/fence/ACK stays a requirement for automatic cross-host dispatch, not silently enabled here.

## Acceptance
Pure fixture tests cover worker mismatch, missing binding, UID mismatch, unsafe path/parents, invalid IDs, partial existing, max slots, idempotence, fail-closed write interruption, and no path disclosure. Exact-head Ruff/pytest/build/installer and attribution CI on source PR. Then independent physical owner-side lab/guest deployed version + first-party exact-target invocation, NEVER directly from central wrong-host Runner-MCP.

## Links
Runner-Fabric #972 (Claude), #1579 (Qwen); Runner-MCP #747. Source from main v0.1.39, candidate v0.1.40. No new service/cost.
