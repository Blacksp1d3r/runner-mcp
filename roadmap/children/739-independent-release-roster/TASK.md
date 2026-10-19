# #739 — independently held exact Q7 33-asset roster comparison

Purpose: prior #743 fixed GitHub metadata access and #745 fixed asset bytes verifier do NOT establish trust in a GitHub-supplied digest. This bounded source child compares every exact Release asset ID, filename, size and SHA256 against a distinct operator-trusted immutable roster. The trusted roster is an input, NEVER populated by the same untrusted GitHub metadata or signed by the process itself.

Acceptance: fixed commit/tag/release ID plus exactly 33 distinct safe assets (four required manifests, one runner_fabric wheel and 28 dependency wheels for Q7); fail closed on mismatches, malformed/unhashable fields, bool-as-int, duplicates, bad types/digests and bounds. Pure and no network, paths, tokens, signatures, downloads, files, side effects or host powers.

`match_only` deliberately leaves `trusted_signer_verified=false`, `download_performed=false`, `mutation_authorized=false`, `original_client_ack=false`. Real independently verified signature/key custody, manifest payload chain, total 33/33 bytes and atomic local import remain separate work.
