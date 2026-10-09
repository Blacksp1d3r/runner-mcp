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

## Additional operator inventory — 2026-10-09

- Operator's own crontab filtered for tunnel/mcp: no matches.
- System-wide active/inactive service listing filtered for tunnel/mcp: no matches.
- Service-account and system-wide candidate executable paths reported absent; executable only previously observed under operator account.
- `loginctl show-user` reported UID not logged in or lingering: user-systemd not available for account at inspection time. A system-managed service does not require enabling linger.
- This strengthens the absent-observed-autostart hypothesis, but does not prove tunnel profile validity, credential availability, server health or external connection. Next classify service-account-readable installed binary and secret reference mechanisms without copying configuration into public sources. Do not execute an unvalidated daemon.

## Operator local health and execution evidence — 2026-10-09 ~17:00 CEST

- Authenticated operator local GET `/healthz` at loopback Runner-MCP endpoint returned **HTTP 200**. This proves only that endpoint responded; it does not prove MCP tool execution or external tunnel connectivity.
- Attempting the operator-home tunnel-client binary as the service account returned **Permission denied**; profile doctor similarly could not execute. This is an executable/path traversal permission barrier (exact component not yet isolated), not doctor failure or proof the YAML is invalid.
- Do not chmod operator home, change directory traversal permissions, run privileged tunnel daemon, or copy a possibly out-of-custody executable directly into privileged executable directories without provenance checks.
- Next diagnose path traversal with `namei -l` on the executable (review privately), and determine the binary installation and SHA256 via controlled package provenance. Plan a dedicated, root-owned, service-account-executable stable location and exact systemd unit only after private auth/profile preflight and ownership review.

## Corrected root-cause history and permissions — 2026-10-09

Earlier interpretation must be corrected: prior conversation evidence reports that on **2026-10-07** the ChatGPT connector worked again after repair; the work was subsequently deprioritized in favor of Bewind. Prior repair included restoring tunnel-client v0.0.16/profile after a reboot and correcting a locally empty MCP Authorization Bearer token that yielded HTTP 401. This **historical** cause does not prove it recurred today. Do not repeat credential replacement or previously failed lab-to-host transfer attempts without fresh private evidence.

Current `namei -l` evidence identifies the immediate service-account execution permission error: the operator home directory lacks 'other' traversal permission, despite the binary itself having execute bits. Do **not** chmod/chgrp the operator home as a workaround. The SHA256 of the observed operator-owned v0.0.16 executable is `01260ee973d5510861bc32979739561edd33869f99f9f8cd324f6d0da5b2e692`. This is a public non-secret reproducibility checksum of the already observed binary, not an approved distribution source or trusted signature. Before installing a system service, validate the package's provenance privately and ensure a dedicated service-account-readable stable executable, secure profile permissions, and auth-header reference only (never token values).

Disambiguate two distinct incidents: (1) Oct 7 previously resolved missing-profile/empty Bearer token, (2) Oct 9 no active tunnel/no supervisor located and the operator-home executable inaccessible to service account. A successful Oct 7 connector round trip is not evidence of live Oct 9 health. No actual daemon startup, package copy, permissions edit or secret change has been performed in this docs-only PR.

## Service-owned executable installation — operator evidence 2026-10-09

- Operator created a service-account-owned private executable directory and copied the existing tunnel-client 0.0.16 executable with file mode 0750; invoking `--version` as service account succeeded and returned upstream build `5f99daabd4aa4a77049e6d81d54a0d8c18335397`.
- Attempted SHA256 of the private copy as operator failed with `Permission denied` (expected for mode 0750 when operator is not owner or group member). This does **not** establish a checksum mismatch. Run `sudo -u gha-runner sha256sum` and compare to known source SHA256 `01260ee973d5510861bc32979739561edd33869f99f9f8cd324f6d0da5b2e692`.
- Executable provenance is not yet vendor-verified, profile doctor not yet run, and no daemon/service started. Copying as observed is a temporary controlled deployment step, not approved automatic update custody.

## Profile doctor / exact credential dependency — 2026-10-09

Operator verified service-owned binary SHA256 equals the original `01260ee973d5510861bc32979739561edd33869f99f9f8cd324f6d0da5b2e692`. `tunnel-client doctor --profile runner-mcp` executed as service account: config_source PASS, profile_load PASS, **control_plane_api_key FAIL**, because referenced environment variable `CONTROL_PLANE_API_KEY` is unset in the noninteractive invocation; exit code 2. This is concrete evidence that the tested process environment cannot satisfy startup. It does not prove the key is missing from every secure store or expired, or that auth is the only remaining issue. Historical Oct 7 MCP Bearer-header failure is a separate dependency; do not conflate control-plane API key and MCP authorization token. No daemon was started.

Next: inspect only whether a canonical root/service-account protected systemd EnvironmentFile or secret-manager reference exists, WITHOUT cat/grep printing token values, and resolve boot-time credential injection from existing managed secret source. Require restricted permissions, rotation/expiry and owner register; no tokens in unit files, public GitHub, or shell command lines. After private approved secret injection, rerun doctor and then bounded live health, never claim readiness from profile load alone.

