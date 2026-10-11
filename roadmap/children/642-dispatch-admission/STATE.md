child_id: RMCP-642-dispatch-admission
status: BLOCKED
owner: Runner-MCP #642
branch_or_worktree: docs/341-a6-fleet-gates-20261011
pr_or_change_request: "PR #653 docs; PR #654 synthetic tests"
ci_or_test_evidence:
  - "PR #654 head c492e31625e653321f3e918adfe32d10a0cbf81f validation 38126280267 SUCCESS and attribution 38126280229 SUCCESS"
  - "PR #653 previous head 68671e05f75435d45360d6aa10025a29d1cd6876 validation 38126071261 SUCCESS and attribution 38126071378 SUCCESS; newer doc head unqualified"
blocker_refs: ["Runner-MCP #590", "Runner-MCP #509", "Fabric #942", "Fabric #943"]
production_changes_applied: false
next_safe_action: "Obtain first-party attested expiring host permit bound to service ID, current process SHA, artifact and catalogue; implement real call_tool gate, then negative integration tests."

## Checkpoint 2026-10-11
Merged #641 source-only oracle is NOT wired into MCPServer.call_tool. No real host permission authority was identified or fabricated. Interception point resolved in src/runner_mcp/server.py build_mcp. PR #654 tests remain oracle-only. No deploy/restart or Claude dispatch.
