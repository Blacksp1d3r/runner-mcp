## 2026-10-27 — RMCP-F-0079: provider lookup/attribute error escapes bounded identity read (SOURCE MERGED)

Review of the existing `bounded_build_identity_payload` path found that unexpected provider or serialization `KeyError`, `IndexError` and `AttributeError` were not caught by its earlier OSError/RuntimeError/TypeError/ValueError error envelope. A read-only live `build_identity` call produced a generic tool failure while `runtime_status` succeeded, but no physical root-cause attribution to these exceptions is claimed. Source v0.1.103 candidate extends the already-existing safe handler with `LookupError`/`AttributeError`, without changing positive identity results. Parametrized synthetic regressions verify no exception private text leaks from both provider and serializer. This repairs SOURCE error containment only; original serving wheel/signer/six role, off-target A6 and independent A7, and new same-campaign requester ACK remain unverified.


PR #862 exact-head validation, clean Ubuntu and attribution all SUCCESS; merge `48496be520901ae018671be83e6c9c5df55ec2c6`. Independent 0.1.103 GitHub wheel candidate bytes verified. Actual original 0.1.88 installed runtime remains unmodified and root-cause correlation of its intermittent tool failure unproven.
## 2026-10-27 — RMCP-F-0078: provisional window misread as retained recovery wheel (SOURCE)

Source review found that a completed self-update job plus pending install transaction could set `provisional_activation_pending=true` even when the previous wheel file had disappeared from the existing staging directory. The status now carries a separate, bounded read-only `provisional_baseline_wheel_present` field: `null` when inapplicable, `false` when missing/unsafe and `true` only for valid path/file presence. A true value is not a wheel hash, qualified rollback or authorization to deploy. Synthetic test removes the previously staged baseline wheel, observes the missing state, restores the same isolated fixture, and verifies attended recovery remains possible. Original live host, A6/A7 and fresh ACK remain WAIT.

## 2026-10-27 — RMCP-F-0077: provisional rollback option not forwarded by app

The manager-level opt-in added in v0.1.96 was not forwarded at either `build_mcp` or `create_app`, so a qualified Fabric caller could not select it during legitimate application construction. New source v0.1.98 forwards one strict boolean through those existing layers, default OFF; malformed values fail at the existing manager. No environment-based opt-in, deployment authorization or automatic A7 acceptance. App-level tests verify actual downstream forwarding, not merely a manager constructor unit test. Serving 0.1.88 unchanged.

## 2026-10-27 — RMCP-F-0076: premature baseline disposal before reconnect (SOURCE-OBSERVED)

- **Earliest layer:** `src/runner_mcp/self_update.py` successful `_run_job` path. After `install_wheel(target)`, `verify_runtime` and restart markers it invoked `clear_transaction()` and `preserve_artifacts=False`, leading `finally` to remove baseline wheel. A failed restart or broken tunnel/Agent Bus can then lose the normal manager's previous wheel before actual requester result/ACK. A green new-process import does **not** prove the original client can still communicate.
- **Fix candidate:** opt-in constructor `retain_activation_baseline=True` on the ORIGINAL manager; require a recorded baseline and keep original transaction + baseline/target wheel until separately confirmed/returned by Fabric A7. Report `provisional_activation_pending`, disallow next update. Existing source default remains false for compatibility; do not mistake this for a physically enrolled A7.
- **Regression:** successful install/restart-manager/retained-wheel/emergency-stop recover; strict bool, baseline-required denial and default legacy unchanged. Exact-head CI required. Fabric #943 still owns real persistent independent A7 hardware/boot/no-NIC tests, #942 off-target A6, #669 original signed live wheel witness. No production incident asserted and no host action performed.

# 01-runtime-self-update — Runtime en self-update — failure register

| Failure ID | Status | Earliest layer | Symptom | Root cause/evidence | Prevention/regression | Tracking |
|---|---|---|---|---|---|---|
| none-migrated | — | — | No additional component-specific reusable failure migrated yet | — | use global taxonomy/template | #569 |

Use the existing repository failure-record template for detailed incidents. Add stable IDs here only for reusable root causes.

## 2026-10-19 — RMCP-F-0045 (source-only, not a live incident)

At the active-revision provider boundary, missing mapping entries or object
attributes could raise `KeyError`, `IndexError` or `AttributeError`, bypassing
the previous bounded exception list and surfacing a generic internal tool error.
PR #742 contains a narrow `LookupError`/`AttributeError` containment fix and
regressions requiring unknown revision, false activation/readiness, a denied
update and no private exception text. No evidence of this path occurring on a
live host; exact-head CI must pass before source acceptance. The separately
missing serving-generation attestation is still UNKNOWN and is not repaired
by this exception-containment change.

