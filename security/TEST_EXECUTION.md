# Controlled test execution

Phase 3 executes only named test profiles from private project configuration.

## Security properties

- the MCP client selects only a project and profile name;
- the executable and arguments are fixed in server-side configuration;
- the executable must use an absolute path;
- subprocesses are started with `shell=False`;
- test working directories must remain inside the configured project root;
- dangerous process-control environment variables are blocked from passthrough;
- each job gets an isolated HOME and temporary directory;
- stdin is disconnected;
- stdout and stderr are combined into a bounded scrubbed job log;
- configured environment values and private paths are redacted from logs;
- one test job per project may be active at a time;
- global concurrency is bounded;
- every profile has a timeout and log-size limit;
- cancel requests and the external operator stop terminate the process group;
- unfinished jobs are marked interrupted after a Runner MCP restart;
- job metadata and logs use restrictive filesystem permissions.

## Trust boundary

Running a test suite executes project code.

In the current implementation, the child process runs with the operating-system identity of Runner MCP. A malicious test can therefore attempt any action available to that Linux account.

Until stronger execution isolation is deployed:

- run only trusted repository revisions;
- never automatically run code from unknown public forks;
- keep the Runner MCP Linux account least-privileged;
- do not give that account broad access to secrets or unrelated project data;
- do not reuse a privileged GitHub Actions runner identity for untrusted pull-request code.

## Future isolation

Before Runner MCP is allowed to test untrusted revisions, add an execution boundary such as:

- a dedicated test-only Linux user with narrower permissions;
- a disposable container or namespace;
- read-only source mounts where practical;
- CPU, memory, process-count and disk quotas;
- network restrictions where the test profile does not require external access;
- no access to operator credentials, deployment credentials or backup stores.

A fixed command profile is not a substitute for sandboxing untrusted code.

## Stop behavior

If the operator emergency stop becomes active while a test is running:

1. no new test jobs are accepted;
2. the running process group receives a graceful termination signal;
3. after a short grace period, remaining processes are force-killed;
4. the job is recorded as stopped;
5. scrubbed output produced before termination remains available for diagnosis.

Cancel requests use the same process-group cleanup but are recorded separately as cancelled.
