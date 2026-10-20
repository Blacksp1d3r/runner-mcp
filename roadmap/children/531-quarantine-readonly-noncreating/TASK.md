# #531 — no synthetic quarantine file created by read-only inspect

Existing `RecoveryQuarantineLedger.inspect(request_id)` must be genuinely noncreating: if owner-private ledger file does not exist, return None without touching filesystem state. Retain fixed absolute path restriction, owner/mode/no-follow checks, shared nonblocking? (existing flock semantics remain), canonical record validation and denial of unsafe parent. Do NOT change the bounded writer lifecycle or claim crash-atomic authority, which remains #615.

Synthetic tests: first inspect absent -> no file; repeat inspect still absent; later first legitimate record_failure -> file; inspect returns exact record; unsafe parent denies and creates nothing. No watcher cursor advancement, Agent Bus relay, service restart or operator approval. Parent #531 remains OPEN until crash-atomic #615, safe cursor #616 and authorized replay #617 qualify.
