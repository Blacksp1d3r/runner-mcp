# Runner-MCP wrong-version confusion — 2026-10-21

## Observed, no speculation

On `aifordable-lab`, the `aifordable-runner` interactive `runner-mcp --version` returned `0.1.3`; an independent operator check of the already-running `runner-mcp.service` MainPID executable returned `runner-mcp 0.1.38`, with no service restart. These are different installed entrypoints and **may legitimately differ**. Meanwhile the ChatGPT-connected primary Runner-MCP on `github-runner` independently returned its own 0.1.38, with neither live source revision nor wheel digest verified. A matching package version on two hosts does NOT establish the answer route.

## Root cause and prevention

A shell PATH CLI is not process evidence. Older client responses only expose package version and lack verified source/wheel/instance, while source/self-update history can diverge after manual installs. A caller must never treat a PATH version, source GitHub `main`, old transaction SHA, or another host as current runtime proof. Existing source `build_identity` already suppresses unverified wheel/source; Fabric #1694 source now tracks canonical host/route and rejects ambiguous replies.

The v0.1.75 code change adds a **stable current-MCP-server epoch** across the two existing read-only tools. Tests ensure epochs differ on fork/instance creation. This is a correlation **hint only**; not a signed/process/host/source attestation. Real original-client route receipt, A6/A7 and wheel/source trust remain separate. No live service update was performed to hide this failure.

## Regression

Unit test `tests/unit/test_serving_instance_epoch.py`; match active session epoch from two tools once version v0.1.75 is separately installed into an isolated disposable target. Independently test wrong-route/version/source negatives in Fabric #1694.
