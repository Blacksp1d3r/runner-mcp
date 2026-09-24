# Task 33 — optional graphical administration boundary review

Status: **COMPLETE — review only; no UI/runtime implementation is queued for alpha.**

## Scope

This review asks whether Runner MCP can eventually expose an optional graphical administration surface without weakening its existing local/private configuration, emergency-stop, approval, staging-only and deny-by-default boundaries.

No web UI, hosted relay, browser authentication flow, public bind, mutation authority or external dependency is added by this task.

## Existing safe information that could be rendered graphically

The current CLI already exposes several deliberately bounded summaries that are suitable inputs for a future **read-only** local view, provided a graphical layer consumes the same sanitized domain results rather than parsing terminal text or re-reading private configuration directly.

Safe candidates include:

- package version, safety mode, emergency-stop state and retention-confirmation state;
- bounded retention-policy numbers already shown by `status`;
- project code/display name and project count;
- `doctor` PASS/WARN/FAIL checks and generic details;
- the generic connectivity category from `guide`, never the configured resource URL or hostname;
- project adapter and allow-listed capability summaries;
- configured test-profile names plus bounded timeout/log/runtime/parallel-safe metadata;
- service **aliases** and enabled action categories, never the private systemd unit or health URL;
- database configured/not-configured state, engine category and migration-configured state;
- staging-deployment configured state and already-safe project-facing aliases;
- GitHub mailbox/completion-notifier configured/initialized booleans;
- managed autostart component state using logical component names;
- safe asynchronous job state/results that are already exposed by existing bounded status APIs;
- approval **status/summary** that is already safe to print locally, while approval mutation remains outside the UI.

A future graphical layer must not treat every current CLI line as automatically safe. Some local operator commands intentionally accept or can display values that are private by design. The UI must use an explicit field allow-list.

## Values that must not enter a graphical response

The existing public/private split must remain unchanged. A future UI response must not contain:

- bearer tokens, GitHub tokens, database DSNs or other credentials;
- private filesystem roots, release/backup paths or executable paths;
- private service-unit names or health-check URLs;
- configured external hostnames, resource URLs, auth issuers, tunnel identifiers or proxy details;
- command/argv/environment contents;
- database dump contents or restore object listings;
- approval fingerprints;
- raw exception text, raw process output or unsanitized logs;
- self-update artifact paths or internal recovery material.

The UI must call the same safe summary helpers or dedicated view-model functions. It must not gain generic config-file browsing, filesystem browsing, shell execution, log tailing or arbitrary MCP dispatch.

## Local administration versus remote control plane

The first graphical surface, if ever justified, should be a **separate local operator surface**. It must not be a hosted control plane and must not reuse the GitHub mailbox as a browser backend.

Required separation:

1. The MCP server remains the AI-facing interface with its existing authentication and transport policy.
2. A graphical operator surface is a separate process or explicitly separate application boundary.
3. Its default and supported alpha/post-alpha bind is loopback only.
4. No automatic tunnel, public reverse proxy, DNS or firewall provisioning is introduced.
5. No browser endpoint may become an alternate way to approve, deploy, migrate, roll back, restore, clear emergency stop or execute arbitrary commands.

A future hosted relay would be a different product/security review because it introduces accounts, pairing, revocation, routing, telemetry and abuse controls.

## Browser security requirements for any future local UI

Loopback alone is not a sufficient browser security boundary. A future implementation must assume hostile web pages can attempt requests toward localhost.

Minimum constraints:

- bind only to `127.0.0.1` / `::1` by default and fail closed on any non-loopback bind;
- use an independent admin endpoint/port rather than mounting the UI into the MCP route tree;
- validate `Host` and `Origin` against exact local values and reject unexpected/missing origins on state-changing requests;
- send no permissive CORS headers and never use wildcard origins;
- use browser sessions that are short-lived, unpredictable and scoped to the admin surface only;
- keep authentication material out of URLs, query strings, browser history and rendered HTML;
- set restrictive cookie attributes where applicable and rotate/invalidate the session when the process restarts;
- require anti-CSRF protection on every future state-changing request even if the bind is loopback;
- return restrictive CSP, frame-ancestors/anti-clickjacking and no-sniff headers;
- avoid third-party scripts, fonts, analytics and CDNs so the UI does not create a new data-exfiltration path;
- keep access logging free of secrets/private values;
- never trust proxy headers automatically.

Before any mutation is considered, the UI would also need explicit same-user/operator authentication stronger than mere localhost reachability. That requirement is intentionally deferred because the recommended first slice is read-only.

## Actions that must remain CLI/local typed-confirmation only

The following existing authority boundaries should **not** move into the first graphical surface:

- clearing the emergency stop (`UNLOCK`);
- approving migration/deploy/rollback plans (`APPROVE <prefix>`);
- self-update recovery;
- destructive configuration removal;
- GitHub watcher abandon/quarantine/resolve recovery actions;
- any future database restore execution;
- production mutations;
- any operation that currently depends on an explicit typed confirmation phrase.

The browser must not synthesize, bypass or auto-submit those phrases. Read-only display of safe status does not imply browser authority to change it.

## Potentially safe first graphical scope

If a concrete usability need is demonstrated later, the smallest defensible first slice is a **read-only local dashboard** containing only already-safe summaries:

- overall safety/doctor state;
- configured project cards;
- generic connectivity category;
- test/service/database/deployment configured-state summaries;
- bounded job/queue health and attention indicators.

There should be no forms, buttons that cause operational side effects, editable settings, arbitrary identifiers, filesystem picker, terminal, log console, approval control or remote access.

The implementation should introduce a dedicated typed view model with adversarial tests proving prohibited private fields cannot be serialized. Reusing raw CLI text or complete internal objects should be rejected.

## Alpha decision

The graphical administration feature should remain **deferred for the first alpha**.

Reasoning:

- the existing CLI, `guide`, `status` and `doctor` already provide the required operational onboarding and diagnosis path;
- Task 32/36 established an alpha-candidate documentation/package baseline without a graphical dependency;
- adding a browser surface creates a new origin/session/CSRF/DNS-rebinding threat model and additional validation burden;
- no concrete alpha blocker currently requires graphical administration.

Therefore this review does **not** queue an implementation task. The roadmap should keep graphical administration optional/post-alpha. If real operator feedback later demonstrates the need, start with the read-only local-dashboard slice above and perform a new implementation-specific threat review before writing runtime code.

## Explicit non-goals preserved

This review does not authorize:

- a hosted or remotely reachable control plane;
- a public bind;
- browser-based approval;
- browser-based emergency-stop clearing;
- generic configuration editing;
- shell/terminal access;
- database restore;
- new deployment/migration/rollback authority;
- external analytics or dependencies.
