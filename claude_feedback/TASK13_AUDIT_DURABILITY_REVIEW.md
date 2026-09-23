# Task 13 — append-only audit durability review

Status: review complete; no production code changed in this task.

## Scope reviewed

- `src/runner_mcp/audit.py::AuditLogger.append`
- current unit coverage in `tests/unit/test_audit.py`
- the secure-I/O inventory's comparison with the other persistent writers
- server usage: one `AuditLogger` instance is injected broadly, but the file format itself is an append-only JSONL security/audit trail.

## Threat and failure model

The current writer serializes threads only within one Python `AuditLogger` instance. That is not a file-level ownership guarantee. Two Runner MCP processes, two logger instances in one process, or another legitimate process writing the same configured audit path can append concurrently without a shared lock.

The audit path is opened with Python's normal append mode. A pre-existing symlink is therefore followed. Because the configured audit path is security-sensitive persistent state, a local same-account attacker or an accidentally planted symlink can redirect audit records to another writable target. The subsequent `chmod(self.path, 0o600)` also follows the path and can unexpectedly change the target's permissions.

The parent directory is created with the process umask and is not itself checked for symlink substitution by `AuditLogger`. The review does not recommend broad parent-directory policy changes in the first fix because deployment/config ownership of that directory is a separate compatibility question; it does require refusing a symlink at the audit file itself.

The append is not `fsync`ed. Python context-manager close flushes userspace buffers and closes the descriptor, but successful return from `append()` does not establish crash/power-loss durability. For an audit trail this creates a real semantic gap: a tool action may complete and the process may report success while the corresponding final audit line is not durable after abrupt host failure.

There is no rotation/pruning. That is intentional current behavior and should remain out of the hardening slice: rotation introduces retention, rename, multi-process and reader semantics that are unrelated to making the existing append operation safe.

## Durability and concurrency assessment

Recommended invariant for one successful `append(event)`:

1. create the parent directory as today;
2. open the audit file with `os.open` using `O_WRONLY | O_APPEND | O_CREAT`, mode `0600`, and `O_NOFOLLOW` where supported/required by the project platform;
3. verify the opened descriptor is a regular file and enforce `0600` with `fchmod`;
4. acquire `flock(LOCK_EX)` on that descriptor;
5. encode one complete JSONL record to bytes and write all bytes while the lock is held;
6. `fsync` the descriptor before reporting success;
7. release/close in `finally`.

The existing in-process `threading.Lock` may remain to avoid unnecessary contention among threads sharing one logger, but it must not be treated as the cross-process integrity mechanism. The descriptor-level `flock` is the relevant shared lock.

A single `os.write` should not be assumed to write the entire record. Use a bounded write-all loop or an equivalent helper while holding the lock. `O_APPEND` preserves append positioning; the lock preserves whole-record ordering among cooperating Runner MCP writers.

No temp+rename primitive should be used here. The semantics are append-only, so replacing the file would create new inode/reader/rotation behavior and is the wrong abstraction.

Directory `fsync` is not required on every append to an already-existing audit file. There is a narrower first-create durability question: making the newly-created directory entry durable after a crash may require parent-directory `fsync`. That can be evaluated separately because it changes the syscall profile only on creation and needs a safe directory-open primitive. The minimum hardening slice should at least `fsync` the audit file for every acknowledged event.

## Concrete proof tests

A CODE task should add tests that prove, rather than infer:

1. **Symlink refusal** — make `audit.jsonl` a symlink to a sentinel file; append must fail and sentinel contents/mode must remain unchanged.
2. **Private mode independent of umask/existing mode** — create under a permissive umask and separately start from mode 0644; after append the descriptor target is 0600.
3. **File type refusal** — configured audit path resolving to a non-regular opened object is rejected.
4. **Cross-instance/process serialization** — two independent logger instances (preferably two processes for the `flock` claim) append many uniquely identified records; every line parses as one JSON object, no records interleave, and all expected IDs occur exactly once.
5. **Partial-write handling** — monkeypatch/inject the low-level write to return short writes and prove one complete record is eventually persisted, or fail without claiming success.
6. **fsync before success** — spy on `os.fsync`; one successful append invokes it on the audit descriptor after the write.
7. **fsync failure propagation** — force `fsync` to fail; `append` must raise rather than silently claim a durable audit event.
8. **No semantic expansion** — two sequential appends retain JSONL order and the existing event schema exactly; no rotation, pruning, repair or rewriting of prior lines occurs.

A crash during the write can still leave a final partial line because append-only files cannot atomically append arbitrary-length records across power loss. The correct contract is therefore not “crash can never produce a partial tail”; it is “successful return means fsync completed, concurrent cooperating writers cannot interleave records, and readers/recovery must never treat malformed data as a valid audit event.” Automatic truncation/repair is not proposed here.

## Smallest recommended implementation boundary

One bounded CODE slice:

- `src/runner_mcp/audit.py`: replace the current `Path.open("a")` writer with one private append helper local to this module (or a narrowly named shared append primitive only if another identical append user is demonstrated first).
- `tests/unit/test_audit.py`: preserve all existing tests and add mode/symlink/short-write/fsync tests.
- `tests/security/test_audit.py` (new, if project convention warrants): cross-process/adversarial symlink tests.

Do not touch server call sites, event schema, log location/configuration, rotation, retention, audit readers, self-update writers, or the replace-style secure-I/O families in this slice.

## Decision

A change is warranted. The combination of symlink following, process-local-only locking and no durability barrier is materially weaker than the rest of Runner MCP's persistent security state, and this file is specifically the audit trail. The fix should remain a dedicated append-only hardening task rather than being folded into the Class B replace-file primitive.
