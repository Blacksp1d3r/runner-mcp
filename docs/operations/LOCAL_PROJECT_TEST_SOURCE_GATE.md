# Local test source gate — Runner-MCP #1062 (source-only)

**Status: SOURCE CANDIDATE / NO LIVE DISPATCH / NO GUEST BINDING.**
GitHub is the source/PR store, not a job scheduler or runner provider. CI,
review, models and tools execute only on qualified owner-managed machines
through existing Runner-MCP → Runner-Fabric/F18 → F4/F26 authority.

## First implemented slice

`src/runner_mcp/local_test_source_preflight.py` contains
`inspect_local_test_source(registry, project=..., suite=..., expected_sha=...)`.

It reuses the **existing** `ProjectRegistry`, explicit `TestProfile`
registration and `source_control` Git inspectors. It does not add another
scheduler, executor, project registry or credential store.

The inspector requires, before returning its bounded source result:

- an already configured staging project code and explicitly registered suite;
- a lowercase, full 40-character Git SHA;
- a pre-existing local Git checkout with no symlink in its root path;
- project root exactly equals the Git top-level (nested folder inheritance refused);
- configured `origin` URL equal to the registered GitHub repository;
- clean tracked and untracked working tree;
- exactly matching checkout HEAD;
- no Git submodule metadata.

It performs **no fetch, package installation, test execution, checkout
change, service mutation or host/guest selection**. It accepts no path,
command, host, token, shell or runtime selector from the caller.

Even when the source check succeeds the result is:
`state=source_checked_wait_f26_guest`,
`dispatch_authorized=false`,
`host_local_fallback_allowed=false`,
`remote_reachability_verified=false`,
`guest_identity_verified=false`,
`fabric_lease_verified=false`.

An origin *configuration match* is **not** remote authentication or an
authoritative provenance receipt. There is no way for this module to return
PASS for actual local test execution. It cannot make the existing host-local
`run_tests` method safe for arbitrary remote/project code.

## Scope and current physical state

No new project was registered, no source was transferred, no guest started,
no Fabric tool changed, no existing runner or local service was touched.

- Hive H03 previously: 178/178 Python and 3/3 Go PASS on exact application
  SHA `bf3c6a41f9c7098a78905c6940bb549554a535cc`, on the separate
  H03 Ubuntu Hyper-V VM. This test did **not** qualify Fabric scheduling.
- Hive H56/H67: a different offline Ubuntu VM with a proven bounded Go-only
  KVM lane. It is **not** an attested Python or Windows worker.
- Academy: content/Python/viewer/browser profiles still need qualified
  local execution; a browser result requires an approved compatible guest.
- Computer Cleaner: stdlib Python can be qualified on Linux; the Windows
  PowerShell/CC01 read-only and mock checks require a separately approved
  real Windows guest. No VHDX/disk changes.

## Required subsequent admission (not implemented)

1. Runner-MCP project + profile are registered in the **correct owner-managed
   guest context**, after verified source permission and owner approval.
   Their roots must not point at the central serving Runner-MCP checkout.
2. Fabric resolves and attests an F26 qualified one-job guest/worker identity
   via existing F4/F5/F6 and F21, without arbitrary caller host/path/argv.
3. Original authenticated F18 request receives an exact generation/lease,
   claim, local test result and a durable original-requester ACK.
4. Teardown and secret/cache/workspace cleanup are independently verified.
   Missing execution/ACK/cleanup or stale lease is WAIT/BLOCK, never PASS.
5. Prove one end-to-end Hive task then a second different project on
   requalified free physical capacity. Do not rerun accepted H03 Python tests
   simply to repeat evidence.

## Tests for this source-only slice

`tests/security/test_local_test_source_preflight.py` adds actual local-Git
fixtures and negative assertions for: unknown project/profile, malformed
identifiers or SHA, mismatched source SHA, wrong origin URL, dirty tree,
submodules, symlinked or nested root, non-staging project and unavailable registry.
The positive check explicitly proves that source admission **never**
authorizes dispatch or host-local fallback, and does not move Git HEAD.

These tests are checked into the development branch but **must not be
presented as executed physical-H56/Fabric evidence until they actually run**.
A source branch and a test file are not acceptance receipts.

No GitHub Actions workflow/runner registration or Actions minute spending is
part of this implementation. The development branch stays unmerged while the
F26 Gate 0/F4–F6 runtime admission is absent.
