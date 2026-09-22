# Contributing to Runner MCP

Contributions are welcome when they preserve Runner MCP's narrow, auditable and deny-by-default design.

## Before changing code

First check whether the use case can be handled through existing configuration or a built-in adapter. Core changes should be the last option, not the first.

Read README.md, QUICKSTART.md, docs/USING_AND_EXTENDING.md, security/SECURITY_BASELINE.md, security/THREAT_MODEL.md and AGENTS.md.

## Development checks

Use Python 3.12 or newer.

~~~bash
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install -e '.[dev]'
pytest
ruff check .
~~~

Before asking for release readiness, run the repository-local convenience check:

~~~bash
bash scripts/release-check.sh
~~~

It runs compile, Ruff, pytest, committed and local whitespace checks, the built-artifact smoke test and the clean demo in fail-fast order. It is a local convenience wrapper only; GitHub CI on the exact commit remains authoritative.

New behavior should include tests. Security-relevant changes should include a negative/fail-closed test as well as a success test.

## Design rules

Keep these properties intact:

- no general remote shell;
- no arbitrary client-supplied commands;
- no secrets in tool output;
- no private paths in normal MCP/CLI summaries;
- allow-listed project/service/test behavior;
- bounded execution and logs;
- emergency-stop support for mutating operations;
- explicit human approval for high-risk actions;
- staging-only mutations unless a future security design explicitly changes that boundary.

## Public repository privacy

Do not submit real infrastructure or deployment information. Use generic placeholders in code, tests and documentation.

## Adapters

Adapters are built-in and allow-listed. Configuration cannot dynamically import arbitrary modules.

A new adapter should expose safe capabilities and select from predefined presets. It should not become a hidden shell or execute arbitrary project-specific commands by itself.

## Pull requests

Keep changes focused. Explain the use case, why configuration alone was insufficient, the safety boundary, tests added, and any documentation or roadmap updates.

Avoid combining unrelated refactors with a security-sensitive behavior change.
