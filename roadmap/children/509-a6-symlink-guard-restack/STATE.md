# A6 state-root symlink safety — handoff

status: SOURCE_CANDIDATE_WAITING_CI
owner_issue: Runner-MCP #509
related: Runner-Fabric #942 / Fleet #924
historic_source_pr: #655 (to close as superseded only after new merge)
branch: `chatgpt/509-a6-dangling-symlink-guard-restack-20261016`
source_version: 0.1.27 CANDIDATE (not installed)
base: current main v0.1.26; distinct from tests-only PR #708
scope: inherited original #655 exact bounded A6 directory symlink guard and tests; four distribution metadata files
runtime_mutation: none
expected_ci: validation + clean Ubuntu installer + commit attribution for exact head
remaining_live_gates: active v0.1.9 unverified, A6/probe absent, original-client ACK and independent host recovery unqualified
next: inspect PR and CI, correct actual errors, merge if green; close old #655 with explicit supersession and update issue/handover.
