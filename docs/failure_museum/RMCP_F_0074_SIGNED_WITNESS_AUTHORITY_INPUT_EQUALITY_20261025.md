# RMCP-F-0074 — signed serving witness accepts subclassed expected identity equality

Date: 2026-10-25
Scope: [Runner-MCP #669](https://github.com/Blacksp1d3r/runner-mcp/issues/669); source-level offline verifier only.

## Failure mode

The original `signed_serving_witness_preflight` validated independent authority inputs with `isinstance(value, str)` and subsequently compared them with values extracted from signed JSON. A Python string subclass with custom `__eq__` or `__ne__` could pass the regular-expression shape checks while treating a *different* source revision, wheel hash, host, nonce, generation or signer digest as equal. This is a same-process trusted-input-type confusion, not a forged Ed25519 signature, a proven compromised host or an actual live-serving provenance elevation.

The comparator correctly kept `active_build_provenance_verified=false` and did not export a source revision or artifact digest even for an otherwise consistent signed offline statement; this safeguard was never relaxed.

## Remediation

[PR #834](https://github.com/Blacksp1d3r/runner-mcp/pull/834), merged at `ce327e5db688fe6bae835a4c181824320f01f762` in Runner-MCP source `0.1.88`, requires exact intrinsic Python `bytes`, `str` and `tuple` at independent authorization-input boundaries. The original six-role process-pin comparator preserves strict six-role input validation. Adversarial subclassed expected-source/wheel/host/nonce/key/version/role inputs are rejected; unmodified honest synthetic inputs still yield **offline statement consistency only**.

Exact-head CI: Runner MCP validation `40228298337` PASS (Ruff/pytest, version reservation, artifact build, clean demo), clean Ubuntu installer `40228298330` PASS, commit attribution `40228298325` PASS. No new service, signer key, tunnel, authority, updater or additional storage inventory.

## Remaining physical gate — NOT RESOLVED

The previously authenticated historical original wheel 0.1.38 (RECORD 117/117, 112-module aggregate MATCH and protected A7 custody) is **already accepted** and must not be rechecked. The currently connected original 0.1.38 build identity still exposes `source_revision=null`, `artifact_digest=null` and `active_build_provenance_verified=false`. A fresh independently authorized original-host six-role loaded process/import-generation witness remains a separate #669 requirement. A7 #943/#1650 physical six-serving-role offline rollback and A6 #942 custody are separate. GitHub 0.1.88 is **not installed** on the original physical serving host.

Status: SOURCE FIX MERGED / PHYSICAL WITNESS OPEN.
