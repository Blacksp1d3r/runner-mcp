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
