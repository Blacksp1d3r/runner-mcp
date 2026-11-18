# #681 child — fail-closed continuity-status response

## Goal
When the already-existing fixed read-only Fabric continuity launcher cannot be qualified, return a bounded structured state instead of an opaque MCP tool exception. Do NOT execute any fallback, retry an uncertain-effect request, or expose endpoint/secret/error details.

## Code and ownership
- src/runner_mcp/fabric_continuity_status.py: allowlisted bounded unavailable result helper
- src/runner_mcp/server.py: catch only FabricContinuityStatusError on existing fabric_continuity_status tool and audit denied
- tests/test_fabric_continuity_unavailable.py: exact response contract plus hostile error text regression.
- GitHub parent issue #681, transport observability #590. Source-only v0.1.17.

## Acceptance
- Missing launcher/config or operational failure returns `runner-mcp/fabric-continuity-unavailable/v1`, state unavailable with sanitized reason; localWorkAllowed=false, externalSubmissionAllowed=false, reconciliationRequired=true, providerMutationEnabled=false.
- No generic exception for expected controlled unavailability; audit denied remains; no real private host path, token, command or arbitrary exception text returned.
- All existing successful continuity-status v1 data unchanged. No new subprocess, network probe, automatic retry or relay mutation.
- Exact PR HEAD Ruff/pytest/build/demo/Ubuntu/attribution SUCCESS. Source merge only under current AGENTS branch rules; not a live rollout.
- Live original client 0.1.9 cannot show this result until independently authorized update; no 0.1.9 process/config/tunnel changes.

## Dependencies
- Existing #681 intermittent host/snapshot issue still separate; Fabric relay unknown and physical host handover remain unresolved. Operator explicitly deferred rollback timer until customer phase. No blocker for this source patch.
