# F30 A6 — fixed local hash-chain READ over the existing MCP bridge (source v0.1.54)

Coordinated with Runner-Fabric #1617/#942/#924, Runner-MCP #509 (private 11-key repair) and #669 (loaded wheel), AIfordable #609 (original-client ACK). This child is a **new conditional read-only interface**, not a second A6 repair owner, updater, journal, relay or service.

## Bounded interface

Expose `fabric_a6_storage_preflight()` with ZERO parameters over existing authenticated central Runner-MCP -> existing bearer-bound `FabricBridgeClient` -> existing Fabric Agent MCP `a6_storage_preflight()` (Fabric #1618/#1626). Its counterpart is already SOURCE MERGED but not deployed. Add only the exact optional peer tool to the allowlist, not required N/N-1 tool inventory; older peers return `wait/fabric_read_unavailable` with NO retry or mutation.

Typed response has fixed `runner.fabric/a6-storage-readonly-preflight/v1` schema and 11 fields. Must fail-closed on missing/extra keys, subclassed/forged string IDs/reasons, invalid root booleans, inconsistent local journal assertions, any `physicalIndependenceVerified`, `offTargetReadbackVerified`, `a6Ready`, `mutationEnabled` or `dispatchAuthorized` claim. A complete existing local hash chain can **only** set `journalIntegrityVerified=true` with reason `local_journal_hash_chain_verified_only`; that is never a physical distinct-medium, target-loss recovery or one-host update permit. No private root path, credential, host ID, arbitrary process/mount input or raw exception crosses the bridge.

## Source and release acceptance

Reserve source v0.1.54 consecutive after existing merged main 0.1.53 (at creation; reconcile current heads before merging). Four version metadata files, exact 99-name tool catalogue attestation and independent clean Ubuntu wheel install checks remain mandatory. Focused unit tests for older peer, happy missing roots, local-only hash success, forged authority, private path leakage, wrong reasons and no retry. No rolling install merely because source tests succeed.

Physical acceptance still WAIT: original installed central Runner-MCP 0.1.38 with unverified current source/wheel, `self_update_ready=false`, A6 0/11, bridge A6 prepare/probe unavailable, Agent Bus UNKNOWN. Fabric #1617 separate medium and #942 real off-target readback, #943 actual disconnected six-role rollback, Runner-MCP #509 fixed private safe config + #669 installed signed import provenance, AIfordable #609 original same-client result digest ACK, and Fabric #924 one protected lease are mandatory.
