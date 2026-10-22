# STATE — #341 fixed Black Control Center bridge (2026-10-22)

- Phase: SOURCE CANDIDATE (Runner-MCP v0.1.80); actual issuer and ACK: WAIT.
- Active central first-party Runner-MCP still v0.1.38; no authenticated Black issuer tool installed in that serving generation.
- Black v0.1.30 and its three services reported locally stable; relay auth-only PASS does NOT prove terminal ACK.
- Fabric PR #1701 merged, receipt-bound status source exists. Fabric Agent MCP does NOT currently expose the three fixed issuer methods. It must reuse its existing commandclient with operator REST-compatible MFA bearer; do not duplicate route/client.
- AIfordable #585 PR #632 SOURCE CANDIDATE (operator REST terminal digest/ACK and proper original MFA requester), not a qualified live deployed API.
- Test/CI: source-only unit tests added on PR candidate; mark green only after exact-head CI evidence.
- Invariants: no arbitrary target/operation/endpoints or new credentials; no mutable six-role services, updater, tunnel, release, shell or direct unmanaged host access; no false “ACK proven” on health/HTTP200/queued.
- Next: Fabric ships the fixed Agent MCP adapter via owner task #924/#1556; AIfordable merges/qualifies #632; original requester MFA and Black terminal result + ACK must be observed independently. Leave #341 OPEN until then.
