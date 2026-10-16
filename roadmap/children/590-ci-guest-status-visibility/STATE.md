# Optional Fabric CI guest status — state

Status: SOURCE_CANDIDATE_WAITING_CI
Branch: `chatgpt/590-bounded-ci-guest-unavailable-v0125`
Source candidate: 0.1.25
PR: to be created and verified against its exact final head.

Scope: status-only safe fallback in existing Runner-MCP server and Fabric bridge, static sanitized errors and tests, official metadata version bump. No live software update or host changes.

Next: run full exact-head GitHub checks; merge under enforced repository rules only after green checks. Then update parent issue/handover. Existing Runner-MCP runtime version 0.1.9 and unverified active source remain unchanged.
