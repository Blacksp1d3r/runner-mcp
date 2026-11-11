# FASTER-13 baseline — state

- Status: COMPLETE_SOURCE_ONLY (actual loopback MCP RTT not measured).
- Branch: chatgpt/383-mcp-local-fastpath-synthetic-baseline.
- Parent source main: 3411ea8dc861bde0f2f3773362c2a04781d313d3; source version candidate 0.1.20.
- Module/tests/CLI are completely local and synthetic; no live networking.
- Next: exact-head CI and source merge, then record bounded evidence and continue independent functional roadmap while real loopback host benchmark remains externally scoped.

- 2026-10-16: PR #698 squash MERGED `844062bec7602df5131f7157f1a8ff074a41653f` from exact CI-green head `79633aabd751a761d9b4b27ab45b7cde03f668a4`. Runner MCP validation `38891328157` Ruff/pytest/release/demo, Ubuntu `38891327629`, attribution `38891327767` all SUCCESS. RMCP-F-0037 loop-variable closure fix qualified. Phase 1b real loopback HTTP MCP/CPU benchmark still not performed and requires authorized host environment; no end-to-end speedup claim.
