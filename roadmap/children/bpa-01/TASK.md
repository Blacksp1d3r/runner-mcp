# BPA-01 — Link shared standards and map legacy layout

Parent: [Runner-MCP #630](https://github.com/Blacksp1d3r/runner-mcp/issues/630). Profile: expanded / compatible legacy. This is an independently bounded **documentation-only** child.

## Goal and outputs
Add explicit pointers to the two Library standards in `AGENTS.md`, retain existing project safety overrides, create a public-safe repository compatibility map, and record this child in `TASK.md` and `STATE.md`.

## Out of scope / prohibited
No functional code, test policy bypass, generic shell/host/tool authority, service/tunnel restart, token/credential changes, GitHub artifact deletion, physical backup activity, mass file rename, Fabric-owned scaffold API or parallel #381/#590 implementation.

## Dependencies and acceptance gates
Library master v1.2 and blueprint v1.0 must be read; current GitHub main, `AGENTS.md`, roadmap, active PRs/claims and architecture must be reconciled. If a writer already owns any of the edited paths, do not edit. Require exact-head attribution plus normal Runner-MCP CI, diff review and approval before merge. Local Git/storage qualification is **not** required for this mapping, but remains BLOCKED for actual scaffold/apply.

## Inputs, outputs and topology
Inputs: public repository file/PR metadata, Library standards. Outputs: `AGENTS.md`, `docs/standards/REPOSITORY_BLUEPRINT_COMPATIBILITY.md`, these two child files. The future executor is owned by Runner Fabric, never by this documentation child.

## Work algorithm and recovery
1. Reconcile main, active workers and file ownership, branch from exact main.
2. Add pointers and classify existing paths as COMPATIBLE, PARTIAL, NEEDS_REVIEW or BLOCKED. Keep one canonical source for each concept.
3. Add only these TASK/STATE child records; do not migrate legacy children.
4. Inspect diff, require exact-head full CI and attribution. If CI fails, classify and change only this branch.
5. Merge only after review; update STATE and global handover with final proof. On interruption, use PR/head and this STATE to resume, not chat memory.

## Failure Museum and negative checks
Prevent false `ALREADY_COMPLIANT` when no project manifest/authority exists, prevent duplicate canonical truth and false auto-claim/auto-scaffold claims, prevent overriding active #381 or backup owners, and ensure no private paths or data appear in Git.

## Exit gate / handover
BPA-01 COMPLETE only when AGENTS pointer, compatibility mapping, no unrelated files and exact green CI are on main with review and documented final SHA. BPA-02 and BPA-03 remain separate.
