# Secure I/O inventory and consolidation plan

This is Task 3 from `claude_feedback/CURRENT_ASSIGNMENT.md`: a design/inventory
document, not a refactor. No production code changes are part of this
document. Every writer listed below keeps its current behavior until a
separate, reviewed migration PR changes it — one semantic class at a time,
per the acceptance criteria in the task.

## Why this exists

Private, atomic, permission-restricted file writes (config, job metadata,
replay ledgers, cursors, approval plans, release metadata, credentials) are
implemented independently in at least 14 modules. They are almost all
correct, but they are not identical, and three materially different
durability idioms currently coexist without a written comparison. Before any
consolidation is attempted, this document answers: which write paths exist,
what do they actually guarantee today, which ones are safe to unify, and
which ones must stay specialized.

## The three coexisting idioms

1. **In-place ledger update** — `flock` the file, `seek(0)`, `truncate()`,
   write, `fsync()`. No temp file, no rename. Used by the three append-style
   ledgers: `bridge_replay.py`, `completion_delivery.py`'s delivery ledger,
   and `github_watcher.py`'s cursor store. A crash mid-write leaves a
   truncated/corrupt JSON file; the next reader raises and fails closed. No
   code anywhere repairs a partially-written ledger automatically — that is
   arguably the correct fail-closed behavior for a replay ledger, but it is
   a real operational property worth stating explicitly rather than leaving
   implicit.

2. **Atomic temp-then-rename with `tempfile.mkstemp`** — a randomly-named
   temp file in the same directory (collision- and pre-plant-proof by
   construction), `fsync()`, `os.replace()`, `chmod` before and after. Used
   by `config_manager.py`'s `_atomic_write_private` and
   `approval_manager.py`'s `_write_locked`. This is the strongest general
   "replace a private file's contents" pattern in the codebase.

3. **Atomic temp-then-rename with a fixed/predictable temp name** — same
   shape as (2), but the temp filename is deterministic (`path.with_suffix(
   ".tmp")` or `.{name}.tmp`) rather than random, and several of these skip
   `fsync()`. Used by `completion_delivery.py`'s config writer,
   `autostart.py`'s unit-file writer, and (in code this task does not touch)
   `self_update.py` and `self_update_install.py`.

A fourth, weaker pattern — `Path.write_text()` to a fixed-name temp path,
`chmod`, `os.replace()`, **no `fsync()`, no `O_EXCL`/`O_NOFOLLOW` on the temp
path** — is used for the highest-churn writes in the codebase: per-job
metadata in `test_runner.py` and `deployment_jobs.py` (and, outside this
task's scope, `self_update.py`'s job metadata). These are rewritten on
every job-state transition, so the tradeoff between durability and write
frequency was presumably deliberate, but it is not written down anywhere —
this document is the first place that states it.

Crash-orphan handling is inconsistent everywhere: directories that store
job/config JSON are re-scanned with a `*.json` glob on restart, so a stray
`*.json.tmp` left by a killed process is silently ignored forever — never
cleaned, never surfaced in `runner-mcp doctor`. `config_manager.py` and
`approval_manager.py` use random `mkstemp` suffixes, so a crash-orphaned
temp file is at least collision-proof, but still never swept.
`database_manager.py` can leave an orphaned `.dump` file with no matching
`.json` metadata if the process is killed between a completed dump and the
metadata write; `list_backups()` only globs `*.json`, so that orphan is
invisible and never pruned. None of this is new risk introduced by this
document — it is existing behavior being made explicit for the first time.

