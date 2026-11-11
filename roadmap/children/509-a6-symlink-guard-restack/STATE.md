# A6 state-root symlink safety — final source-only handoff

status: COMPLETE_SOURCE_ONLY
owner_issue: Runner-MCP #509
merged_pr: https://github.com/Blacksp1d3r/runner-mcp/pull/709
merged_commit: 265dc1fc0866e35df07b05f6bcf3addee4f8dafa
exact_tested_head: 6f75e21b78badea7d0345c1125070809a5a17f83
source_version: 0.1.27 (not installed)
validation_ci: 38934210559 SUCCESS (Ruff, pytest, built release artifact, demo)
ubuntu_installer_ci: 38934210595 SUCCESS
attribution_ci: 38934210533 SUCCESS
historical_pr_655: CLOSED_UNMERGED_SUPERSEDED
failure_museum: RMCP-F-0026 SOURCE_FIXED_LIVE_UNQUALIFIED
production_changes_applied: false

Accepted source patch: reject dangling journal/evidence symlink before Path.exists; refuse symlinked input A6 state-root and cyclic resolution failures with sanitized errors. Tests demonstrate no private configuration or process-environment writes on refusal. No new remote capability, no host update, no A6 binding provisioning executed here.

True Fleet admission still blocked by live original-client Runner-MCP v0.1.9, source revision unavailable and self-update not ready; A6/probe unavailable; independent correct-host wheel attestation #669/AIfordable #428, and physical original-client ACK/rollback (Fabric #942/#943). Operator defers independent timer work until customer phase, but that does not authorize an unqualified live update.
