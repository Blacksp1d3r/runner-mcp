# #341 fleet convergence — 2026-10-11 bounded evidence checkpoint

Status: **BLOCKED_EXTERNAL / SOURCE_INSPECTED**. This is a coordination/evidence contract, **not** deployment approval. Owner: Runner-MCP #341, #509, #642. Fabric #943 is separately owned.

## Confirmed source and connected-runtime divergence

- Current `main` source `src/runner_mcp/server.py` has a sanitized `runtime_doctor` check `fabric_a6_binding_state` (fixed root status, number of 11 fixed bindings, no paths/values), plus `self_update_runtime_activation`.
- Current connected read-only `runtime_doctor` emitted only 12 older checks, including neither of those checks. It returned three warnings: Fabric continuity unavailable, worker qualification unavailable, and migration storage not configured.
- The *same* connected read-only inspection returned `runtime_status` with stored last-installed commit `a0fd964c4a6fe7e0a1506a513e9b2b4059c5453a`, inactive self-update and no pending restart or install recovery. `build_identity` and `fabric_bridge_preflight` both failed with generic connector errors.
- These facts establish diagnostic contract divergence, **not** which enrolled host the connector reached, nor active process source SHA, nor the root cause of A6 missing bindings. `self_update_ready=true` is not a release gate.
- Earlier historical fleet source records `a0fd964c...` and `ed48f048...` are **not current two-host attestations**. AIfordable owns private registry service identity; never publish actual host details or inspect protected Bewind storage.

## Owned next execution steps — strictly ordered

1. **#509 / #590 read-only identity gate:** obtain privately qualified service asset ID + active process build/source digest + artifact hash + full advertised `tools/list` schema hash, bound to the originating client route and one good plus one failing request ID. Distinguish client/connector ingress, dispatcher, server result, response delivery and same-client receipt. No HTTP ingress-as-ACK.
2. **#509 A6 gate:** only after the identity gate, read the existing sanitized `fabric_a6_binding_state` diagnostic from that exact instance. Distinguish roots `absent / incomplete / unsafe / ready`, bindings `0..11`, stale deployed code and peer registration. Repair only the earliest proven Runner-MCP-owned divergence via existing fixed binding repair; no speculative restart or shell. Reuse existing Failure Museum `RMCP-F-0002`.
3. **#642 source admission:** the already-merged `host_tool_admission.py` is **source-only**, not attached to real MCP dispatch. Require a trusted signed/provenance-verified first-party host policy bound to actual process identity and expiring release/schema digest; unknown/stale/expired facts deny before all side effects. Preserve a shared advertised catalogue and structured/audited `HOST_TOOL_NOT_PERMITTED` returning to the *same* client. Never infer host from request arguments/env.
4. **#341 existing updater only:** validate exact selected source SHA, artifact digest and full tool schema across both enrolled services, while host policy permits differ; independent A6 off-target journal (#942) and Fabric-owned A7 (#943) disconnected autonomous timeout/restore must pass *before* an approved one-host canary. Its provisional HTTP marker is not same-client ACK. Verify exact successful result + original-client ACK prior to supervisor commit; only then independently update/verify second service. Quarantine unavailable/mismatching hosts; no blind fan-out.

## Exact-head synthetic regression matrix to run on actual implementation PRs

- A6: fresh fixed dual roots + exactly 11 sanitized bindings; no roots; only one root; unsafe symlink; corrupt private config; stale process diagnostic; absent peer registration; no paths/secrets in response. Assert no restart or mutation in diagnostic.
- Dispatch: same catalogue/schema digest on primary and lab; primary rejects five lab-only OCR tools *before handler invocation*, lab permits only on qualified policy, unknown host/missing signature/expired permit/wrong active SHA/schema/unknown tool all deny, no rerouting and no grant bypassing safety/approval/fencing. Assert denial result and audit correlation reach original caller.
- Activation: inbound HTTP before handler, 401, 500/raise, successful server response without client receipt and lost tunnel **never** commit/disarm rollback; only original-client correlated result+ACK admits independently fenced supervisor commit. Power-loss/timeout recovery restores retained baseline with proof; avoid destructive/production fixtures.
- CI attribution must identify exact PR head SHA and successful relevant lint/tests/artifact; absent CI is `WAITING_CI`, not green. Review `#438` remains open, stale and nonmergeable; do not silently rebase/merge.

## Coordination and safety

No production updates, restarts, tunnel, host policy, services, credentials, secret files, protected data or Claude dispatch occurred in this checkpoint. No duplicate updater or Fabric authority. Fabric #943 is a separate owner; Runner-MCP #590 response-delivery route is a separate acceptance dependency. Relevant linked issues: #341, #509, #590, #642, PR #438, Fabric #942/#943. Canonical project Failure Museum already covers A6 family RMCP-F-0002; do not duplicate.
