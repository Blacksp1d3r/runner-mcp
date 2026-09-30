# Runner MCP lab runtime qualification

This document is a diagnostic decision record for issues #194 and #195.
It is not a production dependency policy and must not be used to enable autostart by itself.

## Current lab facts

- Runner MCP source baseline: `4713108f1665773bba7d0f520d5bde6ffa877478`.
- Lab system/venv Python: CPython 3.12.3.
- Installed MCP: 2.2.0.
- Reproducible native crash boundary:
  - `mcp.server`
  - `mcp.server.mcpserver.utilities.func_metadata`
- Pure `compile()` stress remained stable in previous isolation.
- Python has also crashed during package installation, so an application-only root cause is not established.
- Autostart, mailbox and Agent Bus remain disabled.

## Independent runtime matrix

The diagnostic branch tests:

| Python | Pydantic | MCP |
|---|---|---|
| 3.12.3 | 2.12.5 | 2.2.0 |
| 3.12.3 | 2.13.5 | 2.2.0 |
| current 3.12.x | 2.12.5 | 2.2.0 |
| current 3.12.x | 2.13.5 | 2.2.0 |

Each valid matrix cell must:
1. install successfully;
2. pass `pip check`;
3. confirm exact package metadata;
4. repeatedly import the proven crash-boundary modules in fresh processes.

## Decision tree

### A. All independent cells pass

Do not add a speculative Pydantic pin.

Interpretation: MCP 2.2.0 plus both tested Pydantic versions are stable on an independent Ubuntu/Python runtime, including exact Python 3.12.3.

Next priority:
1. physical host BIOS/microcode/default CPU settings;
2. offline physical RAM test;
3. host CPU/RAM stress at defaults;
4. physical storage health and Windows WHEA/storage logs;
5. Hyper-V/VHDX integrity;
6. recreate/requalify the guest runtime only after host evidence is clear.

### B. Python 3.12.3 fails independently but current 3.12.x passes

Treat CPython patch level as a compatibility candidate.

Do not change Runner MCP dependency policy yet.
Reproduce on a clean newer Python 3.12 patch release in the lab, then rerun the exact import stress.

### C. Pydantic 2.13.5 fails independently and 2.12.5 passes on the same Python

A temporary constraints pin may be justified.

Before changing production metadata:
1. reproduce multiple times;
2. capture exact transitive versions;
3. test full Runner MCP CLI/import stress;
4. document expiry/review condition for the pin.

### D. Both Pydantic versions fail independently with MCP 2.2.0

Escalate toward the MCP/CPython/upstream stack.
Do not hide the failure with installer retries.

### E. Independent matrix passes but lab continues to segfault after host checks

Rebuild the lab guest from a trusted image on known-good host resources and requalify before enabling remote control.

## Host qualification rules

A quiet journal/event log is not proof of healthy hardware.

For this Hyper-V lab:
- Linux guest evidence collector: `scripts/lab-runtime-hardware-evidence.sh`
- Windows host evidence collector: `scripts/windows-host-integrity-evidence.ps1`

The physical-host qualification must include an offline RAM test because a guest-only memory stress test cannot prove the physical DIMMs are healthy.

For the Intel Core i9-14900KS host, verify the motherboard BIOS contains Intel microcode 0x12F or later and use Intel Default Settings during qualification.

## Activation rule

Runner MCP mailbox, Agent Bus and autostart remain disabled until:
- a stable runtime import/CLI qualification passes;
- recent fatal host evidence is absent or understood;
- the host/runtime integrity decision is explicit rather than inferred from a reinstall.
