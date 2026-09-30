# Clean Ubuntu installer proof boundary

This document defines the remaining reproducible proof for the clean installer after the runtime-integrity hardening merged through PR #161. It does not grant package-manager authority to Runner MCP.

## What CI already proves

Normal validation proves the installer fails closed when venv support is unavailable, rejects an unsupported pip floor, performs repeated fresh-process critical imports, performs repeated CLI smoke calls and does not activate the launcher after an integrity failure.

Those deterministic tests are not evidence that an arbitrary private host is healthy.

## Separate clean-image proof

A clean-image validation may use an ephemeral Ubuntu 24.04 CI/container environment to prove the documented operator bootstrap sequence when `python3-venv` is initially absent.

The proof must be outside Runner MCP runtime authority:

1. establish that the image initially cannot create the required venv;
2. install the distribution's venv prerequisite through CI/bootstrap setup, not through Runner MCP or MCP/Agent Bus;
3. invoke the normal `install.sh` with no private host values;
4. require the installer import/CLI stress gates to pass;
5. invoke `runner-mcp --help` from the installed launcher;
6. discard the environment.

## Security boundary

The validation workflow may contain a fixed package-bootstrap command because the CI image is disposable and the workflow itself is repository-reviewed. No package name, repository, command, path or privilege operation becomes caller-selectable at runtime.

The product installer must continue to fail with guidance when venv support is absent; it must not silently call apt, sudo or another package manager.

## Private-host proof remains distinct

Even a green clean-image proof does not clear the live host incident that showed intermittent process corruption. Private-host recovery/diagnosis remains a local operator task under #108/#155 and must not be marked healthy from CI evidence.

## Acceptance

- disposable Ubuntu 24.04 environment;
- explicit initial missing-venv assertion;
- fixed bootstrap of only the OS venv prerequisite;
- normal installer succeeds afterwards;
- launcher exists only after runtime stress succeeds;
- no credentials/private infrastructure;
- no new MCP/mailbox/Agent-Bus/package-manager action;
- clean-image result and private-host integrity status remain separately reported.
