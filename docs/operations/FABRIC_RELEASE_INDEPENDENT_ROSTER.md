# Q7 GitHub release independent roster comparison — SOURCE ONLY

Runner-MCP `compare_exact_pinned_q7_roster` compares a *previously and independently authenticated* Q7 release asset roster with observed GitHub metadata. The input has an exact 40-character source revision, corresponding Q7 tag, numeric GitHub Release ID and 33 distinct canonical safe asset name/ID/byte-count/SHA256 pins.

Critical: `PinnedReleaseRoster` is only a Python data container. A caller constructing it from untrusted GitHub API metadata has NOT obtained a trusted independent pin. No signer verification, expiry, revocation, trusted key distribution, publisher identity, installed process build identity, or customer authority exists here. `match_only` must never be treated as APPROVED, execution, install, or immutable bytes custody.

Negative synthetic tests cover spoofed IDs, malformed/out-of-order items, bool-as-int, duplicate names, digests, tampered release/tag/source, wrong project wheel and unhashable values. No private host, secret, filesystem, external network or GitHub asset is touched by this pure function.

Next acceptance: separately approved signer/public-key custody, signed immutable release manifest and 33/33 actual byte checks, `BUNDLE.json`/`COMMIT_SHA`/`SHA256SUMS`/wheel metadata inspection, rootless atomic replay-denying custody on the correct host, original-client ACK and explicit separate install permission. Parent #739 remains open.
