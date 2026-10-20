# #615 — crash-atomic existing PR #618 reconciliation
status: SOURCE_CANDIDATE_CI_PENDING
source_version: 0.1.62 (candidate; original central 0.1.38 remains live)
draft_pr: https://github.com/Blacksp1d3r/runner-mcp/pull/618
merged_prior_child: #531 PR #780 v0.1.61
failure_id: RMCP-F-0064
unchanged: original six serving roles, Agent Bus relay, physical private A6, Fabric supervisor
not_qualified: physical kill/power-loss safety, offline host custody, authorized rearm and watcher cursor/ACK

ci_2026_10_20: release reservation PASS; initial full pytest failed only legacy corrupt-UTF8 fixture expecting JSON invalid rather than lock-orphan denial; RMCP-F-0065 updated fixture to first create a trusted lock and then corrupt data. Existing deliberate orphaned-lock negative test retained. Rerun exact-head validation required.
