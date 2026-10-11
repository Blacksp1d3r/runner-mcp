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

## 2026-10-11 continuation — qualified source fixture, NOT live policy

- #654 last completed prior head dbf1b0bd12185369f365b40d3d953574444f5ebf: Runner MCP validation 38128064882 SUCCESS and attribution 38128064884 SUCCESS.
- New #654 head ed58704223d424b5d8155f690f2cb538fa929a56 adds AST validation for all eight test fixture tool names (five OCR plus runtime_status, queue_status, fabric_disposable_target_qualify); its exact-head CI is not yet accepted until both checks finish.
- #655 latest head c8dc9b7340eb92e467cbd749c885f3b605eef411: Runner MCP validation 38127697809 SUCCESS, attribution 38127697888 SUCCESS; parent+child A6 symlink guard is SOURCE only. Separate approver still absent.
- #653 head 691606d53da2e715988dce853470a2755cb18f52: validation 38127251289 SUCCESS, attribution 38127251251 SUCCESS.
- No host-provenance issuer, trusted policy signature, installed exact process/catalogue, real dispatcher deny or original-client delivered response was established. Preserve BLOCKED; never promote green synthetic tests to runtime authorization.
## Exact-head CI reconciliation — 2026-10-11

- #653 current head `a20fb8dbe31968d805936e79e0ae94732366d5a0`: validation run `38128716494` SUCCESS; attribution run `38128716500` SUCCESS. Previously documented whitespace failure was fixed at the current head.
- #654 current head `ed58704223d424b5d8155f690f2cb538fa929a56`: validation `38128315342` SUCCESS; attribution `38128315344` SUCCESS.
- #655 current head `c8dc9b7340eb92e467cbd749c885f3b605eef411`: validation `38127697809` SUCCESS; attribution `38127697888` SUCCESS.
- All three remain unmerged and lack independent approving reviews. These results qualify synthetic/source changes only; they do not authorize the unqualified dispatcher or fleet update.
## 2026-10-11 source-only cross-host policy guard

Draft PR #656 adds required independently verified service asset ID to the pure admission evaluator and fails closed on foreign or missing identity; no live identity provider, signature verification or real dispatcher integration. Current PR #656 head `e510e334c8df34525ca000592754d93c95a4a2c4` requires exact-head CI and independent security review. IMPORTANT merge order: #654's tests use prior evaluator call shape, so merge/reconcile #654 first, then rebase #656 and adapt the extra #654 invocations, validating the rebased exact head. Do not merge #656 ahead of #654. No host authority or production impact.
## 2026-10-11 CI-green #656 review checkpoint

PR #656 latest exact head `71eb6343c15cc478ae7cf7724149fd5c62d2f85d`: Runner MCP validation `38129805355` SUCCESS and commit attribution `38129805443` SUCCESS; Ready for Review, independently approving review absent. It adds independent verified-service-ID input and explicit foreign-host policy denial to the *pure* oracle (central Failure Museum RMCP-F-0027). This does NOT authenticate host identity, bind to real MCP dispatch, verify signature, or prove live result+ACK. PR #654 must be reconciled first because it calls the earlier evaluator signature. Overall #642 remains BLOCKED_ON_TRUSTED_POLICY_SOURCE.
