# Owner-local pinned Fabric Release metadata access check — #739

This standalone **read-only** Python 3.12+ script checks one fixed prerelease metadata endpoint for the existing Runner-Fabric Q7 source. It does not need the `gh` binary or an installed/new Runner-MCP service. It is **not** the planned bundle importer.

## Run only on the intended authorized private host

Use a short-lived, fine-grained **single-repository Contents:read token** provided privately through an approved GitHub owner authorization route. Never send it to chat, commit it, put it in a shell command/argument, environment variable, Git remote or file. The script refuses arguments and redirected/proxied HTTP; it requires a genuine interactive terminal for `getpass` rather than an echoing stdin fallback.

```sh
python3 scripts/fabric_release_access_probe.py
```

Operator sees only `PASS_METADATA_READ` or a bounded `WAIT_*` reason. A PASS means the exact GitHub Release metadata request returned a minimally consistent 33-asset prerelease record. It does **not** independently verify the signed source/tag ref, publisher, manifest, archive bytes, per-asset digest, customer host identity, rollback, subscription worker, token subject or original-client ACK; **no new service or installation may be started** on this basis.

HTTP 401 and 403 differ: 403 may be access policy or API rate limiting; avoid repeated requests, follow GitHub account policy. A 302/other redirect never forwards the token. All responses are size bounded. The Python runtime cannot guarantee zeroization of a string from process memory; the script exits and does not persist the token.

## Next bounded task

Implement and separately prove an independently pinned 33-asset importer using exact GitHub REST asset IDs, untrusted download/redirect guard, no forwarded Authorization to blob hosts, fixed size/sha256 checks of all bytes, independently trusted BUNDLE.json/COMMIT_SHA/SHA256SUMS/BOOTSTRAP.py/wheel consistency, owner-only atomic custody, fail-closed replay and recovery. Installation remains a distinct explicit host-authorized step. Physical check stays WAIT until authorized owner interaction.
