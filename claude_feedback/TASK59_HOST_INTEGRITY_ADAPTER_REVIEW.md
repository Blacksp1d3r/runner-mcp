# Task 59 — host-integrity production adapter boundary review

Status: COMPLETE review. Implementation remains a separate code task.

## Decision

A production Linux adapter is justified, but only as a local, fixed journalctl classifier behind the merged HostDiagnosticAdapter boundary. It must not become a generic journal reader, CLI selector, MCP tool, Agent Bus action or Fabric operation.

journalctl is acceptable for the currently supported systemd-based Linux operator path because Runner MCP autostart already depends on systemctl --user. Its absence, execution failure, timeout or unsupported output is not repaired and never falls back to another command: the adapter raises a bounded HostDiagnosticError, which the gate maps to diagnostics_unavailable.

## Fixed query

The implementation owns one fixed argv tuple. The caller supplies only the gate-computed aware since/until timestamps; it cannot supply query text, executable names, units, paths, providers or a time window.
Use JSON output and request only the minimum fields required to classify a fatal process event. Raw records never cross the adapter boundary.

The first implementation classifies supported CPython executable basenames (python3, python3.12) as PYTHON_RUNTIME. A deliberately small reviewed tuple for unrelated system/package utilities is added only when live incident evidence identifies the exact executable. Do not invent a broad list merely to look comprehensive.

## Resource bounds

- fixed subprocess timeout: 5 seconds;
- stdout byte ceiling: 256 KiB;
- stderr is captured only to prevent terminal disclosure and is never parsed or returned;
- no shell, fixed argv and fixed environment policy;
- non-zero exit, timeout, spawn failure, decode failure, oversized output, non-JSON line, missing/invalid required fields or invalid timestamp => HostDiagnosticError;
- cap parsed records at 512 even below the byte ceiling;
- enforce the byte ceiling while collecting output; do not trust unbounded capture_output for journal data.

## Privacy boundary

Public output remains only one of the four merged HostIntegrityState values. Never expose journal text/raw JSON, stdout/stderr, PID/UID/user, executable path, hostname, boot ID, kernel address, coredump metadata, stack, command line/environment, str(exc), or subprocess exception detail.

## Time semantics

The gate remains owner of the fixed 30-minute lookback. The adapter validates aware ordered since/until values and converts them only to the fixed journal timestamp representation. No CLI option alters the interval. Future events are malformed/fail-closed.

## CI and testability

CI never inspects the GitHub runner journal. Unit tests inject a fake bounded runner/output stream and cover Python classification; reviewed unrelated classification once known; irrelevant executable ignored; timeout/nonzero/missing journalctl; oversized stdout and >512 records; malformed JSON/encoding/timestamp/identity; sensitive literals never escaping; fixed argv/no shell; and no new remote action/tool enum.

## Explicit non-goals

No package install, sudo, service restart, coredump retrieval, arbitrary journal query, generic process inspection, hardware diagnosis or automatic repair.

## Next code slice

Implement only the adapter and deterministic tests. Do not wire it into install_user_services in the same PR. Autostart enforcement remains Task 60 so activation ordering can be reviewed independently.
