# #540 — Advertised MCP schema identity source child

- status: COMPLETE_SOURCE_ONLY; LIVE_ACCEPTANCE_BLOCKED
- date: 2026-10-10
- owner: Runner-MCP communication chat
- branch: test/540-advertised-tool-schema-digest
- PR: #649 MERGED
- CI: exact HEAD 8c0ad02ac315e28b7f09e69e09fe0846053f26ea; attribution 38076184097 SUCCESS; full validation 38076184096 SUCCESS (Ruff, 2774 pytest, built release artifact, clean demo)
- source_test: authenticated ASGI same-session build_identity vs tools/list digest
- live_installed_schema: UNKNOWN
- operator_approved_release: BLOCKED_EXTERNAL (#942/#943)
- parent #540: OPEN
- parent #590: OPEN
- Claude/EnerCue: NO_DISPATCH

- squash_merge: 2a8ca54272fe6cf1cc12a2f2aa7919caf8481359

## Next
Review exact-head CI. If mismatch, locate expected versus actual canonical schema rules; fail closed, don't adjust digest to hide difference. On source merge update failure record and handover. Do not infer production version or restart hosts.
