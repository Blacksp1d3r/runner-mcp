# Runner-MCP #590 — MCP read-only wire-test state

Status: IMPLEMENTED_WAITING_CI
Branch: `chatgpt/590-mcp-wire-readiness-regression-20261016`
Parent: Runner-MCP #590 and Fabric #924
Source version: 0.1.26 (unchanged, TESTS ONLY)
Files: new `tests/integration/test_fleet_readonly_failure_mcp_wire.py` and this child packet.
No live host changes, update approvals, release publish, File/DB changes, credentials or tunnel changes.

Next: inspect exact-head PR CI. If a test fails, reproduce the failed step, fix narrowly, record Failure Museum if distinct, then verify all required checks. Do not equate successful synthetic MCP response with a true independently observed server generation.
