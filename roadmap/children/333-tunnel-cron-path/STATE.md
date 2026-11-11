# Child STATE — RMCP-333-CRON-PATH

child_id: RMCP-333-CRON-PATH
status: WAITING_CI
owner: Runner-MCP source lane (ChatGPT, bounded)
claim_id: null
lease_generation: null
base_revision: 77b5bdd5141cb19617d64b0592f79711bb434f0a
branch_or_worktree: fix/333-tunnel-cron-path-v016-20261013
pr_or_change_request: https://github.com/Blacksp1d3r/runner-mcp/pull/670
ci_or_test_evidence:
  - github-actions:38347077667:success_at_initial_head
  - github-actions:38347077664:in_progress_at_initial_head
  - github-actions:38347077668:in_progress_at_initial_head
blocker_refs:
  - https://github.com/Blacksp1d3r/runner-mcp/pull/661
  - https://github.com/Blacksp1d3r/runner-mcp/pull/668
  - https://github.com/Blacksp1d3r/runner-mcp/issues/590
  - https://github.com/Blacksp1d3r/runner-mcp/issues/669
last_verified_at: 2026-10-13
production_changes_applied: false

## Verified

- Separate attended operator intervention changed **only the managed tunnel cron PATH** with a secured prior crontab backup; on-host state moved from `configured/process_not_running` to `local_ready/control_plane_not_authenticated`.
- No local tool call in this PR modified the live runtime, auth configuration, secrets, tunnel ID or other cron components.
- Proposed source fix/tests and four version-bearing files committed on a stacked branch; initial head `808b5add0dd815e3cd766f5b787e7b86153cdbf2`.

## Not established

- Remote control-plane polling 401/403 or network failure root cause (can be post-start transient until a fresh authenticated poll)
- Original client's advertised tool catalogue equality
- Full exact-head CI / independent code review / protected merge
- Real installed/serving wheel-provenance identity; see #669
- A6/A7 and production rollout authorization

## Next safe action

Reconcile **latest PR HEAD** after this docs commit, collect full workflows and only diagnose concrete failed tests. Independent review of #661/#668/#670 and safety gates precede live activation. If the user reports persistent `control_plane_not_authenticated`, inspect ONLY the category-safe loopback control-plane health snapshot: `status`, `state`, `failure_category`, `http_status`, `last_success_present`; never print raw config, environment or support archives in public Git.
