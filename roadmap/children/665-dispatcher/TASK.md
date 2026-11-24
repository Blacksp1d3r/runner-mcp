# #665 — Admission and zero-side-effect denials

## Parent / owner / identity
- Parent: Runner-MCP #665; ADR: docs/architecture/ADR-2026-10-12-TOOL-IDENTITY-ALERTS.md
- Scope owner: Runner-MCP; where applicable Fabric #1471 explicitly owns fleet tenant inventory
- Status: UNCLAIMED; no exclusive code claim until checked against current Git/CI/worker queue

## Objective and bounded scope
Before execution match registered tool ID/name/revision/schema and authenticated tenant/host policy; detect disabled vs absent.

## Dependencies
registry; handshake; #642 host-policy authority

## Inputs / outputs
- Input: reviewed ADR, latest reconciled main, prior child evidence and authenticated host policy where relevant.
- Output: versioned source changes and focused tests in separate reviewable PR, with safe public handoff; avoid writing private machine/customer details.

## Acceptance
Unknown ID, swapped name, duplicate, denied policy and stale generation prove zero handler calls; no retry of unknown-effect writes.
- Exact-head Ruff/pytest, artifact and negative test evidence; independent review before merge.
- A production-capable code change requires unique strictly increased package version via #661/#663, no unapproved deployment.

## Forbidden
No server restart, deployment, authentication bypass, host-wide shell, unsafe tool replay, customer data in public Git, fake success or cross-tenant notifications. No edits to another active owner's code scope.

## Recovery, errors and handoff
Fail closed on missing evidence. Reference central Failure Museum for real defects; document exact head, CI, PR, rollback expectations and next safe action in STATE.md.
