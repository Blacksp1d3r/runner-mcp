# Runner MCP 0.1.3 release notes

Status: published on 2026-10-02 from exact commit `0aa013c279128e22fbd53be32c35bced3ae26834`. Protected workflow run `36962568072` passed the full release check, published the package to PyPI with OIDC, published matching metadata to the official MCP Registry, and created GitHub pre-release tag `v0.1.3` at the same commit.

## What changed

Runner MCP 0.1.3 consolidates the post-0.1.2 hardening and control-plane work into one published alpha release.

### Safer autonomous execution

- Added explicit AI fault-containment regression coverage: AI/client text remains intent, while deterministic code owns authorization and capability boundaries.
- Added cross-process release-operation locking so separate Runner MCP processes cannot concurrently mutate the same deployment release root.
- Added bounded local one-release retention pruning without arbitrary historical-target or deletion authority.

### Migration and recovery

- Added durable internal migration jobs.
- Added explicit asynchronous migration start/status integration with a distinct approval operation.
- Preserved the existing synchronous migration path and deployment-triggered migration semantics.

### Runner Fabric integration

- Added the optional three-tool coarse Runner Fabric work-unit transport.
- Added bounded first-install Fabric bootstrap with fixed canonical source/runtime rules and additional recovery/runtime guards.
- Live Fabric work-unit activation is still not claimed ready: current Fabric service-level durable resume integration remains an upstream gate.

### Agent Bus

- Added private Agent Bus configuration.
- Added managed worker lifecycle and outbound relay foundations.
- Added one-shot worker qualification so the local control path can be tested without enabling continuous operation.
- GitHub mailbox remains available as a bounded fallback path; live primary cutover proof remains separate.

### Local diagnostics and host-integrity gating

- Added local-only bounded service-journal reading behind explicit per-service opt-in.
- Added a local host-runtime integrity model and fixed Linux diagnostic adapter.
- Added bounded hardware/runtime fault evidence categories without exposing raw journal records.
- Added fresh-process autostart runtime smoke checks.
- Autostart installation now fails closed unless emergency-stop, install-recovery, restart-pending, runtime-smoke and host-integrity conditions all clear.
- Added `runner-mcp autostart preflight` to run that same activation decision read-only before attempting installation.

### Installer and self-update hardening

- Added a clean Ubuntu install proof for the current installer path.
- Added bounded timeout/native-crash classification for installer/runtime probes.
- Added offline packaging capability preflight before self-update wheel-stage mutation.
- Hardened self-update baseline/bootstrap and installed distribution identity handling.

## Security-relevant behavior changes

- A caller cannot bypass the autostart host-integrity gate by selecting systemd or cron directly; both backend installers require an internal clear permit.
- Runtime/host diagnostic output remains local and category-only at the activation boundary.
- Autostart preflight performs no unit-file, systemctl or crontab mutation.
- Fabric, Agent Bus and mailbox additions do not add a generic shell, arbitrary executable/path selector or production mutation authority.
- Production mutation remains disabled.
- Database restore execution remains unimplemented.

## Upgrade notes

The Python, build-backend and runtime dependency contract is unchanged from 0.1.2:

- Python `>=3.12`;
- `setuptools.build_meta` / `setuptools>=75`;
- `mcp>=2.0,<3`;
- `pydantic>=2.10,<3`;
- `PyYAML>=6,<7`;
- `starlette>=0.48,<1`;
- `uvicorn>=0.35,<1`.

That means 0.1.3 does not introduce a package-metadata dependency migration. The existing self-update compatibility preflight remains authoritative: hosts with an invalid/missing compatibility baseline or pending recovery must use the documented local bootstrap/recovery path instead of forcing self-update.

Autostart behavior is intentionally stricter than 0.1.2. A host that previously allowed autostart may now be blocked until fresh runtime and local host-integrity checks pass. Use:

```bash
runner-mcp autostart preflight
```

before installation to obtain the bounded local readiness category without mutating startup state.

## Known limitations

- Runner MCP is still alpha.
- Public CI proves the package/repository candidate, not the health of any particular private host.
- Untrusted public-fork code is not sandboxed for execution on a privileged persistent runner.
- Production mutation remains disabled.
- Database restore/PITR execution remains outside the implemented runtime authority.
- Runner Fabric coarse bridge live activation remains gated on upstream durable service/resume integration and private end-to-end proof.
- Agent Bus primary cutover remains gated on live private restart/replay/no-duplicate proof.
- Automatic tunnel/TLS/DNS/firewall/reverse-proxy provisioning remains operator-managed.

## Release validation

For the published 0.1.3 release:
- version metadata must match in `pyproject.toml` and `server.json`;
- exact candidate-head attribution and full Runner MCP validation must be green;
- built wheel/sdist smoke and clean five-minute demo must be green;
- the public-repository hygiene review must find no private installation values;
- publication must use the exact green main commit and must not move an existing tag.

Publication completed in protected workflow run `36962568072`; the GitHub `v0.1.3` tag and release assets are pinned to the exact validated main commit and must not be moved.
