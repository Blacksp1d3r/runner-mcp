# Self-update dependency compatibility contract

This document records the implemented compatibility boundary for the current Runner MCP self-update path. The exact-contract preflight described below is active in v0.1.0 candidate code; broader dependency resolution remains deliberately out of scope.

The self-update installer intentionally builds and installs only the Runner MCP wheel. It uses `pip wheel --no-deps --no-build-isolation` and `pip install --no-index --no-deps --force-reinstall`. Mailbox/MCP callers cannot supply package-manager arguments, repositories, indexes, paths or dependency choices.

## Current package dependency sets

The current packaging metadata declares:

| Set | Current contract |
| --- | --- |
| Python | `>=3.12` |
| Build backend | `setuptools.build_meta` |
| Build requirements | `setuptools>=75` |
| Runtime | `setuptools>=75`, `mcp>=2.0,<3`, `pydantic>=2.10,<3`, `PyYAML>=6,<7`, `starlette>=0.48,<1`, `uvicorn>=0.35,<1` |
| Development/test | `httpx>=0.28,<1`, `pytest>=8,<9`, `ruff>=0.13,<1` |

`setuptools>=75` is intentionally both a build requirement and a runtime dependency today because offline self-update wheel staging disables build isolation and dependency resolution.

## What the current no-dependency path can safely assume

A self-update may change Runner MCP code while keeping the Python/build/runtime dependency contract unchanged. The existing lint/unit gates can then validate the target source before the fixed local wheel build and package mutation.

The current installer must not be treated as a dependency resolver. A successful wheel install proves only that the Runner MCP wheel was installed; it does not prove that a changed target dependency set was installed or that obsolete dependencies were removed. The fresh-process verification currently proves that `runner_mcp` and `runner_mcp.self_update` import, not that every optional or lazily imported runtime path is dependency-complete.

## Change classification

| Target change | Current self-update disposition | Reason |
| --- | --- | --- |
| Pure Runner MCP code; dependency and interpreter contract unchanged | Eligible | Existing environment contract is unchanged; normal source/test/install/recovery gates still apply. |
| Dependency constraint changes but the local environment may already satisfy it | Bootstrap/manual by default | The current path does not resolve or authoritatively prove the changed dependency contract. A future local preflight may safely relax this case. |
| New runtime dependency | Bootstrap/manual | `--no-deps --no-index` will not install it. |
| Higher minimum version for an existing runtime dependency | Bootstrap/manual | The installed version may be below the new floor and self-update will not upgrade it. |
| Runtime dependency removal | Bootstrap/manual | The old package is not removed by the Runner MCP wheel reinstall; environment cleanup/conflict semantics must remain explicit. |
| Python interpreter requirement change | Bootstrap/manual | Self-update must not replace or select an interpreter. A target that changes the interpreter contract requires the normal installation/bootstrap path. |
| Build backend or build requirement change | Bootstrap/manual | Wheel staging uses the existing environment with `--no-build-isolation` and no dependency acquisition. |
| Development/test dependency change required by the fixed lint/unit gates | Bootstrap/manual | Self-update does not install dev dependencies; a gate may otherwise depend on tooling that the current environment does not contain. |

“Bootstrap/manual” means use the normal dependency-resolving installation/upgrade path under local operator control, then re-establish and validate the self-update baseline. It does not mean allowing a mailbox request to pass pip arguments.

## Implemented fail-closed preflight

The current implementation uses a conservative exact compatibility contract rather than trying to infer that a changed requirement is probably compatible.

Before normal target validation/package mutation, trusted current-runtime code parses the target checkout's `pyproject.toml` with the standard-library TOML parser and canonicalizes:

- `requires-python`;
- build backend and build requirements;
- direct runtime dependencies;
- development/test dependencies needed by the fixed self-update validation gates.

That target contract is compared exactly with the trusted local compatibility baseline. A missing baseline fails closed as `bootstrap_required`; any contract difference fails closed as `dependency_contract_changed`. The comparison does not resolve dependencies, contact an index, inspect caller-supplied paths or accept package-manager arguments.

Exact equality is deliberately conservative. It can refuse an update whose changed requirement would happen to be satisfied locally, but it cannot silently authorize dependency acquisition. Such a refusal means the operator uses the normal local bootstrap/manual upgrade path and re-establishes the baseline afterward.

A future design may relax exact equality only if trusted local code can prove a changed constraint from installed-distribution metadata without network access or caller-controlled package-manager behavior. That future relaxation is not part of v0.1.0.

## Safe observability

Compatibility state should remain host-neutral.

The compatibility refusal itself is implemented. Additional bounded observability may use surfaces such as:

- `runtime_status`: a boolean indicating whether the installed compatibility record is present and valid;
- `runtime_doctor`: a bounded pass/fail compatibility-record integrity check;
- `self_update_status`: a fixed error category such as `dependency_contract_changed` when target preflight refuses an update;
- local CLI `status`/`doctor`: the same bounded ready/invalid state when useful to an operator.

Do not expose installed dependency versions, interpreter paths, virtual-environment paths, package-manager output, index configuration or host-specific environment details through MCP/mailbox status.

## Release/bootstrap consequence

The current private-host bootstrap must use the normal dependency-resolving installation path whenever the dependency/interpreter/build contract has changed since that host's installed baseline. Only after that baseline is installed and validated should the `--no-deps` self-update path be used for contract-preserving code updates.

This boundary also applies to future releases: changing a dependency in `pyproject.toml` is an upgrade-note event until a compatibility preflight capable of safely handling that class is implemented.
