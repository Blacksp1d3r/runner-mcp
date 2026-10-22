# RMCP-F-0072 — Black runtime_status issuer absent despite healthy worker

Date: 2026-10-22
State: SOURCE FIX CANDIDATE; physical root-cause end-to-end proof WAIT.

Observed:
- Connected original Runner-MCP 0.1.38 has worker-side control relay but NO operator-side Control Center issuer MCP command; Fabric source commandclient is not surfaced by its Agent MCP.
- Fabric client assumed `/internal/control-relay/commands` and `X-AIfordable-Control-Credential`; AIfordable's real operator route is `/control-relay/commands` with existing MFA bearer/capability, HTTP 201 and different schema. Internal routes are worker claim/complete/fail. Claim/heartbeat/synthetic probe != original result ACK.
- Existing AIfordable Control MCP has durable result digest/ACK. AIfordable #585 PR #632 proposes extending SAME operator REST API with digest/ACK, not a second relay. Fabric #1701 already protects source receipt-to-status correlation but cannot by itself issue a live command.

Prevention:
- Keep exactly fixed `runner:black` + `runtime_status` through existing Fabric bridge. Require Fabric Agent MCP to expose only three bound issuer/result/ack operations that use its existing commandclient and properly authenticated original MFA operator route.
- Runner-MCP source validates request ID, exact target and operation, canonical fingerprint, original authenticated subject+MFA, queue version, bounded result, terminal digest, explicit ACK and post-ACK readback. Reject unsupported peer tools and mismatches.
- Tests include wrong-host, wrong-operation, wrong-requester, weak MFA, stale fingerprint, premature result and ACK, contaminated result and mismatched ACK.
- No host/update/auth changes; physical proof stays WAIT until original issuer -> Black -> result -> explicit original-client ACK observed with durable evidence.
