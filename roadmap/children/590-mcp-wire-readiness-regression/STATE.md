# Runner-MCP #590 — MCP read-only wire-test state

status: COMPLETE_TEST_GUARD_ONLY
owner_issue: Runner-MCP #590
merged_pr: https://github.com/Blacksp1d3r/runner-mcp/pull/708
merged_commit: 6e3e8e9dcffb9a6fe7b6fb4b7436612f1ad2fa1a
exact_tested_head: 54f682ddd584dd4ede1b9c05e72b62b9793fc7c6
validation_ci: 38933713969 SUCCESS (Ruff, pytest, distribution build, five-minute demo)
attribution_ci: 38933714024 SUCCESS
source_version: 0.1.26 (unchanged, TESTS ONLY)
production_changes_applied: false

New MCP protocol integration test covers authenticated initialize and actual tools/call for both update-readiness error cases and optional CI guest unavailable, including error redaction, unknown guest state, unchanged valid success payloads, and no mutation calls. This does NOT qualify remote original-client ACK, installed source/wheel identity or any update/revert operation.

Next: #669 actual independently attested serving process/wheel and #942/#943 canary/restore acceptance. #590/Fleet #924 stay open for live failures.