## Secret source discovery — 2026-10-09 operator evidence

- The Runner-MCP environment file exists, and a separate `tunnel.env` was discovered in the private service-account configuration. The previous command searching `CONTROL_PLANE_API_KEY` used a filename glob under the Runner-MCP directory and was not an exhaustive inspection of the newly discovered file contents. The file's existence **does not prove** it contains the needed key or that any key is valid.
- Do not publish the file path, content, token, or environment dump. Next verify privately only key-name presence, file owner/mode, and whether systemd can read it under the selected service identity; avoid `cat`, `source` or printing secrets. Don't copy credentials into a public unit or repository. The service design should use protected EnvironmentFile/credential storage and not depend on interactive shell exports.

## Credential presence and custody — 2026-10-09

Operator confirmed presence (name only) of `CONTROL_PLANE_API_KEY` in existing protected tunnel environment file. Metadata: owner and group are the service account, mode `0600`. This supports use of the existing secret source rather than issuing a new key. It does **not** validate that the value is nonempty, unexpired, or valid for tunnel identity, and does not prove complete MCP Bearer credential injection. Prior doctor ran without this environment file loaded and failed only `control_plane_api_key`. Next test doctor using a private, non-printing environment loader under the service identity, check exit code and sanitized check names; then design systemd `EnvironmentFile` against same protected source. Do not record secret values.

## Successful doctor with protected environment — 2026-10-09

Operator invoked v0.0.16 `doctor --profile runner-mcp` under service account after loading existing protected tunnel environment in a temporary shell. Result **ok**: profile and tunnel identity PASS, control-plane API-key reference PASS, local MCP target PASS (HTTP 401 challenge counts as reachable, not authenticated access), protected-resource OAuth metadata PASS (HTTP 200), health interface binding configured. Codex plugin SKIP. No long-lived daemon was started and no actual ChatGPT end-to-end connection proven. This does not certify the control-plane key against the remote service, nor the MCP bearer token for application calls.

Next: identify whether the env file is compatible with systemd EnvironmentFile syntax (without printing its content); then prepare a reviewed systemd system unit using dedicated service account, explicit executable/profile/EnvironmentFile, restricted umask, restart policy and system startup dependency. Before enabling confirm no competing tunnel instance, run controlled start, inspect sanitized journal/health, perform connector round-trip and later reboot test. No plaintext secrets in repository or unit.

## Last operator preflight — 2026-10-09

`pgrep -af '[t]unnel-client run'` returned no matching running daemon. A bounded awk syntax scan of the existing protected environment file returned all nonblank/noncomment lines matching KEY=VALUE shape; this is only a basic lexical check, not a full systemd EnvironmentFile parse and says nothing about authentication validity. Combined with successful doctor, this permits preparing a *disabled* system service for review and verify, with no claim of operational connectivity yet.

Proposed service properties: system-level service `User=` and `Group=` service account, protected `EnvironmentFile=` reference, `ExecStart=` service-account executable with explicit profile name, `After=network-online.target` / `Wants=network-online.target`, `Restart=on-failure`, `RestartSec=10s`, `UMask=0077`, no dynamic secret injection in `ExecStart`. Unit must be reviewed with `systemd-analyze verify` before controlled activation. Keep existing four cron watchdogs unchanged. After live start, require authenticated tunnel readiness and bounded ChatGPT MCP read-only round-trip before reporting fixed. No reboot until explicit maintenance coordination with running CI jobs.

## Staged systemd unit verified — operator evidence 2026-10-09

Operator created the proposed dedicated system-level tunnel unit referencing the private protected env file and existing service-owned v0.0.16 executable. `systemd-analyze verify` completed without diagnostics, `daemon-reload` completed, and `is-enabled` returned **disabled**, as designed for preflight. No process activation or authenticated tunnel health proven yet. Next perform coordinated single start, inspect sanitized service status, local readiness and ChatGPT read-only round-trip before enabling persistence; do not reboot an active CI host merely to test without scheduling.

## Live restoration and read-only client verification — 2026-10-09 17:32 CEST

Operator started the dedicated system-level tunnel service; `systemctl is-active` = **active**, log reported MCP session initialized and tunnel-client started, and `systemctl enable` established a multi-user boot dependency. This proves enabled configuration, **not reboot recovery**. Service logs additionally show an auth-server discovery 404 warning and HTTPS-only Harpoon auto-registration warnings for optional loopback targets. Do not blindly enable plaintext HTTP or relax auth to silence warnings; separate mandatory MCP control path from optional discovery paths. Tunnel metadata description still references a lab topology: reconcile private intended target/current machine mapping before changing any route.

A subsequent ChatGPT connector read-only check **succeeded for runtime_status**, returning version 0.1.3, mode operational, emergency_stop false, six projects and no pending restart. In the same test, **list_projects failed internally** with no structured application response. Therefore external connector is partially restored, not fully qualified. The first failing edge for list_projects remains unknown. No customer, deployment, Fabric or CI state was modified by this check.

