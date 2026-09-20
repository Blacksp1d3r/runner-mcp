## Summary

Describe the problem and the smallest change that solves it.

## Security boundary

Explain whether this changes authentication, project/path validation, subprocess execution, test profiles, service/database/deployment behavior, approval gates, mailbox protocol, result scrubbing or private configuration handling.

## Validation

- [ ] Python compile succeeds
- [ ] Ruff passes
- [ ] pytest passes
- [ ] whitespace check passes
- [ ] security-sensitive behavior has regression coverage where practical
- [ ] documentation matches the implemented behavior

## Public-repository hygiene

- [ ] No credentials, tokens or private keys
- [ ] No real IP addresses, hostnames, internal domains or private endpoints
- [ ] No real usernames or database endpoints
- [ ] No real absolute deployment paths, private service names, dumps or backups
- [ ] Examples use generic placeholders only

## Safety invariants

- [ ] This does not add arbitrary shell input from an MCP/mailbox client
- [ ] Mutating behavior remains deny-by-default
- [ ] Higher-risk staging actions retain required approval/operator-safety gates
- [ ] Production mutation is not enabled
- [ ] Failures do not expose raw private process output
