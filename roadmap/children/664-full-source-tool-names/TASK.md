# #664 complete source tool name inventory guard (tests only)

## Goal
Freeze the currently source-registered complete MCP tool-name inventory from v0.1.24 as a CI regression fixture. New names may be added; previously present registration names may not disappear without an intentional compatibility decision.

## Implementation
- tests/fixtures/source_tool_name_inventory_v0124.json: 95 names harvested directly from main 53455720232ddf4de4e7d934bccb112fcb16e6df.
- tests/test_source_tool_name_inventory.py: AST-based scanner of `@mcp.tool()` and `mcp.tool()(callable)`; fails on removed/renamed names. Includes mutation tests.
- Tests only, no production source or release version modification.

## Constraints
- Static name list includes conditional registrations and tools not enabled for every customer. Do NOT confuse list with live tools/list on an authenticated 0.1.9 installation, immutable released wheel schema, tool permission or API compatibility of argument/output/error semantics.
- Complements #702 sampled callable signature guard. Parent #664 remains open for actual release artifacts, generated MCP schema, old/new client calls, explicit LTS/support policy and safe upgrade.
- No network, host, secrets, tunnel, cron, rollback or model dispatch operations.

## Acceptance
- Fixed source registration list captured from actual current source, at least 90 distinct names; AST guard allows additions and detects removals/conditional registration loss.
- Exact-head CI Ruff/pytest/demo/build/attribution, independent Ubuntu if generated for this tests-only PR.
- Do not change installed 0.1.9; source version remains 0.1.24.
