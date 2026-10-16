# #669 detached signature — state

- Status: CHATGPT_IN_PROGRESS, source-only.
- Branch: `chatgpt/669-detached-signature-source-v0115` based on main `ce1a4846ce28a13569baf45a3f7fe4abd77a0c0f`.
- Candidate 0.1.15; `cryptography` declared explicitly as OSS package dependency.
- Pending: create PR, exact head CI, correct real defects, reconcile merge/handover.
- No independent trusted key fingerprint/key rotation authority enrolled. In particular, caller-provided matching key and hash is not authentication.
- Serving MCP remains 0.1.9 with null source/digest; source merge must never trigger a host update.
