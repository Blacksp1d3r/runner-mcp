# STATE — #341 fixed Black Control Center bridge (2026-10-22)

- Phase: SOURCE MERGED (PR #804, commit ea641e691796556cd9f612b01946d7ab45951d5e; Runner-MCP v0.1.80); actual issuer and ACK: WAIT.
- Active central first-party Runner-MCP still v0.1.38; no authenticated Black issuer tool installed in that serving generation.
- Black v0.1.30 and its three services reported locally stable; relay auth-only PASS does NOT prove terminal ACK.
- Fabric PR #1701 merged, receipt-bound status source exists. Fabric Agent MCP does NOT currently expose the three fixed issuer methods. It must reuse its existing commandclient with operator REST-compatible MFA bearer; do not duplicate route/client.
- AIfordable #585 PR #632 SOURCE CANDIDATE (operator REST terminal digest/ACK and proper original MFA requester), not a qualified live deployed API.
- Test/CI: CI workflows #39747583227 (Ruff, pytest, release gate, built artifact, demo), #39747583162 (clean Ubuntu) and #39747583241 (commit attribution) all SUCCESS for tested PR head 202b0141c0f28e03cd9a4f2ce0479f17008c7483. This is source-only, not live command evidence.
- Invariants: no arbitrary target/operation/endpoints or new credentials; no mutable six-role services, updater, tunnel, release, shell or direct unmanaged host access; no false “ACK proven” on health/HTTP200/queued.
- Next: Fabric ships the fixed Agent MCP adapter via owner task #924/#1556; AIfordable merges/qualifies #632; original requester MFA and Black terminal result + ACK must be observed independently. Leave #341 OPEN until then.
