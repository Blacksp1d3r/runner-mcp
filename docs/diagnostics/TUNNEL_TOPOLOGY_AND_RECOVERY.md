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

## Operator evidence update — 2026-10-09 ~17:00 CEST

- `tunnel-client --version`: **0.0.16**, source build fingerprint `5f99daabd4aa4a77049e6d81d54a0d8c18335397`. This is tunnel-client's own upstream build fingerprint, **not** the Runner-MCP installed commit or tunnel profile schema version.
- `run --help` confirms supported `--profile`, `--profile-file`, `--profile-dir` and `--config` selectors, with precedence flags > environment > YAML > defaults. Supported MCP target and control-plane key references are documented in CLI; do not serialize their actual values in public git.
- `doctor --help` confirms offline/preflight command accepts `--profile`, `--profile-file`, `--json`, `--explain`. Doctor success alone cannot establish authenticated external round trip.
- `sudo -u gha-runner -H systemctl --user list-unit-files ...` returned `Failed to connect to bus: No medium found`; this means the service account's user bus is unavailable in this invocation, **not** proof that no user unit exists.
- The operator account has an executable, but `command -v tunnel-client` is empty under service account. **Do not** point a root-run service at an operator-home executable as a permanent deployment. First establish supported installation/package custody and service-account executable location, then choose a stable, access-controlled installation method.

**Next read-only checks:** inspect current supervisor/cron inventory without printing secret environment or configuration, then run the existing profile's doctor using a service-account-readable installed binary only after validating binary provenance and permissions. Record results privately with sanitized summaries. Avoid ad-hoc daemon startups, profile edits, copy/restore of secrets, and systemd unit enablement until the exact intended owner and authenticated health are verified.

## Supervisor inventory evidence — 2026-10-09 ~17:00 CEST

Operator read-only checks establish that root's crontab does not contain tunnel/MCP matching lines; the service account crontab contains **four** `RUNNER MCP AUTOSTART v1` once-per-minute `cron-run` entries: server, github-watcher, agent-bus-worker, completion-watcher. No tunnel-client entry appears in those returned matching lines. System-wide service inventory (`list-units --all` filtered for tunnel/mcp) returned no matching units. Service account user-systemd query failed due to unavailable bus, so presence of user units is still UNKNOWN. This is evidence of an absent tunnel supervisor in the inspected mechanisms, not proof of every possible startup method or the cause of the previous shutdown.

**Important:** do not replace existing cron-based MCP watchdogs with systemd during tunnel repair; preserve and monitor them separately. Before changing anything, examine the operator account's own cron/user services and alternative launchers (bounded names only), check service-account ability to run an independently installed tunnel-client, and classify missing auth/dependency dependencies without disclosing configs. Proposed tunnel systemd unit requires a dedicated stable executable, private profile/secret custody and rollback/boot acceptance; not yet approved or installed.
