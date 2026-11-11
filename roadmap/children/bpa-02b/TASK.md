# BPA-02B — Operational repository authority qualification

Parent: [Runner-MCP #630](https://github.com/Blacksp1d3r/runner-mcp/issues/630); independent blocker issue: [#634](https://github.com/Blacksp1d3r/runner-mcp/issues/634). Profile: expanded. Status: BLOCKED until independent authority evidence exists.

## Goal, scope, output
Convert the **draft only** symbolic repository candidate to an actual root `project.yml` *only after* the Git primary, optional mirror, read-only evidence registry, local storage, claim/fence ownership and clean restore have been independently proven. Output is a separate authorized PR for a machine-readable manifest bound to symbolic IDs. No deployment or Fabric apply follows implicitly.

## Out of scope / forbidden actions
No current host/volume path inspection through unrestricted shell or Desktop Commander, no guessed local Git primary, blanket repo-create or shell capability, tunnel/service restart, sudo, private data, credential rotation, production restore, archival deletion, Fabric scheduler parallelism, Claude #381 execution or bootstrap, or modifications to the #590/#587/#588 owner lanes. GitHub source success or a memory of an 8TB disk is **not** mount/namespace authorization.

## Sources, data lineage, topology
- Public: [blueprint candidate](../../../docs/standards/PROJECT_MANIFEST_CANDIDATE.md), candidate YAML/schema, `AGENTS.md`, roadmap, CURRENT_STATE, issue and GitHub exact HEAD.
- Trusted private authorities (must be accessed by approved read-only bounded operator tools, never copied here): canonical inventory mapping of project -> service/runtime -> host -> Git primary -> independent storage volume/delegated namespace; owner/mode/symlink/freshness evidence; Fabric lease/fencing policies.
- Outputs: sanitized evidence *identifiers*, never raw paths, hostnames, mount IDs, tokens, personal data or private logs. Future proposed manifest will reference only symbolic authority IDs and approved revisions.

## Bounded execution children — do not parallelize destructive gates

1. **BPA-02B.1 — read-only authority admission:** operator verifies exact physical/source ownership, identity, freshness, conflict-free writable primary and admitted namespace; resolve UNKNOWN to either independently attested evidence or BLOCKED. Never infer from public GitHub visibility.
2. **BPA-02B.2 — independent restore/fencing:** after admitted target, isolated no-production reset Git bundle snapshot/hash/read proof, independent actual restore and one-writer/fenced-mirror negative cases. No live code deploy, provider deletion or production data replay.
3. **BPA-02B.3 — schema promotion:** after 1/2, independently design and review strict *operational* manifest schema. Reject candidate-only `BLOCKED_AUTHORITY/UNKNOWN`, stale/future revisions, missing authority, invalid symbolic ID, accidental private selectors, symlink/traversal, duplicate child, cycle, wrong owner/tenant and expired lease. Add synthetic negative tests.
4. **BPA-02B.4 — reviewed manifest PR:** only after approved owner/integrator evidence, create root `project.yml` in new scoped branch, compare expected base HEAD and all manifests, test full exact-head CI, approve merge separately. `project_scaffold_apply` is future Fabric authority, never granted by this PR.

Each subchild needs its own bounded status/claim before execution; if work expands, create separate TASK+STATE folders instead of a giant multi-agent write lane. Physical release archive #587/#588 recovery is a different custody and restore contract, not evidence of Git primary restore.

## Test matrix / Failure Museum
- Positive: source/authority exact match, revision/fence valid, clean isolated restore and reversible no-write dry run.
- Negative: wrong host or storage role; missing/mismatched source primary; same-device replica misclassified independent; stale/expired lease; symlink/traversal; non-owner permissions; duplicate/wrong repository identity; concurrent claims; corrupted Git bundle or failed restore; private path in public manifest; unexpected source overwrite; uncontrolled GitHub/CI outage.
- Fail closed on missing evidence; identify first divergent edge and register one root-cause Failure Museum entry. No generic fallback tool.

## Exit gate and handover
BPA-02B can only be COMPLETE with independently approved private authority, isolated restore receipts and exact reviewed code/CI for promoted root `project.yml`. Until then STATE remains BLOCKED; project #630 stays OPEN. No automation, worker or backup mutation is authorized by this document.
