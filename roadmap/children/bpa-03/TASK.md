# BPA-03 — Non-disruptive legacy child mapping and two-file new child contract

Parent: [Runner-MCP issue #630](https://github.com/Blacksp1d3r/runner-mcp/issues/630). Profile: expanded legacy-compatible. Scope: public documentation/index only.

## Goal / deliverables
Preserve existing authoritative legacy issue and component/Claude documents while adding an explicit, stable index `roadmap/children/README.md`. Prove that new BPA child task has exactly the two core `TASK.md` and `STATE.md` records; spell out the default for future children. Never mass migrate older docs.

## Exclusions and security boundaries
Do not edit issue #381/Claude worker code, another chat's child/claim, active Fabric code, tunnel/connector state, private host/storage bindings, GitHub provider artifacts, credentials or live services. No generic shell, arbitrary repo generator, project scaffold activation, forced git rewrite or CI bypass. The index itself cannot assign tasks, approve mutations or qualify storage.

## Dependencies and topology
Requires merged BPA-01 `AGENTS.md` reference and compatibility mapping. Inputs: current GitHub repository tree, existing `roadmap/children/381-claude-worker-lifecycle.md`, `claude_feedback/CURRENT_ASSIGNMENT.md`, `docs/diagnostics/component_registry.yml`, canonical session/blueprint standards. Outputs: the index plus these two BPA-03 documents; no runtime dependencies.

## Implementation algorithm
1. Compare exact GitHub HEAD, existing children, agents and open PR owners.
2. Reference (never duplicate) the legacy #381 and Claude queue, preserve diagnostic component topology.
3. Publish two-file TASK/STATE contract for *future* children and explicitly leave absent `project.yml` and local-Git authority to BPA-02.
4. Inspect docs-only diff and references; run exact-head attribution and full required CI.
5. Obtain review, merge with expected-head gate, reconcile parent #630 stays OPEN for BPA-02, record terminal evidence. On interruption resume by PR SHA and STATE.

## Failure Museum / negative tests
Missing legacy reference; accidental duplicate #381 owner; treating documentation as an authority/lease; breaking relative links; unverified local storage claim; accidentally closing operational issue #381 or blueprint parent; stale CI after main changes. Fail closed on any unknown owner/authority or conflicting claim.

## Exit and handoff
BPA-03 COMPLETE only after exact-head all CI jobs green, review, merged docs and updated handover. BPA-02 remains separately blocked unless authority and symbolic schema tests are resolved.
