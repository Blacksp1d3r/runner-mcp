# Current state

Date: 2026-09-20

## Status

Runner MCP Phase 0/1 and Phase 2 are merged to main. Phase 2.5, Phase 3 and Phase 3.5 are on the open review branch. Phase 4 and Phase 5 are complete on stacked follow-up branches.

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

Phase 2.5 operator safety:
- external operator-stop file policy added;
- future operator actions fail closed until stop mechanism is configured;
- future operator actions remain read-only until retention values are explicitly confirmed;
- `safety_status` exposes safety state without returning private paths;
- code-release cleanup requires both count and age thresholds;
- default proposal is 20 releases and 90 days;
- PITR and pre-migration backup retention are separate controls;
- one approved code rollback may move back exactly one release;
- database restore always requires explicit approval;
- automatic production database restore is prohibited;
- operator-safety rules documented for later test/deploy/migration phases.

Phase 3 controlled test execution:
- private predefined test-profile schema added;
- MCP clients select only project and profile name, never a command string;
- executables must be absolute and are launched with `shell=False`;
- unsafe working-directory traversal and process-control environment variables are blocked;
- asynchronous jobs expose safe status, cancellation and paged scrubbed logs;
- per-project and global concurrency are bounded;
- test timeout and log-size limits are enforced;
- external operator stop terminates running test process groups;
- unfinished jobs are marked interrupted after Runner MCP restart;
- job metadata/logs use restrictive permissions;
- environment secrets, project paths and absolute command paths are scrubbed from logs;
- MCP lifecycle from `run_tests` through `test_status` and `get_test_log` is tested end-to-end;
- test-code trust boundary is documented; untrusted public-fork code remains excluded until stronger isolation exists.

Phase 3.5 onboarding:
- installable `runner-mcp` console command added;
- non-root `install.sh` added;
- interactive setup supports safe local mode and explicit public mode;
- generated private config uses restrictive filesystem permissions;
- inherited shell variables do not override setup-managed private runtime config;
- setup overwrite preserves the existing bearer credential unless `--rotate-token` is explicit;
- `status`, `doctor`, `emergency-stop` and `serve` commands added;
- project add/list/remove commands added without manual YAML editing;
- test-profile add/list/remove commands added;
- pytest and Ruff presets auto-detect project virtual environments;
- custom executable and project paths reject symlink components;
- project config updates are lock-protected and atomic;
- user-first README and QUICKSTART added.

Phase 4 staging service management:
- private service aliases map to systemd-user units;
- service aliases default to read-only;
- start, stop and restart permissions are independently opt-in;
- MCP list/status output never exposes private unit names or health URLs;
- optional HTTP health checks return only safe health state;
- operator emergency stop blocks mutating service actions while status stays available;
- systemctl invocation uses fixed argument arrays with `shell=False`;
- raw systemctl failure output is not returned to MCP;
- no sudo or generic system-service control;
- CLI service-config add/list/remove avoids manual YAML editing;
- MCP list/status/restart/emergency-stop flow is integration tested.

Phase 5 PostgreSQL backup and migrations:
- private DB connection strings use dedicated `RUNNER_MCP_DB_*` variables;
- CLI database connection input is hidden and never echoed;
- setup overwrite preserves existing DB secrets;
- backup root/project directories and dump/metadata files have restrictive permissions;
- pg_dump receives the DSN via child environment and not command-line arguments;
- MCP exposes backup metadata only, never dump contents or private paths;
- migration status/apply use predefined argv arrays and `shell=False`;
- migration output is bounded and scrubbed for DSN/private paths/secrets;
- apply always creates a pre-migration backup and rechecks operator stop afterwards;
- migration failure keeps the backup and never performs automatic restore;
- database restore, PITR/WAL orchestration and retention pruning remain intentionally unimplemented.

## Validation

Local trusted-runner validation is green:
- Ruff: green;
- pytest: 135 tests green;
- HTTP auth/rate-limit tests: green;
- authenticated MCP handshake/tool-discovery test: green;
- unexpected Host rejection test: green;
- traversal/symlink/secret/binary/size/pagination file tests: green;
- MCP file-read allow/deny integration test: green;
- operator-stop/retention/rollback guard tests: green;
- startup fail-closed retention-confirmation tests: green;
- MCP safety-status integration test: green;
- controlled test-runner timeout/cancel/stop/concurrency/log-redaction tests: green;
- MCP test-job lifecycle integration test: green;
- test-profile schema and startup fail-closed tests: green;
- dependency check: green;
- non-root installer integration test: green;
- installed console command version/help smoke test: green;
- onboarding/project/test-profile CLI tests: green;
- service manager permission/emergency-stop/subprocess tests: green;
- MCP service alias/status/restart integration test: green;
- service-config CLI/config-manager tests: green;
- PostgreSQL backup/metadata/permissions/secret-isolation tests: green;
- migration timeout/failure/pre-backup/redaction tests: green;
- MCP database backup/migration/emergency-stop lifecycle test: green;
- database-config and hidden-prompt CLI tests: green;
- git diff whitespace check: green;
- private-address/path scan: clean.

## Deliberately not implemented yet

- arbitrary shell;
- production actions;
- database restore;
- PostgreSQL WAL/PITR orchestration;
- automated backup-retention pruning;
- deployment or rollback.

## Next steps

Merge the Phase 2.5/Phase 3/Phase 3.5 review branch, then rebase/open the Phase 4 and Phase 5 follow-up branches in order. Next development phase is Phase 6 staging deployment. Before activating real project test/service/database profiles, create the private runtime configuration and verify the Linux-account and PostgreSQL recovery boundaries on the actual host.

Repository license remains intentionally undecided pending owner choice.

Do not add real environment values to this repository.
