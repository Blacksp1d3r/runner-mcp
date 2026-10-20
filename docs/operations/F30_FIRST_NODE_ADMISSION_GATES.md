# F30 first central node: non-mutating admission and A6/A7 evidence

Status: **WAIT / NO UPDATE**. Merged source v0.1.49 (#763/#764) is NOT live on central 0.1.38. Local fixed A6 keys, unlinked paths, and safe directories do NOT establish physically independent off-target journal, A7 rollback, or original-client ACK. Reconciled 2026-10-20 against first-party connected Runner-MCP and GitHub main. This runbook is a public, host-path-free operator handoff; it is not authority to run a command or change a server.

## Fixed observed facts and interpretation

| Evidence | Observed | Meaning |
| --- | --- | --- |
| Central original-client `runtime_status` | running/installed 0.1.38; `self_update_ready=false` | MCP route works; in-place updater must NOT be called |
| `build_identity` | source revision NULL; artifact digest NULL | active source/wheel is NOT attested |
| Doctor | `source_baseline_drift`, `active_revision_unavailable` both FAIL | preserve failures, historical self-update transaction is NOT active-generation proof |
| Doctor A6 | **`pass / not_configured_0_of_11`** | this PASS classifies safe absence, **NOT A6 update readiness** |
| Fabric bridge | `ready` but `a6_prepare_available=false`, `synthetic_probe_status_available=false`, `mutation_enabled=false` | read-only connectivity only; A6 not admitted |
| Fabric snapshot | `agent-bus.relay=unknown/evidence-unavailable`, execution=false | not evidence the independently inspected relay transport is down |
| Repo main | package v0.1.46, source PR #756 merged | NOT installed; 0.1.46 worker-process inspection must not be reported as a live tool |
| Service continuity | six managed roles on original central node | keep all serving launchers, cron entries and existing rollback escrow untouched |

Previous operator-observed relay listener/health routing already passed; do NOT rebuild a relay, reissue credentials or repeat that physical test to disguise missing target-bound ACK.

## A6 state-machine cause (Runner-MCP #509 / Fabric #942)

Source `fabric_a6_binding_repair.inspect_a6_binding_state` reads **11 fixed** private env keys and the pair of owner-only A6 journal/evidence roots. Doctor reports `not_configured_0_of_11` and marks it PASS only when both roots are absent and no keys are configured. Treat this as safe intentionally uninitialized, not a completed update qualification. Mixed roots or partial keys must be WARN/BLOCKED and never automatically repaired.

The existing `repair_a6_qualification_binding` is triggered through the already-defined bounded `fabric_agent_restart` path **only after** BOTH durable A6 state roots exist and are safe, correct owner, private 0700, non-symlink, and the existing private `runner-mcp.env` is safe. It requires an existing authenticated runner bearer and a trusted 40-hex Fabric source revision. It merges ONLY the 11 fixed keys; it does not create missing roots, mint credentials, produce separate-volume guarantees or qualify A6/A7. Do **not** call `fabric_agent_restart` just because 0/11 appears: it restarts a running agent and is a service mutation. Do not manually type arbitrary environment keys, set dummy bearer values, copy credentials from another host or expose private paths in public issues.

If both private roots do not already exist, the next missing capability is **fixed, operator-approved, correct-host, off-target A6 root admission and storage-domain proof** under Fabric #942 and Runner-MCP #509; absent that bounded capability, WAIT. A6 roots on the same target disk are not proven off-target evidence. Once the private owner supplies independent evidence, authorize one guarded A6 preparation, bounded restart and post-restart preflight in a separate controlled step with read-only categorical receipts. No alternate shell/sudo/mount/remote-desktop fallback.

## Admission dependencies (strict order)

1. **Correct host and immutable old generation** — independently read and bind actual central listener/serving PID, the six managed role owners and launch targets, source checkout, imported module bytes, installed RECORD/wheel digest, previous intact known-good install and recovery artifacts. Validate on the actual serving host, not another host's localhost. Report public status only. A matching version string or GitHub artifact hash is insufficient.
2. **Trusted active-generation witness** — compare installed RECORD/module bytes to a wheel independently pinned and signed by approved authority, bind correct serving process and generation with fresh nonce/expiry, then compare via existing #669 offline witness primitive. Keep `self-update-state.json` immutable; never falsely mark provenance verified from a self-update history commit.
3. **A6 off-target durable journal** — independently qualify the physically separate storage and two private state roots, fixed 11/11 binding plus actual Fabric peer tools, protected journal integrity and a genuine off-target lab update receipt (#509/#942).
4. **A7 independent offline restore** — verified exact old wheel/launcher custody, independent supervisor armed BEFORE switching, locally tested rollback with control path unavailable, bounded deadline and documented disarm/commit; supervisor cannot be updated with the protected component (#341/#943).
5. **One first-node Fabric lease and real ACK** — Fabric #924 alone authorizes a single target update after all above checks and compat N/N-1. Original authenticated requester must receive an exact terminal result and ACK digest through the existing scoped Agent Bus (#609). Only then accept `SERVING_VERIFIED` and provision worker-local Q7/Claude/Qwen paths, never centrally cross-UID.

## Non-mutating checks safe to repeat through the existing original MCP client

- `runtime_status`, `build_identity`, `runtime_doctor`, `fabric_bridge_preflight`, `fabric_operational_snapshot`.
- Where already supported, fixed `fabric_release_archive_mirror_readiness()` is diagnostic only; an unconfigured separate-volume mirror is neither backup proof nor permission to mount or copy.
- Existing GitHub PR/CI/artifact SHA inspection is SOURCE evidence only.

**NEVER** invoke `self_update`, `fabric_agent_restart`, A6 prepare/finalize, Fabric update/rollback, worker start, or production restore while the qualifying authority/lease/recovery chain is unknown. An unavailable tool / generic connector error is UNKNOWN rather than PASS or host outage.

## Operator handover receipt (redacted categories only)

Record `observed_at`, correct host/role reference, source+installed+loaded versions as separately identified, `activeBuildVerified`, `baselineReady`, `a6StateRootsReady`, `a6FixedBindingsCount`, `a6OffTargetDeviceProven`, `a6JournalVerified`, `a7IndependentOfflineRestoreProven`, `sameRequesterAckVerified`, `releaseCandidateSha`, `mutationAllowed`, and categorized blocker/next owner. No host paths, UID, token, PID, command-line, filesystem device, raw log or private bytes in public issues.

Expected at this checkpoint: loaded 0.1.38, candidate source 0.1.46, `activeBuildVerified=false`, `a6FixedBindingsCount=0`, `mutationAllowed=false`. Treat all unmeasured physical fields as UNKNOWN, never auto-fill true. Defer OIDC/MFA change; existing authentication remains mandatory. No incremental paid software or unbounded external provider use.

Owners: Runner-MCP #669 serving provenance and #509 fixed binding; Fabric #942 A6, #943 A7, #924 only activation; AIfordable #609 original-client receipt. Definition of DONE requires actual original-client and physical evidence, not this document, synthetic tests or merged code.
