# Host-integrity evidence gate

Runner MCP uses a local-only, bounded host-integrity gate as one input to
activation decisions. The gate is deliberately conservative: recent fatal
runtime or host-fault evidence blocks activation, and unavailable or malformed
diagnostics fail closed.

## What is classified

The Linux journal adapter uses fixed, non-caller-controlled queries and returns
only sanitized evidence classes:

- `python_runtime`: a recent fatal Python runtime record;
- `hardware_machine_check`: machine-check or hardware-error evidence;
- `memory_error`: EDAC, uncorrectable-memory, or memory-failure evidence;
- `storage_io_or_filesystem`: block, NVMe, I/O, or filesystem corruption
  evidence.

Raw journal messages, paths, hostnames, device names, serial numbers, memory
addresses, and similar host details are not returned from the adapter.

## Bounds and failure behavior

Each fixed journal query is bounded by:

- a five-second subprocess timeout;
- at most 256 KiB of output;
- at most 512 records;
- a caller-independent time window supplied by the gate;
- strict UTF-8 and JSON parsing.

Nonzero journalctl exits, malformed records, future timestamps, oversized
output, excessive record counts, and unavailable diagnostics are converted to
the generic `diagnostics_unavailable` activation state. Diagnostic stderr and
raw exception details are not surfaced.

The kernel query is fixed to `_TRANSPORT=kernel`; callers cannot provide
selectors or arbitrary shell commands.

## What a quiet journal does not prove

No matching journal evidence means only that this bounded query found no
matching evidence in the inspected window. It is not proof that the CPU, RAM,
storage, filesystem, hypervisor, firmware, or operating system is healthy.

In particular, this gate is not a substitute for:

- an offline multi-pass memory test such as MemTest86+ or an equivalent vendor
  diagnostic;
- CPU and platform diagnostics supplied by the hardware vendor;
- SSD/HDD/NVMe vendor health and extended self-tests;
- filesystem checks performed under the operating system's recommended
  maintenance procedure;
- BIOS, firmware, microcode, and hypervisor qualification.

Runner MCP therefore must not enable autostart merely because the journal is
quiet. A passing runtime smoke test and the rest of the activation policy still
apply.

## Privacy model

Only the stable enum classification and event timestamp leave the diagnostic
adapter boundary. Matching is performed locally. This feature does not provide
a general-purpose remote log reader or shell.
