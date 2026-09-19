# Threat model

## Assets

- source code and release integrity;
- staging environments;
- databases and backups;
- credentials and tokens;
- audit history;
- runner and host privileges.

## Threat scenarios

- stolen MCP credential;
- prompt injection attempting a dangerous tool call;
- path traversal or symlink escape;
- command or argument injection;
- malicious branch, commit, dependency, or wrapper script;
- cross-project access;
- secret leakage through logs or errors;
- backup exfiltration;
- privilege escalation;
- deploy race conditions;
- disk exhaustion from jobs, logs, or backups;
- denial of service from expensive operations;
- untrusted public pull-request code reaching a self-hosted runner.

## Primary mitigations

Use deny-by-default tool registration, explicit schemas, fixed command templates, project isolation, secret scrubbing, least privilege, timeouts, output limits, per-project locks, audit logging, dependency review, and security regression tests.

## Residual risk

Runner MCP remains a privileged operational component. Compromise of its host, private configuration, trusted wrapper scripts, or operator credentials can bypass application-level protections. Host hardening and credential management therefore remain separate required controls.
