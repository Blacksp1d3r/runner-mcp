# Runner-MCP #509 — A6 private env hardlink guard

status: SOURCE_CANDIDATE_CI_PENDING
source_version: 0.1.58 (candidate only)
related_failure: RMCP-F-0060
production_mutation: false
live_original_client: 0.1.38 / A6 not_configured_0_of_11 / self_update_ready=false

Source changes: reuse existing fixed A6 inspection and repair, reject multiply-linked 0600 private env files before reading/merging bindings, maintain sanitized output, add non-mutating synthetic negative tests. No new authority or service restart.

Operational acceptance still WAIT: correct host original six-role loaded wheel/source witness #669, physically independent A6 journal Fabric #1617/#942, disconnected A7 rollback #943, original-client ACK Fabric #1556/#1563 and AIfordable relay #585, Fabric #924 one authorized targeted cutover. Do not bypass.
