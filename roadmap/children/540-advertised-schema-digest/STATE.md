# #540 — Advertised MCP schema identity source child

- status: IMPLEMENTING_SOURCE
- date: 2026-10-10
- owner: Runner-MCP communication chat
- branch: test/540-advertised-tool-schema-digest
- PR: PENDING
- CI: PENDING
- source_test: authenticated ASGI same-session build_identity vs tools/list digest
- live_installed_schema: UNKNOWN
- operator_approved_release: BLOCKED_EXTERNAL (#942/#943)
- parent #540: OPEN
- parent #590: OPEN
- Claude/EnerCue: NO_DISPATCH

## Next
Review exact-head CI. If mismatch, locate expected versus actual canonical schema rules; fail closed, don't adjust digest to hide difference. On source merge update failure record and handover. Do not infer production version or restart hosts.
