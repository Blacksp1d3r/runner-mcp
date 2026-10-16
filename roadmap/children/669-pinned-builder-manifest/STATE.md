# #669 pinned builder manifest — current state

- Status: CHATGPT_IN_PROGRESS (source-only).
- Branch: `chatgpt/669-pinned-builder-manifest-v0112`, parent main `f563cb49e2f3fa8db81f3239c1f118e0922ddc44`.
- Candidate version 0.1.12. Source and tests created; four version metadata files aligned.
- No independent protected manifest digest signer/provisioning configured, and no service/installer/runtime changes. A synthetic SHA is used only for unit tests.
- Next: source CI, security negative vectors, existing issue #669 handover. PR creation, latest SHA and acceptance status must be reconciled from GitHub.
- Separate live evidence: original connected Runner-MCP last reported 0.1.9 with active revision/digest null. Fabric A6/A7/rollback are independently gated.
