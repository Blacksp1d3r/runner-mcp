# Runner MCP Future Lab

Runner MCP is in maintenance mode, but maintenance mode is not idea mode off.

This document is the deliberately experimental counterweight to the stable core. It captures ideas
that may be useful later, including speculative or unconventional ones. Nothing here is a promise,
a roadmap commitment, or justification for weakening the security boundary.

The rule is simple:

> Do not adopt an idea because it is popular. Do not reject an idea because it is unusual.
> Compare alternatives, measure them, attack the assumptions, and keep the one that works best for
> Runner MCP's goals.

## Stable core versus Future Lab

The production/core track remains conservative:

- security fixes;
- correctness bugs;
- compatibility fixes;
- concrete operational requirements;
- protocol conformance needed for supported clients.

Future Lab is allowed to be ambitious:

- prototype outside the stable path;
- benchmark competing designs;
- test ideas that may fail;
- compare standard and non-standard approaches;
- keep experiments isolated from production authority;
- promote an idea only after it has evidence.

An experiment must never silently become new production authority.

## Evaluation method

For every serious experiment, define these before implementation:

1. Hypothesis — what should improve?
2. Baseline — what does Runner MCP do today?
3. Alternatives — include the boring/simple option.
4. Metrics — latency, model round-trips, CPU, memory, I/O, response bytes/tokens, failure rate,
   recovery time and operator effort where relevant.
5. Safety boundary — what new authority or failure mode could this introduce?
6. Reversibility — how easily can the experiment be removed?
7. Promotion rule — what evidence would justify moving it toward the stable core?

Prefer measurements over intuition, but keep room for ideas that cannot initially be reduced to one
metric.

## FL-1 — Performance instrumentation before optimization

Research a privacy-safe timing and cost profile for bounded actions.

Possible measurements:

- total wall-clock time;
- queue wait;
- validation/policy time;
- subprocess or backend time;
- serialization time;
- response bytes and approximate token footprint;
- retries/replays;
- cancellation-to-termination delay;
- per-action success/failure classes.

Constraints:

- no private hostnames, paths, commands, credentials or raw environment values;
- metrics must not become a side channel;
- instrumentation should be cheap enough not to distort the measurement.

Question to answer:

> Where does real user-visible time go: model reasoning, MCP transport, Runner MCP, Fabric, process
> execution, storage, or repeated status polling?

## FL-2 — Operational snapshot / decision bundle

Hypothesis: one decision-oriented read can replace many AI/MCP round-trips.

Prototype a bounded read-only snapshot that can combine only information relevant to one decision,
for example:

- runtime mode and readiness;
- worker/queue summary;
- project health summary;
- active bounded jobs;
- restart/recovery state;
- relevant service health;
- current revision/fingerprint.

Research variants:

- fixed snapshot schema;
- purpose-specific snapshots such as deploy-readiness or test-readiness;
- server-selected fields;
- caller-selected detail level without caller-selected authority.

The snapshot must not become an arbitrary query language.

Primary metric: reduction in model/tool round-trips for the same correct decision.

## FL-3 — Compact response profiles

Research caller-selectable response detail such as:

- summary;
- normal;
- full.

The detail level may reduce output, never expand authority or bypass redaction.

Questions:

- How many tokens can be saved in normal workflows?
- Can summary responses still preserve enough evidence for safe decisions?
- Should large diagnostic detail require an explicit second read rather than being returned by
  default?

## FL-4 — MCP 2026-07-28 conformance laboratory

Track and test the stateless MCP direction rather than assuming the old session model remains the
best architecture.

Research:

- request independence and routing;
- cache hints where semantically safe;
- multi-worker behavior;
- compatibility with current Python MCP SDK releases;
- impact on authentication and request correlation;
- failure behavior when requests land on different server workers;
- which Runner MCP state is truly local and which must become durable/shared before scaling.

Do not rewrite working transport merely to follow fashion. Measure before and after.

## FL-5 — Durable Tasks integration

Long-running Runner MCP actions already have durable job concepts. Research mapping them onto MCP
Tasks when the Python SDK/runtime support is mature enough.

