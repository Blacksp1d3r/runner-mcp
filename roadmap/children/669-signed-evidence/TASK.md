# #669 — source-only signed evidence chain

## Goal
Compose strictly offline Ed25519 detached builder-manifest signature verification with existing offline wheel/module/receipt/generation consistency checks. This ensures synthetically matching bytes and signatures under caller-supplied independently pinned identities, NOT serving-process attestation.

## Source and scope
- src/runner_mcp/offline_signed_evidence.py
- tests/test_offline_signed_evidence.py
- Input: manifest, wheel, candidate receipt, installed package, generation, externally protected manifest SHA pin, detached signer public key+signature and externally protected public-key SHA pin.
- Result: offline_signed_candidate_match/unverified with active_build_provenance_verified always false; active source/digest always null.
- No key issuance, signing secrets, trust root enrolment, revocation, immutable release approval, process identity, host/tunnel, A6/A7 mutation or paid agent dispatch in this child.
- A caller presenting both their own key/pin and manifest/pin has only self-consistency, not independent authentication.

## Acceptance
- Positive synthetic bundle passes offline without claiming serving provenance.
- Altered manifest/receipt/wheel/module/signature/public-key/keypin/manifest-pin fail closed.
- Four shipping versions aligned to 0.1.16. Exact latest PR HEAD GitHub checks must succeed: commit attribution, Ruff and pytest, built release artifact, clean demo and independent Ubuntu installer.
- Source merge is NOT release or completion of parent #669.

## Handover
See STATE.md, umbrella issue #669, ROADMAP and CURRENT_STATE; future trust-custody/immutable install/active process chain belongs to independently authorized operators.
