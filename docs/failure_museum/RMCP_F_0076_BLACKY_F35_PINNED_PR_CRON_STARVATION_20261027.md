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