Candidate mappings:

- tests;
- deployment;
- rollback;
- migration;
- self-update;
- Fabric work-units where appropriate.

Key requirement:

> Cancellation must propagate to the actual owned process/job tree, not merely change a task status.

Research restart survival, idempotency, cancellation races, reconnect behavior and task retention.

## FL-6 — General mutation idempotency

Runner MCP already has replay protection for bridge requests using request identity plus a canonical
fingerprint.

Research promoting that principle into a general mutation invariant:

- same operation key + same canonical request -> return/continue the same operation;
- same operation key + different request -> fail closed;
- duplicate delivery must not duplicate a mutation;
- durable state must survive service restart.

Compare file-backed, SQLite and externally shared stores before choosing anything.

This becomes especially important if protocol traffic is stateless or horizontally distributed.

## FL-7 — Safe caching experiments

Do not add caching merely because it is fast.

Candidate cache classes:

- static/capability discovery;
- configuration-derived summaries;
- immutable release metadata;
- expensive read-only health data only where stale reads are demonstrably harmless.

Rules to test:

- mutation-triggered invalidation;
- revision/fingerprint binding;
- explicit freshness metadata;
- never cache authorization decisions across changing policy;
- never let cache state conceal restart/recovery transitions.

A 500 ms cache is not automatically safer than no cache. Benchmark first.

## FL-8 — Adaptive batching

Go beyond a fixed snapshot and research whether Runner MCP/Fabric can combine related safe reads
automatically.

Example:

An AI asks for project readiness, then immediately asks worker state, service health and current
revision. Could the system recognize the decision context and answer from one bounded acquisition?

Possible approaches:

- static bundles;
- Fabric-generated read plans;
- server-side coalescing within a very short window;
- client hints describing intent.

Danger: do not create an unrestricted query planner.

## FL-9 — Capability negotiation

Research whether clients should see only the smallest capability set relevant to the current task
rather than a large global tool catalog.

Possible benefits:

- fewer model tool-selection mistakes;
- fewer tokens;
- clearer authority boundaries;
- easier policy review.

Possible designs:

- project-scoped capability manifest;
- task-scoped capability lease;
- read-only capability discovery;
- Fabric-issued bounded capability context.

Any lease/token must be independently validated; AI text cannot grant itself authority.

## FL-10 — Policy compiler

Moonshot: convert a high-level human policy into a deterministic capability model without making
the AI itself the policy engine.

Example input:

"On staging, tests may run automatically. App service may restart only after green tests.
Production is read-only."

Possible output:

- typed capabilities;
- preconditions;
- approval class;
- exact allowed target classes;
- postconditions;
- rollback requirements.

Research whether a small policy DSL, Python model, Rego/Cedar-like approach, or compiled static
configuration gives the best combination of auditability, speed and simplicity.

Never execute raw natural language as policy.

## FL-11 — Simulation / dry-run execution

Research a first-class simulation mode for mutations.

A simulation could return:

- which capability would run;
- current-state preconditions;
- expected state changes;
- approvals required;
- rollback boundary;
- resources touched as semantic identifiers;
- reasons a real execution would fail.

The simulation must not mutate and must not be presented as proof that real execution will
succeed; state can change between simulation and execution.

Potential use: let an AI reason cheaply before requesting a real mutation.

## FL-12 — Zero-trust task contracts

Moonshot: Fabric sends a bounded desired-outcome contract instead of a long sequence of commands.

A contract could bind:

- work-unit identity;
- expected revision;
- desired end state;
- permitted capabilities;
- resource/time budget;
- deadline;
- validation profile;
- approval class;
- rollback boundary;
- idempotency key.

Runner MCP would still execute only predefined local primitives and independently enforce policy.

Research question:

> Can a higher-level contract reduce dozens of AI round-trips while improving, rather than
> weakening, deterministic control?

This should remain separate from generic "AI decides what commands to run."

## FL-13 — Signed/declarative capability packs

Moonshot: keep Runner MCP as a small trusted micro-kernel while optional packs describe bounded
platform integrations.

Possible future packs:

