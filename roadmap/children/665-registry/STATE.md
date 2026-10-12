# #665 — Immutable tool-ID register: STATE

- State: DESIGN_SPECIFIED / IMPLEMENTATION_UNCLAIMED (2026-10-12)
- Parent: Runner-MCP #665; proposed ADR draft PR #666
- Proposed source contract: `docs/architecture/665-TOOL-ID-REGISTRY-CONTRACT.md` (commit c28b6cc0b0ce3573f9b87ba959744cee48a393e3)
- Branch: `docs/665-tool-identity-alert-contract-20261012`; no production code claim
- Implemented tool registry: NO
- Synthetic acceptance tests executed: NO
- Production changed: NO
- Reviewed active catalogue/schema evidence: NOT YET QUALIFIED
- Prior head of main at reconciliation: `2d025ce72443853795aa87b4ec96b83a25064634`
- Earlier draft PR #666 head `ba86b18b5261537530a45cb02a1d9116f84b233c`: exact-head attribution and validation success (runs 38216093203 and 38216093258). Newer heads require fresh CI.
- Dependencies: merge and reconcile #661, then #663; preserve #664 legacy tool contracts; #590/#642 real routing and host admission separately owned.
- Next safe action: independently review design, check for active worker leases, create isolated pure-registry-validator/test source PR with a UNIQUE updated release version, and compare proposed registry against actual isolated `tools/list`. No live rollout or magic-prefix changes.
- Safety/rollback: avoid modifying dispatcher or host; keep #341, Fabric A6 #942 and A7 #943 independent gates; Failure Museum only for observed defects.
