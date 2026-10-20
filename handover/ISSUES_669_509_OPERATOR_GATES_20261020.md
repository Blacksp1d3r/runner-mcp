## 2026-10-20 — source v0.1.63 #669 six-role process pins accepted, operational #509 still 0/11

Source [PR #781](https://github.com/Blacksp1d3r/runner-mcp/pull/781) is MERGED `8d0405490c73bc324a522e66e5e596649d169371`, full exact-head CI validation #39479195410, clean Ubuntu #39479195458 and attribution #39479195285 SUCCESS. New source-only `signed_six_role_process_pin_preflight` reuses original Ed25519 signed statement and requires exactly SIX owner-independently expected roles with distinct owner-independently expected process-instance SHA-256 pins. Missing, swapped, extra, malformed process roles, substituted source/wheel/version/generation/host/nonce and expiration deny. Source result is **`six_role_process_pins_consistent_offline` only**, with **live identity false/null**. No new MCP tool, bridge, agent, signer or service was installed.

**This source change cannot prove the current six serving process instances.** The original client still observes only installed+loaded `0.1.38` with active wheel SHA/revision NULL, A6 0/11 and update not ready. The six listed projects are not the independently pinned actual six process roles. The owner/Fabric correct-host witness must supply trusted *actual* six-process source and instance expectations, the old wheel bytes/RECORD and signature plus protected prior generation **before** any live software upgrade. No A6 private binding change or `fabric_agent_restart` is allowed while Fabric #1617/#942 off-target root/media has not independently qualified. Closed GitHub #509 is source completion only.

---
## 2026-10-20 20:30 Europe/Brussels — original-client check: #509 closed IN SOURCE; A6 operational WAIT

Fresh read-only first-party commands: `runtime_status`, `build_identity`, `runtime_doctor`, `fabric_bridge_preflight`, `fabric_host_inspect`, `fabric_release_archive_mirror_readiness`, `fabric_operational_snapshot`. GitHub #509 is **CLOSED 2026-10-20 17:20:58 UTC** (source acceptance); #669 remains **OPEN**. No call to `fabric_agent_restart`, self-update, installer, shell, create/mount, or private state mutation.

- **Connected process** reports loaded version `0.1.38` and installed distribution `0.1.38`; `build_identity.source_revision=null`, `artifact_digest=null`; `active_build_provenance_verified=false`, `self_update_ready=false`. The source-history marker `a0fd964c4a6fe7e0a1506a513e9b2b4059c5453a` is a **2026-10-07 completed self-update job**, NOT a current serving revision nor wheel SHA.
- `runtime_doctor`: 2 failures `source_baseline_drift` / `active_revision_unavailable`; historical live A6 check `pass/not_configured_0_of_11` means SAFE ABSENCE only, **not update admission**. Source v0.1.62 treats absent A6 configuration as WARN.
- GitHub `main` source **0.1.62** after #615 atomic quarantine PR #618; it contains `fabric_a6_binding_repair.py`, a **conditional** #509 fixed 11-key repair behind the SERVICE-guarded existing `fabric_agent_restart()`: only when BOTH fixed owner-private A6 journal/evidence roots already exist, with trusted peer source revision, valid locally held auth and private `runner-mcp.env`. It does NOT create A6 roots or independently qualify their failure domain. Source v0.1.58 PR #776 guarded private env hardlinks; this new source is NOT confirmed installed or loaded by live 0.1.38.
- Read-only Fabric bridge: `state=ready` for handshake only, peer revision `51c37f1eac65951e15a5122b89f368aa6e18c1f5`, `a6_prepare_available=false`, `synthetic_probe_status_available=false`, `mutation_enabled=false`. Agent Bus `UNKNOWN/evidence-unavailable`, no execution/ACK. Bounded external target preflight and inspect errored; mark **UNKNOWN**, not proved offline. `fabric_host_inspect` is only `host:local`, not six original runner roles. `runtime_status.projects=6` represents managed **projects**, NOT a six-role process inventory.
- Independent release mirror `storage-bindings-unconfigured`. Fabric #1617/#942 owner-private off-target A6 medium and target-loss readback remain unproven. Correct-host six-role installed/loaded wheel bytes, provenance, previous-generation escrow, operator-trusted signer, fresh nonce and original-client receipt remain **UNKNOWN**.
- **Wheel SHA-256 limitation:** a reported package version, GitHub build artifact hash, wheel `RECORD`, current checkout hash, or retained old self-update commit does NOT establish the SHA of the wheel actually used to load a running process. To claim a matching active wheel, independently obtain the original immutable wheel bytes/sha256 or trusted build receipt from owner-controlled escrow, compare installed exact RECORD/module contents and process/launcher mapping for **each** real role on the verified correct host. If the old wheel or attestation anchor does not exist, report `unverified`; do not reconstruct a claimed installed wheel digest from package metadata.

**Strict order, no circular bypass:** independent existing owner/Fabric #924 correct-host PRE-admission receipt for loaded old 0.1.38 generation + protected previous-good wheel/role map; Fabric #1617/#942 qualify off-target physical two-root A6 journal and target-loss readback; then only after protected staged update authority #943 and original-client result+ACK #1556/#1563, install ONE guarded successor through #924 and confirm live generation. Only when the fixed two A6 roots already exist, with trustworthy revision and explicit SERVICE authority, may source-available #509 conditional repair be invoked as part of the approved sequence. #509 stays CLOSED as source issue; operational dependency is tracked by #669 + Fabric #1617/#942/#924, not as a duplicate new tool.

**No production, service, agent, private env, disk, tunnel, relay or credential mutation in this verification.**

---

# Runner-MCP #669 + #509 — correct-host first-admission handover

Status: 2026-10-20 — SOURCE READY IN PART, PHYSICAL LIVE GATES WAIT. This document is an evidence contract, not a new automation or permission to modify production. Check current live status again before any authorized operation.

## Evidence from the original authenticated client

- Server: loaded `0.1.38`; installed distribution `0.1.38`; build revision/digest NULL; active_build_provenance_verified=false, self_update_ready=false, current Doctor provenance two FAIL.
- A6: local fixed keys 0/11; no qualified pair of owner-private off-target journal/evidence roots; peer source `51c37f1eac65951e15a5122b89f368aa6e18c1f5`, bridge handshake read-only; prepare/probe unavailable.
- GitHub source: Runner-MCP `0.1.63` on main, including #509 PR #776 from v0.1.58, but NOT installed. #669 offline receipt/RECORD/signature/three-module checks and #739 33/33 manifest remain candidate consistency only.
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
2. Fabric #943 and operator-protected existing recovery authority must independently inventory/custody the CURRENT old 0.1.38 six-role wheel and launcher generations under #669 before any post-0.1.38 first guarded update. Read-only host-local witness cannot be issued by the very upgrade it is meant to authorize.
3. Once Fabric #1617 has accepted BOTH exact private A6 roots, reuse Runner-MCP #509 existing `fabric_agent_restart()` conditional repair with the current authenticated Fabric peer revision, no new parameters, with separately approved SERVICE action. Check persisted **and loaded** private bindings, original-client prepare/probe, independent journal and target-loss evidence. Runner-MCP PR #776 merely adds local 0600 single-inode alias denial.
4. Fabric #943 disconnected rollback and Fabric #1556/#1563 exact same-request/result/ACK must be exercised on real authorized target. Fabric #924 may then perform one attended/guarded cutover, never before.

## Hard exclusions

No production mutation performed in this checkpoint. Preserve six serving roles, local previous rollback sources, existing tunnel, relay, credentials, private disk and project workers. Do not reactivate postponed OIDC/MFA or duplicate the updater/relay. Never record host paths, auth tokens, signer private keys, PIDs, machine or service secrets in GitHub handover.