- Windows/JEA;
- PostgreSQL;
- Podman/Docker;
- Kubernetes;
- Hyper-V;
- VMware;
- storage/NAS;
- observability;
- read-only industrial/OT diagnostics.

Research requirements:

- explicit schema;
- version pinning;
- provenance/signature model if justified;
- no dynamic arbitrary Python import from untrusted projects;
- capability and parameter allow-lists;
- deterministic validation;
- upgrade/rollback compatibility.

First compare this with simply shipping built-in adapters. Extension systems create supply-chain
risk and maintenance cost.

## FL-14 — Windows/JEA adapter

Windows support is a valid future use case even if Linux remains the preferred server platform.

Start by researching Microsoft Just Enough Administration (JEA) and WinRM/PowerShell remoting
rather than shipping a generic PowerShell executor.

Candidate semantic capabilities:

- Windows service status/start/stop/restart;
- IIS site/app-pool status and bounded restart;
- Event Log bounded reads;
- Windows Update status;
- disk/CPU/RAM health;
- Scheduled Task status;
- Hyper-V VM status and explicitly permitted lifecycle actions;
- certificate expiry inspection.

Desired shape:

AI/Fabric -> semantic Runner MCP action -> Windows adapter -> restricted JEA endpoint -> predefined
command/parameter set.

Explicitly forbidden:

- caller-supplied PowerShell;
- generic cmd.exe;
- arbitrary script paths;
- arbitrary WinRM endpoints;
- caller-selected credentials.

Only build this after a real Windows host/use case exists.

## FL-15 — Native helper experiments

Do not assume Python must implement every host-specific primitive forever.

If a real need appears, compare:

- Python;
- OS-native tools behind fixed argv;
- PowerShell JEA;
- a small Rust/Go/C# helper;
- existing audited system APIs.

A native helper must win on evidence: packaging, security, performance or compatibility. The cost
of signing, distribution, updates and vulnerability response counts against it.

## FL-16 — Runner MCP Edge

Long-term experiment, not a current product commitment.

Question:

> At fleet scale, is a tiny local bounded executor more efficient than installing the full current
> runtime everywhere?

Potential Edge properties:

- tiny capability surface;
- outbound-only connectivity;
- device identity;
- signed updates;
- minimal local durable state;
- no orchestration logic;
- Fabric as central planner.

Before building Edge, compare it against:

- ordinary Runner MCP;
- SSH with fixed forced commands;
- JEA/WinRM;
- container/VM-native agents;
- cloud provider management APIs.

Only real fleet requirements should justify the identity, key-management and lifecycle burden.

## FL-17 — Multi-host/fleet experiments

If Runner Fabric reaches hundreds or thousands of hosts, study:

- host capability inventory;
- locality-aware scheduling;
- cold/idle host reuse;
- energy-aware placement;
- queue fairness;
- failure domains;
- update rings/canaries;
- heterogeneous Linux/Windows/architecture fleets.

Runner MCP should remain the bounded local executor; fleet scheduling belongs to Fabric.

## FL-18 — Energy-aware execution

Speculative but potentially valuable for AIfordable-scale infrastructure.

Measure real systems rather than assuming maximum utilization is always most efficient.

Possible signals:

- power draw;
- CPU package power;
- utilization;
- thermal state;
- room temperature where available;
- job duration;
- performance per watt;
- cooling overhead.

Research scheduling to the best energy/performance point rather than simply lowest CPU load or
highest throughput.

Keep physical/environmental telemetry optional and outside Runner MCP's core security boundary.

## FL-19 — Local anomaly detection

Research whether Runner MCP can detect surprising behavior without delegating authority to an AI.

Examples:

- a normally 2-second bounded operation suddenly runs 30 seconds;
- output volume changes dramatically;
- a health endpoint changes pattern;
- restart frequency spikes;
- repeated fail-closed policy violations occur.

Start with deterministic/statistical thresholds. Machine learning is optional and must prove value.

Anomaly detection should alert or reduce authority; it must not invent new mutation authority.

## FL-20 — Automatic safety tightening

Moonshot: the system may automatically become more restrictive under uncertainty.

