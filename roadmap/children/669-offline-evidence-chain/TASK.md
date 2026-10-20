# #669 source child — Offline evidence consistency chain

## Purpose
Combine existing read-only offline builder manifest SHA pin, receipt/module SHA verifier and generation-layout guard. Detect inconsistent source revision and wheel digest across supplied evidence.

## Scope
- Code: src/runner_mcp/offline_evidence_chain.py; tests: tests/test_offline_evidence_chain.py
- Candidate source 0.1.14.
- All outputs remain offline-only; source_revision and artifact_digest of serving process always null, active_build_provenance_verified always false.
- Never call this chain trusted installer, independently sealed evidence, signer, or runtime witness.

## Dependencies and trust boundaries
- Uses source-complete children PR #689 (receipt), #690 (builder digest comparator), #691 (layout).
- Caller MUST obtain builder-manifest digest from independent trusted custody. If caller controls both manifest and digest, chain only proves self-consistency.
- Even valid inputs can mutate during sequential checks: no filesystem sealing, process loaded-module attestation, executable generation or original client ACK exists.
- No production, network, keys, host privilege, Fabric authority or tunnel mutation permitted.

## Synthetic acceptance
- Positive fabricated evidence returns offline_candidate_chain_match, but active identity stays false/null.
- Tampered manifest/wheel/module/receipt/generation fails closed.
- Mismatched source and expected pin fail closed.
- Exact commit CI lint/pytest/demo/build/Ubuntu/attribution must succeed before source merge.

## Handover
Follow roadmap/ROADMAP.md, handover/CURRENT_STATE.md and issue #669. Later dedicated children must implement independent trusted builder custody, immutable installation, and serving generation/rollback proof.
