# #669 pinned builder manifest — current state

- Status: COMPLETE_SOURCE_ONLY (serving provenance NOT qualified).
- Branch: `chatgpt/669-pinned-builder-manifest-v0112`, parent main `f563cb49e2f3fa8db81f3239c1f118e0922ddc44`.
- Candidate version 0.1.12. Source and tests created; four version metadata files aligned.
- No independent protected manifest digest signer/provisioning configured, and no service/installer/runtime changes. A synthetic SHA is used only for unit tests.
- Next: source CI, security negative vectors, existing issue #669 handover. PR creation, latest SHA and acceptance status must be reconciled from GitHub.
- Separate live evidence: original connected Runner-MCP last reported 0.1.9 with active revision/digest null. Fabric A6/A7/rollback are independently gated.

- 2026-10-16: PR #690 merged `215218cd06786838ca3e7ea86ae770b07eec4a84`; exact PR head `af90c798178c2565f4217acd0111099cbe62c4ba` was validation/Ubuntu/attribution SUCCESS. No trusted signing authority or deployment.
