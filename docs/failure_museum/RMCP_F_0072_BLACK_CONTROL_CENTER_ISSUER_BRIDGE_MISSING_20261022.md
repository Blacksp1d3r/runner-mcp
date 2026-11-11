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

## 2026-10-22 — CI recurrence prevention and source closure

- During PR #804, exact-head CI first rejected newly registered MCP tools because the frozen `docs/operations/TOOL_CATALOGUE_BASELINE.json` still counted 100 instead of approved 103. Updated baseline and the attestation test together, without suppressing the safety gate.
- Second round Ruff import-order check rejected the unsorted `config` / `control_center_black` imports. Reordered imports. Subsequent exact-head CI (validation #39747583227, clean Ubuntu #39747583162, attribution #39747583241) SUCCESS, then PR #804 SOURCE MERGED `ea641e691796556cd9f612b01946d7ab45951d5e`.
- Prevent new feature-tool PRs from omitting approved static tool-catalogue baseline/test updates. These CI errors were source/process bugs, not a physical Control Relay outage. Physical original-client Black result ACK remains WAIT; no production changes.


## 2026-10-23 — Original publisher correct-host configuration directory mismatch

- Original `github-runner` / `gha-runner` PID/start-generation guarded operator read-only: active parent gets private Runner-MCP config from its existing CLI, and that config is valid but `af585-control-issuer.env` is MISSING there. The existing separately owner-private Runner-Fabric sibling file was already proven nonsecret-shape PASS **and actually authenticated against** the original fixed SQL GET as `runner:control`, with SQL command still absent. Source #813 expected only the Runner-MCP directory. This is *two verified distinct namespaces*, not a missing token in the private Infrastructure Authority.
- Fail-safe prevention: the one existing qualification loader may examine the standard same-owner Fabric sibling only when the Runner-MCP config directory matches the owner's own default. Reject two competing files, weak or symlinked custody, role/origin drift and custom-path auto-discovery. Preserve separate storage, no copy/mint/rotate and no worker token promotion.
- **Source-only; no live fix claim:** original serving MCP remains 0.1.38 without qualified provenance/update, Fabric issuer process stays unbound, no original Black SQL POST/worker claim/result/digest/ACK. Previous original slot 407 RECORD and doctor PASS are not repeated. Require independently qualified existing update/rollback before any runtime cutover.
