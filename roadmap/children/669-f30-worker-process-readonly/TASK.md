# Runner-MCP #669 — existing Fabric bridge worker process read-only

Partner: Fabric #924 source [PR #1614](https://github.com/Blacksp1d3r/Runner-Fabric/pull/1614), merged `20c8cc44`; AIfordable #585 existing-relay H-transport accepted. No new bridge, relay, tunnel, credential, SSH, updater or orchestrator.

## Shipping v0.1.46

On existing authenticated Runner-MCP MCP transport, a new conditional tool `fabric_worker_process_inspect(worker: "claude"|"qwen")` proxies a single read over the **existing** `FabricBridgeClient` and its loopback bearer-bound Fabric peer `worker_process_inspect` function. It has NO caller-supplied host, port, PID, UID, executable, path, URL, token or argv. Missing capability from an N-1 Fabric peer returns WAIT. Exact returned contract, service/host asset ID, freshness, shape and permanent denial flags are validated before response; invalid answer returns WAIT, does not reveal transport/private secrets and never authorizes mutations.

Valid observations on the appropriate host can report PID/UID/proc start ticks, timestamp and optional software claims; `buildProvenanceVerified=false`, `mutationEnabled=false`, `dispatchAuthorized=false` in all cases. A source SHA or wheel SHA claim is NOT a cryptographically verified installed/imported serving generation.

Release metadata: pyproject, server.json top+package, glama.json and runtime __version__ all v0.1.46 on current main v0.1.45. Preserve exactly merged #753 release reservation and its policy; no previous version reuse. Registered tool catalogue grows from 97 to 98 names, with attestation of source/wheel.

## Checks and live admission

Exact-head Ruff/pytest, release admission/version metadata, tool catalogue, wheel/clean-demo, Ubuntu/attribution. No merge on stale/failed CI. Correct host identity, local Fabric agent, private process pin, installed signed wheel + process import RECORD, trusted original requester and durable exact result ACK, off-target A6/A7 recovery and Fabric #924 single lease are separate prerequisites.

Do not repeat existing October 18 physical rollback drills. No deployments, model calls, provider billing, credential updates, Qwen guest service installations or automatic dispatch in this PR.
