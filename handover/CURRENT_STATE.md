# Current state

Date: 2026-09-19

## Status

Runner MCP Phase 0/1 is merged to main. Phase 2 safe project-file access is in progress on a separate branch.

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
- unauthenticated MCP requests verified to fail closed;
- project roots/repositories/services validated before use;
- DNS-rebinding protection bound to the private runtime MCP resource URL;
- authenticated MCP handshake and tool discovery verified end-to-end.

Phase 2 safe file access:
- `read_project_file` added with bounded line pagination;
- `list_project_files` added with bounded non-recursive listing;
- `file_metadata` added without exposing configured root paths;
- absolute paths, traversal, backslashes and symlinks rejected;
- secret paths such as environment files, keys and database artifacts blocked;
- binary/private-key content blocked;
- known literal secret values redacted;
- file-size, line-count and directory-entry limits enforced;
- MCP-level allowed/denied file reads and audit behavior tested end-to-end.

## Validation

Local trusted-runner validation is green:
- Ruff: green;
- pytest: 25 tests green;
- HTTP auth/rate-limit tests: green;
- authenticated MCP handshake/tool-discovery test: green;
- unexpected Host rejection test: green;
- traversal/symlink/secret/binary/size/pagination file tests: green;
- MCP file-read allow/deny integration test: green;
- git diff whitespace check: green;
- private-address/path scan: clean.

## Deliberately not implemented yet

- arbitrary shell;
- production actions;
- test execution tools;
- service control;
- database operations;
- deployment or rollback.

## Next steps

Review and merge the Phase 2 pull request, then begin Phase 3 controlled test execution with predefined project test profiles, timeouts, process cleanup and bounded output.

Repository license remains intentionally undecided pending owner choice.

Do not add real environment values to this repository.
