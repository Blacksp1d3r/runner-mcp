# Runner-MCP #341 — baseline wheel seal performed before validation (source-only regression)

- Date: 2026-10-28
- Owner: Runner-MCP A / #341
- Fix: [PR #911](https://github.com/Blacksp1d3r/runner-mcp/pull/911), merged 489530681939c831ea5a31d7ce093867b302c9ea, source 0.1.126
- Scope: disposable GitHub CI tests; **no observed live host failure, no production mutation**.

## Root cause

The first implementation of a new SHA-256 check for the existing staged recovery baseline wheel computed the seal immediately after build-wheel staging, *before* the ordinary lint, unit and source-compatibility checks. Legacy isolated pre-install tests deliberately substitute a synthetic wheel path without persisting an actual wheel, because their failure is supposed to happen before installation. Consequently the new digest precondition prematurely stopped four existing source rollback/failure tests and mislabeled their error categories. Initial exact-head validation run 40740188123 correctly FAILED.

## Correction and verification

Take the owner-local baseline wheel digest **after** lint/unit/source contract checks, directly before the already-existing `begin_transaction` boundary, while leaving old pre-install error recovery unchanged. Only freshly created optional sealed transactions get a SHA-256 field. Existing four-key transactions still parse with a NULL verification claim, not a fabricated success. Before attended recovery, a mismatching retained file denies pip install and the pending transaction is preserved for safe diagnosis. Newly added isolated tests cover same-path tamper, invalid digest, legacy transaction and prevention of pip install after mismatch.

Final exact PR head 744cf7f95a845238180a124fc101cc2f0db307d6 passed validation 40740612292 (Ruff/full pytest/release gate/built wheel/disposable systemd/five-minute demo), clean Ubuntu 40740612531, attribution 40740612308.

## Boundary and prevention

Never introduce recovery-artefact admission checks *earlier* than the safety condition for which the artefact is required. For pre-install failures, source restoration must remain independent of recovery wheel availability. SHA-256 of the same-manager local staged file is a **local tamper check**, not independently authorized wheel identity, current process memory provenance, full six-role restored service, independent Fabric #942 A6 journal, #943 no-NIC A7 rollback or original-client result/durable ACK. No new updater, signer, daemon or live cutover was added.
