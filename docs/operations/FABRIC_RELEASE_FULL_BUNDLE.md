# Q7 33-asset offline consistency — unprivileged source helper

`check_complete_q7_bundle(admission, independently_held, asset_bodies)` is read-only in-memory verification only. It first compares GitHub metadata to a separately acquired exact 33-file roster and then requires exactly 33 Python `bytes` values with independently pinned names, lengths and SHA256 hashes; rejects total over 256 MiB and item over 64 MiB. It does not fetch, stage, write, execute, install, enroll or send anything.

Checks exact `COMMIT_SHA` source, valid Q7 `BUNDLE.json` schema and bootstrap SHA, the project wheel and `wheelCount=29`, and `SHA256SUMS` lines for exactly the 29 wheels plus `BOOTSTRAP.py`. Malformed/truncated/oversized JSON and duplicate keys/names fail closed with a constant category.

This function deliberately does NOT authenticate the publisher/signature, verify wheel ZIP/METADATA or dependencies, prove source provenance, pin trusted key expiry/revocation, ensure storage durability/sealing, or qualify running host/Agent Bus/caller ACK. A matching all-in-memory bundle is still **not** ready for physical import or activation. Future importer needs independent authority, filesystem race/hardlink controls, atomic fsync receipts, protected rollback and explicit separate operator approval.
