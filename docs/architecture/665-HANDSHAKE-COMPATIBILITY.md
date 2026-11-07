# #665-handshake — optional MCP-compatible build negotiation

Status: PROPOSED / NOT IMPLEMENTED. Child: roadmap/children/665-handshake.
Prerequisites: approved #665-registry, serving evidence #665-attestation, existing #590 no-replay transport, #664 legacy compatibility.

## Compatibility first

Never change the standard MCP `tools/list` and `tools/call` names, or require an unrecognized metadata field from a generic MCP client. A proprietary prefix is not authorization. The extension must be explicitly negotiated between trusted first-party peers, using a dedicated namespaced optional capability and existing authenticated session transport. Unextended peers retain existing allowed behavior and must not gain new high-risk privileges from fallback.

## Proposed wire-level capability (illustrative, not yet implemented)

Namespace: `com.aifordable.runner-mcp`.
Negotiation version: `1`.
Optional client and server capability metadata:
- `supported_contract_revisions`: bounded positive integers
- `expected_registry_sha256`: hex digest of approved immutable tool registry
- `observed_catalogue_sha256`: digest of actual server-advertised name/inputSchema/outputSchema
- `actual_build_fingerprint`: independently attested source SHA and artifact digest
- `policy_generation`: serving policy generation, not client-provided authority
- `opaque_session_generation`: bound to authenticated target, never a reusable bearer

No arbitrary secret/path/customer payloads in public telemetry. Compare authenticated observations rather than trusting a version string supplied by a caller.

## Machine decisions

| Condition | Decision |
|---|---|
| Both peers support version 1 and actual fingerprints match | NEGOTIATED |
| Generic MCP peer, no extension | LEGACY, preserve reviewed existing operations |
| Extension revision unsupported | INCOMPATIBLE_EXTENSION; no unsafe downgrade for protected actions |
| Authenticated server fingerprint changes mid-session | STALE_SESSION; invalidate cache |
| Registry or schema digest differs | SCHEMA_MISMATCH; block before side effects |
| Connection lost after possible mutating work | EFFECT_UNKNOWN; do not automatically replay |
| Claimed namespace/build not authenticated | UNTRUSTED_TOOL_IDENTITY |
| No actual serving evidence | UNKNOWN; do not label compatible |

## Test obligations

1. Simulated legacy peer operates with the existing MCP wire format; unknown extension ignored without creating privilege.
2. Two fresh first-party peers negotiate a registry and schema digest; fixed build evidence is checked.
3. Malformed/duplicate capabilities, stale generations, mismatched digests and spoofed claimed build fail closed for protected actions.
4. A changed tool inventory invalidates old cache; client requalifies only on next separate explicit request.
5. Delivery acknowledgment from the original client is separately proven; handshake alone never certifies deployment success.
6. No mutating call retries on unknown HTTP status, redirect, timeout or expired MCP session.

## Owner and implementation gate

Implement only after registry/attestation boundaries are independently reviewed. Separate source PR with unused incremented version under #661/#663. Runtime rollout requires #590 client route, #642 host policy, and Fabric A6 #942/A7 #943 independent restore and ACK; no self-authorized deployments.
