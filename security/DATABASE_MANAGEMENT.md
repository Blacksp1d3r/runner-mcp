# Database backup and migration safety

Runner MCP currently supports PostgreSQL database backups and controlled migration commands.

Database restore is deliberately not implemented in this phase.

## Private credentials

A project database references only the name of a private runtime variable beginning with `RUNNER_MCP_DB_`.

The connection string itself:

- is stored only in the private 0600 runtime environment file;
- is entered through a hidden CLI prompt;
- is not stored in project YAML;
- is not placed in process command-line arguments;
- is not returned by MCP tools;
- is not written to audit metadata.

Re-running `runner-mcp setup --overwrite` preserves existing private database secrets. Token rotation remains separate and explicit.

## PostgreSQL backups

`backup_database` uses `pg_dump` in custom format.

The PostgreSQL connection string is supplied to the child process through its environment rather than `argv`.

Backup storage is private:

- root directory mode 0700;
- per-project backup directory mode 0700;
- dump files mode 0600;
- metadata files mode 0600.

MCP clients receive metadata only. They do not receive dump paths, dump bytes, hostnames or credentials.

A failed or timed-out backup removes its partial dump and does not create valid backup metadata.

## Migration status

`migration_status` runs a predefined read-only command profile.

The MCP client cannot supply an executable or shell string.

Output is bounded and scrubbed for:

- the configured database connection string;
- private project and executable paths;
- generic password/token/secret patterns.

Migration status remains available while the emergency stop is active because it is read-only.

## Applying migrations

`apply_migrations` is a mutating operation and therefore passes through the operator safety guard.

The order is fixed:

1. verify the operator safety state;
2. create a `pre_migration` database backup;
3. verify the operator safety state again;
4. run the predefined migration command;
5. report the result and recovery-point metadata.

If the emergency stop becomes active while the backup is being created, the migration does not start after the backup completes.

If a migration command fails, Runner MCP reports failure and keeps the pre-migration backup. It does not automatically restore the database.

## No automatic restore

Phase 5 does not expose database restore through MCP or CLI.

This is intentional. A database restore can discard newer data and requires a separate recovery plan and explicit human approval.

Future restore support must comply with `security/OPERATOR_SAFETY.md` and must never silently follow a code rollback or failed migration.

## Point-in-time recovery

The retention policy already has a PITR retention setting, but PostgreSQL WAL archiving and point-in-time recovery orchestration are not implemented yet.

Do not interpret the PITR retention setting as proof that PITR is active on a host. A future `doctor` check must verify the real PostgreSQL recovery configuration before Runner MCP can claim PITR availability.

## Migration profiles

The CLI supports:

- an Alembic preset when a project-local Alembic executable is available;
- a custom profile with separately configured status/apply executables and literal argument arrays.

All migration commands use `shell=False` and a restricted child environment.

Custom profiles remain trusted configuration. They must only point to trusted project tooling.
