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
- append-oriented audit logging added.

## Validation

Local trusted-runner validation is green:
- Ruff: green;
- pytest: 5 tests green;
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

Finish Phase 1 request identification and basic rate limiting, strengthen HTTP auth tests, then review the bootstrap pull request.

Do not add real environment values to this repository.
