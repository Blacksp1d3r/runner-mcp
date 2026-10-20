# Runner-MCP #665 — recovery-aware alert suppression
status: SOURCE_CANDIDATE_CI_PENDING
source_version: 0.1.60 (not installed)
owner_issue: #665
failure_record: RMCP-F-0062
source_file: src/runner_mcp/tool_alert_dedupe.py
test_file: tests/test_tool_alert_dedupe.py
live_notifications_enabled: false
serving_runtime_updated: false

Scope is pure metadata summarization. Trusted observer/issuer, persisted alert delivery, cooldown journal, original-client ACK and host policy all remain separate future work. Exact-head validation/Ubuntu/attribution required before source merge.
