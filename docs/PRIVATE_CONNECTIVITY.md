# Private connectivity guide

Runner MCP should stay private unless a deployment has a clear reason to expose a public HTTPS MCP endpoint.

This guide separates three different connectivity problems that are easy to confuse:

1. how an AI client sends bounded Runner MCP requests;
2. how a human operator reaches the host for administration;
3. how a public MCP consumer reaches a stable HTTPS endpoint.

Those paths do not need to be the same.

## Recommended order

Use the narrowest path that satisfies the actual client.

| Need | Preferred pattern | Public inbound Runner MCP port required? |
| --- | --- | --- |
| ChatGPT/GitHub-assisted project status and predefined tests | GitHub mailbox bridge | no |
| Supported OpenAI product needs direct private MCP calls | OpenAI Secure MCP Tunnel | no |
| Another remote MCP client requires a normal public MCP URL | Hardened HTTPS reverse proxy | yes, at the proxy boundary |
| Human SSH/host administration | Existing enterprise VPN or private overlay | no public Runner MCP endpoint |

A VPN/overlay that lets a human laptop reach the server does not automatically give a cloud AI product access to the MCP server. Treat operator networking and MCP transport as separate trust boundaries.

## Option A — GitHub mailbox bridge

For routine development work, the GitHub mailbox bridge is the lowest-change remote path already built into Runner MCP.

The chain is:

```text
AI client
  -> private GitHub request mailbox
  -> Runner MCP watcher
  -> loopback Runner MCP
  -> configured project
  -> sanitized GitHub result mailbox
  -> AI client
```

This path keeps the MCP HTTP listener on loopback and requires no inbound firewall rule.

Use it when the supported mailbox actions are sufficient:

- project/status/capability inspection;
- commit-pinned source synchronization;
- predefined test profile discovery/execution;
- queue/worker/job status;
- test cancellation.

Do not widen the mailbox into a generic remote-control channel just to avoid configuring another transport. Migration, deployment, rollback, arbitrary shell, executable paths, environment input and service names remain outside the mailbox allow-list.

See [GITHUB_MAILBOX_BRIDGE.md](GITHUB_MAILBOX_BRIDGE.md).

## Option B — OpenAI Secure MCP Tunnel

For supported OpenAI products that need a normal MCP connection to a private Runner MCP instance, OpenAI documents Secure MCP Tunnel as an outbound-only path.

Current OpenAI documentation:

- https://developers.openai.com/api/docs/guides/secure-mcp-tunnels

The important deployment boundary for Runner MCP is simple:

```text
supported OpenAI product
        |
        | OpenAI-managed tunnel transport
        v
tunnel-client inside your trust boundary
        |
        | local/private reachability
        v
Runner MCP on loopback/private networking
```

The private Runner MCP server does not need a public listener. The tunnel client runs where it can already reach Runner MCP and initiates outbound HTTPS to the tunnel service.

### Runner MCP side

Keep the Runner MCP resource URL private/loopback whenever the tunnel client runs on the same host or can reach it privately.

Before adding a tunnel, verify:

```bash
runner-mcp doctor
runner-mcp status
runner-mcp emergency-stop status
```

Start/supervise Runner MCP using the managed autostart path:

```bash
runner-mcp autostart install
runner-mcp autostart status
```

The tunnel identity, API credential and tunnel-client profile are private deployment state. Do not place them in this public repository or in Runner MCP project configuration.

Follow the current OpenAI tunnel documentation for creating the tunnel and for installing/configuring the current tunnel-client release. Do not hard-code a historical tunnel-client download URL into a long-lived runbook.

### What Runner MCP does not automate here

Runner MCP deliberately does not create an OpenAI Platform tunnel, request workspace permissions, store an OpenAI API key, or manage the tunnel-client lifecycle.

Those are separate platform/host-administration actions. Keeping them outside the MCP execution boundary avoids turning Runner MCP into its own privilege/bootstrap channel.

## Option C — HTTPS reverse proxy

Use a public HTTPS reverse proxy only when a client truly requires a publicly reachable MCP URL.

Preferred topology:

```text
remote MCP client
      |
      | HTTPS
      v
hardened reverse proxy
      |
      | loopback/private
      v
Runner MCP
```

The proxy should terminate TLS and forward only the required Runner MCP endpoint. Keep firewall exposure minimal.

Runner MCP's safe server default is loopback. A non-loopback bind requires an explicit local `--allow-public-bind` override; that override is not permission to expose plain HTTP to the internet.

At minimum:

- use a valid TLS certificate;
- preserve the configured MCP resource URL and authentication issuer consistently;
- keep Runner MCP bearer credentials private;
- do not put tokens in URLs;
- disable unnecessary proxy endpoints/features;
- restrict accepted hostnames;
- keep request/body/time limits bounded;
- do not expose local admin/debug interfaces;
- verify `runner-mcp doctor` after changing the configured resource URL.

Real domains, addresses, ports, certificate paths and proxy service names belong only in private deployment configuration.

## Option D — operator VPN/private overlay

A corporate VPN, site-to-site route or private overlay can be useful for SSH and host administration.

That solves a different problem from cloud MCP connectivity.

For example, a laptop may be able to SSH to a private server address from one office but not another because only one network has a route/VPN to the server. That does not imply a Runner MCP failure, and it is not a reason to open SSH or MCP directly to the public internet.

Prefer reproducing an existing secure private route or adding an approved private overlay rather than forwarding SSH/MCP ports through a consumer router.

## Preflight checklist

Before changing connectivity:

- Runner MCP is installed under the intended non-root service account;
- `runner-mcp doctor` has no failures;
- the emergency stop is available and inactive;
- autostart/supervision is stable;
- GitHub mailbox replay/cursor state is healthy if the mailbox is used;
- private credentials are not present in the repository;
- the desired client actually needs a direct MCP connection rather than the mailbox;
- there is a rollback path to the current working transport.

After changing connectivity:

- verify local `/healthz`;
- verify MCP authentication still rejects unauthenticated requests;
- verify the client can discover only the expected Runner MCP tools;
- verify no private paths/credentials appear in client-visible output;
- verify emergency-stop behavior;
- keep the old working transport until the new path is proven, then remove obsolete duplicate supervisors/routes deliberately.

## Public repository rule

Never paste real deployment values into issues, examples, screenshots or documentation.

Keep private:

- hostnames and internal domains;
- IP addresses and real ports;
- usernames;
- absolute host paths;
- service identifiers;
- tunnel IDs;
- API/bearer tokens;
- certificate/key paths;
- reverse-proxy installation details;
- database endpoints or credentials.

The public repository should contain only generic architecture, placeholders and reproducible safety tests.
