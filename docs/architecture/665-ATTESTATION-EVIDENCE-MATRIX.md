# #665-attestation — evidence boundary and synthetic acceptance matrix

Status: PROPOSED / NOT IMPLEMENTED. Companion to #665-registry and existing source-only #649.

## Evidence hierarchy

1. A requested version, client-declared tool ID or untrusted metadata is **reported**, never attested.
2. An exact release manifest with verified artifact digest and source SHA is **build evidence**, not evidence it is serving.
3. Authenticated actual process identity, current policy generation and isolated real `tools/list` name/inputSchema/outputSchema hash is **serving evidence** only for the measured process and session.
4. Actual original-client result and ACK prove communication across the checked route, never automatically host rollback safety.
5. No observation or stale observation must result in `UNKNOWN` or `STALE_INVENTORY`, not healthy or updated.

## Comparison contract

Compare normalized tuple (service asset authority, source SHA, artifact/payload SHA-256, advertised tool+schema digest, host policy generation, session generation). SemVer is informational: equal SemVer with different source SHA must be marked inconsistent. A tool absent on an older supported build is `UNSUPPORTED_TOOL_VERSION`, not necessarily a malicious event; foreign asset/route and unverifiable metadata have distinct failure classifications.

## Negative scenarios

| Scenario | Safe result |
|---|---|
| Same version, different source hash | VERSION_MISMATCH; no dispatch |
| Same source, different exact wheel digest | Require payload/approved artifact provenance check; do not assert identical wheel |
| Tool list same names, input schema differs | SCHEMA_MISMATCH |
| Tool list missing the expected tool | UNKNOWN_TOOL or negotiated UNSUPPORTED_TOOL_VERSION |
| Client supplies fake SHA | Ignore; require first-party attested serving evidence |
| Expired session/catalogue cache | Requalify on new explicit request; no mutating replay |
| Server healthy but original client has no response/ACK | DELIVERY_UNVERIFIED; no production promotion |
| Missing build or policy identity | UNKNOWN; fail closed for high-risk operations |
| Two legitimate tenants present the same failure | Separate asset/tenant incidents, no cross-tenant facts |

## Rollout boundaries

This is source-only acceptance specification and allocates no host authority. First implementation may prove isolated in-process attestation; live serving validation requires #590 and AIfordable #428, host admissions #642 and authorized Fabric A6 #942/A7 #943. No native tool name changes, active release installs or alerts here.

Next safe action: after #667 integration, capture reviewed registry ID/schema bindings with isolated actual tools/list, implement bounded attestation matcher in a new uniquely versioned source PR and negative unit tests.
