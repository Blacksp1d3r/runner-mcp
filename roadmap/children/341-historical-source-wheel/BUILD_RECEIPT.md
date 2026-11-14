# Read-only build receipt — historical Runner-MCP source wheel

This is an independently checked **candidate reconstructed package**, NOT a captured installed wheel, NOT a signed recovery package and NOT live rollback authority.

| Attribute | Verified value |
|---|---|
| Historical source | `a0fd964c4a6fe7e0a1506a513e9b2b4059c5453a` |
| Run | [GitHub Actions 38172448547](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/38172448547) SUCCESS |
| GitHub job | `114567711972` |
| Pinned source checkout | `git rev-parse HEAD` matched exact historical SHA |
| Builder | GitHub-hosted Ubuntu 24.04, CPython 3.12.15 |
| GitHub artifact | ID `11714820810` / `unverified-recovery-wheel-a0fd964c` |
| Wheel | `aifordable_runner_mcp-0.1.3-py3-none-any.whl` |
| Wheel bytes | `302031` |
| Wheel SHA-256 | `f3b6513f7dfa1800fab9efbbc001f6e0dbb33ae81b522578f3804c002d62a8b2` |
| Artifact ZIP bytes | `296255` |
| ZIP SHA-256 | `e350215ccd625e82fc8f29f865628031cfbe02833cc7f774019cf301e305e246` |
| Wheel internal file count | `91` |
| Source wheel package metadata | `Name: aifordable-runner-mcp`, `Version: 0.1.3` |
| Safe isolated install/uninstall | PASS on disposable Python 3.13.5 venv, no dependencies |
| Installed extracted CLI digest | `5690884ac7eb896a97203ea1282c4b0e21959ebedb18b8b377fc006f3bcdbe55` matches wheel |
| Private off-target copy | User Library `Backups/Runner-MCP/Recovery-Wheels/runner-mcp-exact-source-a0fd964c-20261011.zip` confirmed by independent listing |

**Important**: Published GitHub release tag `v0.1.3` corresponds to `0aa013c279128e22fbd53be32c35bced3ae26834`, **280 commits** behind the stored installed source and not an acceptable substitute for this archive. CI test on exact historical SHA previously passed but had no retained wheels. This rebuild closes that *source artifact availability* gap only.

No live-active package/module byte hash, no recovery signer, no second physical medium guarantee, no actual service restart, no full 3.12 runtime restore and no original-client ACK. Continue independent qualification. No runtime, tunnel, A7 machine, GitHub Actions self-hosted runner or protected project storage was modified.

Cross-refs: #341, #590, docs/operations/RECOVER_EXACT_INSTALLED_WHEEL_2026-10-11.md in handover PR #659, Failure Museum RMCP-F-0032/0034, A6 Fabric #942 and A7 #943.

## Second independent Python 3.12 build + artifact comparison (2026-10-11)

- GitHub-hosted run [38172776852](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/38172776852) SUCCESS, artifact id `11715250071`, Python 3.12.15 isolated venv wheel installation/compile/uninstall SUCCESS; this is not a running MCP service test and uses no runtime dependencies.
- New downloaded ZIP size `296572` bytes, SHA256 `797a64412a2298de0229f6a2062e79c32d7bf071482914f98103a360ca529ea8`.
- New contained wheel `aifordable_runner_mcp-0.1.3-py3-none-any.whl`, size `302031` bytes, SHA256 `2fe8ed42a51ad9ba351b74f8f651da4d0e89ce36b84cfb97bc70ac207142b5bc`.
- Old wheel SHA256 was `f3b6513f7dfa1800fab9efbbc001f6e0dbb33ae81b522578f3804c002d62a8b2`. The two wheels had EXACTLY the same 91 member paths AND the SHA256 of each uncompressed member was identical; their overall ZIP/wheel byte hashes differ. Thus the source-package payload is stable while binary archive-level reproducibility remains **UNQUALIFIED** (likely wrapper metadata, not proven). Release signing/restoring must PIN the actual selected binary SHA256; do not substitute a differently hashed rebuild merely because version and source match.
- New artifact privately retained separately from previous ZIP at Library `/Backups/Runner-MCP/Recovery-Wheels/runner-mcp-a0fd964c-python312-proof-20261011.zip`; previous artifact untouched. Still no active host loaded-module proof, full dependency restore, immutable signature or original-client ACK.
