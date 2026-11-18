# #669 — detached builder signature, offline source child

## Goal
Verify a detached Ed25519 signature over exact manifest bytes, with the raw 32-byte public key itself SHA-256-pinned by an **independent operator-controlled channel**. This prevents a supplied signature without the specified key from matching, but does NOT create trust in the key.

## Source, data, and authority
- Source: `src/runner_mcp/detached_builder_signature.py`
- Tests: `tests/test_detached_builder_signature.py`
- Manifest/signature/public key file inputs are untrusted local bytes. External expected public-key fingerprint must never be taken from the same untrusted manifest or from the signature.
- No private signing key, operator secret, host path, actual signing custody, endpoint, worker/model usage or credential committed.
- Output is `offline_signature_match` or `unverified`; `active_build_provenance_verified=false`, source/digest null ALWAYS.

## Acceptance and risk
- Use Ed25519 raw 32-byte public key and detached 64-byte signature; compare exact manifest bytes.
- Negative tests: altered manifest, key mismatch, wrong signature, linked or group-writable evidence, oversized manifest, missing pin.
- Exact-head GitHub validation/pytest/build/demo + clean Ubuntu and attribution SUCCESS required for source merge.
- Even a valid signature does not indicate key authorization, revocation/freshness, actual installed bytes, process identity, immutable storage, or activation approval.
- Operator-protected key enrollment and revocation plus installer/load generation and A6/A7 rollback are separate trust gates, outside source-only child.

## Handover
See STATE.md, roadmap/ROADMAP.md, handover/CURRENT_STATE.md and parent issue #669.