Next: repeat neither failing call in a loop nor any write action; check bounded `runtime_doctor` once, isolate list_projects session/catalogue/transport vs endpoint, and verify journal/health without leaking tunnel IDs or tokens. Ensure reboots tested during CI maintenance only; check `is-enabled` and restart policy. Track exact checks as SUCCESS/FAILED independently and retain rollout rollback plan.

## Persistence verified / mixed endpoint results — 2026-10-09

Operator confirmed `systemctl is-enabled` = `enabled`, `is-active` = `active`. Boot-start configuration is now verified; a true post-reboot recovery test is still pending. Post-activation ChatGPT read-only checks: `worker_status` SUCCESS (concurrency_limit 2, available_workers 2, claimed_jobs 0, running_jobs 0); `runtime_doctor` generic internal failure. Previous `runtime_status` SUCCESS, `list_projects` generic internal failure. Thus connectivity is partially operational with method-dependent errors; avoid asserting complete recovery or triggering write tests. Track the failing bounded endpoints via #590 without blind retries.

## Bounded log count — 2026-10-09 operator check

Operator's 10-minute tunnel-unit journal count for regex `error|failed|timeout` returned **5 lines**. This is only a count of matching log lines (possibly repeated startup warnings, not five unique incidents), and does not establish which endpoint failed. Next classify sanitized distinct message labels and timestamps, avoiding raw logs or secrets; do not restart the healthy active tunnel while connector has partial success.

## Port hypothesis and intermittent tool behavior — 2026-10-09

Current observed private topology distinguishes Runner-MCP MCP listener 8000 from tunnel-client local health/UI listener 8080; these are different functions. Logs show `mcp session initialized`, `control-plane route resolved`, and two `dispatcher forwarded command to MCP server` messages. Only startup warning classes counted: one OAuth auth-server metadata fetch failure and three Harpoon loopback HTTP auto-registration failures; there is no evidence from these observations that the MCP target port is wrong. ChatGPT bounded `list_projects` later succeeded returning six configured project entries while `runtime_status` in the same pair gave generic internal failure, reversing previous success/failure pattern. Treat as intermittent tool/transport/session behavior, not port misrouting proven. Confirm endpoint identity against current profile privately, without publishing topology or opening ports. Avoid noisy repeated probes and unqualified permission or plaintext-HTTP changes.

## Additional read-only connector sampling — 2026-10-09

One bounded batch returned `runtime_doctor` SUCCESS with `state=warn`, zero failed checks and three warnings: Fabric continuity configuration unavailable, Fabric worker qualification unavailable, migration storage not configured. `worker_status` SUCCESS with concurrency limit 2, available workers 2 and no active jobs. `runtime_status` and `list_projects` returned generic internal errors in that same batch; previously both had independently succeeded. This *cross-over* rules out a claim that either method is permanently broken, but does not prove whether failure originates in the tunnel control plane, connector wrapper, session reuse or local server. No port changes or write requests justified. Correlate a single failed vs successful invocation with sanitized tunnel dispatcher response classification, timestamps and bounded request identifiers before changing routing or concurrency.

## Dispatcher evidence — 2026-10-09 latest operator check

Ten-minute tunnel-unit journal histogram returned exactly five occurrences of `dispatcher forwarded command to MCP server` and no other `msg` labels in that same time window. The observation proves five forwarding log events, not five completed application calls or delivered client responses. Earlier intermittent structured successes and generic failures must therefore be correlated at the *response* boundary, with no unsupported conclusion that the port or server is faulty. Next collect bounded counts of completion/failure/status categories after one controlled read-only probe; preserve privacy and avoid full raw logs.

## Thirty-minute event distribution — 2026-10-09

Operator supplied a 30-minute tunnel journal message histogram: five `dispatcher forwarded command to MCP server` events, one MCP session initialized, one successful control-plane route resolution, one OAuth auth-server metadata fetch warning, three Harpoon host auto-registration warnings, and no separately named completion event in the reported message labels. Absence of a completion-labelled event is **not evidence of failure**: this runtime may not emit completion logs at this level. Do not request repetitive message histograms; next inspect a single bounded, redacted request-response trace or dedicated structured completion metrics, correlated across MCP server/tunnel/connector. Preserve credentials, identifiers and customer data. No operational mutation.

## Tunnel health acceptance — 2026-10-09 operator evidence

Operator read-only checks: loopback tunnel `/readyz` returned HTTP **200**; systemd state `ActiveState=active`, `SubState=running`, `NRestarts=0`. Operator previously verified `is-enabled=enabled`. Therefore readiness at the tunnel's local interface and no systemd-detected restarts during the current service lifetime are proven. This is not proof of a post-reboot recovery or 100% MCP request success. Preserve running service, do not adjust ports or auth on the strength of these checks, and address intermittent tool responses as an independent issue.
