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
- explicit risk classes for operational tools;
- DNS-rebinding protection tied to the runtime MCP resource URL;
- external operator emergency stop;
- rollback retention based on both release count and age;
- database restore separated from code rollback and always approval-gated.

## Public repository rule

This repository must never contain real infrastructure details. Do not commit IP addresses, hostnames, internal domains, real service endpoints, real ports, usernames, absolute deployment paths, database endpoints, credentials, tokens, or other environment-specific values.
Public examples use placeholders only. Real values belong in private server-side configuration or secret stores.

## Initial scope

Implemented capabilities now include the secure MCP foundation, safe project-file access, operator-stop and rollback-retention policy, and controlled asynchronous test jobs.

Current test tools are `list_test_profiles`, `run_tests`, `test_status`, `get_test_log`, and `cancel_test`. Test commands come only from private predefined profiles; MCP clients cannot submit arbitrary shell commands.

Later phases add staging service management, backups, migrations, staging deploys, rollbacks, and project adapters.

## Development

Target runtime: Python 3.12+.

The implementation follows the official MCP Python SDK v2 line and Streamable HTTP transport. External deployment must terminate TLS before traffic reaches the MCP service.

Do not connect a privileged self-hosted runner to untrusted public pull-request code. See `security/SECURITY_BASELINE.md`.

Operator-stop, retention and rollback rules are documented in `security/OPERATOR_SAFETY.md`.

Controlled test execution and its trust boundary are documented in `security/TEST_EXECUTION.md`.

## Status

Bootstrap work is tracked in `handover/CURRENT_STATE.md`.
