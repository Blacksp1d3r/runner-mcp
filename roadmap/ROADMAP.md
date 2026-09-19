# Runner MCP roadmap

This public roadmap is intentionally infrastructure-neutral. Real deployment details belong only in private configuration.

## Phase 0 — repository and design

Establish repository structure, security baseline, threat model, configuration model, handover notes, dependency policy, and public-repository hygiene controls.

## Phase 1 — minimal MCP server

Implement Streamable HTTP, authentication, health endpoint, project registry, structured audit logging, request identification, basic rate limiting, `list_projects`, and `project_status`.

## Phase 2 — safe file access

Add allow-listed project file reads, metadata, pagination, path traversal protection, symlink escape protection, secret deny-lists, and file-size limits.

## Phase 3 — controlled test runner

Add predefined test profiles, bounded execution, timeouts, process cleanup, server-side logs, and concise result summaries.

## Phase 4 — staging service management

Add allow-listed service status, start, stop, restart, and health checks. No arbitrary service names.

## Phase 5 — backups and migrations

Add controlled database backups, backup metadata, migration status, migration execution, retention policy, and fail-closed behavior.

## Phase 6 — staging release engine

Add immutable releases, preflight checks, required tests, backups where needed, migration orchestration, activation, health checks, metadata, and automatic code rollback on failed activation.

## Phase 7 — rollback engine

Add release listing and controlled rollback. Database restoration remains a separately protected operation.

## Phase 8 — multi-project adapters

Move project-specific behavior behind a common adapter interface. New projects should normally require configuration/adapters rather than core changes.

## Phase 9 — approval and risk gates

Add two-step plans, short-lived approvals, environment-specific permissions, and stronger safeguards before any production capability is considered.

## Phase 10 — optional restricted command templates

Only if concrete use cases remain unmet, add tightly allow-listed executable templates under a sandboxed account. No free-form root shell.

## MVP completion

The MVP is complete when one pilot project can be inspected, tested, backed up, migrated, deployed to staging, health-checked, and rolled back without a general remote-shell dependency, while all actions remain auditable and secrets stay inaccessible.
