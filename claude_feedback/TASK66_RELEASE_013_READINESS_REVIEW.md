# Task 66 — Runner MCP 0.1.3 release-readiness review

Status: COMPLETE review. No tag or publication performed.

## Baseline

Canonical released baseline:
- version: `0.1.2`;
- exact release commit: `83175f439c60346f92b5759a90993c3b8f5352f8`;
- PyPI, official MCP Registry and GitHub pre-release were all completed for that exact version.

Current reviewed main:
- `5d2616b559825a46b196376b49f4ddb516fa369e`;
- 55 commits ahead of the 0.1.2 release commit;
- no divergence from the released baseline.

## Dependency compatibility

The current `pyproject.toml` dependency/interpreter/build contract is byte-for-byte unchanged in substance from 0.1.2:
- Python `>=3.12`;
- build backend `setuptools.build_meta`;
- build requirement/runtime `setuptools>=75`;
- `mcp>=2.0,<3`;
- `pydantic>=2.10,<3`;
- `PyYAML>=6,<7`;
- `starlette>=0.48,<1`;
- `uvicorn>=0.35,<1`;
- dev/test dependency bounds unchanged.

Therefore a 0.1.3 release does not require a dependency-contract bootstrap solely because of package metadata changes. Existing self-update compatibility and host-integrity gates remain authoritative.

## User-visible changes since 0.1.2

The 55-commit delta contains substantial release-worthy work:

1. AI fault containment and proportional deterministic security gates.
2. Optional coarse Runner Fabric work-unit transport and bounded first-install Fabric bootstrap.
3. Durable asynchronous migration-job substrate plus explicit start/status integration.
4. Cross-process deployment/rollback release locking and bounded local retention pruning.
5. Local-only bounded service-journal reading with explicit per-service opt-in.
6. Agent Bus private configuration, managed worker lifecycle, outbound relay core and one-shot qualification.
7. Self-update bootstrap, packaging-capability preflight, safer wheel-stage failure classification and runtime distribution identity fixes.
8. Clean-Ubuntu install proof and stronger installer/runtime integrity checks.
9. Host-runtime integrity model, fixed Linux journal adapter, bounded hardware-fault evidence and fixed autostart runtime smoke.
10. Shared fail-closed autostart activation gate plus read-only local `autostart preflight`.

## Release-document drift

Before 0.1.3 can be tagged:
- `pyproject.toml` and `server.json` still say `0.1.2`;
- `.github/workflows/publish.yml` still defaults to `0.1.2`;
- `CHANGELOG.md` still keeps 0.1.1/0.1.2 publication work under `Unreleased`;
- `docs/LAUNCH_READINESS.md` still lists canonical 0.1.2 publication/verification as future work although issue #101 records it complete;
- dedicated 0.1.3 release notes do not yet exist.

## Known boundaries that must remain explicit

A 0.1.3 package release must not be described as proof that any specific private host is healthy or ready for autonomous activation.

Open live/operator blockers remain separate:
- private-host recovery/qualification (#198 and #108);
- Runner Fabric live activation (#110), because Fabric's current `AgentWorkUnitService` still keeps active work-unit state in memory rather than consuming the durable journal;
- live Agent Bus cutover proof (#125/#130).

Those issues do not invalidate the public package code, but the release notes must preserve the distinction between green public CI and private-host readiness.

## Decision

A 0.1.3 release candidate is justified.

Queue a separate Task 67 to:
- bump version metadata consistently to 0.1.3;
- reconcile CHANGELOG and launch-readiness documentation;
- add explicit 0.1.3 release notes;
- keep the runtime dependency contract unchanged;
- run exact-head full validation, built artifact and clean demo;
- stop before tag/publication.

Actual PyPI/MCP Registry/GitHub publication remains a separate explicit release action after the exact candidate commit is green.
