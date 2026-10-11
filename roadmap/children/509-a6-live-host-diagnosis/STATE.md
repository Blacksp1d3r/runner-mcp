child_id: RMCP-509-live-host-diagnosis
status: BLOCKED_EXTERNAL
owner: Runner-MCP #509
linked_issues: ["Runner-MCP #590", "Runner-MCP #341", "Fabric #942", "Fabric #943"]
parallel_source_fix: "Runner-MCP PR #655 head c8dc9b7340eb92e467cbd749c885f3b605eef411 CI GREEN, separate from live qualification"
source_runtime_alignment: UNQUALIFIED
same_client_result_ack: UNQUALIFIED
actual_service_asset_id: UNQUALIFIED
active_process_artifact_digest: UNQUALIFIED
fixed_a6_roots_and_11_bindings: UNOBSERVED
peer_a6_prepare: FALSE_OBSERVED_UNQUALIFIED
peer_synthetic_probe: FALSE_OBSERVED_UNQUALIFIED
agent_bus_relay: DEGRADED_UNKNOWN
production_changes_applied: false
next_safe_action: "Obtain first-party enrolled asset+active process identity tied to one original-client read-only call, then run current sanitized A6 doctor before any mutation."

## Source-vs-runtime checkpoint

Current main server has sanitized `fabric_a6_binding_state` and activation checks; connected runtime had stale 12-check doctor or generic error. Connected build_identity returned source a0fd964c... and null artifact. Connected Fabric bridge appeared ready but A6 named tool flags false and operational Agent-Bus relay evidence unavailable. Classify this as incomplete identity/capability evidence, not a proven config root cause. Reuse RMCP-F-0002 and issue #509 chronology rather than duplicate an incident.
