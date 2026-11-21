# Runner-MCP #341 exact historical wheel — STATE

## Evidence as of 2026-10-11

Status: **CANDIDATE_WHEEL_BUILT_AND_ARCHIVED / PRODUCTIVE_RESTORE_NOT_QUALIFIED**.
Pinned old source: `a0fd964c4a6fe7e0a1506a513e9b2b4059c5453a`. Main base at task creation: `2d025ce72443853795aa87b4ec96b83a25064634`. Source/branch ownership: own isolated evidence workflow only, not the live Runner-MCP installation or A6/A7.

- GitHub-hosted isolated Ubuntu workflow run [#38172448547](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/38172448547) **SUCCESS**, job 114567711972. Checkout verified EXACT pinned detached commit, wheel built on Python 3.12.15.
- Artifact `unverified-recovery-wheel-a0fd964c`, GitHub artifact ID 11714820810, uploaded 2026-10-11, nominal expires 2026-11-10. The archive was separately downloaded and rehashed, not merely trusted from CI output.
- Wheel `aifordable_runner_mcp-0.1.3-py3-none-any.whl`, 302031 bytes, SHA256 `f3b6513f7dfa1800fab9efbbc001f6e0dbb33ae81b522578f3804c002d62a8b2`; nested artifact ZIP size 296255 bytes, SHA256 `e350215ccd625e82fc8f29f865628031cfbe02833cc7f774019cf301e305e246`.
- Wheel package contains 91 files and `runner_mcp/cli.py`; internal METADATA Name/Version validated; `SOURCE_COMMIT`, `BUILD_INFO.json` and SHA256SUMS all checked against actual wheel contents.
- On a **separate disposable tool container**, Python 3.13.5 isolated venv installed the wheel with `--no-deps --no-index`, verified installed `runner_mcp/cli.py` digest SHA256 `5690884ac7eb896a97203ea1282c4b0e21959ebedb18b8b377fc006f3bcdbe55` equals wheel bytes, and successfully uninstalled it. NOT a full runtime/dependency test, nor Python 3.12 restore; no live machine touched.
- Copy is saved in user's **private persistent Library**, `Backups/Runner-MCP/Recovery-Wheels/runner-mcp-exact-source-a0fd964c-20261011.zip`; independent Library listing matched 296255 bytes. This is off-target documentation/artifact custody but NOT signed, independently recoverable host restore authority. GitHub artifact will expire, Library copy preserved independently.
- PR [#660](https://github.com/Blacksp1d3r/runner-mcp/pull/660) is intentionally **DRAFT NONMERGE**: ephemeral one-off evidence workflow, no runtime code change. Other source/CI PR owners untouched. Exact receipt in [BUILD_RECEIPT.md](BUILD_RECEIPT.md).

## Unmet release/rollback gates

1. Independently attest the ACTIVE server's installed package/loaded Python executable/modules, package origin and exact source generation; `self-update-state.json` is stored commit only, NOT proof of byte identity.
2. Rehearse complete original Python 3.12 dependency protocol/runtime and restart under a qualified disposable guest and external/off-target rollback recovery, not only a venv wheel reinstall.
3. Separate signature/immutable escrow, independent signer/reader, operator-owned physical recovery path with test, user-scoped approval, original client return path and explicit ACK. Neither wheel SHA nor GitHub CI alone can authorize mutation.
4. A6 #942 off-target campaign evidence and A7 #943 independent disconnect rollback remain separate. Source, CI, Claude Q7 NON-RUN need not wait for full A7.
5. No production update, tunnel/service restart, current host disk writes, backup media change or remote Claude call performed.

Next safe task: share receipt to parent #341/#590 and Fabric #942; defer ephemeral workflow merge; qualify active package digest via first-party correct-host collector with private results and full Python 3.12 rehearsal.

## Second independent Python 3.12 build + artifact comparison (2026-10-11)

- GitHub-hosted run [38172776852](https://github.com/Blacksp1d3r/runner-mcp/actions/runs/38172776852) SUCCESS, artifact id `11715250071`, Python 3.12.15 isolated venv wheel installation/compile/uninstall SUCCESS; this is not a running MCP service test and uses no runtime dependencies.
- New downloaded ZIP size `296572` bytes, SHA256 `797a64412a2298de0229f6a2062e79c32d7bf071482914f98103a360ca529ea8`.
- New contained wheel `aifordable_runner_mcp-0.1.3-py3-none-any.whl`, size `302031` bytes, SHA256 `2fe8ed42a51ad9ba351b74f8f651da4d0e89ce36b84cfb97bc70ac207142b5bc`.
- Old wheel SHA256 was `f3b6513f7dfa1800fab9efbbc001f6e0dbb33ae81b522578f3804c002d62a8b2`. The two wheels had EXACTLY the same 91 member paths AND the SHA256 of each uncompressed member was identical; their overall ZIP/wheel byte hashes differ. Thus the source-package payload is stable while binary archive-level reproducibility remains **UNQUALIFIED** (likely wrapper metadata, not proven). Release signing/restoring must PIN the actual selected binary SHA256; do not substitute a differently hashed rebuild merely because version and source match.
- New artifact privately retained separately from previous ZIP at Library `/Backups/Runner-MCP/Recovery-Wheels/runner-mcp-a0fd964c-python312-proof-20261011.zip`; previous artifact untouched. Still no active host loaded-module proof, full dependency restore, immutable signature or original-client ACK.
