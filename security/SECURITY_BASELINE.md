# Security baseline

Runner MCP is an operations boundary, so security requirements are product requirements.

## Required properties

- deny by default;
- strong HTTP authentication;
- TLS for external traffic;
- service process must not run as root;
- project and service allow-lists;
- no arbitrary shell in normal tools;
- no secret values in output or audit logs;
- bounded input, output, runtime, and concurrency;
- append-oriented audit logging;
- explicit separation between read, operator, and future production capabilities.

## Public repository hygiene

The public repository contains code and placeholders only. Real infrastructure configuration remains private and server-side.

Do not commit network addresses, hostnames, internal domains, actual ports, usernames, absolute deployment paths, actual service identifiers, database endpoints, credentials, tokens, private keys, dumps, or backups.

## Self-hosted runner safety

A public repository must not automatically execute code from untrusted forks or public pull requests on a privileged persistent self-hosted runner. Any self-hosted CI for this project must use trusted/manual gates or a disposable isolated runner.

## Deployment boundary

The MCP process should bind only where required and sit behind a hardened TLS reverse proxy. Firewall exposure should be minimal. Private runtime configuration must not be returned by MCP tools.

## High-risk actions

Deploys, migrations, restores, rollbacks, privilege changes, and production actions require additional safeguards. Production support is explicitly excluded from the MVP.
