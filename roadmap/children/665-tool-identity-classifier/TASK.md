# #665 — bounded tool identity classifier (source-only)

## Goal
Pre-dispatch, pure classification of explicitly supplied expected and observed tool contracts, distinguishing unknown tool, disabled tool, wrong name/id, schema mismatch, contract revision mismatch, stale inventory and runtime unavailability.

## Implementation
- src/runner_mcp/tool_identity_classifier.py
- tests/test_tool_identity_classifier.py
- Candidate source version 0.1.21 aligned in all four shipping metadata files.

## Trust boundary
- The classifier must be fed by an independent trusted registry and an authenticated actual-serving inventory. Its boolean inputs are **not proof of authenticity**; this is a composable helper, not a runtime handshake, dispatch gateway or signer.
- READY is comparison-only, NOT permission to run. Existing MCP tools/list and tools/call unchanged; no new tool, route, network, alert dispatcher, worker, host, or credential.
- Fail closed on forged namespace, invalid stable ID, mismatched ID/name, malformed schema SHA, revision or enabled flag.
- Existing old customer tools remain undisturbed. Legacy compatibility policy #664 separate.

## Acceptance
- Unit regressions for typed distinct mismatch categories and malformed witnesses.
- Exact-head CI successful for Ruff/pytest, built release, five-minute demo, clean Ubuntu and commit attribution.
- No operational deployment. Need separate real authenticated serving process, tenant/policy, freshness, duplicate registry validation and alert/deduplication layers before dispatch enforcement.

## Dependency and handover
#665 parent remains open. #664 compatibility and #590/#669 verified real serving identity are prerequisite. Operator intentionally deferred rollback timer to customers.