Design: [SERVING_GENERATION_ATTESTATION.md](SERVING_GENERATION_ATTESTATION.md).

## 2026-10-19 — RMCP-F-0046 (synthetic source boundary, no live incident)

Source checkout baseline evaluation previously expected a valid `clean_head` dict and coerced unknown commit values to string. A malformed provider result could escape status/Doctor or produce a noncanonical source revision. The #742 source fix strictly checks dict, `clean is True`, and lowercase 40-character commit, or returns `(None, False)` without exposing private exception detail. Tests cover ten malformed forms plus a provider error and assert no updater job is queued. This does NOT reconcile the real manual installation or alter historical state. Exact-head CI pending.

## 2026-10-20 — RMCP-F-0054 (source-only installed RECORD parser negative admission)

The existing offline installed RECORD comparator accepted *any* pip RECORD entry not present in the source wheel unless its path began `runner_mcp/`. That silently tolerated arbitrary exterior paths and duplicate console entries as if they were normal installer metadata. The source-MERGED v0.1.50 correction admits only known bounded pip console scripts and common installer metadata, validates optional external digest/size shape and refuses duplicates with synthetic negative tests. No evidence of real host exploit, no installed-process proof, no live updater/host action, and no change to A6/A7/ACK gates. Tracking #669.

## 2026-10-20 — RMCP-F-0055 (offline evidence path redirection)

The offline evidence chain previously delegated each input to separate helpers and used lexical `Path.is_relative_to()` for generation membership. Source-only negative review exposed that lexical `..` or linked ancestors can reference a different physical path while looking generation-relative. Source-MERGED v0.1.51 refuses nonabsolute inputs, lexical parent traversal and symlinked ancestors for every path, with parametrized synthetic tests. No proof of a live incident; even successful offline chain remains `active_build_provenance_verified=false`, never independently signed correct-host process trust. Tracking #669.

## 2026-10-20 — RMCP-F-0056 (source-only current-generation admission contradiction)

`fail_closed_runtime_provenance()` correctly cleared current source/wheel and historical source-commit labels, but preserved a manager-supplied `self_update_ready=True` during merge of a transaction status into `runtime_status`. A stale or independently unqualified update manager could therefore expose contradictory `{active_build_provenance_verified:false, self_update_ready:true}` and prompt a fleet control consumer to attempt activation. SOURCE MERGED v0.1.52 forces readiness false until independent correct-host currently serving identity and A6/A7 restore authority are accepted. Negative regressions cover stale/invalid readiness and loaded-vs-installed version mismatch; no live incident asserted. Issue #669 remains OPEN and central connected live 0.1.38 must not be updated.

## 2026-10-20 — RMCP-F-0057 (standalone receipt path alias)

The standalone offline artifact/receipt comparator inspected final-path `lstat` and rejected a linked leaf, but linked grandparent directories could redirect valid receipt/wheel/installed module reads before source generation trust was bound. While `offline_evidence_chain` was previously hardened against this, the independently reusable standalone receipt validator remained permissive. SOURCE MERGED v0.1.53 rejects relative, lexical `..` and symlinked ancestors across all three arguments before touching bytes. Negative tests cover each path class; no live exploit asserted. This remains strictly OFFLINE evidence and does not establish live wheel, A6, A7 or result ACK. #669.

## 2026-10-20 — RMCP-F-0058 (connected process cannot distinguish old loaded modules from newer dist-info)

Current read-only `runtime_status` provides two versions but not a capped current-process module-roster observation. A separately installed wheel may change metadata without replacing old imported Python modules. SOURCE MERGED v0.1.55 adds fixed zero-input `serving_process_observation_preflight`: checks only `runner_mcp`, `runner_mcp.server`, `runner_mcp.build_identity` presence and loaded-versus-dist-info version categorically, no filesystem paths/host identifiers, no signer/rollback/Agent Bus authority. Even exact local agreement returns `observed_local_only`, never `activeBuildProvenanceVerified`, a nonnull digest or update approval. This does not settle host identity, true memory byte hashes or other five roles. Tracking #669.

## 2026-10-22 — RMCP-F-0071 (synthetic original-wheel receipt publication uncertainty)

Source review found that `capture_candidate_wheel_receipt` deleted the newly
created private receipt even after offline wheel+installed-module agreement, if
the final directory fsync failed. On a power-loss/durability boundary, that
operation could destroy reconciliable evidence while inviting a subsequent
create-once retry. v0.1.79 candidate preserves a byte-validated receipt on
post-validation directory fsync failure and raises a fixed
`WheelReceiptPublicationUncertain` error; earlier unvalidated file failures
still remove partial receipts. Injected file-versus-directory fsync regressions
distinguish the two boundaries. This is a synthetic source finding, not a
verified live incident or a current source/wheel identity; #669 A6/A7 and
original-client admission remain WAIT.
