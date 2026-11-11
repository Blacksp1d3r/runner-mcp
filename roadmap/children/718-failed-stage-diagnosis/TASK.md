# RMCP #718 — read-only failed-stage diagnosis

## Ownership and dependency
Runner-MCP #716 canonical RMCP-F-0030, operational Fabric #1562 (physical first-host bootstrap failed), dependent #1563 remains BLOCKED. Original local stage source merge was `a2d34dc80550ef744acf0ff927344b000a832dcc`; physical operator's first accepted `stage` returned `existing_installer_failed`. Follow Library master v1.5, blueprint v1.1, AGENTS.

## Goal / output
Add exact private-manifest and same-host bound `diagnose` to current rootless local bootstrap, for the original partly-created revision-named prefix. Output fixed allowlisted filesystem metadata only; no machine digest or private path. The diagnosis can run from a *different, clean, independently approved source checkout*, because it must not stage or authorize the original revision.

## Boundaries / authority
- No pip, venv, installer, startup, CLI, shell, dpkg or untrusted partial code execution; no filesystem writes, credential ingestion, repo or network mutation.
- Private manifest owner/0600 and host identity must match; root refused; stage must exist and be owned/0700; symlinked parent or nested stage directories denied.
- An existing marker or pip file cannot grant success or authorize service/relay/ACK; exact root cause remains undetermined until private operator package checks.
- No new remote agent, SSH/Desktop Commander host-control path, HDD format, website deployment, or repair/retry/cleanup of original partial stage.

## Algorithm
Validate current OS/user and private manifest; same-host machine digest; derive original stage root by schema-pinned commit; `lstat` root and fixed components only; reject symlink/non-dir at privileged nesting; fixed source commit and component kinds only, authorization flags false. All error messages are bounded fixed reason codes.

## Tests / exit
Synthetic partial venv with missing pip/CLI/marker, pip+marker spoof, wrong host, root, absent stage, symlinked stage/runtime and unsafe directory permissions. Verify never executing subprocess or writing files. Version metadata 0.1.30 synchronized and exact-head Ruff/pytest/build/demo, clean Ubuntu installer proof and attribution SUCCESS before guarded source merge. Source merge is **not** a Black physical fix.

## Failure Museum / handoff
RMCP-F-0030 and canonical detailed record #716, root cause UNKNOWN. Exact operator next step after source merge: independent local read-only distro venv/ensurepip/pip package inventory and privately approved generation-safe recovery. For source evidence see `STATE.md`.
