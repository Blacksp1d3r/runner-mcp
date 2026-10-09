# Tunnel connectivity topology and recovery ledger

Status: **observed partial outage; no runtime repair performed**. Owner: Runner-MCP #590 / component 11. Last evidence: 2026-10-09 16:59 CEST, operator-provided host probes. This document records a *single logical ChatGPT-to-Runner-MCP control route*, not a mandate to multiplex customer production traffic or to replace Fabric's separate controlled execution connections.

## Observed dependency topology

```text
ChatGPT connector (calls currently fail generically)
  -> OpenAI tunnel control plane (live routing/auth not verified)
  -> tunnel-client daemon (NOT observed running on github-runner)
  -> local Runner-MCP MCP endpoint (serve process observed, bound to loopback)
  -> bounded MCP tools / local watchers / Agent Bus (process presence != end-to-end health)
  -> GitHub or strictly admitted project work units
```

Runner Fabric is a separate trust/policy and execution orchestration component, NOT proof of tunnel readiness, and must not be used to repair the current connection without its own qualification. Safety production data and CI runner identities must remain isolated from tunnel repair.

## Evidence ledger (privacy-preserving)

- 2026-10-09 ~16:59 CEST: host reported as github-runner. Process list: local Runner-MCP MCP server, GitHub watcher, completion watcher, Agent Bus worker parent, and Actions runner supervisor/listener. No process matching tunnel-client. Local server actual HTTP health *not yet checked*.
- The operator's account resolves tunnel-client binary; its help output identifies an outbound long-lived daemon plus `doctor`, `health`, `profiles`, `run`, and `runtimes`. Installed binary version and binary reproducibility/hash **not yet verified**.
- Service inventories shown for system-wide and operator's user services contain no matching tunnel service. **This does not exhaust gha-runner's own user units, cron, or other supervisors.**
- A tunnel YAML profile exists readable only by the gha-runner service account, last modified Oct 7. Earlier backups exist. Never publish their contents, sensitive env names/values, internal endpoints or profile diff to GitHub.
- 2026-10-09: ChatGPT read-only runtime_status and project_status failed with generic internal errors, consistent with but not proof of the missing tunnel.
- Previous #590 and diagnostics/CONNECTOR_READONLY_TRIAGE.md remain the owner for the earliest failing edge; no claim of connector recovery.

## Desired state and drift evidence

| Component | Desired | Current evidence | Proof still required |
|---|---|---|---|
| MCP server | one bounded loopback listener and automatic restart | process observed | local authorized readiness, system supervisor |
| tunnel-client | one controlled daemon, no duplicate tunnel identity | not in process listing | binary version, valid profile doctor, owner/supervisor |
| daemon startup | systemd or existing canonical supervisor, restart on failure and boot | no matching system unit from provided inventory | full inventory including service-account user units; reboot acceptance |
| ChatGPT connector | authenticated end-to-end, bounded reads succeed | internal errors | fresh read-only list_projects, runtime_status, doctor |
| Fabric | distinct protected execution trust boundary | no operational claim | separate Fabric readiness |

## Recovery checklist — read-only first

1. Identify *which* user and supervisor should own the existing tunnel. Inspect only service-account user units, existing cron and startup records; do not create duplicate autostarts.
2. Record `tunnel-client --version`, executable provenance, package/update method and the nonsecret output of `tunnel-client run --help`, `doctor --help`, `health --help`. Do not copy executable into a second account or change YAML ownership as a shortcut.
3. Use only vendor-supported doctor/health against the existing profile, redact credentials and sensitive URLs from any output before sharing.
4. After identifying exact first failing edge, propose one supervisor unit (prefer system-managed unit with dedicated identity, restrictive permissions, dependencies and bounded restart policy). Require operator review of service identity, command and config profile before enabling; no blind `run` or unit creation.
5. Verify local health, tunnel health, and client-tool round-trip independently. Prove boot recovery, exactly one process and no security regression; test after a maintenance window only.
6. Record versions, installed commit, binary SHA256 (private host record), profile schema version, deployment/update mechanism, UTC timestamps, test evidence, rollback/restore procedure and owner after every update.

## Secure operation and rollback

Never commit real YAML, tokens, profile backups, full env, internal hostnames, private paths or endpoint maps. Preserve existing profile and launcher until verified replacement passes acceptance. Failed startup must not spawn repeated duplicate tunnel identities. Rollback consists of stopping only the **new** unit if authorized and restoring the previously validated service state; never reset Runner Fabric or GitHub Actions runners as part of tunnel remediation.

## Next bounded operator commands

```bash
sudo -u gha-runner -H systemctl --user list-unit-files --type=service --no-pager
sudo -u gha-runner -H crontab -l
/home/gerard/.local/bin/tunnel-client --version
/home/gerard/.local/bin/tunnel-client run --help
/home/gerard/.local/bin/tunnel-client doctor --help
```
The first command can fail when the service user's D-Bus user manager is unavailable; record the error instead of improvising `XDG_RUNTIME_DIR`. Do not publish cron environment lines containing secrets. The executable path above is *observational host-specific* and intentionally does not define a canonical production installer.

## Change history

- 2026-10-09: initial evidence/topology/recovery ledger proposed. No production changes, daemon start, service creation, token or profile modification.
