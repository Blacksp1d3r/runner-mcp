# Task 14 — secure-I/O migration candidate selection

Status: review complete; no production code changed in this task.

## Recommendation

The next coherent non-self-update migration should be **Class B extraction plus one Class C caller: completion-delivery private JSON state**.

Do not start with the high-churn job stores and do not combine autostart in the same implementation PR.

### Shared primitive source candidates

Existing strongest equivalent implementations:

- `src/runner_mcp/config_manager.py::_atomic_write_private`
- `src/runner_mcp/approval_manager.py::ApprovalManager._write_locked`

They already agree on the essential replace-file semantics: random same-directory `mkstemp`, mode 0600, write+flush+`fsync`, atomic `os.replace`, target mode tightening, cleanup on ordinary exceptions.

The bounded extraction should introduce a small private-file replace primitive (for example in `runner_mcp/secure_io.py`) whose contract is explicitly **overwrite/replace**, not create-only.

The first migrated weaker caller should be:

- `src/runner_mcp/completion_delivery.py::_atomic_private_json`

It currently uses a predictable fixed `.{name}.tmp`, `Path.write_bytes`, no exclusive temp creation and no `fsync`. Its external semantics are already “replace this bounded private JSON state”, so it is the cleanest proof that the extracted Class B primitive works for a real caller.

## Why not autostart in the same slice

`src/runner_mcp/autostart.py::_write_managed_unit` has the same weak fixed-temp mechanics, but it also carries a separate semantic guard: an existing unit may be overwritten only when its content begins with the Runner MCP managed marker. That inspection-before-replace policy is important and has a TOCTOU surface distinct from generic private-file replacement.

Autostart is a good **second** Class C migration after the primitive has landed, with tests focused on preserving the managed-marker refusal. Combining it with completion delivery would make one PR responsible for two policy domains (secret-bearing private state and systemd unit ownership) without a dependency reason.

## Semantics that must be preserved

### Shared replace primitive

- overwrite semantics only; it must not silently become a create-only API;
- same-directory temporary file so `os.replace` remains atomic on the same filesystem;
- random/exclusive temp creation;
- exact final mode 0600 independent of umask;
- reject a pre-existing symlink target rather than following it;
- flush and `fsync` the temp content before replace;
- remove ordinary exception temp artifacts;
- raise a bounded caller-owned error rather than exposing private path data.

A directory fsync is a desirable durability strengthening but is a separately visible syscall/guarantee. If introduced in the extraction, state it explicitly and test it. Do not accidentally claim directory durability if only the temp file is fsynced.

### config_manager

- caller continues to hold the whole configuration lock;
- registry/environment ordering remains unchanged;
- ConfigManagerError mapping remains bounded;
- no change to YAML serialization or validation.

### approval_manager

- caller continues to hold the whole approvals-directory lock;
- approval state-machine ordering remains unchanged;
- newline and JSON canonicalization remain unchanged;
- ApprovalError behavior remains bounded.

### completion_delivery

- size limit is checked before any persistent replacement;
- exact JSON canonicalization and `allow_nan=False` remain;
- parent creation behavior remains;
- final file remains 0600;
- loader's strict schema/size/mode checks remain unchanged;
- no notifier token or path can enter an exception/log message.

## Migration hazards

1. **Create-only confusion.** Database/release metadata writers depend on `O_EXCL`; they must not be routed through an overwrite primitive.
2. **Lock ownership.** The primitive should not invent a global lock. Config/approval already provide higher-level transactional locks; completion config currently has no cross-process transaction spanning multiple files.
3. **Error taxonomy leakage.** A low-level helper should expose a small typed error or let callers translate it; raw `OSError` text can contain paths.
4. **Temp cleanup behavior.** Random `mkstemp` changes the name of crash-orphaned temp files. Ordinary-exception cleanup should be guaranteed; crash-orphan sweeping is not part of this migration.
5. **fsync cost.** Completion configuration/bootstrap writes are low-frequency enough that adding file fsync is appropriate. This reasoning does not transfer automatically to high-churn job metadata.
6. **Symlink race.** A pre-check alone is not a complete hostile-directory guarantee. The primitive's temp file is safe because `mkstemp` creates it exclusively. The target check protects the explicit “do not replace a symlink entry” policy, but full parent-directory adversarial ownership is outside this bounded slice.
7. **Exception cleanup after replace.** Cleanup must tolerate the temp path no longer existing after successful replace.

## Regression matrix for the first CODE slice

Primitive-level:

- permissive umask still yields mode 0600;
- existing symlink target is refused and its referent remains unchanged;
- existing regular target is atomically replaced;
- random temp creation cannot be pre-planted with a predictable name;
- write/flush/fsync failure leaves previous target content intact;
- replace failure leaves previous target intact and cleans the temp on ordinary exception;
- `fsync` is observed before `os.replace`;
- two independent writes never expose a truncated target to a reader (bounded concurrency test).

Existing strong callers:

- config-manager current tests remain unchanged/green;
- approval-manager current tests remain unchanged/green;
- add focused assertions only where extraction otherwise loses proof of mode/symlink/error mapping.

Completion-delivery caller:

- current notifier config round-trip stays byte/schema compatible;
- broad-permission rejection remains;
- oversize/unsafe values still fail before replacement;
- symlink target test proves referent content/mode unchanged;
- injected fsync/replace failure maps to `CompletionDeliveryError` without path/token leakage;
- no predictable `.<name>.tmp` contract is relied on by tests.

## Suggested bounded CODE task

1. Extract the proven Class B mechanics from config/approval into one internal secure-I/O overwrite primitive.
2. Migrate **config_manager and approval_manager** to that primitive without changing their higher-level locking or serialization.
3. Migrate **completion_delivery._atomic_private_json** as the first Class C hardening caller.
4. Add primitive security tests and completion-delivery adversarial tests.
5. Stop. Do not touch autostart, job metadata, ledgers, create-only writers, deployment activation, tar extraction or self-update.

A separate follow-up can migrate `autostart._write_managed_unit` once the primitive is established and can preserve the managed-marker ownership policy explicitly.
