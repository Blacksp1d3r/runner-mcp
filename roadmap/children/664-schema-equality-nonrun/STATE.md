# #664 — strict legacy tool schema equality, source-only
status: SOURCE_CANDIDATE_CI_PENDING
source_version: 0.1.59 (candidate, not installed)
owner_issue: Runner-MCP #664
source: src/runner_mcp/legacy_schema_compatibility.py
tests: tests/test_legacy_schema_compatibility.py
active_runtime_unchanged: true
next: exact-head CI, clean Ubuntu, attribution, guarded merge; never label this as historic customer binary compatibility or serving proof.

2026-10-20 CI finding RMCP-F-0061: first validation run #39467971129 negative deep-schema case revealed Python JSON encoder depth variation, source now uses explicit depth/node/alias guard, tests include recursive/shared containers. Re-run exact HEAD CI before source merge.
