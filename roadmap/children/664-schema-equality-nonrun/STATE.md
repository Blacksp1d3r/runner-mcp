# #664 — strict legacy tool schema equality, source-only
status: SOURCE_MERGED_LIVE_UNQUALIFIED
source_version: 0.1.59 (merged, not installed)
owner_issue: Runner-MCP #664
source: src/runner_mcp/legacy_schema_compatibility.py
tests: tests/test_legacy_schema_compatibility.py
active_runtime_unchanged: true
next: exact-head CI, clean Ubuntu, attribution, guarded merge; never label this as historic customer binary compatibility or serving proof.

2026-10-20 CI finding RMCP-F-0061: first validation run #39467971129 negative deep-schema case revealed Python JSON encoder depth variation, source now uses explicit depth/node/alias guard, tests include recursive/shared containers. Re-run exact HEAD CI before source merge.

merged_pr: https://github.com/Blacksp1d3r/runner-mcp/pull/778
merged_commit: 55c26eaef2d7f08a1f84c1c79df03898fd413842
validation: 39468368681 SUCCESS
ubuntu: 39468368736 SUCCESS
attribution: 39468368707 SUCCESS
failure: RMCP-F-0061 SOURCE_MERGED
