# Connector recovery and response-lineage acceptance

Scope: #590 (intermittent read-only invocation failures), #333 (tunnel startup and readiness), #540 (runtime/catalogue generation compatibility). This document deliberately contains no private hostnames, identifiers, ports, filesystem paths, credentials, or endpoint topology.

## Verified operator evidence (2026-10-09)

- Existing dedicated tunnel-client executable was installed under the designated service identity with a verified SHA256 match to the operator-observed binary; installed client version 0.0.16. A hash match establishes byte equality, not vendor provenance.
- Existing protected environment source was found; its presence and restricted access were verified without exposing its values.
- A protected-profile doctor check succeeded once the environment was made available, including local MCP connectivity and resource metadata. An authentication challenge at the local MCP endpoint was expected, not proof of authorization for every call.
- A dedicated system unit was configured and verified. Operator reported enabled and active/running, no service-manager restarts, and local readiness HTTP 200. Post-reboot recovery was **not** tested.
- Through ChatGPT the four read-only tools `list_projects`, `runtime_status`, `runtime_doctor`, and `worker_status` have each returned a structured success at least once; at other times the same tools returned a generic internal failure.
- Local authenticated MCP dispatch passed earlier CI tests (#595). That does not prove consistency of the live connector.
- Tunnel logs show multiple requests forwarded to MCP. Forwarded is **not equivalent** to a completed MCP response delivered to the original client.
- Startup logs included optional OAuth discovery and Harpoon warnings. They must not be bypassed by relaxing transport security without a verified root cause.

## Ownership

- #333: readiness, process-loss and boot-recovery acceptance. Preserve the current working service until a safe maintenance window.
- #540: stale runtime/tool catalog generation fencing and deterministic compatibility response. Do not duplicate its work in #590.
- #590: identify the first failing edge of intermittently failing read-only invocations and verify request/response correlation. Prior local test #595 is its baseline.

## One-pair diagnostic procedure

1. Choose one bounded read-only client call. Record outcome class, UTC timestamp, and only an authorized opaque correlation handle **if one is supplied by the diagnostic surface**.
2. Through approved private diagnostics, look for matching tunnel ingress and forwarding state. Distinguish `received`, `forwarded`, `completed`, `failed`, and `unknown`; never infer completion from forwarding.
3. Confirm the same handle at the MCP-server receipt and completion boundary, if such evidence is safely available. If absent, classify unknown and stop.
4. Compare with client response-delivery evidence. The answer must correspond to the original logical request/session and current catalog generation. The physical TCP connection need not be identical.
5. Attribute to the earliest failing boundary; do not change ports, authentication, listener configuration, or worker capacity on speculation.
6. After a verified correction, qualify `list_projects`, `runtime_status`, `runtime_doctor` through a fresh authorized connector session. Separately schedule post-reboot readiness with CI workload coordination.

## Negative tests to implement under existing owners

- Simulated stale catalog generation must fail closed with an actionable compatibility reason (#540).
- Simulated mismatched response correlation must be rejected without delivering data to another requester (#590).
- Configured but stopped/unrestartable tunnel must present explicit degraded readiness (#333).
- A successful server-side completion with missing client delivery must remain a downstream transport/correlation problem, not be reported as server business logic failure.

## Privacy and release gates

No raw transport capture, request payloads, credentials, internal mapping or infrastructure-specific identifiers in GitHub. No live restart, self-update, fabricated health claim, environment change or release without separately approved operational evidence. Track correction SHA, exact CI result and rollout acceptance before closure.

**As of 2026-10-09: tunnel autostart and local readiness observed; request/response lineage still UNQUALIFIED and #590 remains OPEN.**
