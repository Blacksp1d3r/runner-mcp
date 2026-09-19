# Runner MCP

Runner MCP is a small, self-hosted Model Context Protocol service for controlled development and staging operations.

It is intentionally not a general remote shell. The service exposes a limited set of audited tools for project status, testing, staging services, database operations, deployments, logs, backups, and rollbacks.

## Security model

- deny by default;
- explicit project allow-lists;
- no arbitrary shell as a normal interface;
- no secrets in tool output;
- strict path validation;
- auditable actions;
- least-privilege runtime permissions;
- explicit risk classes for operational tools.

## Public repository rule

This repository must never contain real infrastructure details. Do not commit IP addresses, hostnames, internal domains, real service endpoints, real ports, usernames, absolute deployment paths, database endpoints, credentials, tokens, or other environment-specific values.
Public examples use placeholders only. Real values belong in private server-side configuration or secret stores.

## Initial scope

Phase 0 and Phase 1 establish the repository, security baseline, threat model, project registry, MCP server skeleton, authentication hook, health endpoint, audit logging, `list_projects`, and `project_status`.

Later phases add safe file access, controlled tests, service management, backups, migrations, staging deploys, rollbacks, and project adapters.

## Development

Target runtime: Python 3.12+.

The implementation follows the official MCP Python SDK v2 line and Streamable HTTP transport. External deployment must terminate TLS before traffic reaches the MCP service.

Do not connect a privileged self-hosted runner to untrusted public pull-request code. See `security/SECURITY_BASELINE.md`.

## Status

Bootstrap work is tracked in `handover/CURRENT_STATE.md`.
