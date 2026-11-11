# #669 / #341 — runtime_doctor historical baseline and serving identity reconciliation

## Grounded problem (2026-10-19)
The original connected central Runner-MCP client reports installed runtime 0.1.38 but `runtime_doctor` still fails `self_update_source_baseline=source_baseline_drift` and `self_update_runtime_activation=active_revision_unavailable`. `self_update_ready=false`. This is **not** an MCP availability failure.

## Observed lineage
- `server.py:runtime_doctor` projects `SelfUpdateManager.runtime_status()` classifications.
- `self_update.py` compares private historical `last_installed_commit`, current source checkout and the optional active-revision provider.
- `build_identity.py:installed_source_revision` intentionally returns `None`: a historical self-update transaction is never an attestation of the currently serving wheel.
- Manual isolated-prefix cutovers from 0.1.9 to 0.1.27 and then 0.1.38 succeeded with first-party client version checks, but those checks do not prove a signed wheel/loaded-process generation.

## Implementation sequence (independent, fail-closed)
1. READ-ONLY operator-bound inventory: identify exact serving generation, interpreter/import origins, installed RECORD/module digests, immutable source/wheel identity, existing historical transaction, current project source head and all managed service owners; compare evidence on the **correct host**. Return only redacted categories publicly.
2. Qualify an independently trusted signer/manifest pin and its custody, expiry/revocation and anti-rollback policy. Reuse existing #669 offline receipt, layout and signed-evidence primitives; do not accept a candidate-supplied key/fingerprint as independent trust.
3. Design a narrow, versioned, atomic owner-local reconciliation receipt for a manually installed generation. It must preserve the historical self-update transaction and bind active process/launch generation to independently verified wheel+source; missing or contradictory evidence must remain false/null.
4. Only after verified host-side evidence exists, wire the provider so `active_runtime_revision` can report the proven revision; preserve `runtime_doctor` fail behavior when evidence is missing. Baseline reconciliation must be separately authorized and must not silently overwrite self-update history.
5. Add negative tests: stale old commit, same version/different wheel, post-pip pre-restart process, altered RECORD, broken/symlinked or partial receipt, wrong host, mismatch between six managed roles, stale signer and rollback generation. Use narrow tests first, then exact-head full validation and clean Ubuntu installer.
6. Qualify original-client live revision/catalog/result/ACK and separately owned Fabric A6/A7 recovery before any managed automatic update or fleet rollout.

## Explicit non-goals
No arbitrary shell or secret-bearing diagnostic output; no self-update guard bypass; no manual rewrite of `self-update-state.json`; no extra updater; no live server, tunnel, cron, credential, production or customer mutation in this source branch.

## Existing authority
Runner-MCP #669, #341, #590; Runner-Fabric #924, #942, #943. Follow AGENTS.md and diagnostic topology rules. Earlier #669 source children are COMPLETE_SOURCE_ONLY; never duplicate their implementation.
