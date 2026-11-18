# #669 / child: Offline artifact receipt preflight

## Goal
Establish independently testable, **offline-only** candidate receipt writing and
wheel/installed-Python-module SHA-256 comparison without promoting unverifiable
historical self-update revision to the actively serving process.

## Source / ownership
- GitHub issue #669 is the authority; PR #689 is the single owned source child.
- Source: `src/runner_mcp/artifact_receipt_preflight.py`,
  `src/runner_mcp/offline_receipt_writer.py`.
- Tests: `tests/test_artifact_receipt_preflight.py`,
  `tests/test_offline_receipt_writer.py`.
- Canonical logical topology: `docs/diagnostics/topology/SYSTEM_TOPOLOGY.md`.

## Authorized scope and forbidden actions
- Allowed: source edits on the single bounded branch, synthetic tests, CI, safe
  public CI evidence and nonsecret handover.
- Not authorized: privileged installer/release/production activation, private
  host or tunnel changes, hidden credentials, A6/A7 bypass, or advertising
  `active_build_provenance_verified=true` from a self-declared receipt.
- Trust: SHA-256 checks prove candidate **byte equality**, not authentic origin.
  Signer/trust root and serving process are external prerequisites.

## Dependencies
- Base source `main` was 0.1.10 before candidate 0.1.11.
- Trusted builder manifest, immutable release venv, independently authorized
  receipt publication, runtime import generation and original-client ACK remain
  dependent follow-up; track under #669, not in this child.

## Acceptance
- Positive receipt write + candidate verifier results in `offline_bytes_match`
  and **false/null active identity**.
- Negative tests: malformed/changed wheel and modules; missing/oversized receipt;
  incomplete manifest, native extensions, path traversal, symlink directories
  and ancestors, hardlinks, nonprivate receipt modes, concurrent create-once,
  interruptions before and after publication, and publication uncertainty.
- Exact latest-head GitHub attribution, Ruff/pytest, demo, built artifact, clean
  Ubuntu installer verification must pass before source merge.
- No release, runtime process change, or #669 closure based on source CI alone.

## Failure and recovery
- RMCP-F-0029 tracks receipt path/collision hazards.
- A post-publication directory-sync failure is `ReceiptPublicationUncertain`,
  not a retryable “nothing happened”.
- Return failed/unverified for every unknown candidate state; never reuse
  historical self-update markers as active build proof.
- Continue from STATE.md, PR #689, and fresh original connector diagnostics.
