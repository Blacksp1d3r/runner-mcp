# #665 — Serving-build and catalogue attestation

## Parent / owner / identity
- Parent: Runner-MCP #665; ADR: docs/architecture/ADR-2026-10-12-TOOL-IDENTITY-ALERTS.md
- Scope owner: Runner-MCP; where applicable Fabric #1471 explicitly owns fleet tenant inventory
- Status: UNCLAIMED; no exclusive code claim until checked against current Git/CI/worker queue

## Objective and bounded scope
Bind observed process build commit, installed artifact digest, actual tools/list schemas, policy generation and authenticated asset; separate reported from attested.

## Dependencies
registry; existing #649; #590 and AIfordable #428 for live qualification

## Inputs / outputs
- Input: reviewed ADR, latest reconciled main, prior child evidence and authenticated host policy where relevant.
- Output: versioned source changes and focused tests in separate reviewable PR, with safe public handoff; avoid writing private machine/customer details.

## Acceptance
Same SemVer different SHA detected; forged build/ref rejected; isolated actual tools/list matches exact schema digest; missing evidence UNKNOWN.
- Exact-head Ruff/pytest, artifact and negative test evidence; independent review before merge.
- A production-capable code change requires unique strictly increased package version via #661/#663, no unapproved deployment.

## Forbidden
No server restart, deployment, authentication bypass, host-wide shell, unsafe tool replay, customer data in public Git, fake success or cross-tenant notifications. No edits to another active owner's code scope.

## Recovery, errors and handoff
Fail closed on missing evidence. Reference central Failure Museum for real defects; document exact head, CI, PR, rollback expectations and next safe action in STATE.md.
