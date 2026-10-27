# RMCP-F-0076 — Blacky F35 fixed PR cron failure starved generic reviewer

Date: 2026-10-27
Owner: Runner-MCP #844; coordinating Runner-Fabric #1491 and AIfordable #428.
Scope: Existing, rootless **physical Blacky** quick scanner only. This is not a
new Runner-MCP daemon, Fabric work-unit executor, GPU reviewer or remote ACK.

## Failure and verified impact

On the correctly targeted original device `blacky`, Ubuntu 24.04, local
`blacky` UID 1000, the **one existing** hourly user crontab entry at minute
17 ran a fixed `run-pr661-review.sh` and the generic
`review-public-open-prs.py` joined by shell `&&`. A failure in the fixed
PR #661 review therefore prevented all unrelated generic open-PR reviews.

- The fixed PR #661 was already **merged on 2026-10-14**. Continuing to fetch
  and review that one stale PR on every hourly tick added no useful work.
- The fixed review status on Blacky reported `execution=failed` at
  **2026-10-27 19:17:01 UTC** (again at **20:17:01 UTC**); its prior report
  dated 2026-10-14. The generic review manifest was last updated
  **2026-10-13 08:17 UTC** before the corrective work.
- Correctly targeted Blacky read-only discovery through the existing
  credential-free GitHub reader found **12 bounded public open PRs**. That
  confirmed the general discovery path itself was not the missing function.
- The installed rule scanner had separately been replaced on Blacky, from
  Git blob `0807341bc874db1ce8be867b2a76eec541e0f9df` to the actual
  official merged Fabric source blob
  `1bbd78baf69f8db5aa54155f3b1d618012b1257a`.
  The historical complex `RF-PR-007` misses changed from 0/3 to 3/3 in
  isolated tests. **Scanner correctness did not repair the cron dependency.**

## Actual local correction, existing path only

One original same-owner crontab snapshot was retained locally, owner UID
1000, mode 0600, for attended recovery. First isolated the generic public
batch from the fixed task; ultimately removed the obsolete fixed PR #661
step **from the same existing crontab line**, preserving the hourly cadence
at minute 17 and all unrelated crontab entries:

```text
17 * * * * /usr/bin/python3 /home/blacky/f35-reviewer/review-public-open-prs.py
```

This is a local existing reviewer invocation, **not** a new scheduler or
execution channel. The original pinned shell script was retained, not
deleted, and no host-wide changes, tunnels, models, SSH credentials,
providers, new authentication, backup cycles or services were created.

## Functional result and authority boundary

An independently executed **real public PR** advisory using the installed
scanner succeeded with exit code 0: **PR #678** produced
`REVIEW_REQUIRED / manual_review_pending`, with one new review and 11
previously reviewed PRs skipped. The existing `review-678.latest.json`
and `review-public-manifest.json` both persisted the same state at
**2026-10-27 20:17:13 UTC**. The report explicitly had:
`approval_authorized=false`, `merge_authorized=false`,
`dispatch_authorized=false`, `evidence_authenticated=false`.

After the cron change, a read-only check at **20:23:30 UTC** confirmed
exactly one expected single-line hourly entry. Since the next scheduled
tick was **21:17 UTC**, **that first unattended post-correction execution
was not yet observed** in this receipt. Do not relabel a manual run or a
valid crontab string as an observed scheduled completion.

The report is a local non-authorizing source preview, not an
authenticated/Fabric-issued GitHub review, automatic GitHub approval,
deep Windows RTX 5080 GPU inference, or originating-client durable ACK.
Windows Ollama loopback `:11434` and Blacky old private `:11435` are
different, and no remote review route was activated here.

## Prevention / no-repeat rule

- Never couple independent periodic batch work behind a stale pinned
  PR's success using `&&`. Check whether a special-case PR is still OPEN
  before retaining its periodic task.
- Qualify actual scheduled completion from the **same owner-local
  timestamped report/manifest**, not from `crontab -l` alone.
- Preserve previous exact source and original cron recoverability once;
  do not run another automatic backup/supervisor/relay to make a basic
  public reviewer work.
- A `REVIEW_REQUIRED` advisory never grants GitHub reviewer approval,
  execution rights, GPU source transfer or merge privileges. Fabric #1491
  remains owner of the missing fixed admitted `review_local` operation,
  lease/fence and existing Agent Bus/outbox/original-client ACK.
  Runner-MCP #844 owns only later bounded host-local execution/return.
- The single central AIfordable topology is canonical. Blacky has no
  separately qualified immutable Fabric asset ID; do not infer one
  from host nicknames or machine-local observations.

## Evidence links

- Runner-MCP #844: exact physical scan, post-install validation, cron
  root cause, executed PR #678 preview, recovery readbacks.
- Runner-Fabric #1491: F35 review owner and fixed admission dependency.
- AIfordable #428; merged topology PR #720 for Blacky hardware/software
  scope, plus Worker PR #719. Do not treat YAML evidence comments as
  live Fabric dispatcher attestation.

## 2026-10-27 follow-up: successful 0-review runs left no durable stamp

After removing the stale pinned task, the original generic Blacky script
`review-public-open-prs.py` had another proof gap: its existing manifest was
written only *inside* the per-new-PR loop. A successful 0-new-review run
exited 0 but left the manifest timestamp unchanged; the lack of a new
receipt was not trustworthy evidence that the cron had failed.

A one-line change in the **same existing rootless script** now calls the
**already-existing** `atomic_json(manifest, history)` once after a
successfully completed batch, even when `reviewed=0`. No new status
file/registry, heartbeat daemon, scheduler, tunnel, remote source route,
review authority, or model call was introduced. Discovery failure exits
before that new final write and therefore cannot assert success.

