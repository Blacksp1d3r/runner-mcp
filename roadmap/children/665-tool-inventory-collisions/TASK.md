# #665 bounded tool inventory collision preflight

## Goal
Pure offline structural validation of two bounded, independently authenticated tool inventory snapshots, finding duplicate stable tool identifiers, duplicate names, malformed contracts and mismatched schemas/contract revisions.

## Inputs, outputs, authority
- Code: src/runner_mcp/tool_inventory_preflight.py, tests: tests/test_tool_inventory_preflight.py.
- Source candidate version 0.1.22. Uses previously source-complete 0.1.21 pure ToolContract/classifier.
- Result: enum READY (structural equality only), INVALID_TOOL_CONTRACT, DUPLICATE_TOOL_ID, DUPLICATE_TOOL_NAME, INVENTORY_MISMATCH, UNTRUSTED_INVENTORY, STALE_INVENTORY, INVENTORY_TOO_LARGE.
- Maximum 256 tools; accepted collections must be list/tuple; flag inputs strictly booleans.
- No protocol changes or network/dispatch/alerts. READY is NOT execution permission; authoritative registry, actually loaded/serving inventory, tenant/host policy, caller authenticated transport, replay fencing, legacy compatibility and alert delivery are separate children.

## Acceptance
- Synthetic duplicate/mismatch/spoofed authority tests.
- Current source exact HEAD CI Ruff+pytest, built release, clean demo, clean Ubuntu installer and commit attribution all successful before merge.
- Nothing installed on live server; independently gated operational/rollback/security custody unchanged.
- Parent #665 stays open.
