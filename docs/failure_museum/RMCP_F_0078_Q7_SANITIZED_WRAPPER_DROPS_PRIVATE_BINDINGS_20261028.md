# RMCP-F-0078 — Q7 prepared but omitted from sanitized Runner-MCP Fabric launch

Date: 2026-10-28
Owner: Runner-MCP B / #381; original LAB operational owner Fabric #972 / AIfordable #609
Status: SOURCE FIX MERGED, true-host rollout + original ACK WAIT
Fix: [PR #916](https://github.com/Blacksp1d3r/runner-mcp/pull/916), tested head `4fe45ecd7557a68ae39dd45f213c5a53e8812f46`, merged `dab20b7248d59b456d31aba5eaba5f340006de20`, version 0.1.129.

## Observed failure and cause

On original `aifordable-lab`, owner-attested new Fabric qualification source `2d4b7ae...` served :9020 as PID9265. The effective process environment had zero of seven `RUNNER_FABRIC_CODING_Q7_*` keys even though the private Q7 mapping had been staged separately. Investigation of the EXISTING Runner-MCP `run_fabric_agent_qualification_process` revealed an explicit sanitized `execve` environment assembled by `qualification_agent_environment_additions`, which forwarded A6 and worker qualification groups but not Q7. A systemd Environment directive alone is insufficient: the wrapper discards keys it has not explicitly admitted. Prepared private files are distinct from effective process bindings, and the shared user private .env is not automatically the same as the staged systemd-side `q7-private.env`.

## Corrective change and evidence

Reuse existing owner-private Runner-MCP `read_private_runtime` / `load_env_file`, no new source or credential store. Require seven exact Q7 values as a complete group; reject missing/empty/unknown or invalid fixed project/provider/repository/loopback values, nonabsolute/unsafe/oversized paths or bearer shape; build the forwarded group before updating launch environment. Optional explicit `RUNNER_FABRIC_AGENT_QUALIFICATION_MODE` is accepted only as `subscription-coding-q7-v1`, and the seven fields alone do not activate Q7. No ambient environment variable inheritance, credential output, new authentication, worker, relay or service.

Exact-head CI: Runner MCP validation #40747041346 SUCCESS including Ruff/pytest, release gate, built wheel, disposable systemd and clean five-minute demo; clean Ubuntu #40747041302 SUCCESS; commit attribution #40747041624 SUCCESS. Synthetic tests cover accepted execve environment, absent mode, all seven omissions and empties, invalid fixed values/path/secret/mode, unknown field, attempted ambient contamination and coexistence with existing A6.

## Prevention / remaining physical boundary

Any future new Fabric qualification environment keys require a fixed, fail-closed, all-or-nothing admission test at the *actual wrapper execve boundary*; file existence, systemd directives and an upstream Fabric module do not prove inheritance through an explicit sanitized environment. Preserve separate original owner identities and deny accidental Q7 mode enablement. Source merge is not proof of deployed wrapper, proper existing private value consumption, imported module identity, immutable update/rollback, original issuer/fence/lease, real model patch, independent Git acceptance or terminal result+ACK to the initiating client. Lab rollout remains Fabric #972/AIfordable #609; #381 stays open.

## 2026-10-28 — source compatibility follow-up

Fabric also supports the legitimate `synthetic-read-only-v1` mode. The initial #916 all-or-none Q7 key forwarding could newly reject a private Runner-MCP config that contained only this non-Q7 mode. [PR #918](https://github.com/Blacksp1d3r/runner-mcp/pull/918) fixed this independently: with no Q7 fields and no explicit Q7 mode, preserve the previous sanitized wrapper behavior (no forwarding); any Q7 fields plus a different mode still reject, and standalone explicit Q7 mode remains incomplete. Exact tested head `9ff2654322433c1eb54d24edacfae6d4042590ae`, squash `22b73f454f3b3844cfb4ae7e85342f2ff6837f85`, v0.1.130, validation #40748541909, Ubuntu #40748542079, attribution #40748542125 all SUCCESS. No original LAB deployment or client ACK.
