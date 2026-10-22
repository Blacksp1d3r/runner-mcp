# #341 — fixed Black Control Center runtime_status bridge

Owner: Runner-MCP source. Integration dependencies: Runner-Fabric #924/#1556/#1563 and AIfordable #585.

## Owner-approved order, 2026-10-22

1. Prove one real machine-authenticated original request `qual:black:runtime:v1`, fixed `runtime_status`, fixed target `runner:black`, SQL claim/terminal result/digest and explicit same-original-issuer retained ACK.
2. Prove one real Claude programming task and one real Qwen programming task on their existing qualified labworkers.
3. **Only afterward:** optional human Control Center login/MFA/OIDC. A nonexistent human login screen must not block steps 1–2.

## Canonical existing implementation (source DONE)

- AIfordable #636 extends the **existing SQL Control Relay** with exactly three fixed machine-issuer routes: submit, original-owner status and explicit ACK. Auth via its existing runner-service identity provider; separately authorized original issuer subject must be **`runner:control`**, never worker `runner:black`/`runner:primary`. Its distinct private credential, SHA-256-only identity record and generation/expiry are **operator/host custody**, not public source.
- Runner-Fabric #1715 provides the preexisting Agent MCP `control_center_black_submit/status/ack` methods and `AIfordableMachineIssuerExchange`. Private `RUNNER_FABRIC_CONTROL_RELAY_ISSUER_MODE=machine_control_credential` with privately custodied origin/credential must be configured before tools are offered; human MFA operator mode is historical/optional, not required for the machine test.
- Runner-MCP #804/#806/#809/#810 provide the existing three bounded first-party proxy tools and fail-closed source validators for exact machine requester, fixed request/target/operation, fingerprint, positive worker generation, terminal digest, actual result payload and durable explicit ACK + post-ACK readback.
- No second relay, controller, tunnel, updater, arbitrary shell/host/operation, new authentication suite or blind six-role replacement. Existing A6/A7/provenance checks apply to serving primary upgrade.

## Live evidence and remaining gates — 2026-10-22

- **PASS** original canonical AIfordable backend and Nginx installed on same original relay, physical Black outbound HTTPS GET new machine issuer result endpoint **401 application/json without credential** and **403 application/json using real existing `runner:black` credential**. These are genuine auth/role-boundary and transport proofs; no SQL command was queued.
- **PASS** physical Black v0.1.30 existing Fabric worker locally executed a real authenticated `runtime_status`, `result_code=ok`; three original user services healthy.
- **PASS** connected first-party Fabric Agent handshake now reports **serving** source `2ff81b299e8d0b3f156d666ddc9719b97657664e` after already finished managed local update; this is not dispatch acceptance.
- **SOURCE PASS ONLY** Runner-MCP v0.1.83 [PR #810](https://github.com/Blacksp1d3r/runner-mcp/pull/810) merged `6ed9ad1a4edc124b2e39d1e82b086cde78bca243`; exact-head release reservation, Ruff/pytest, built wheel, clean Ubuntu, demo and attribution PASS. Child-state/handover reconciliation [PR #811](https://github.com/Blacksp1d3r/runner-mcp/pull/811) merged `9f1b7a3d573b44cdf71db9cc5c16ea2097a38229`.
- **WAIT** distinct `runner:control` does **not** exist in actual original SQL relay private identity provider; required Fabric private machine-issuer binding not yet demonstrated. Connected six-role primary Runner-MCP still **0.1.38**, source/wheel SHA unavailable, `self_update_ready=false`, A6 0/11; do not force cutover. Agent Bus relay `UNKNOWN`, `execution_enabled=false`.
- **NOT PROVEN** physical original client POST → durable SQL one-shot → positive `runner:black` claim/generation → terminal result/payload/digest → same-original `runner:control` ACK with retained SQL status. Never count HTTP 401/403, local Black result or GitHub/staging tests as that ACK.

## Exact next action and acceptance

AIfordable #585 original-host owner uses only **existing authorized private identity configuration** to qualify `runner:control` (never print/check in any credential); Fabric #924 binds that same original controller to its existing private machine issuer mode and verifies actual tool presence. Runner-MCP #341/#669 then qualifies the correct serving release with the *existing* rollback-capable upgrade path, not a blind primary six-role switch. Submit exactly one existing `qual:black:runtime:v1` read-only Black command, verify actual positive worker claim/result fingerprint/digest, explicitly ACK as the same original authenticated issuer and inspect persisted status. If any private authorization or serving version is missing, remain WAIT, and work independently without improvising another transport.