Original Blacky user UID1000 script SHA-256:
- Before: `5743f7e6b0c65793ee8c52ed62e6f39006d08743996453694c0c2cd90ef89517`.
- Installed: `4e6a47c54cdbd201ef0863f4aa9f265d95bc807758cead8f028d64a9fae707d2`.

One original same-owner local script is retained for manual rollback.
Candidate and actual post-install module separately passed isolated,
no-network tests: completed no-op writes the SAME manifest; second no-op
replaces its inode; injected GitHub discovery error returns 2 without
changing the prior successful manifest. No privileged service involved.

Two later real minimal-cron-environment runs on Blacky also succeeded.
One scanned new public PR #857 (`REVIEW_REQUIRED` advisory); the next
scanned **zero new PRs / 12 previously checked**, exited 0 and refreshed
the existing manifest timestamp. Neither granted `approval_authorized`,
`dispatch_authorized` or `merge_authorized` nor exercised Windows GPU.

**Do not overclaim:** both were still attended invocations. The first
genuinely unattended post-repair hourly cron completion remained
**NOT TESTED** when this follow-up was recorded. The manifest timestamp
is an operational completion hint, not an authenticated Fabric issuer
receipt, verified source bundle, same-original-client ACK, or a
permission to call Ollama. Source-of-truth: Runner-MCP #844 and the
central AIfordable topology; the local shell script has not been
promoted into a fabricated repository release.

## 2026-10-27 acceptance: unattended cron really ran at 21:17 UTC

The first **genuinely unattended** tick after removing the PR #661
starvation condition and fixing empty-batch manifest persistence is now
**PROVEN**, not inferred from a manual command. On original Blacky
(`hostname=blacky`, user `blacky` UID1000), `cron` was active and the
single existing `:17` crontab row was still unchanged. At original
host UTC `21:17:17`, its **systemd cron journal** contained exactly one
matching invocation of the bounded `review-public-open-prs.py` command
in the `21:16:50–21:18:00` window. The same existing atomic
`review-public-manifest.json` had a fresh mtime of
**2026-10-27T21:17:01.732936Z** and 18 tracked PR records.

The executing file SHA256 still matched
`4e6a47c54cdbd201ef0863f4aa9f265d95bc807758cead8f028d64a9fae707d2`.
No attended/manual review was executed since 20:43 UTC; the cron
journal and existing manifest together qualify this specific real tick.
This is local **quick advisory scheduler** acceptance only, NOT Fabric
Agent Bus dispatch, authenticated reviewer publication, model/GPU
review of actual PR content or original requester durable ACK.

## Follow-up: official pinned-commit producer needs matching local allowlist

After the first scanner upgrade, Blacky's installed
`runner_fabric/review_github_readonly.py` was still the older Git blob
`4a6c552a6d5c3603a224f40c631aac678e91109d`. Merged Fabric
source from #1834 was
`7a0b37be5b30ec0aaab6fdbe304e72024fd6af3c`.
The new producer additionally cross-checks mutable PR file listings
with the immutable GitHub `compare/{base_sha}...{head_sha}` resource.
**Installing only the new producer would cause all normal Blacky
reviews to return WAIT**, because the existing rootless
`public_pr_review.py` allowlist admitted only `pulls/*` paths.

The same existing credential-free wrapper was therefore updated to
accept *only* a fixed SHA-paired `compare` resource with exact
`per_page=1&page=1`; no arbitrary URLs, redirects, credentials, review
publication or broader network interface were introduced.
The resulting local wrapper Git blob is
`75ae7f7941101c4cd208456349897b7881036b9a`
(previous `19b12a2b580755d0397db08b5a52768000750dd0`).

The staged upstream producer and wrapper passed seven strict
resource-allowlist negative checks and source mismatch fail-closed
cases. Two **real public open PR** reads, #678 (9 files) and #710
(12 files), gave `REVIEW_REQUIRED`, all four authority booleans false,
with exact pinned compare checks. A single owner-local switch under the
**existing batch flock** preserved an original private source copy for
each file and atomically replaced the two existing module files.
Actual live post-install PR #678 read returned `REVIEW_REQUIRED`,
`github_head_rechecked=true`, 9 files and a valid 64-hex
`preview_sha256`. This preview hash is NOT authenticated reviewer or
GitHub signing evidence. A separate on-host check confirmed both
active and recovery Git blobs; cron, model and SSH routes unchanged.

The separate physical Windows Worker locally executed an **original
synthetic** Python bug-finding prompt with installed local Ollama
Qwen2.5 Coder 7B, returning the right finding in 20.63 seconds with
22 generated tokens. Ollama `/api/ps` showed the model GPU-resident
(`4,530,089,491` bytes) and `nvidia-smi` showed one RTX5080
snapshot at 6% utilization and 6,820/16,303 MiB VRAM in use. This
is only Windows-local GPU model availability, **not** a real PR
GPU review or a Blacky-to-Windows transport qualification. The
historical Blacky loopback reverse-review listener `:11435` was
still absent when last checked. Fabric #1491 retains exclusive
ownership of admitted F18 `review_local` work-unit, issuer,
host identity, lease/fence, Conductor and original-client ACK;
Runner-MCP #844 can actuate locally only after that contract exists.

**No-repeat guidance:** for source updates of the *existing* quick
reviewer, inspect the selected producer's fixed resource vocabulary
and the consumer wrapper's exact allowlist together; validate
standalone current public PRs before replacing active files.
Do not mistake a valid SHA digest, file write, two local model
responses, or a connector connection for an authenticated F18 review
receipt. The central AIfordable topology, not another registry, is
the canonical physical topology.
