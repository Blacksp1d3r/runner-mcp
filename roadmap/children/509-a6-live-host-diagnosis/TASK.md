#509 — A6 live host/process diagnosis (read-only child TASK)

Status: BLOCKED_EXTERNAL. Owner Runner-MCP #509; source patch PR #655 is a distinct child. Linked communication owner #590, Fabric #942, Fabric #943. Do not duplicate source binding repair #512/#515 or change Fabric-issued host authority.

## Inputs to qualify

1. Privately resolve actual enrolled host/service asset identity via trusted first-party AIfordable/Fabric registry (not any caller-provided name or network address); identify the exact client→connector route used in the SAME request.
2. Observe actual running PID/source revision, installed artifact hash, registered tool schema SHA and release generation; distinguish disk source SHA and stored self-update SHA from running source. Qualify the original-client receipt of both one successful and one failing read-only MCP request, with correlation ID and server audit.
3. Read the current source's sanitized `runtime_doctor.fabric_a6_binding_state` only on the attested service. Interpret fixed A6 roots `absent/incomplete/unsafe/ready` and eleven binding counts without reading credentials or arbitrary files.
4. On precisely verified host, run existing bounded peer preflight and classify peer `a6_prepare_available` and `synthetic_probe_status_available`, peer revision, Agent-Bus relay visibility and error boundaries. Do not confuse bridge READY with A6 READY.
5. If necessary, propose one narrowly scoped existing binding repair only after identifying the first failing edge and obtaining independent safety approvals. No new dynamic tool, shell, arbitrary path, env dump or speculative restart.

## Current bounded evidence (2026-10-11)

- Connected build_identity self-reports version 0.1.3/source a0fd964c4a6fe7e0a1506a513e9b2b4059c5453a/schema 711f96eb3d9cc5dcd2c6476f87ab70f34b69dc87c394b33d0d5b4ae8f308045f, artifact_digest null; physical service identity still unknown.
- Verified code provenance: current `build_identity.py` obtains `installed_source_revision` only from `self-update-state.json` (`commit`) and `runner_mcp_mcp_build_identity` sets `artifact_digest=None` unconditionally. The self-reported revision is therefore persisted install state, NOT attested active process code or artifact provenance; do not use it as rollout or host authorization.
- Connected runtime_doctor intermittently emits an OLD 12-check set lacking `fabric_a6_binding_state` or fails generically; current main source includes that check. Do not infer roots state from its absence.
- Fabric bridge preflight self-reports READY/peer revision 66e9dcdcc80e708e653dd324778d75f7587ca9bc but A6 prepare and synthetic probe capabilities both FALSE; mutations FALSE.
- Operational snapshot degraded, Agent-Bus relay evidence unknown; fabric_host_inspect failed generically. These are observations, not release approval.
- Keep #341 self-update blocked until Fabric #942 journal and #943 independent timeout/revert supervisor and original-client full result+ACK.

## Acceptance

Produce a single proven request route+identity/source/artifact/tool schema+actual A6 diagnostics with no secrets; close root-cause classification only if same-host evidence supports it; record any new failure mode in canonical Failure Museum if not already covered by RMCP-F-0002. CI any source PR on its exact head. No customer/production activation.
