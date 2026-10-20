# BPA-02 — Symbolic repository manifest proposal, authority-gated

Parent: [Runner-MCP #630](https://github.com/Blacksp1d3r/runner-mcp/issues/630). Existing source layout preserved. Profile: expanded. Scope: **design, strict schema and synthetic tests only**, not creation of operational root `project.yml`.

## Goal and artifacts
Specify `docs/standards/project_manifest_candidate.yml`, a strict proposal-only schema, a matching explanatory safety/authority design and tests that reject guessed primary Git, private storage authority and automatic claims.

## Out of scope / forbidden mutations
No `project.yml` at root until independently qualified Git/storage/lease ownership; no runtime registration, project scaffold API, generic shell, privileged host path, Fabric task, agent lease, production deployment, service restart, credentials, mirror write/cleanup, storage copy, restore or provider artifact deletion. No edits to parallel #381 or Fabric owners.

## Dependencies, sources and topology
BPA-01 merged in #631; Library master v1.2 and blueprint v1.0 are canonical. Main GitHub tree and AIfordable/Fabric authority are distinct: the **actual local primary Git and storage authority are UNKNOWN** from these public sources. The draft's symbolic paths refer only to current repository files. No private physical locations may be committed. BPA-03 legacy child mapping is independently being worked and not a blocker for this proposal.

## Algorithm / acceptance
1. Reconcile exact main, active PR owners and existing absent root manifest.
2. Encode only symbolic fields, fail-closed proposal state and execution disabled by default.
3. Build a schema that rejects extra values/unsafe role claims and a read-only sample outside repository root.
4. Add offline unit tests for matching sample and adversarial false promotion / private fields.
5. Exact-head attribution, Ruff/pytest, release artifact and clean demo, then review and source-only merge if safe.
6. Keep full BPA-02 **operational promotion** blocked and parent #630 open; live authority and isolated restore need independent operator evidence and future approval.

## Failure Museum and recovery
False operational identity (a GitHub repo mistaken for approved local primary); unknown host or mount claimed qualified; stale review date; auto-claim granting execution; private file path leaked; duplicate/parallel writable Git authority. A code schema does not enforce OS privileges or certify restore. On CI failure preserve failed HEAD/error, fix only branch-scoped tests and rerun.

## Handoff
Use `STATE.md` and the draft manifest explanation to resume. A future separate authority-promoting child must verify real read-only registry evidence, fencing, restore proof and owner approval; do not mark `project.yml` completed here.
