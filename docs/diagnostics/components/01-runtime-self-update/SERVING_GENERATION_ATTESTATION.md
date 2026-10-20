# #669 / #341 — Serving-generation provenance admission design (source-only)

Status: DESIGN / NO LIVE ATTESTATION / NO NEW UPDATE AUTHORITY (2026-10-19).

## Why the two Doctor failures remain correct

The historical self-update transaction commit, the local Git checkout, an installed
distribution version and the *currently serving* imported process are four distinct
facts. Manual wheel installation must not rewrite historical self-update state or
silently grant a new updater. Existing first-party offline checks validate **candidate
consistency only**, not the active process or independently protected trust roots.

Read the existing implementations before building anything:
- `build_identity.py`: explicit unknown current identity; historical transaction retained.
- `artifact_receipt_preflight.py`, `builder_manifest_preflight.py`:
  offline wheel, module and independently pinned manifest equality.
- `detached_builder_signature.py`, `offline_signed_evidence.py`:
  offline signature comparison, not signer custody.
- `offline_evidence_chain.py`, `generation_layout_preflight.py`:
  consistent candidate graph/layout, not live process proof.
- `self_update.py`, `self_update_install.py`:
  existing update transaction, restart and recovery. Do not create a second updater.

## Required independently owned evidence edges

| Boundary | Trusted provider / verification | Reject as insufficient |
| --- | --- | --- |
| Builder identity | Pre-authorized signing key or independently protected manifest digest, version, source commit and wheel SHA-256; rotation and revocation policy | Key/digest supplied solely by the candidate, GitHub branch tip or version text |
| Installed bytes | Operator-owned bounded verification of wheel, installed RECORD and *all* imported package/module byte classes against sealed generation custody | Matching filenames, one module hash or mutable working-tree files alone |
| Generation | Existing immutable/versioned generation, verified owner/mode and protected previous generation, rollback eligibility | Naming/layout check as proof of immutability |
| Actual serving process | Correct independently identified physical host and exact service role(s), process/launcher start generation, loaded interpreter/import origin and fresh original-client response linked to that generation | Package metadata after `pip` when old process remains loaded; status from a different tunnel/host |
| Operator authority | Host-local protected, versioned, anti-replay and atomic receipt issued only after the above checks and bound to the attested generation | A manually edited transaction marker or a self-signed/candidate-supplied receipt |
| End-to-end admission | Unique request/correlation, result delivery and original-client ACK, with off-target A6 journal and independently exercised A7 revert | HTTP 200, running PID, source CI, or signed offline candidate by itself |

Evidence must be fresh and verified at consumption, not inferred once at build time.
The attested process may have older already-imported modules while on-disk metadata
shows a newer wheel; if the verifier cannot establish the relation unambiguously,
active revision and artifact digest stay null. Check each managed process role
independently; a role-mismatch must not be averaged into an overall green result.
Do not publish private host, process, filesystem or credential details.

## Proposed admission states (separate from historical transaction)

1. `unknown`: any missing, invalid, stale or non-independent evidence.
2. `mismatch`: trustworthy evidence of source, wheel, loaded generation,
   host binding, signer or process-role conflict.
3. `candidate_consistent_offline`: offline validation only; still **unverified live**.
4. `serving_generation_verified`: all independent local and process proofs
   reconcile within the authorized freshness window, and original-client identity
   is bound to that exact generation. This state is **not yet implemented**.

Only a separately qualified provider for state 4 may project a non-null
`active_runtime_revision` and `active_artifact_digest`. A verified manual
generation would establish a **separate** authenticated baseline and allow a
revised Doctor classification; it must never overwrite
`self-update-state.json` or retroactively relabel an old self-update. Prior
self-update history remains visible as history even when it diverges from a
new independently attested manual installation.

No activation, self-update, rollback, key creation, private config change or
live installation is authorized by this document or the source PR.

## Required negative regressions before implementation admission

- Missing/invalid/exception-raising revision provider; no exception leaks.
- Historical source equals checkout but does **not** prove active wheel.
- Stale old update commit and manual install produce different identities.
- Same version with different wheel digest; modified/missing RECORD or module.
- Process loaded before a new on-disk wheel; generation/role switch without ACK.
- Symlink, linked ancestor, partial receipt, duplicate fields, unsafe permissions.
- Wrong host/tunnel/service role, expired/revoked or candidate-supplied signer.
- Replayed receipt or sequence, rollback/restart generation, lost original-client
  ACK, and disagreement across all configured service roles.
- No current independently qualified witness always means
  `self_update_ready=false` on the serving first-party route.

Current live read-only status: 0.1.38; source and active wheel identity unverified;
the two doctor FAILs and `self_update_ready=false` are expected. Ownership of
live acceptance stays with #669/#341/#590 and Runner-Fabric #924/#942/#943.

## 2026-10-19 source implementation update

The existing offline artifact receipt/manifest/signature/layout validators now have a supplemental `offline_installed_record_preflight` consistency comparator. `offline_signed_installed_record_preflight` composes these tools and still returns `active_build_provenance_verified=False`, `source_revision=None` and `artifact_digest=None`, even when all offline source/wheel/RECORD bytes agree. `candidate_revision_with_wheel_identity` and the server active-revision adapter reject source-only identities, wrong loaded version, wrong component and missing wheel digest. They cannot manufacture a qualified host witness, signer custody, live imported module proof, protected manual baseline or original-client ACK. Do not connect offline result directly to the self-update manager as live authority.
