# #665 — Immutable tool-ID register: STATE

- State: DESIGN_SPECIFIED / IMPLEMENTATION_UNCLAIMED (2026-10-12)
- Parent: Runner-MCP #665; proposed ADR draft PR #666
- Proposed source contract: `docs/architecture/665-TOOL-ID-REGISTRY-CONTRACT.md` (commit c28b6cc0b0ce3573f9b87ba959744cee48a393e3)
- Branch: `docs/665-tool-identity-alert-contract-20261012`; no production code claim
- Implemented tool registry: NO
- Synthetic acceptance tests executed: NO; machine-readable 12-case test vectors recorded in `docs/architecture/665-REGISTRY-TEST-VECTORS.json` (declarative, not a passing validator test).
- Production changed: NO
- Reviewed active catalogue/schema evidence: NOT YET QUALIFIED
- Prior head of main at reconciliation: `2d025ce72443853795aa87b4ec96b83a25064634`
- Earlier draft PR #666 head `ba86b18b5261537530a45cb02a1d9116f84b233c`: exact-head attribution and validation success (runs 38216093203 and 38216093258). Newer heads require fresh CI.
- Dependencies: merge and reconcile #661, then #663; preserve #664 legacy tool contracts; #590/#642 real routing and host admission separately owned.
- Next safe action: independently review design, check for active worker leases, create isolated pure-registry-validator/test source PR with a UNIQUE updated release version, and compare proposed registry against actual isolated `tools/list`. No live rollout or magic-prefix changes.
- Safety/rollback: avoid modifying dispatcher or host; keep #341, Fabric A6 #942 and A7 #943 independent gates; Failure Museum only for observed defects.

## 2026-10-12 implementation checkpoint
- Separate stacked source PR #667: https://github.com/Blacksp1d3r/runner-mcp/pull/667 ; branch `feature/665-registry-validator-20261012` based on PR #663; candidate version 0.1.6 only.
- Pure `tool_identity_registry.py` and synthetic unit tests created. No production registry assignments, dispatcher changes or live alerts.
- First exact-head CI at `24c7fdd849c211877594bf9e26af25f5fbc0aea2`: attribution SUCCESS, clean installer SUCCESS, validation FAILED on Ruff I001 import grouping in test file (no pytest result).
- Ruff grouping fixed at `745619bb4075b0df9ae1130bf1afe0f10b0a7061`; fresh exact-head CI still required. Do not declare tests passing before results.
- Next: qualify complete CI and independent review, revisit immutable-retirement semantics before relying on validator, then rebase only after #661 and #663 integration, preserving unique release number.

## 2026-10-12 source corrections — latest
- Source PR #667 head `8e9475e00d9fa9d40c374771ffcb617259891af8` at update; check live GitHub HEAD before executing further.
- First CI failed on Ruff import order; second failed on Ruff blank line, both corrected. Subsequent branch pushes cancelled earlier CI runs due to concurrency group; cancelled is NOT passing.
- Strengthened validator against one ID aliased to different names across revisions and non-string policy/status values; new negative tests included.
- Fixed legitimate tool lifecycle: active → deprecated → retired allowed, **no reactivation**; historical tool ID, name, schemas, revision and permission immutability retained.
- Latest-head full CI and independent review still required; no runtime invocation, no dispatch enforcement, no customer alarms, no production install.

## 2026-10-12 validated exact head
- PR #667 candidate source head `8e9475e00d9fa9d40c374771ffcb617259891af8` exact-head GitHub workflows SUCCESS:
  - attribution run 38219997872
  - validation run 38219997875
  - clean Ubuntu installer run 38219997913.
- State: SOURCE_CANDIDATE_CI_GREEN / NOT_MERGED / NOT_DEPLOYED. Independent review still pending; staged release chain #661→#663→#667 unchanged.
- Registry validator is a pure offline source check; no actual per-tool IDs registered in live serving process; alerts/handshake/dispatcher not yet active.
- Next: independent review, review explicit registry migration and schema semantics; then rebase onto merged unique-version main and re-run exact-head CI. Do not claim runtime/tool fleet convergence.

## 2026-10-12 exact-head hardened schema validation
- PR #667 new source HEAD `a4a8e765c33e0ad89e8e2214fa5b292fb75b0794`: strict JSON-only schema hash inputs (including recursively rejecting non-string object keys and non-JSON values) with negative regression coverage; prevents key-normalization hash ambiguity.
- Exact-head three workflows PASS: validation `38227136986`; attribution `38227137004`; clean Ubuntu installer `38227137044`.
- This supersedes earlier head `8e9475e0` evidence. Source status: CI_GREEN / INDEPENDENT_REVIEW_MISSING / STACKED_DRAFT / NOT_MERGED / NOT_DEPLOYED.
- #661 is still open (HEAD `bad5eab79f5e4453237af5a26094ef03de9b4fa2`), zero independent PR reviews; #663 remains draft against #661, so do not bypass release ordering.
- Next: independent exact-head review; after #661/#663 merge, recompute candidate version and rerun CI. No live tool IDs, alerts or host qualification claimed.
