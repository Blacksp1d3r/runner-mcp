# Runner-MCP — Child task index and legacy compatibility

Canonical standards: Library `MASTER_AI_ENGINEERING_SESSION_HANDOFF_PROTOCOL.md` v1.2 and `AI_REPOSITORY_BLUEPRINT_STANDARD.md` v1.0. Tracking parent: [#630](https://github.com/Blacksp1d3r/runner-mcp/issues/630).

This is an **index**, not a second task backlog or execution authority. Actual PR/issue state and qualified Fabric leases always win over an index, chat or stale STATE. No implicit claim, automated execution, approval or completed test is implied by a link.

## Legacy path mapping (do not move or duplicate)

| Stable work item | Existing authoritative document | New TASK/STATE? | Ownership/interpretation |
|---|---|---|---|
| #381 — Claude lifecycle | [381-claude-worker-lifecycle.md](381-claude-worker-lifecycle.md) | No; existing detailed child document is preserved | Separate active owner/chat; issue #381 and its operator/Fabric gates control acceptance. Do not create a second #381 task or reassign |
| Historical Claude review queue | [CURRENT_ASSIGNMENT.md](../../claude_feedback/CURRENT_ASSIGNMENT.md) | No; legacy queue is preserved | Its claims/PRs and current GitHub evidence win; do not rewrite old tasks |
| Diagnostic component children | [component registry](../../docs/diagnostics/component_registry.yml) and [components](../../docs/diagnostics/components/) | No; existing ROADMAP/SOURCES/DATA_LINEAGE/FAILURES are canonical | Diagnose by component registry; do not rename or copy diagnostic files |
| BPA-01 — standards reference | [bpa-01/TASK.md](bpa-01/TASK.md), [STATE.md](bpa-01/STATE.md) | Yes | COMPLETE with merge proof, no runtime/storage authority implied |
| BPA-02 — symbolic manifest draft | [bpa-02/TASK.md](bpa-02/TASK.md), [STATE.md](bpa-02/STATE.md) | Yes | Design/tests landed in PR #633; operational primary Git, storage, lease and root project.yml remain BLOCKED_AUTHORITY |
| BPA-02B — operational manifest authority | [bpa-02b/TASK.md](bpa-02b/TASK.md), [STATE.md](bpa-02b/STATE.md) | Yes | BLOCKED: issue #634 requires operator-qualified canonical Git primary, one writer, isolated restore and Fabric lease/fence before root project.yml |
| BPA-03 — this index and future contract | [bpa-03/TASK.md](bpa-03/TASK.md), [STATE.md](bpa-03/STATE.md) | Yes | COMPLETE: PR #632 reviewed and CI green; existing children unchanged |

## Canonical rule for new executable children

Create `roadmap/children/<stable-id>/TASK.md` and `STATE.md` as the two primary records when a **new** executable child begins. Choose a non-colliding lowercase ID. A simple fixed checklist suffices; do not create additional boilerplate Markdown for every child:

- `TASK.md`: ID/parent, owner and scope, explicit exclusions, dependencies and authority gates, source/topology/data lineage, permitted changes, bounded implementation algorithm, test matrix, Failure Museum cases, completion gate and next-agent handoff.
- `STATE.md`: status, claim identity (or explicit null), lease (or null), base/head, branch/PR, terminal evidence, blockers, verification timestamp, next safe action and whether production changes occurred. Record UNKNOWN instead of guessing.
- GitHub issue/PR and exact CI evidence are source-of-truth for live task progress. Do not duplicate their full narratives in STATE or treat a STATE field as an execution token.
- Legacy standalone children and diagnostic component trees stay mapped **as-is**. Map, do not mass-rename or backfill incomplete historical child records.
- No writes to another agent's active branch, no automatic claim creation, no privileged host or filesystem action. A validator/checklist may identify missing docs but **cannot** authorize execution, storage custody, deploy or merge.

## Minimal verification

A new child directory must have both `TASK.md` and `STATE.md`, with stable parent references; each existing legacy single-file task in this index must still exist. Compare actual current GitHub branches/issues and recorded owners before starting anything. Follow `AGENTS.md` and the session handover when state differs.
