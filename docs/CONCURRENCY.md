# Controlled concurrency

Runner MCP uses bounded concurrency so one long-running test does not globally block unrelated projects or short status requests.

The design goal is controlled parallelism, not maximum throughput.

## Architecture

Conceptually:

```text
AI client
    |
    v
strict mailbox transport
    |
    v
bounded mailbox workers
    |
    +--> read-only/status request --> immediate bounded execution
    |
    +--> run_tests --> durable queued job ID
                         |
                         v
                 fair project scheduler
                         |
                         v
                 bounded test workers
                         |
                         v
                    safe results
```

Request acceptance and test execution are separate. A valid `run_tests` request starts only a predefined allow-listed test profile and returns a job ID without waiting for the suite to finish.

No concurrency feature accepts shell commands, executable paths, environment variables, service-unit names, internal paths or arbitrary MCP tool names from mailbox requests.

## Safe defaults

The defaults are intentionally conservative:

- mailbox request workers: 4;
- global concurrent test workers: 2;
- maximum queued test jobs: 64;
- per-project `max_parallel_tests`: 1;
- test-profile `parallel_safe`: false.

With these defaults, different projects can use the global worker pool in parallel, but tests inside the same project remain serialized.

A project can opt in to more parallel tests only by increasing `max_parallel_tests`. Each profile that may overlap must also set `parallel_safe: true`. If either side is not explicitly enabled, the project remains locked for that test.

The global test-worker setting is private runtime configuration. Queue capacity is also bounded. Capacity exhaustion fails closed instead of silently dropping work.

## Job lifecycle

Test jobs expose these normal states:

- `queued`;
- `claimed`;
- `running`;
- `passed`;
- `failed`;
- `cancelled`;
- `timed_out`.

Additional fail-closed operational states can be reported when required, such as an external operator stop, an execution error or an interrupted process after restart.

A queued job is persisted before execution. After restart, still-queued work may be scheduled again. A previously claimed or running job is not blindly replayed; it is marked interrupted so an uncertain action is never silently executed twice.

## Fair scheduling

The test scheduler maintains logical queues by project.

When a worker becomes available, it considers the oldest runnable job for each project and selects fairly between projects using round-robin dispatch history. This prevents one project with a large backlog from continuously taking every free worker.

Within a project:

- the default capacity is one test;
- non-`parallel_safe` profiles act as a project test lock;
- explicit parallel-safe profiles may overlap only up to the project's `max_parallel_tests` limit.

Queued jobs expose a bounded waiting reason such as:

- `global_worker_capacity`;
- `project_parallel_limit`;
- `project_lock`;
- `scheduler_fairness`;
- `project_unavailable`.

These labels reveal scheduling state only, not server paths, process names or infrastructure details.

## Safe observability

Runner MCP exposes safe capacity/status tools:

- `queue_status`;
- `worker_status`;
- `job_status`;
- `cancel_job`.

`queue_status` can report:

- queued, claimed and running counts;
- available workers and the global concurrency limit;
- queue capacity;
- oldest queued age;
- bounded waiting-reason counts;
- counts per configured project;
- each project's `max_parallel_tests`;
- whether a project test lock is active.

`worker_status` reports logical worker capacity only. It deliberately does not expose hostnames, process identifiers, service names or filesystem locations.

`job_status` and `cancel_job` accept only a validated Runner MCP job identifier.

## Mailbox concurrency

The GitHub mailbox remains a transport layer, not a global execution lock.

A watcher cycle can process multiple independent requests with a bounded worker pool. Long test execution does not occupy a mailbox worker because `run_tests` returns immediately after the job is accepted.

GitHub result-branch writes are kept in a short serialized critical section. This prevents concurrent Contents API updates from racing on the same branch while leaving request validation and Runner MCP execution parallel.

Malformed or recovery-required requests prevent cursor advancement, but they do not stop other independent requests in the same discovered batch from being processed. Replay protection ensures that successfully handled requests are not executed again during later reconciliation.

## Scaling capacity

Capacity can be increased later without changing the mailbox protocol.

The main controls are:

1. increase the global Runner MCP test-worker limit when CPU, memory and I/O capacity allow it;
2. increase the watcher worker count when request acceptance itself needs more throughput;
3. raise `max_parallel_tests` only for projects with isolated test environments;
4. mark only proven independent test profiles as `parallel_safe`;
5. add additional execution hosts later behind the same job/request contract rather than changing what the client sends.

Increasing a limit does not weaken validation or add new executable authority.

## Runner MCP versus GitHub Actions

Use Runner MCP test profiles for interactive development validation when:

- an AI client needs a quick job ID and later status;
- tests are already available in a trusted local checkout;
- several projects need to share bounded local capacity fairly;
- repeated development checks would otherwise create a second long CI queue;
- the command can be represented as a fixed allow-listed profile.

Keep GitHub Actions for repository-governance work when:

- a pull request or protected branch requires an independent merge check;
- the result should be part of GitHub's native checks/status history;
- a clean hosted environment is important;
- release, packaging or multi-version/multi-platform matrix validation is needed;
- the workflow does not require private privileged infrastructure.

Avoid automatically duplicating every development test in both systems. A useful pattern is:

- Runner MCP for fast iterative lint/unit/integration profiles during development;
- GitHub Actions for final PR/merge gates and clean-environment verification.

A self-hosted Actions workflow remains separately capacity-bound by the number of eligible Actions runners. Runner MCP concurrency does not make an unavailable GitHub Actions runner available, so self-hosted workflow capacity should be managed independently or the workload should be moved to an allow-listed Runner MCP test profile when it is development validation rather than a repository gate.

## Operations that remain excluded

Mailbox concurrency does not authorize migration, deployment, rollback, database restore, arbitrary service control or arbitrary commands.

Higher-risk operations retain their existing approval and safety boundaries. They are not automatically placed into the parallel mailbox scheduler merely because test execution is concurrent.
