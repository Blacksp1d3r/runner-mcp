# F30 H — read two fixed workers through existing authenticated MCP

Source (NOT live availability proof):
- Existing central `Runner-MCP` conditional authenticated `fabric_worker_process_inspect(worker)` invokes `FabricBridgeClient.worker_process_inspect`, not HTTP requests to an invented host.
- Underlying already existing private loopback Fabric agent MCP endpoint has optional `worker_process_inspect` from Fabric #1614.
- Allowed aliases: Claude AF-SVC-0011 on AF-VM-0001, Qwen AF-SVC-0019 on AF-VM-0003. No arbitrary host/PID/UID/URL/path/shell input.
- Fabric owner-local private /proc pinned observer can optionally inspect a process under a pre-authorized host-local PID, UID and start tick, without execution. A different host/guest cannot be observed from central github-runner just by changing an ID.
- Existing relay is reachable (github-runner PID 1103700, 127.0.0.1:8020 healthz GET 200, public claim GET 405) per operator-attended AIfordable #585; do not rebuild it. That transport result is not worker authorization.
- Existing bootstrap/private configuration must independently attest correct host, service and per-subject original requester before route is qualified. This source PR does not deploy the worker-local Fabric agent into Claude or Qwen or expose arbitrary remote access.
- On unavailable/no private observer/wrong host/error: WAIT, no auto retries, no build attestation, no task dispatch.
- On fresh shape-valid process observation: `observed_unverified`, non-authorizing; PID/UID/ticks alone do NOT prove wheel or original-client fingerprint ACK.
- For software authority Runner-MCP #669 independently checks loaded installed source/Wheel RECORD, right-host UID and signed serving generation. Fabric #924 controls one guarded host promotion with off-target journal and offline recovery; AIfordable #585/#609 owns existing authenticated issuer/relay/original terminal ACK.

After a source-only merge, `main` or a green release workflow is not the installed 0.1.38 host. An authorized physical deployment with exact-wheel evidence is a different, still-open step.
