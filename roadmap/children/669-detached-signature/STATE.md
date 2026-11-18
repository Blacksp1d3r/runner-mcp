# #669 detached signature — state

- Status: COMPLETE_SOURCE_ONLY (not enrolled/operationally trusted).
- Branch: `chatgpt/669-detached-signature-source-v0115` based on main `ce1a4846ce28a13569baf45a3f7fe4abd77a0c0f`.
- Candidate 0.1.15; `cryptography` declared explicitly as OSS package dependency.
- Pending: create PR, exact head CI, correct real defects, reconcile merge/handover.
- No independent trusted key fingerprint/key rotation authority enrolled. In particular, caller-provided matching key and hash is not authentication.
- Serving MCP remains 0.1.9 with null source/digest; source merge must never trigger a host update.

- PR #693 created, candidate 0.1.15. Initial CI validation 38870971649 FAILED (Ruff RUF059 unused digest variable); fix 6bcf7c04..., Failure Museum RMCP-F-0034. Current exact-head CI must succeed before merge. Active runtime unchanged.

- Source hardening: Ed25519 valid signature alone does not authorize arbitrary JSON; exact builder-manifest/v1 schema and duplicate-key rejection added, with negatives and Failure Museum RMCP-F-0035. Latest head after handover to be reconciled; do not confuse previous green CI with this changed code.

- 2026-10-16: PR #693 merged source-only at `e85b15924790d22a90b9a54cef1b55d10379d785`, exact HEAD `eedc369f695cabbc4ef837a822d22cc33de3d44b`. Validation `38871536393` (Ruff, pytest, release artifact, demo), Ubuntu install `38871536397`, attribution `38871536337` all SUCCESS. RMCP-F-0034/RMCP-F-0035 source fixes included. Original server remains 0.1.9 with null active revision/digest. No signer key custody enrolled.
