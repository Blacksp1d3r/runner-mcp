# Runner-MCP #381 — fixed unit listener-owner child state

- owner: Runner-MCP #381 chat
- date: 2026-10-10
- status: COMPLETE_SOURCE_ONLY; LIVE_ACCEPTANCE_BLOCKED
- branch: safety/381-fixed-service-listener-pid-evidence
- source_pr: #645 MERGED
- exact_head_CI: head 446a1edc8129a51421a6ef1b6516f2a84e1ab93f; attribution 38071120207 and 38071261321 SUCCESS; full validation 38071120259 SUCCESS (Ruff, 2752 pytest PASS, built artifact, clean demo)
- source_paths: src/runner_mcp/fixed_coding_worker_actuator.py; tests/unit/test_fixed_coding_worker_actuator.py
- rootless_host_proof: BLOCKED_EXTERNAL (AIfordable #370)
- trusted_Fabric_intent: BLOCKED_EXTERNAL (#1172/#1400/#1398)
- authenticated_Q7: BLOCKED_EXTERNAL (#972)
- Claude_project_dispatch: NO_DISPATCH

- squash_merge: e29105cf6ed5baed42849dcdc8d706df97b182bc

## Scope
Distinguish fixed unit's MainPID socket inode from a foreign loopback listener, preserving bounded reasons. Conservative deny if socket is delegated to a child process. Source-only, no host state changes or paid provider API calls.

## Next
Exact-head CI green and source PR merged; do not mistake local MainPID snapshot for live signed Fabric authority. Integrate actual physical process attribution in AIfordable's qualified right-host proof; keep issue #381 OPEN until all cross-repo gates.
