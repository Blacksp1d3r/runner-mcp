## 2026-10-22 — v0.1.82 machine requester evidence SOURCE PR, live Black still WAIT

The owner deferred human Control Center login/MFA until Black, Claude and Qwen are genuinely working. Runner-MCP #341 source validator previously hard-required `mfa` even for independently authenticated `machine` relay issuer. Source v0.1.82 narrowly admits only the original fixed `qual:black:runtime:v1` and `runner:control` machine issuer claim from the EXISTING authenticated Fabric Agent MCP, retaining the old MFA path. No client-selected host, credential, shell or service; no caller field is an authentication claim. Tests cover same-original actor retained ACK and wrong worker/identity/digest negatives. **Exact CI/merge pending**; current central actual 0.1.38 and physical `runner:black` original result/ACK still WAIT. AIfordable #636 and competing #637/Fabric #1714 must be reconciled (one SQL relay, no second publisher). No production role change.

## 2026-10-22 — v0.1.81 SOURCE MERGED, terminal ACK physically unverified

Runner-MCP #806 commit `2fd8dcacc4c357663457d6651a93d572c31fe36a` with exact-head CI validation #39756255817, Ubuntu #39756255754 and attribution #39756257158 **SUCCESS**. Fabric #1710 fixed issuer Agent MCP methods and AIfordable #632 authenticated operator ACK API are also SOURCE MERGED, without evidence that the original controller/relay processes were updated. Central connected 0.1.38 has execution disabled/relay unknown; isolated `runner:black` original-client result/durable ACK remains WAIT. No service/host/credential update performed. #341 OPEN.

# STATE — #341 fixed Black Control Center bridge (2026-10-22)

- Phase: SOURCE MERGED (PR #804, commit ea641e691796556cd9f612b01946d7ab45951d5e; Runner-MCP v0.1.80); actual issuer and ACK: WAIT.
- Active central first-party Runner-MCP still v0.1.38; no authenticated Black issuer tool installed in that serving generation.
- Black v0.1.30 and its three services reported locally stable; relay auth-only PASS does NOT prove terminal ACK.
- Fabric PR #1701 merged, receipt-bound status source exists. Fabric Agent MCP fixed three issuer methods are NOW SOURCE MERGED via Fabric #1710 (docs #1711); Fabric #1706/#1708 reuse ONE operator REST-compatible MFA commandclient. No deployed/live issuer credential proven.
- AIfordable #585 PR #632 SOURCE MERGED as a9bf1519ded257fdc73850fafad831b95a6e08b5 (operator REST terminal digest/ACK with original MFA requester); actual deployment and original control issuer still unverified.
- Test/CI: CI workflows #39747583227 (Ruff, pytest, release gate, built artifact, demo), #39747583162 (clean Ubuntu) and #39747583241 (commit attribution) all SUCCESS for tested PR head 202b0141c0f28e03cd9a4f2ce0479f17008c7483. This is source-only, not live command evidence.
- Invariants: no arbitrary target/operation/endpoints or new credentials; no mutable six-role services, updater, tunnel, release, shell or direct unmanaged host access; no false “ACK proven” on health/HTTP200/queued.
- Next: AIfordable #632 qualified operator REST deployment; Fabric isolated original MFA issuer activation; one true original client Black terminal result/ACK. Runner-MCP v0.1.81 candidate closes local zero-generation and changed-generation false-positive paths; exact-head CI required. Leave #341 OPEN until live acceptance.

- 2026-10-22 correction: Fabric #1710 and #1711 are SOURCE MERGED, not a missing source implementation. Runner-MCP v0.1.81 candidate guard and RMCP-F-0073 do not permit a central 0.1.38 cutover; original isolated ACK still WAIT.
