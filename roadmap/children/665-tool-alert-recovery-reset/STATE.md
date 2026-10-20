# Runner-MCP #665 — recovery-aware alert suppression
status: SOURCE_MERGED_LIVE_UNQUALIFIED
source_version: 0.1.60 (merged, not installed)
owner_issue: #665
failure_record: RMCP-F-0062
source_file: src/runner_mcp/tool_alert_dedupe.py
test_file: tests/test_tool_alert_dedupe.py
live_notifications_enabled: false
serving_runtime_updated: false

Scope is pure metadata summarization. Trusted observer/issuer, persisted alert delivery, cooldown journal, original-client ACK and host policy all remain separate future work. Exact-head validation/Ubuntu/attribution required before source merge.

merged_pr: https://github.com/Blacksp1d3r/runner-mcp/pull/779
merged_commit: 2188fd3f89d05ae6c50d0fbe5a3216de0dc5a740
validation: 39469163886 SUCCESS
ubuntu: 39469163938 SUCCESS
attribution: 39469163766 SUCCESS
