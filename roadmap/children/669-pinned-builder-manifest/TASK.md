# #669 child — Pinned builder manifest (source-only)

## Purpose
Compare the SHA-256 of an offline builder manifest against an independently supplied, externally protected expected manifest digest; then compare pinned wheel bytes with the manifest. This is NOT an authentication service or runtime provenance attestation.

## Ownership and scope
- Source: `src/runner_mcp/builder_manifest_preflight.py`.
- Tests: `tests/test_builder_manifest_preflight.py`.
- GitHub issue #669 remains the umbrella and source-of-truth for trusted installer / active-process generation.
- Allowed: repository edits, synthetic fixtures, CI, GitHub handover.
- Disallowed: inventing any trust root, unapproved signing key, arbitrary private host access, process restart, installer activation, production verification claim.

## Input / output
- Inputs: local regular manifest, local regular wheel, an exact 64-hex expected SHA-256 supplied over an independently trusted channel.
- Manifest v1 fields: schema_version, source_revision, distribution_version, wheel_sha256, interface_schema_digest.
- Result: `offline_manifest_and_wheel_match` or `unverified` without digest/revision disclosure and `active_build_provenance_verified=false` always.
- SHA input provenance is a caller responsibility. A malicious caller can submit its own SHA; this comparator explicitly cannot confer cryptographic trust by itself.

## Negative tests
- forged or changed manifest with old digest, replaced wheel, mismatched source/version/schema, extra fields, absent trusted digest, symlink and writable evidence files.
- Strict no-merge gate: exact-HEAD Ruff, pytest, Ubuntu installer, demo, build artifact and attribution successful.

## Dependencies / excluded next child
An authorized trusted builder and pinned digest distribution, immutable environment and release-generation installation receipt, and authenticated active-process ACK are separate operational steps. Source merge does not permit deployment. See topology and current handover.

## Failure recovery
Fail closed; if CI fails, inspect exact failing step, fix root cause and record in component Failure Museum. Reconcile PR and main before progressing.
