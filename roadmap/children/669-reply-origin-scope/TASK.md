# Runner-MCP #669 — label current reply scope, not fleet provenance

## Problem
Identical displayed version strings across separately serving hosts, or a different interactive CLI version on a single host, can be mistaken for proof that an authenticated reply came from the same wheel/process/route. Existing source correctly hides unverified active wheel SHA and revision but does not explicitly distinguish local reply scope from fleet attestation.

## Bounded change
Reuse existing `fail_closed_runtime_provenance` normalization called by `runtime_status`; add constant `reply_identity_scope=this_connected_process_only` and explicit false values for host identity, loaded wheel/module identity and real six-role process roster verification. Add a narrowly scoped boolean for loaded-vs-installed **version string equality only**, without promoting equality into attestation. Reject manager-injected optimistic values.

## Definition of done
1. The answering service's imported version is preserved even if installed dist-info changes.
2. Equal package versions across distinct hosts remain explicitly unverified.
3. A stale CLI reading a different version cannot overwrite imported serving process identity.
4. Status contains no host address, user, filesystem path, PID, token or new remote capability.
5. Synthetic positive/negative regression and exact-head normal CI green. Version unique and consistent.
6. Source merge does not authorize any installation, update or cross-host role claim.

## Separate physical gate
Parent #669 still requires correct-host old installed wheel SHA/RECORD, exact serving process/launcher provenance and protected previous-generation custody; Fabric A6/A7 and original-client ACK remain separate.
