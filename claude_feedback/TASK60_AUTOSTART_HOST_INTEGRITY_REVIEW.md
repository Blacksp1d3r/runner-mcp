# Task 60 — autostart host-integrity enforcement review

Status: COMPLETE review. Implementation must be a separate code slice after Task 59 lands.

## Finding

The current local `runner-mcp autostart install` path can enable services without consuming the merged HostRuntimeIntegrityGate. For systemd, `cmd_autostart` selects the backend and calls `install_user_services`; that function writes units, reloads systemd, then calls `systemctl --user enable --now`. Cron has a separate install path and therefore must not be forgotten when enforcing the same safety intent.

## Exact enforcement point

Host-integrity evaluation belongs in the local CLI orchestration before either autostart backend mutates persistent startup state. Do not bury the gate only inside `install_user_services`, because `--backend cron` would bypass it. The CLI should obtain one bounded local activation decision, require CLEAR, and only then call the selected backend installer.

`install_user_services` should additionally accept a narrow already-evaluated activation permit/value and refuse when it is not CLEAR. This is defense in depth against future internal callers. The cron installer needs the equivalent guard or a shared guarded installer wrapper.

## Runtime-smoke evidence

The installer already performs 32 fresh-process critical import iterations plus 8 no-bytecode `runner-mcp --help` iterations, but that success is not durable evidence available to a later autostart command. Therefore Task 60 must not simply pass `runtime_smoke_passed=True`.

The implementation should add a local bounded smoke helper that repeats the installed-runtime checks at autostart time using the currently executing Runner MCP interpreter/launcher. It returns only pass/fail, uses fixed modules/argv/counts/timeouts, captures no caller input, and leaks no process output. Reusing a shared Python implementation is preferable to parsing installer text or trusting an old marker file.

Minimum autostart-time smoke: fixed critical imports in fresh Python processes and fixed launcher `--help` checks. Counts may match the installer (32 + 8) unless profiling shows an operator-host timeout concern; any reduction requires a separately documented evidence basis.

## Required ordering

1. Resolve local config/executable and reject an already-installed conflicting backend.
2. Check self-update/install recovery state and any pending restart/update state before host diagnostics.
3. Run the fixed autostart-time runtime smoke.
4. Run the Task 59 production diagnostic adapter through HostRuntimeIntegrityGate.
5. If and only if state is `host_integrity_clear`, create/replace managed autostart files and enable the selected backend.
6. Any other state exits with one bounded category and performs no autostart mutation.

Systemd `show-environment` may be used as a read-only availability preflight before the integrity decision, but unit-file writes, daemon-reload, disable/remove of optional units and enable/start all remain after CLEAR.

## Partial-mutation rule

The current systemd installer writes all unit files before daemon-reload/enable. A blocked integrity state must occur before `_safe_unit_dir` creates directories or `_write_managed_unit` changes files. Existing managed units must not be disabled/removed as a side effect of a failed integrity check.

For failures after CLEAR during normal installation, existing managed-file atomicity and bounded systemctl errors remain in force; this review does not add rollback or repair authority.

## Emergency stop and recovery

Autostart installation is local operator mutation. Before implementation, reuse the existing operator-stop/recovery authorities rather than creating a new override. An active emergency stop, pending/invalid install recovery, or pending self-update restart must fail closed before activation. There is no remote force flag and no `--ignore-host-integrity` option.

## Public result

CLI output may identify only the bounded HostIntegrityState/category and generic next action. It must not print journal records, executable paths, PIDs, stderr, exception strings or private host identifiers.

## Tests required

- CLEAR reaches exactly one backend installer; each other state reaches neither systemd nor cron mutation;
- runtime smoke failure skips diagnostics and all autostart writes/systemctl enable/cron writes;
- diagnostics unavailable/crash evidence skips both backends;
- active emergency stop and recovery-pending/invalid block before smoke/diagnostics where existing authority requires it;
- systemd and cron cannot bypass the shared decision;
- direct internal installer call without CLEAR permit fails closed;
- sensitive diagnostic/process literals never reach CLI output;
- status/remove behavior is unchanged and does not require host-integrity evaluation.

## Next code task

After Task 59 merges, implement (a) the fixed production diagnostic adapter, (b) a local fixed runtime-smoke helper, and (c) shared autostart activation gating in separate small PRs. Do not combine journal parsing, smoke execution and backend mutation into one large change.