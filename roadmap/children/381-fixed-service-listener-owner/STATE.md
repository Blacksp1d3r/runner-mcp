# Runner-MCP #381 — fixed unit listener-owner child state

- owner: Runner-MCP #381 chat
- date: 2026-10-10
- status: SOURCE_PR_IN_PROGRESS; LIVE_ACCEPTANCE_BLOCKED
- branch: safety/381-fixed-service-listener-pid-evidence
- source_pr: pending
- exact_head_CI: pending
- source_paths: src/runner_mcp/fixed_coding_worker_actuator.py; tests/unit/test_fixed_coding_worker_actuator.py
- rootless_host_proof: BLOCKED_EXTERNAL (AIfordable #370)
- trusted_Fabric_intent: BLOCKED_EXTERNAL (#1172/#1400/#1398)
- authenticated_Q7: BLOCKED_EXTERNAL (#972)
- Claude_project_dispatch: NO_DISPATCH

## Scope
Distinguish fixed unit's MainPID socket inode from a foreign loopback listener, preserving bounded reasons. Conservative deny if socket is delegated to a child process. Source-only, no host state changes or paid provider API calls.

## Next
Record exact-head CI and merge SHA only after checks succeed. Integrate actual physical process attribution in AIfordable's qualified right-host proof; keep issue #381 OPEN until all cross-repo gates.
