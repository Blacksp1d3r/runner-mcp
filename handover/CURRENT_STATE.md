# Current state

Date: 2026-09-19

## Status

Runner MCP repository bootstrap is active.

Phase 0:
- repository structure defined;
- public infrastructure-data ban documented;
- security baseline drafted;
- threat model drafted;
- example project configuration added;
- public example safety tests added;
- manual privacy scan clean.

Phase 1 foundation:
- MCP server skeleton added;
- bearer-token verification hook added;
- health endpoint added;
- project registry added;
- `list_projects` added;
- `project_status` added;
- append-oriented audit logging added;
- per-request IDs added;
- bounded in-memory rate limiting added;
- health endpoint exempted from operator rate limiting;
- unauthenticated MCP requests verified to fail closed.

## Validation

Local trusted-runner validation is green:
- Ruff: green;
- pytest: 7 tests green;
- HTTP auth/rate-limit tests: green;
- git diff whitespace check: green;
- private-address/path scan: clean.

## Deliberately not implemented yet

- arbitrary shell;
- production actions;
- file access;
- test execution tools;
- service control;
- database operations;
- deployment or rollback.

## Next steps

Review the bootstrap pull request, add any remaining Phase 1 configuration validation, then begin Phase 2 safe project-file access behind explicit path and secret-deny policies.

Do not add real environment values to this repository.
