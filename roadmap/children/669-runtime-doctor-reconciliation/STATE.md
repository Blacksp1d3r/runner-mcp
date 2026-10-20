## 2026-10-20 — A6 source 0.1.47 and six-role witness tests MERGED / live WAIT

Runner-MCP PR [#760](https://github.com/Blacksp1d3r/runner-mcp/pull/760) SOURCE MERGED squash `0f3fa078e97458c8ae3982ec71251422b2e10151`, v0.1.47, exact tested head `11cf153ad19325113c947e0b3115fa2920172556`; validation #39371276604, clean Ubuntu #39371276607 and attribution #39371276627 ALL SUCCESS. `runtime_doctor.fabric_a6_binding_state` now reports `warn/not_configured_0_of_11` for both private roots and all keys intentionally absent, instead of prior misleading PASS. Structural binding READY is NOT off-target A6 journal readiness. No live install, restart, folder or token mutation.

Runner-MCP PR [#761](https://github.com/Blacksp1d3r/runner-mcp/pull/761) TEST-ONLY MERGED squash `f7c37c53197f6c06207c646db3af41e0b0454858`, exact tested head `abe615d89b997641859bc83f3a3a0898f0b9c615`; validation #39371812361 and attribution #39371812310 SUCCESS. Synthetic six-role signed witness parity and eleven wrong/missing/duplicated/stale role, host, nonce and expiry negative regressions remain `active_build_provenance_verified=false`. No operational worker role names asserted, no runtime tool change or shipping-version bump.

The v0.1.47 pushed source artifact is independently checked OFF-HOST only: GitHub Actions #39371598373 candidate SHA wheel `d0dd841c9da39d9d85c26221c207c488fe091aaf22dd459caedaa0767fb9bef6`, sdist `258e2cc5c99cecb9616f0e3a1d6b6275473882fed4db8f7f34a6b336f2ff3c69`, 123/123 RECORD file checks, 117/117 package module equality; no loaded-process/signer/restore proof. Current original first-party LIVE central Runner-MCP remains 0.1.38, source/wheel NULL, `self_update_ready=false`, A6 0/11 live historical PASS/no readiness, Fabric Agent Bus relay UNKNOWN; six roles untouched. Next real accepted operator proofs: #669 correct-host generation+witness, Fabric #1617/#942 independently off-target A6 and #943 A7 offline rollback, AIfordable #609 exact same-original-client terminal ACK. Fabric #924 alone may later admit one guarded target. GitHub required admission branch policy #757 remains independent.

---

## 2026-10-20 — #669 six-role signed witness negative regression (TEST ONLY)

Following Runner-MCP [#760](https://github.com/Blacksp1d3r/runner-mcp/pull/760) SOURCE MERGED v0.1.47, an independent bounded test-only child now checks a deliberately SYNTHETIC six-role Ed25519 offline serving-statement comparator: all six consistent roles STILL return `active_build_provenance_verified=false` with source/wheel null, and eleven missing/foreign/stale/duplicated role, signer-host/nonce/expiry and expected-list mismatches refuse without promoting a live identity. No real host role names are asserted and no worker/service is contacted; this reuses existing pure comparator, makes NO executable release or version bump, and requires exact-head CI before merge. Correct-host actual loaded process, trusted issuer/revocation, original-client ACK, Fabric #1617/#942 A6 and #943 A7 remain WAIT. Existing connected central v0.1.38 is not changed by this test branch.

---

## 2026-10-19 — Second bounded source-hardening checkpoint

Malformed source-baseline checkout evidence now returns `source_commit=None` and `source_baseline_aligned=False`; synthetic malformed and thrown-provider negative tests deny updater start even where a fake active identity matches history. RMCP-F-0046 recorded as source-only, NOT a confirmed live failure. Serving 0.1.38 remains separately unverified and `self_update_ready=false`; physical proof still requires trusted host operator and Fabric A6/A7. The 0.1.40 metadata bump is retained, but exact-head CI is still required before merging.

---

## 2026-10-19 — Release version guard corrected / exact-head CI pending

2026-10-19 gate adjustment: source-code fix from PR #742 requires a unique shipping version relative to main 0.1.39. Candidate 0.1.40 is now synchronized in pyproject.toml, server.json (top + packages), glama.json and src/runner_mcp/__init__.py; CHANGELOG updated. Static metadata cross-check PASS, exact-head full Actions pending. Earlier head 0864b6d and prior queued jobs cannot qualify the newer code. Host operator and independent loaded-generation witness remain unsatisfied.

---

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
