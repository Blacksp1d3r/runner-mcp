# #669 — runtime doctor reconciliation state

- Status: BLOCKED_EXTERNAL_FOR_LIVE_ATTESTATION; source scope documented.
- Date: 2026-10-19.
- Working branch: `fix/runtime-doctor-provenance-20261019`.
- Base main: `9aff9b8662ff108639d81b9075617ed7bb760fd9`.
- Latest first-party runtime evidence: 0.1.38 serving; source baseline drift and active revision unavailable; self-update not ready.
- Source diagnosis: `installed_source_revision` deliberately returns null; self-update history and active runtime identity are separate authority classes.
- Already completed: #669 artifact receipt, signed offline evidence and generation-layout *source-only* primitives; owner-attended 0.1.38 active cutover.
- Still missing: independently trusted installer/signer custody and serving-generation attestation, safe baseline reconciliation, complete original-client ACK and independent recovery acceptance.
- Branch mutation: documentation/task scoping only. No live host changes, fake pass, update attempt, source code change or version bump.
- Next executable action: source regression design based on this exact lineage; live reconciliation awaits authorized private correct-host operator evidence and physical safety qualification.

- 2026-10-19 source negative regressions added in tests/security/test_self_update.py at commit `3e874bd96d11117dd372fc53ac466c7bb5b0ab1e`: invalid/missing provider, bounded exceptions, stale historical baseline, false update readiness. GitHub validation run #39278937691 observed QUEUED; not claimed green. Runtime code remains unchanged.

## 2026-10-19 follow-up — source containment, no live admission

- Live first-party `runtime_status` and `runtime_doctor` read-only results reconfirm 0.1.38, history commit distinct from source checkout, two Doctor FAILs and `self_update_ready=false`; `build_identity.source_revision` and artifact digest remain null.
- PR #742 same branch: `self_update.py` exception containment commit `e46da3eafcf11eb5e0f1225012fa6813ae394faf`; negative tests commit `e9d17f822903a26c61865daf9f4a032da54caf24`.
- RMCP-F-0045 is a **synthetic source-observed** provider exception escape, NOT an observed live failure. Catch missing field/attribute errors; never promote historical self-update evidence as the current process.
- Detailed independent trust/serving-generation acceptance requirements specified in `docs/diagnostics/components/01-runtime-self-update/SERVING_GENERATION_ATTESTATION.md` (design only).
- Exact-head GitHub Actions on previous `068e96ac` were queued; new commits invalidate that head's CI as merge evidence. Local full repository test unavailable due GitHub DNS resolution. Recheck newly triggered exact-head CI; do not merge red/pending/unverified.
- Physical correct-host attestation, trusted signer custody, manual baseline admission, original-client ACK and A6/A7 recovery remain OPERATOR/FABRIC BLOCKED. No host or state file mutation attempted.
