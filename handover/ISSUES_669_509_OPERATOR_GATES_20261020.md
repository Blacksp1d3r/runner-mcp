# Runner-MCP #669 + #509 — correct-host first-admission handover

Status: 2026-10-20 — SOURCE READY IN PART, PHYSICAL LIVE GATES WAIT. This document is an evidence contract, not a new automation or permission to modify production. Check current live status again before any authorized operation.

## Evidence from the original authenticated client

- Server: loaded `0.1.38`; installed distribution `0.1.38`; build revision/digest NULL; active_build_provenance_verified=false, self_update_ready=false, current Doctor provenance two FAIL.
- A6: local fixed keys 0/11; no qualified pair of owner-private off-target journal/evidence roots; peer source `51c37f1eac65951e15a5122b89f368aa6e18c1f5`, bridge handshake read-only; prepare/probe unavailable.
- GitHub source: Runner-MCP `0.1.58` after PR #776, but NOT installed. #669 offline receipt/RECORD/signature/three-module checks and #739 33/33 manifest remain candidate consistency only.
- Unconfigured archive mirror is separate from off-target A6; neither local host snapshot nor HTTP health is correct-host six-role/process proof.

## Required independent receipts — keep identities and secrets private

| Gate | Owner | Accepted receipt (categorical/sanitized) | Fail closed |
| --- | --- | --- | --- |
| H — correct serving host | Runner-MCP #669 with operator-controlled pre-existing host witness, Fabric #924 for admission | Independently pinned correct host and complete six-role process inventory, actual loaded Python module/launcher generation, exact old installed wheel RECORD and immutable builder/source signature, current wheel SHA, signed nonce/time window; same ORIGINAL authenticated client sees matching generation | Historical self-update commit, pip dist metadata, newly deployed source-only tool, host:local or a different tunnel do not qualify |
| P — intact previous generation | #669 + Fabric #943 | Independently stored, owner-immutable working prior-version wheel, receipt, launcher/service mapping for all six roles; offline restoration still possible without the updated MCP | Candidate wheel alone, an unarmed watchdog or mutable same-root copy |
| A — independent A6 roots | Fabric #1617 and #942, then Runner-MCP #509 | Independently qualified off-target physical medium and failure domain; two fixed non-symlink/private 0700 roots, journal append/hash-chain and readback **after target loss**; only then conditional fixed 11-key repair from trusted actual peer revision and existing private bearer; bridge prepare + probe transition to READY on original client | 0/11 or even structurally 11/11, identical device/renamed folder, local-only journal hash, manual unrestricted env edits, token/path disclosure |
| U — autonomous offline revert | Fabric #943 | Previous generation actually restored while client/tunnel is deliberately unavailable; six-role serving and original client reappear, with supervisor independent of updated target | Source tests, timer existence or rollback command requiring same broken MCP |
| K — end-to-end original-client ACK | Fabric #1556/#1563, AIfordable #585 relay | One request/correlation through existing relay and worker returns exact terminal result, persisted digest, durable ACK to SAME original client; no UNKNOWN hop | Local HTTP 200, read-only bridge status, synthetic-only dispatch |
| Cutover | Fabric #924 | One guarded correct-host lease, operator admission, H/P/A/U/K all proven and fresh; original-client exact source/wheel/catalog/ACK verified before release commit | Any missing/UNKNOWN gate; do not self-update directly |

## Immediate bounded order

1. Fabric #1617 owns the correct-host **noncreating** fixed root preflight and physical target-loss proof. Its source PR #1637 is merged, but deployment and physical results are not established. Do not invent a second storage manager, mount disk or create directories from MCP based on candidate/source assumptions.
2. Fabric #943 and operator-protected existing recovery authority must independently inventory/custody the CURRENT old 0.1.38 six-role wheel and launcher generations under #669 before any 0.1.58-first update. Read-only host-local witness cannot be issued by the very upgrade it is meant to authorize.
3. Once Fabric #1617 has accepted BOTH exact private A6 roots, reuse Runner-MCP #509 existing `fabric_agent_restart()` conditional repair with the current authenticated Fabric peer revision, no new parameters, with separately approved SERVICE action. Check persisted **and loaded** private bindings, original-client prepare/probe, independent journal and target-loss evidence. Runner-MCP PR #776 merely adds local 0600 single-inode alias denial.
4. Fabric #943 disconnected rollback and Fabric #1556/#1563 exact same-request/result/ACK must be exercised on real authorized target. Fabric #924 may then perform one attended/guarded cutover, never before.

## Hard exclusions

No production mutation performed in this checkpoint. Preserve six serving roles, local previous rollback sources, existing tunnel, relay, credentials, private disk and project workers. Do not reactivate postponed OIDC/MFA or duplicate the updater/relay. Never record host paths, auth tokens, signer private keys, PIDs, machine or service secrets in GitHub handover.