Locking granularity also varies by design, not by accident: a single
whole-directory lock guards the entire project registry plus every
project-scoped secret in `config_manager.py` (`.projects.lock`) and the
entire approvals directory in `approval_manager.py` (`.approval.lock`); each
ledger file locks only itself (`bridge_replay`, `completion_delivery`,
`github_watcher`'s cursor); job stores use an in-process `threading.Lock`
only, with no cross-process guarantee; `cron_autostart.py` uses `flock`
purely as a liveness/singleton mutex with no data file behind it at all;
`audit.py` uses only a per-instance `threading.Lock` with no cross-process
guarantee and no `flock`, `O_NOFOLLOW`, or `fsync` — the weakest posture of
any writer in this inventory, worth a standalone look given it is the audit
trail (see **Findings that are not migration candidates** below).

## Full inventory

Columns: create-only vs overwrite; target mode; temp+atomic-replace
strategy; symlink safety; locking; `fsync`; cleanup/orphan behavior.

| Writer (file:line) | Writes | Create/Overwrite | Mode | Temp+replace | Symlink-safe | Locking | fsync | Cleanup |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `onboarding.py:222` `_write_private_file` | env file / `projects.yml` content | Either (`overwrite` flag toggles `O_EXCL`) | 0600 | No — direct `os.open` | No explicit target check; `O_EXCL` covers create-only path | None (single-shot CLI) | Yes | n/a |
| `onboarding.py:242` `install_private_configuration` | private config directories | mkdir idempotent | 0700 | n/a | `is_symlink()` refusal | None | n/a | Rolls back the just-written projects file if the env-file write fails |
| `onboarding.py:399` `enable_operator_stop` | emergency-stop marker | Overwrite | 0600 | No — direct `os.open(O_TRUNC)` | Yes, `O_NOFOLLOW` | None | Yes | n/a |
| `config_manager.py:62` `_configuration_lock` | `.projects.lock` | Create-if-missing | 0600 | n/a | `O_NOFOLLOW` | `flock`, whole-config-dir | n/a | Permanent |
| `config_manager.py:92` `_atomic_write_private` | `projects.yml` / env file content | Overwrite | 0600 | **Yes — `mkstemp`, random suffix** | Yes (mkstemp + target check) | Caller holds `_configuration_lock` | Yes | Unlinks temp on exception; crash leaves untracked random-suffix orphan |
| `config_manager.py:613` `_write_private_environment` | `runner-mcp.env` (DB DSNs, mailbox token) | Overwrite | 0600 | Delegates to above | Delegates | Delegates | Delegates | Delegates |
| `config_manager.py:711/762` `add/remove_database_config` | secret + registry pointer, ordered | Overwrite | 0600 | Delegates | Delegates | One `_configuration_lock` acquisition covers both writes | Delegates | Deliberate ordering: secret written before the pointer on add, pointer disabled before secret deleted on remove |
| `bridge_replay.py:195` `_open_ledger` | opens replay ledger | Create-if-missing | 0600 | n/a | `O_NOFOLLOW` + regular-file check | n/a | n/a | n/a |
| `bridge_replay.py:82/121/292` `claim`/`complete`/`_store` | request replay state | Upsert | 0600 | **No — in-place seek/truncate/write** | Covered by open() | `flock` (EX write / SH read), per-file | Yes | Capacity-bounded (5000), no pruning; crash leaves corrupt JSON, fails closed |
| `completion_delivery.py:145` `_atomic_private_json` | notifier config / bootstrap state | Overwrite | 0600 | Yes — **fixed-name** temp | Target checked; temp not | None | **No** | Orphaned fixed-name `.tmp` never scanned |
| `completion_delivery.py:345/310/390` ledger open/`contains`/`mark_delivered` | delivery dedupe ledger | Upsert | 0600 | **No — in-place** (same as bridge_replay) | Covered by open() | `flock`, per-file | Yes | Capacity-bounded (5000), no pruning |
| `cron_autostart.py:259` `_open_component_lock` | per-component lock file (no content) | Create-if-missing | 0600 | n/a | `O_NOFOLLOW` | `flock`, **liveness mutex only, no data guarded** | n/a | Permanent |
| `database_manager.py:104/151` `__init__`/`_backup_project_dir` | backup directories | mkdir idempotent | 0700 | n/a | `is_symlink()` refusal; path-escape re-check | None | n/a | n/a |
| `database_manager.py:193` `_write_metadata` | backup metadata JSON | **Create-only** (`O_EXCL`) | 0600 | Yes — fixed-name temp, `O_EXCL` | `O_EXCL` + `O_NOFOLLOW` | Caller's per-project `threading.Lock` | Yes | n/a |
| `database_manager.py:216` `_backup_database_locked` | `.dump` file (pg_dump output) | **Create-only** (`O_EXCL`) | 0600 | No temp — the `O_EXCL` file is final | `O_EXCL` + `O_NOFOLLOW` | Per-project `threading.Lock`, in-process only | Yes | **Gap:** a kill between dump success and metadata write leaves an orphaned, invisible `.dump` — no prune logic exists |
| `deployment_jobs.py:88/107` `__init__`/`_persist` | deployment/rollback job metadata | Overwrite/upsert | 0600 | Yes but **weak** — `write_text`, no `O_EXCL` | No explicit check in this function | In-process `RLock` | **No** | Orphaned `*.json.tmp` never cleaned; also the restart-recovery writer (flips stuck jobs to `INTERRUPTED`) |
| `deployment_manager.py:157` `_prepare_release_root` | release-root directory tree | mkdir idempotent, **re-verified on every call** | 0700 | n/a | `is_symlink()` refusal at every level | None | n/a | n/a |
| `deployment_manager.py:233` `_write_metadata` | release metadata | **Create-only** (`O_EXCL`) | 0600 | No temp (fresh dir already unique) | `O_EXCL` + `O_NOFOLLOW` | Caller's per-project lock | Yes | n/a |
| `deployment_manager.py:255` `_activate_release` | `current` symlink | Atomic symlink swap | n/a | **Yes, plus directory fsync — the strongest durability pattern in the codebase** | UUID temp name; refuses non-symlink `current` | Caller's per-project lock | Yes (file **and** directory) | Orphaned `.current-{uuid}` possible but harmless/unreferenced |
| `deployment_manager.py:402` `_create_release` | extracted release tree + metadata | Create-only (`mkdir` fails if exists) | 0700 dir / 0600 metadata | tar members with symlink/hardlink rejected; private temp archive checked and always unlinked | Yes | Caller's per-project lock | Indirect only (metadata fsync) | `shutil.rmtree` on any exception; no fsync of extracted content itself |
| `deployment_manager.py:480` `_update_release_metadata` | patches `migrations_applied` etc. | Overwrite (true read-modify-write) | 0600 | Yes — UUID temp, `"x"` mode | UUID + `"x"` mode | Caller's per-project lock | Yes | n/a |
| `test_runner.py:126/194` `__init__`/`_persist` | test job metadata | Overwrite/upsert | 0600 | Yes but **weak** — same as `deployment_jobs._persist` | No explicit check | In-process `RLock` | **No** | Orphaned `.tmp` never cleaned; also flips stuck jobs to `INTERRUPTED` on restart |
| `test_runner.py:706` `_short_job_tmp` | ephemeral per-job scratch dir | `mkdtemp` (collision-proof) | 0700 | n/a | `is_symlink()` + ownership check post-creation | None | n/a | Removed in `finally`; leaked to `/tmp` only if the process is killed before that runs, and nothing sweeps `/tmp` on restart |
| `test_runner.py:861+` `_run_job` | job work dir + append-only log | Create-only (`exist_ok=False`) | 0700 dir / 0600 log | No — live append stream by design | `touch(exist_ok=False)` is effectively `O_EXCL` | Single owning worker | Flushed per chunk, **no fsync** | Log is permanent, never pruned; content is secret-scrubbed before writing |
| `github_watcher.py:135` `_open` | opens cursor store | Create-if-missing | 0600 | n/a | `O_NOFOLLOW` + regular-file check | n/a | n/a | n/a |
| `github_watcher.py:106/119/191` `initialize`/`advance`/`_store` | fast-forward cursor SHA | Create-only init; compare-and-swap advance | 0600 | **No — in-place** (same idiom as the other ledgers) | Covered by open() | `flock` (EX write / SH read), per-file | Yes | Crash mid-write leaves corrupt JSON, fails closed, requires bootstrap |
| `autostart.py:241` `_write_managed_unit` | systemd unit file text | Overwrite only if existing file carries the managed marker | 0600 | Yes — **fixed-name** temp | Target checked; temp not | None | **No** | Orphaned fixed-name `.tmp` never scanned; marker prevents clobbering a user-authored unit |
| `approval_manager.py:102/113` `__init__`/`_lock` | approvals root + whole-dir lock | mkdir idempotent / create-if-missing | 0700 / 0600 | n/a | `is_symlink()` / `O_NOFOLLOW` | `flock`, whole-approvals-dir | n/a | n/a |
| `approval_manager.py:196` `_write_locked` | approval plan JSON | Overwrite/upsert (state machine) | 0600 | **Yes — `mkstemp`, random suffix** | mkstemp + target check | Caller holds whole-dir lock | Yes | Unlinks temp on exception; random-suffix orphan never swept |
| `audit.py:26` `AuditLogger.append` | audit JSONL, one line per tool call | **Append-only** | 0600 (re-chmod every append) | **No temp/rename at all** | **No** symlink check on the log path itself | In-process `threading.Lock` only, **no cross-process lock** | **No** | Never rotated or pruned; unbounded growth by design |

`self_update.py` and `self_update_install.py` were inventoried for
completeness (8 writer functions: restart markers, job metadata, the
installed-commit record, the install transaction file, per-job wheel
artifacts) but are **owned by the parallel self-update workstream and are
not touched here**. Two gaps were found there worth flagging to that
workstream rather than fixing in this document: `self_update_install.py`'s
`begin_transaction` and `self_update.py`'s `_record_installed_commit` both
use the fixed-name-temp idiom **without `fsync()`**, and the transaction
file in particular is what makes the in-place `pip install` step
crash-recoverable. This is recorded in `handover/AGENT_EXCHANGE.md` as a
handoff note, not fixed here. `github_runtime.py` has no writer of its own;
it only wires together `BridgeReplayLedger` and `GitHubWatcherCursorStore`,
both already itemized above.

## Semantic classes: what can safely share a primitive

**Class A — single-value/ledger stores (safe to unify).**
`bridge_replay.py`, `completion_delivery.py`'s delivery ledger, and
`github_watcher.py`'s cursor store already share an *almost* identical
`_open()` helper (`O_NOFOLLOW` + regular-file check + `fchmod(0600)`) and an
identical write shape (`flock` + `seek(0)` + `truncate()` + write +
`fsync()`, no rename). A shared `PrivateJsonLedger` primitive (open, read,
write-in-place-under-lock) would remove three near-duplicate
implementations with very low behavioral risk, since the three call sites
already agree on every observable property. The one thing a migration must
preserve exactly: fail-closed on corrupt JSON, no auto-repair.

**Class B — general atomic "replace this private file's content" (safe to
unify, and should become the shared primitive).**
`config_manager._atomic_write_private` and `approval_manager._write_locked`
already implement the strongest pattern in the codebase (`mkstemp` random
suffix, `fsync`, `chmod` before and after, `os.replace`). This is the
natural target primitive — e.g. `atomic_write_private(path, data,
mode=0o600)` — that other overwrite-style writers should move *toward*.

**Class C — fixed-name-temp overwrite writers (candidates to migrate to
Class B, not a drop-in merge).**
`completion_delivery._atomic_private_json` and `autostart._write_managed_unit`
use a fixed temp name and skip `fsync`. Moving them onto the Class B
primitive would add `fsync` and randomize the temp name, closing the
(small, same-privilege, low-severity) TOCTOU window between the
`is_symlink()` check and the open. This is a low-risk mechanical migration
once Class B is factored out, but it is still a behavior change (adds an
`fsync` syscall to every call) and should be its own reviewed PR with
before/after timing awareness, not silently bundled into the Class A/B
extraction.

**Class D — high-churn job-metadata writers (candidates to migrate, but only
after an explicit durability decision).**
`test_runner._persist` and `deployment_jobs._persist` use the weakest
overwrite idiom (`write_text`, no `O_EXCL`, no `fsync`) and are called on
*every* job state transition. Before moving these onto Class B, the
maintainer should decide whether per-transition `fsync` is worth its I/O
cost for job-metadata churn — this is a design tradeoff, not a bug, and
this document deliberately does not decide it. If the answer is "yes,
durability wins", the migration is mechanical. If the answer is "no, this
was already an intentional tradeoff", the right outcome is only to add the
`O_EXCL`/`O_NOFOLLOW` temp-path protection that Class B has, without adding
`fsync` — i.e. Class D may end up as a documented, deliberate fourth
primitive rather than folded entirely into Class B.

**Class E — one-shot private-directory/lock-file creators (safe, low-value
dedup).**
Every module's `__init__` creates a 0700 directory with an `is_symlink()`
refusal, and every `flock`-based store opens its lock/ledger file with the
same `O_NOFOLLOW` + regular-file-check + `fchmod(0600)` shape. A small
`ensure_private_dir(path, mode=0o700)` and `open_private_lock(path)` helper
would remove the most repeated-but-lowest-risk code in this inventory
(there is no data-loss risk here — these are idempotent, contentless
creators), so this is good cleanup but not urgent.

**Class F — create-only content writers (must stay distinguishable from
Class B, not merged carelessly).**
`database_manager._write_metadata`, `database_manager`'s dump file,
`deployment_manager._write_metadata` (release metadata), and
`onboarding._write_private_file`'s create-only branch all rely on `O_EXCL`
to guarantee they never silently overwrite an existing file. If a future
Class B primitive gains a generic `mode="create_only"` parameter, these
could route through it — but accidentally defaulting a shared primitive to
"overwrite" and reusing it here would be a real correctness regression
(silently overwriting a dump or release-metadata file). Any migration of
this class must add a regression test that specifically proves the
create-only guarantee survives the migration (see below).

## Findings that are not migration candidates

These should stay specialized rather than being pulled into a shared
primitive, for reasons specific to each:

- **`deployment_manager._activate_release`** — the atomic symlink swap plus
  explicit containing-directory `fsync` is the strongest durability
  guarantee in the codebase. It is a different write shape (a symlink, not
  file bytes) and should be treated as the *reference pattern* other
  primitives could learn from, not something to generalize away.
- **`deployment_manager._create_release`** — a multi-file tar-extraction
  operation with symlink/hardlink member rejection, not a single private
  file write. Stays specialized.
- **`audit.py AuditLogger.append`** — semantically an append-only log, not
  a "replace current value" writer, so it does not belong in the same
  primitive family as the rest of this inventory. It is, however, the
  weakest-postured writer found (no `O_NOFOLLOW` on the log path, no
  cross-process lock, no `fsync`), and it is the audit trail. That is worth
  a standalone look by the maintainer independent of this consolidation
  effort; this document flags it but does not propose a fix, since
  "harden the audit log" is a different, security-relevant decision that
  deserves its own review rather than being a side effect of an I/O
  refactor.
- **`test_runner._short_job_tmp`** — an ephemeral `mkdtemp` scratch
  directory, not a persistent private-config writer. Stays separate.
- **Everything under `self_update.py` / `self_update_install.py`** — owned
  by the parallel self-update workstream. Inventoried above for
  completeness; not a migration candidate from this side, and not to be
  edited here.

## Regression tests required before any migration

None of these exist as shared tests today because none of the candidate
primitives exist yet. Before any call site is migrated (one semantic class
at a time, per the task's own constraint), each new shared primitive needs:

1. **Mode enforcement** — the resulting file/directory has the exact
   expected mode regardless of the process `umask`.
2. **Symlink refusal** — a pre-existing symlink at the target path is
   rejected, never followed or replaced through the symlink.
3. **Create-only vs overwrite** — a create-only call against an existing
   path raises without modifying it; an overwrite call replaces content
   atomically (readers never observe a truncated/partial file).
4. **Concurrent-writer safety** — two threads (and, where the primitive
   claims cross-process safety, two processes) writing through the same
   lock never interleave or corrupt output; the loser waits rather than
   silently losing its write.
5. **Crash simulation** — with `os.replace` (or the final `fsync`)
   monkeypatched to raise partway through, the previously-committed file on
   disk is either unchanged (temp-then-rename primitives) or is corrupt in
   the already-understood, fail-closed way (in-place ledger primitives) —
   never silently truncated-but-treated-as-valid.
6. **fsync invocation** — for any primitive that claims durability,
   `os.fsync` is actually called on the right file descriptor (and, for the
   Class B/`_activate_release`-style primitive, on the containing directory
   too), verified with a spy rather than inferred from the absence of an
   error.
7. **Orphan-temp characterization** — a test that captures today's exact
   orphan behavior (a killed write leaves an untouched temp file that
   nothing sweeps) so that a future decision to add orphan cleanup is a
   deliberate, tested change rather than an accidental side effect of
   swapping the underlying primitive.

Each call-site migration PR must keep that call site's *existing* tests
passing unchanged first (proving the externally observable behavior is
byte-for-byte the same), and only then add primitive-level tests as a
superset. A migration PR that touches more than one semantic class at once,
or that changes durability behavior (adding/removing `fsync`) without an
explicit note in its description, should be treated as out of scope for
"migration" and re-split.

## What this document does not do

It does not introduce `runner_mcp/secure_io.py` or any other new module. It
does not change a single call site. It does not decide the Class D
durability tradeoff. Those are follow-up work for a later, separately
reviewed slice, one semantic class at a time, per the task's own
instruction not to do a mass refactor here.
