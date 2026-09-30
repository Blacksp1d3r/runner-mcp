# Clean Ubuntu installer proof boundary

This document defines the remaining reproducible proof for the clean installer after the runtime-integrity hardening merged through PR #161. It does not grant package-manager authority to Runner MCP.

## What CI already proves

Normal validation proves the installer fails closed when venv support is unavailable, rejects an unsupported pip floor, performs repeated fresh-process critical imports, performs repeated CLI smoke calls and does not activate the launcher after an integrity failure.

Those deterministic tests are not evidence that an arbitrary private host is healthy.

## Bounded installer execution

The source installer now treats package installation and post-install runtime
smoke checks as bounded operations.

- package installation has a 600-second default wall-clock limit;
- each runtime import/CLI smoke process has a 30-second default wall-clock limit;
- local operators may lower or raise those limits only within 1..3600 seconds;
- timeout exit 124 is reported explicitly as a timeout;
- exit 139 is reported explicitly as `SIGSEGV`, with guidance to stop reinstall
  loops and verify runtime/host integrity;
- a failed or timed-out install never creates the public `runner-mcp` launcher.

These bounds do not turn an unstable host into a healthy one. They make failure
finite and unambiguous enough for the operator to stop before activation.

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
