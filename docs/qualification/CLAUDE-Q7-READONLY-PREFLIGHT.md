## Application-level Q7 communication errors — 2026-10-10

Runner-MCP [PR #646](https://github.com/Blacksp1d3r/runner-mcp/pull/646) source-merged `a8833190b62e1ace6d88617951116cca541cf8ba` after exact-head Ruff/2768 pytest/release/demo/attribution SUCCESS. The authenticated `fabric_coding_availability_qualify` tool now returns a fixed response schema `runner-mcp/coding-availability-qualification-unavailable/v1` for known application-level failures. This is **NOT** the successful Fabric qualification schema.

Constant values:
- `blocked/invalid_fixed_case`, `blocked/invalid_fixed_revision`, `blocked/operator_stop_active`, `blocked/operator_safety_unqualified`, `wait/fabric_launcher_unqualified`, `wait/q7_private_configuration_incomplete` are certain pre-invocation failures with `qualification_effect=not_started`.
- `unknown/q7_execution_unverified` and `unknown/q7_output_unverified` represent an *uncertain* effect after possible subprocess/transport invocation; require independent per-request execution/receipt reconciliation, do not resubmit blindly.
- Every failure has `result_verified=false`, `dispatch_authorized=false`, `retry_authorized=false`, no work-unit count or provider/session/private endpoint details. Fixed sanitized reason only goes to audit.

This distinguishes handler-known failures **on the installed matching release** only. A generic client/tunnel failure **before the MCP handler executes** remains #590 UNQUALIFIED. The connected client still reports the old doctor vocabulary and lacks source-merged `fabric_coding_availability_preflight` in its advertised tool set. No claim of live rollout or actual AIfordable worker/auth readiness follows. Requires qualified exact A6/A7 fleet release and request→response association without host/tunnel changes as a workaround.

# Claude Pro coding worker — bounded Q7 bridge preflight

The Claude Pro coding worker is already implemented on AIfordable behind a
dedicated `aifordable-coder` rootless identity, fixed first-party Agent Bus/
Runner-MCP lifecycle (#381), and Fabric Q7 subscription availability mapping
(#972). The operator wants **actual Claude use**, not a second worker daemon,
a second scheduler or pay-as-you-go Anthropic API charges.

## Observed transport limitation (2026-10-10)

Through the currently connected ChatGPT Runner-MCP control instance,
`build_identity()` returned the older source revision
`a0fd964c4a6fe7e0a1506a513e9b2b4059c5453a` and package version
`0.1.3`. The read-only Fabric operational snapshot/bridge preflight and
one fixed Q7 `subscription-auth-required` qualification returned generic
internal/tool errors, not a qualified Claude availability or authorization
result. They do **not** prove OAuth expiry, missing Claude binary or service
failure. The host's registered release, loaded process and client tool
catalogue may differ; do not infer a duplicate tunnel.

The existing `fabric_coding_availability_qualify` handler maps multiple
real pre-run failures (operator stop, missing exact Fabric executable, missing
private Q7 bindings) into one generic MCP error. That prevents a safe,
actionable diagnosis when the real Q7 transport is unqualified.

## New safe read-only preflight

`fabric_coding_availability_preflight()` calls the *same fixed* managed
Runner Fabric launcher and existing private configuration validation used by
Q7, but does NOT execute a subprocess or test a model session.

Exact sanitised result:
```json
{
  "schemaVersion": "runner-mcp/coding-availability-preflight/v1",
  "state": "ready-for-qualification",
  "reason_code": "bounded_q7_preflight_passed",
  "qualification_executed": false,
  "provider_session_checked": false,
  "dispatch_authorized": false
}
```

Alternate fixed statuses, without host/user/path/token/provider exposure:
- `blocked/operator_stop_active` or
  `blocked/operator_safety_unqualified`;
- `wait/fabric_launcher_unqualified`;
- `wait/q7_private_configuration_incomplete`.

Even the positive result only says *a safe Q7 qualification may be attempted*.
It never means a Claude session is authenticated, subscription billing is
qualified, a worker is registered, a durable Fabric lease/fence exists or
an EnerCue job can start.

This preflight has zero arguments, cannot invoke Claude or a shell, and logs
only the fixed safe reason. Tests cover the real authenticated MCP
`tools/call` registration, extra-argument rejection, no subprocess,
redacted response/audit and each preflight blocking state.

## Operational next gates

1. Bring BOTH intentionally distinct managed Runner-MCP installations to
   **one exact approved security release**, as required by operator/Fabric
   #924/#1439. Before control-path updates, the qualified A6 off-target
   journal and independent A7 rollback supervisor must actually be able to
   restore a broken server without the tunnel (Fabric #942/#943).
2. On the correct dedicated host, independently verify exact
   `aifordable-coder` identity, Claude Pro subscription-only auth, no API key,
   fixed rootless worker service and local endpoint + process ownership
   (AIfordable #370; Runner-MCP #381). Never print tokens or run broad sudo.
3. Run this read-only preflight on the **matching live build**, then run all
   three existing Q7 synthetic availability cases over the real bearer-
   authenticated loopback MCP route (Fabric #972) and correlate responses.
4. Qualify trusted signed Fabric intent, durable cross-host lease/fencing
   and local executor pre-action revalidation (Fabric #1398/#1400). A
   successful availability probe is not authority for a coding work-unit.
5. Admit ONE bounded disposable docs/test-only Claude task and inspect
   exact revision, attribution, tests, independent validation and return ACK
   before EnerCue work (#88/#89). Never auto-push/merge/deploy or purchase
   credits.

Source-only merge does NOT change current installed runtime or make Claude
available until these physical gates are observed.
