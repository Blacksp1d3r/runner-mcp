# Runner-MCP — Repository blueprint legacy compatibility mapping

Issue: [#630](https://github.com/Blacksp1d3r/runner-mcp/issues/630). Library authority: `/Standards/AI_REPOSITORY_BLUEPRINT_STANDARD.md` v1.0, plus session master v1.2. Checked against main at the BPA-01 start commit `4981fa648aa127e5d2e0538b9eefec170f816466`. **This is a compatibility map, not a capability activation record.**

| Blueprint requirement | Existing authority/path | Classification | Next bounded decision |
|---|---|---|---|
| README and root AGENTS | `README.md`, `AGENTS.md` | COMPATIBLE | Keep security rules; add Library pointers in BPA-01 |
| Root project identity `project.yml` | Absent | BLOCKED | BPA-02: use only symbolic IDs after source-of-truth, local Git/storage and manifest schema are independently qualified; do not guess mounts |
| Roadmap | `roadmap/ROADMAP.md` | COMPATIBLE | Keep canonical file and existing relative links; no redundant root ROADMAP |
| Dependencies | `roadmap/DEPENDENCIES.md` | COMPATIBLE | Existing issue/PR dependencies remain authoritative after live Git reconciliation |
| Architecture and safety | `docs/architecture/`, `SECURITY.md`, `AGENTS.md` | PARTIAL | Keep current diagnostics and security references, review semantic equivalence before adding standalone root files |
| Changelog | `CHANGELOG.md` | COMPATIBLE | Preserve existing source/release semantics |
| Session and agent handover | `handover/SESSION_HANDOFF.md`, `CURRENT_STATE.md`, `AGENT_EXCHANGE.md`, `NEXT_ACTION.md` | COMPATIBLE | GitHub/live truth wins; update top checkpoint after material changes |
| Legacy executable issues/children | issue bodies, `roadmap/children/381-claude-worker-lifecycle.md`, `claude_feedback/CURRENT_ASSIGNMENT.md` | PARTIAL | Preserve legacy paths and owners; BPA-03 adds translation index, not mass migration |
| New child TASK + STATE | `roadmap/children/bpa-01/TASK.md` + `STATE.md` | COMPATIBLE FOR NEW WORK | No automatic claims without qualified coordinator/lease; do not backfill 100s of legacy children |
| Diagnostic topology and Failure Museum | `docs/diagnostics/` component index, field lineage, failures | COMPATIBLE | Keep component ownership and traceability as existing authority |
| Local primary Git/storage and optional GitHub mirror | GitHub repo is proven; private local Git/storage authority not established by this mapping | BLOCKED | BPA-02/independent operator proof, single writable authority and restore rehearsal before asserting local-first |
| Automated Fabric scaffold generation | Separate Fabric owner, no proven `project_scaffold_plan/apply` | BLOCKED | Do not add generic shell/repo creation; future Fabric epic and tests, external to BPA-01 |

## Scoped adoption order

1. BPA-01 (this change): cross-standard AGENTS links, transparent gap map and self-contained TASK/STATE. Source-only documentation, no server or host change.
2. BPA-02: independently specify/validate manifest and storage authority with symbolic IDs only; `project.yml` remains intentionally absent until safe schema and authority are verified.
3. BPA-03: for new work use two-file child contract; map older issue/Markdown children to one source of truth and ensure their prior owners/leases are respected.

## Non-negotiable proof boundaries

- No secret values, personal data, actual host paths, volume identifiers, operator credentials or raw private registry copied to this public mapping.
- `AGENTS.md` describes intent, never operating-system authority. No code, deployment, runner enrollment, backup media, real restore or existing worker queue changed by BPA-01.
- No mass `mv`/rename, no forced history rewrite, no duplicate canonical documents, no false claims that an unimplemented future Fabric generator is active.
- Formal completion of a child requires exact-head CI and acceptance evidence; a source-only docs merge never qualifies physical custody or live Claude execution.
