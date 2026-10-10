# BPA-02 — Safe repository manifest proposal (not activated)

Tracking: [Runner-MCP #630](https://github.com/Blacksp1d3r/runner-mcp/issues/630). Source standards: Library `AI_REPOSITORY_BLUEPRINT_STANDARD.md` v1.0 and session master v1.2.

## Decision

The repository blueprint calls for symbolic `project.yml` at the root of a **qualified** project. Runner-MCP currently has a proven GitHub repository, but this chat has **not** qualified the actual canonical local Git authority, independent local archive custody, claim/lease authority or physical storage mappings. Therefore **do not create a root `project.yml` yet** or assert `source_of_truth.code: local_git` as a fact. Doing so could make Fabric's eventual generator believe it may write to the wrong host or create split-brain.

The only checked-in output is a **nonoperational example** `project_manifest_candidate.yml` and a strict JSON Schema for the proposal, plus offline synthetic tests. `proposal_state: BLOCKED_AUTHORITY` and `UNKNOWN` are deliberately incompatible with a promoted, executable blueprint manifest. The schema validates the *draft* state only. Treat this file as human-reviewed source documentation, **never** as a runtime configuration or a policy grant.

## Current symbolic mapping

- `project_id=runner-mcp`, profile `expanded`, owner domain `runtime-controls`. These are public proposal labels, not host IDs.
- `roadmap=roadmap/ROADMAP.md` and `child_root=roadmap/children/` preserve the existing, proven repository layout.
- New children use `TASK.md` and `STATE.md`; the legacy issue and component documents remain mapped rather than renamed.
- `source_of_truth.code/evidence/coordination=UNKNOWN`: no inference from the connected Runner-MCP plugin's runtime, an old user handover, GitHub visibility, or a remembered server mount.
- `mirrors.github=reference_only`: presence of this public repo does not establish it is a correctly fenced mirror of a locally qualified Git authority.
- `auto_claim=false`, `protected_mutations=human_approved` and synthetic-only metadata tests. These are design constraints, not OS permission enforcement.

## Promotion gate (future BPA-02 operator/authority substep)

1. Get read-only, owner-authorized authoritative registry evidence for the intended project repository, writable Git primary/remote and host mapping; verify freshness, owner, authorized namespace, and no competing write authority. Do not copy private paths/hostnames/UUIDs into public Git.
2. Independently prove local Git bundle/snapshot restoration on isolated approved storage and stable revision mapping; distinguish a GitHub mirror from primary and prove mirror fencing.
3. Qualify identity/lease policy in Fabric: executor may only consume approved symbolic IDs, never free local paths or a client-supplied claim.
4. Version and independently review a *new operational schema*, with explicit fail-closed rejection of all `UNKNOWN` and `BLOCKED_AUTHORITY` states, duplicate children, circular dependencies, symlinks, stale leases and private-data fields.
5. Only then propose root `project.yml` through a separate small reviewed PR with exact-head CI; require operator/integrator approval before any Fabric `project_scaffold_apply`.

## Security and failure cases

- A source-only merge is **not** local authority, a deployment, or restore proof.
- The candidate has no host names, real disk identifiers, user secrets, private paths, service endpoints or absolute target directories.
- No shell, mount, service, credentials, Fabric mutable APIs, GitHub artifact cleanup or backup copies are operated by this task.
- Reject synthetic examples with unrecognized fields, wrong roots, false `QUALIFIED` states, activated `auto_claim`, alternative child contracts or any untrusted code/evidence source. All tests are offline and never query a host.
- Failure Museum class: *documentation falsely implies operational execution authority*. Prevent by explicit proposal-only schema, negative tests, owner authorization and final restore proof.

BPA-02 may complete its design/test slice after exact-head green CI and review. **Operational manifest promotion remains BLOCKED_AUTHORITY** and is not included in this design change.
