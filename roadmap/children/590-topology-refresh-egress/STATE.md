# #590 — Topology refresh egress child state

- status: SOURCE_PR_OPEN_DRAFT; CI_AND_REVIEW_PENDING
- owner_lane: Runner-MCP communication / #590
- related_original_client: 0.1.4 manually installed; 100/100 files matched pinned wheel; source version differs from canonical self-update state until proper attestation
- PR: https://github.com/Blacksp1d3r/runner-mcp/pull/668
- stacked_base: https://github.com/Blacksp1d3r/runner-mcp/pull/661 (source commit 6adf6afe8054025a3b575ebde37b670522069378)
- version: 0.1.5; not published, installed or merge-authorized
- source_change: fixed explicit no-proxy/no-redirect opener with synthetic security tests
- initial_ci: attribution PASS, release-version guard PASS, 95-tool catalogue PASS, compilation PASS; first Ruff import-order issue corrected in follow-up commit; fresh head CI pending
- risk_state: SYNTHETIC_SOURCE_RISK_NO_LIVE_EXFILTRATION_OBSERVED
- live_deploy: NONE; installed 0.1.4 preserved
- original_client_tool_catalogue: 88 exposed versus source 95 registered, exactly seven missing from connected registration, still unqualified
- related_gates: #341 attended rollback/ACK, #590 method-level transport and schema exposure, Fabric #972 Claude Q7, A6 #942/A7 #943

## Next action
Check the current PR #668 exact head and all CI terminal results; fix real failures without bypass. Request independent review; merge only after base #661 reviewed/landed and rebase/unique-version checks. Privately qualify original client tools/list, source attestation and tunnel process separately, without using unsafe live topology refresh.
