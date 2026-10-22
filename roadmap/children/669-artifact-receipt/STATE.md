## 2026-10-22 — #669 v0.1.78 SOURCE MERGED; independent live wheel/route still WAIT

- **Source reconciled**: PR [#800](https://github.com/Blacksp1d3r/runner-mcp/pull/800) merged 2026-10-21T20:34:26Z as `0daa8e7fd2c6edcb53c17d7f024efbb1e3d9e7c4`; exact PR HEAD `acf9e5e7b480e422ff1b6f2d64b27f4515a41732`, validation + clean Ubuntu installer + attribution SUCCESS. Source `pyproject.toml=0.1.78`. Earlier #794, #796, #797 and docs #798 are merged and MUST NOT be repeated. Supersedes the earlier “v0.1.78 candidate/pending” language below.
- **What exists**: `artifact_receipt_capture.py` can write one private 0600 candidate receipt of retained original wheel SHA-256 + installed `runner_mcp` Python-module checksums, requiring offline byte agreement. It does **not** independently authenticate the claimed source commit, attest process-imported wheel, protect an earlier generation, bind six real process roles, or yield A6/A7/update admission. #800 intentionally has not connected an installer hook or changed live services.
- **Fresh original-client primary** on 2026-10-22: loaded=installed `0.1.38`; `build_identity.source_revision=null`, `artifact_digest=null`, `active_build_provenance_verified=false`, `self_update_ready=false`; Runtime Doctor two provenance FAIL (`source_baseline_drift`, `active_revision_unavailable`), A6 `pass/not_configured_0_of_11` (safe absence, not qualified); Fabric bridge `ready` but `a6_prepare_available=false`, `synthetic_probe_status_available=false`, `mutation_enabled=false`. Reading local `host:local` inspection does not independently attest another host or wheel. Fabric #1697 pure fleet read projection is source merged, not a physical host scan.
- **Next executable dependencies (do not add another updater/relay)**: (1) Fabric #924 via authorized correct-host route independently inventories the *actual six launchers/process instances* and previously serving 0.1.38 original wheel bytes, installed RECORD and current loaded module evidence, retaining independently validated previous-good wheel; UNKNOWN remains WAIT. (2) Connect the existing #800 receipt emitter only within the already-authorized installer/generation custody (no generic path API); qualify its independent trusted source/bytes witness and original-client epoch. (3) Fabric #1617/#942 physical independent A6 journal, #943 disconnected A7 six-role rollback, #1556/#1563 terminal original-client result+ACK before #924 one-target staged update. None is complete merely because source CI passed.
- **Operational boundary**: no production install, six-role restart, A6 binding creation, storage formatting, Agent Bus dispatch, tunnel, secrets, OIDC/MFA or forced self-update in this session. #509 remains closed SOURCE-ONLY; #669 stays OPEN. Live baseline must not be relabeled as current GitHub main.

## 2026-10-21 — v0.1.78 original wheel candidate custody writer (new code, not live)

- Previous source-only read-side `offline_artifact_receipt_preflight` is merged. Follow-up complements it with bounded original `*.whl` candidate receipt capture: SHA-256 of the retained original zip wheel and every `runner_mcp/` Python entry, checked against installed module content; 0600 atomic-create-once owner-private file in existing 0700 generation directory, no caller-specific dynamic shell, no new runner/relay/updater.
- Exact wheel is still an **independently untrusted input** at this point. Claimed source revision is NOT verified against CI issuer, currently serving interpreter, or original-client Agent Bus receipt; live source revision/digest must remain NULL. Continue #669 active loaded-module/wheel witness and Fabric #924 original-client route; preserve 0.1.38 roles, no restart/deploy.
- Isolated positive and tamper/rollback safety tests required via ordinary CI; PR #pending.

# #669 offline receipt — state

- Owner: ChatGPT bounded source child.
- Status: COMPLETE_SOURCE_ONLY (not production-qualified).
- PR: https://github.com/Blacksp1d3r/runner-mcp/pull/689
- Source branch: `chatgpt/669-offline-artifact-receipt-preflight`.
- Candidate distribution version: 0.1.11 (source-only).
- Source merged from validated exact head `b2f0b0138849195cc5eba94df4c8dcef80547148`
  into `main` squash `4a7a03fb9f0785a5d8fe20e4a3ba2176b2ff508a` on 2026-10-16.
  Runner MCP validation 38860034267, Ubuntu installer 38860034274,
  attribution 38860034268 / 38860276351 were SUCCESS at exact PR head.
  Source merge is not authorization to install or attestation of a serving process.
- Main last observed `ff16511889758f3057a9781759aa1c6a7bf96f6f` (0.1.10).
- Original connected server last observed 0.1.9; active artifact digest and
  source revision not verified, as designed; `self_update_ready=false`.
- Implemented: private candidate receipt writer, atomic exclusive publication,
  pre-/post-publish failure distinction, offline wheel+module digest check,
  negative tests and latest code hardening for explicit absolute, no-`..`,
  no-linked-ancestor receipt path plus two-thread write race.
- Next: validate post-merge main CI separately; scope next #669 child for
  independently trusted builder evidence/immutable installation. Do not mistake
  merged source for a production release.
- Follow-up #669 remains: independent trusted builder evidence, immutable
  installation, actual serving-generation verification and original-client ACK.
- Failure register: docs/diagnostics/components/12-diagnostics-audit/FAILURES.md
  RMCP-F-0029.