Examples:

- repeated mismatched idempotency keys -> temporarily reject that mutation class;
- integrity inconsistency -> read-only mode;
- unexpected recovery state -> block overlapping operations;
- anomalous failure burst -> require explicit operator approval.

Runner MCP already follows parts of this philosophy. Future experiments could generalize it while
avoiding self-lockout and preserving operator recovery.

## FL-21 — Differential and fault-injection testing

Build experiments that compare two implementations against the same semantic contract.

Examples:

- old versus new transport;
- cached versus uncached read;
- single-call snapshot versus multi-call workflow;
- file ledger versus SQLite;
- Python adapter versus JEA;
- one-worker versus multi-worker stateless runtime.

Fault injection targets:

- crash between claim and commit;
- lost result;
- duplicate request;
- stale revision;
- backend timeout;
- cancellation during child-process creation;
- partial restart;
- storage full/corrupt;
- clock skew where timestamps matter.

Prefer evidence from failure behavior over happy-path benchmarks.

## FL-22 — Security-performance frontier

Do not treat security and speed as automatic opposites.

For each guard, measure:

- latency cost;
- CPU/I/O cost;
- risk reduction;
- whether the guard can be moved earlier/later;
- whether one stronger coarse validation can replace many repeated weak validations.

Goal:

> Find architectures that are both faster and safer by reducing unnecessary transitions and
> authority, rather than removing checks.

## FL-23 — AI round-trip budget

Introduce an experimental metric: how many model/tool turns are needed to complete a representative
task correctly?

Example benchmark tasks:

- diagnose why a test worker is idle;
- determine staging deploy readiness;
- run tests and interpret completion;
- recover from a failed restart;
- inspect one Fabric work-unit.

A design that saves 5 ms of Python but adds two AI turns is probably slower in practice.

## FL-24 — Cost-aware output and execution

Track not just server compute but end-to-end cost:

- model tokens;
- model calls;
- CPU time;
- network bytes;
- CI/runtime minutes;
- storage writes;
- human approvals/interruptions.

This may reveal counterintuitive trade-offs: a slightly more expensive local operation can be much
cheaper overall if it avoids another model reasoning round.

## FL-25 — Ideas we have not thought of yet

Future Lab must remain open-ended.

Periodically inspect:

- new MCP specifications and SDK behavior;
- real user failure patterns;
- other MCP servers and agent runtimes;
- operating-system security mechanisms;
- distributed-systems research;
- developer tooling;
- CI/CD systems;
- orchestration platforms;
- databases/message buses;
- observability systems;
- techniques outside the MCP ecosystem entirely.

Borrow principles, not dependencies.

A useful idea does not become correct merely because a large project uses it, and an unusual idea
does not become wrong because nobody else uses it yet.

## Promotion into the stable core

An experiment may move toward production only when:

- a concrete use case exists;
- the baseline and alternatives were compared;
- the result is measurably useful or materially safer/simpler;
- the authority change is understood;
- fail-closed behavior is tested;
- rollback/removal is possible;
- public/private configuration boundaries remain clean;
- documentation and tests exist.

Large experiments should normally start in a separate branch, prototype repository, test harness or
Runner Fabric lab path rather than destabilizing Runner MCP main.

## Research backlog order

This order is a starting hypothesis, not doctrine:

1. measurement/instrumentation;
2. operational snapshot and AI round-trip benchmark;
3. compact responses;
4. MCP 2026-07-28 conformance experiments;
5. general mutation idempotency;
6. Tasks integration when SDK support is mature enough;
7. safe caching/adaptive batching;
8. capability negotiation and simulation;
9. zero-trust task contracts;
10. platform experiments such as Windows/JEA;
11. capability packs/native helpers only if justified;
12. Edge/fleet/energy ideas when real scale creates the need.

If evidence says a later idea has more value, reorder it.

## Final principle

Runner MCP should remain small enough to understand and strict enough to trust, while Future Lab is
allowed to ask uncomfortable questions about how it could become radically faster, cheaper, safer
or more useful.

Stability protects what works.

Experimentation discovers what works next.
