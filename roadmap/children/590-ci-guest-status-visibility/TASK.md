# Optional Fabric CI guest status — task

Parent: Runner-MCP issue #590; coordinating Fleet issue Runner-Fabric #924.

Goal: when the optional Fabric CI guest status call fails, return a fixed, read-only unavailable envelope instead of a generic connector exception. Unknown guest state must remain unknown (null) rather than claiming the guest does not exist. Distinguish a recognized invalid payload from other read failures using static reason codes. No sensitive exception text in public responses.

Boundaries: unchanged successful guest contract, unchanged guest start/enroll/stop, no retry, no additional authority, no host action, no network/service changes. Version metadata for this source candidate is 0.1.25.

Acceptance: exact-head lint, tests, build/demo, clean installer, attribution. A source merge is not an installed release. Real host identity/provenance and A6/A7 update qualification remain separate.
