# RMCP-F-0073 — unfenced terminal Black result or changed worker generation across ACK

Date: 2026-10-22
Scope: Runner-MCP #341 source-only; physical original issuer ACK remains WAIT.

## Reproduction in existing v0.1.80 validator
- A synthetically crafted `completed`/`failed` status with valid request ID, exact fixed target, MFA requester field, fingerprint, result SHA and `owner_generation=0` was structurally accepted although the relay had not attested a positively fenced worker claim.
- An ACK response followed by a second status GET with the same ID, digest and version but changed `owner_generation` could be represented as verified by Runner-MCP; Fabric #1708 independently checks retained worker generation already, and Runner-MCP must not weaken that invariant if peer code or schema changes.
- This is a source/test gap, **not evidence of real Black falsification or compromised relay**.

## Corrective control
- Require queued=0 and claimed/terminal strictly positive worker generation, rejecting booleans.
- Require the post-ACK readback to preserve exact original claimed worker generation, requester subject, fingerprint, request ID and result digest/version, as well as `requester_acknowledged=true`.
- Test negative generation, missing target, foreign operation, unavailable Fabric peer and forbidden arbitrary tool choice, all offline.
- Keep one existing Fabric adapter, AIfordable SQL relay and MFA control issuer; no new host scope, credential, controller or live server install.

## Remaining independent gates
Fabric #1710/#1711 SOURCE MERGED, no active confirmation on old 0.1.38; AIfordable #585 PR #632 has now SOURCE MERGED as a9bf1519ded257fdc73850fafad831b95a6e08b5; actual API deployment and original MFA issuer are not qualified. Do not mark live `runner:black` claim/result/original-client durable ACK proven from GitHub CI.

## CI regression: error message over-specificity

- First PR #806 full CI ran 4,037 pytest cases: 4,035 passed, 2 failed solely because tests demanded the word `generation` in a rejection message. The existing type/negative-value guard correctly rejected those two values earlier with the generic `invalid control evidence` message; the new generation-state guard handles otherwise-valid values.
- Corrected test assertions to require the fail-closed `BlackControlEvidenceError` regardless of which of these two deliberately safe guards rejects first. No runtime validation was loosened or bypassed. Exact-head CI must still rerun green before merge.

## Resolution: source-level controls merged

- #806 v0.1.81 SOURCE MERGED `2fd8dcacc4c357663457d6651a93d572c31fe36a`, exact-head validation #39756255817, clean Ubuntu #39756255754 and attribution #39756257158 all SUCCESS.
- Failing tests were an over-specific regex assertion on two existing earlier safe-denial guards; correction retained all denials, tests green. Production activation and physical Black original-client ACK remain a separate WAIT gate.
