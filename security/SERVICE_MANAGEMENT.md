# Staging service management

Runner MCP exposes staging services through private aliases rather than raw operating-system unit names.

## Current backend

The initial backend supports systemd user services only.

Runner MCP does not invoke sudo and does not provide generic system-level service control.

## Allow-list model

A private project configuration maps an alias such as `web` to a systemd-user unit. MCP clients use only the alias.

For each service, the owner independently enables or disables:

- start;
- stop;
- restart.

All three mutating permissions default to disabled.

## Information boundary

Normal MCP output may contain:

- project code;
- service alias;
- load/active/sub state;
- health result;
- allowed-action booleans.

It must not return the private systemd unit name or private health-check URL.

## Emergency stop

Read-only service status remains available while the operator emergency stop is active.

Start, stop and restart are blocked by the operator safety guard.

## Process execution

The systemd backend uses a fixed `systemctl --user` argument array and `shell=False`.

Raw stderr/stdout from a failed systemctl operation is not returned to MCP clients because it may contain private unit or host details.

## Health checks

Health URLs come only from private configuration. MCP clients cannot supply arbitrary health-check destinations.

The result is reduced to a safe state such as `healthy`, `unhealthy` or `not_configured`; the URL itself is never returned.
