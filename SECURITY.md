# Security policy

Runner MCP is security-sensitive software. Please report potential vulnerabilities carefully and avoid publishing information that could expose a real installation.

## Supported versions

Until the first tagged public release, security fixes target the current `main` branch.

After versioned releases begin, this section will list the supported release lines explicitly.

## Reporting a vulnerability

Prefer GitHub's private vulnerability-reporting flow when the repository offers a **Report a vulnerability** option.

If no private reporting option is available, open a minimal public issue asking for a private security contact. Do not include exploit details, credentials, tokens, private keys, real hostnames, IP addresses, internal domains, database endpoints, private service names, customer data or absolute deployment paths in that public issue.

A useful initial report includes only non-sensitive information such as:

- the affected Runner MCP version or commit;
- the affected public component;
- a short impact category;
- whether the issue is reproducible against placeholder/demo configuration;
- whether you believe exploitation is currently public.

Do not test a suspected vulnerability against infrastructure you do not own or have explicit authorization to test.

## Security model boundaries

Runner MCP is designed to reduce routine authority, not to make arbitrary code execution harmless.

Important boundaries include:

- trusted project code can still execute with the permissions of the Runner MCP operating-system account when a predefined test profile runs;
- Runner MCP is not a sandbox for hostile public-fork code;
- production mutations are currently out of scope;
- a local read-only PostgreSQL restore preflight can validate one existing private backup, but database restore execution, PITR and production recovery are not implemented;
- private runtime configuration and credentials must remain outside the public repository;
- higher-risk staging actions use separate approval and operator-safety controls.

Before reporting expected behavior as a vulnerability, review:

- [security/SECURITY_BASELINE.md](security/SECURITY_BASELINE.md)
- [security/THREAT_MODEL.md](security/THREAT_MODEL.md)
- [security/OPERATOR_SAFETY.md](security/OPERATOR_SAFETY.md)
- [security/TEST_EXECUTION.md](security/TEST_EXECUTION.md)

A bypass of those documented boundaries is security-relevant even if the bypass does not immediately lead to full system compromise.

## Disclosure

Please allow reasonable time to investigate and prepare a fix before publishing exploit details. Security fixes should include a regression test whenever practical.

Runner MCP will not ask a reporter to place private installation data in the public repository.
