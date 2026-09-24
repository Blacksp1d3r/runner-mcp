# Task 25 — private connectivity / TLS onboarding contract review

Date: 2026-09-24

## Scope

Review only. No network exposure, firewall, certificate, tunnel, reverse-proxy or deployment configuration is changed here.

Goal: turn the remaining guided private-tunnel/TLS roadmap item into a concrete infrastructure-neutral contract while preserving Runner MCP's loopback-first security boundary.

## Current implemented behavior

### Setup modes

`runner-mcp setup` currently supports:

- `local`
  - resource URL: `http://127.0.0.1:8000/mcp`
  - auth issuer: `http://127.0.0.1:8000/`
- `public`
  - operator supplies a public MCP URL;
  - non-loopback values must use HTTPS;
  - auth issuer defaults from the supplied HTTPS origin.

Important: setup mode configures the runtime identity/URLs. It does **not** open a firewall, bind the server publicly, install TLS, configure a proxy or create a tunnel.

### Serving

`runner-mcp serve`:

- defaults to `127.0.0.1`;
- refuses non-loopback bind unless `--allow-public-bind` is explicitly supplied;
- tells the operator to prefer a TLS reverse proxy;
- does not trust proxy headers automatically.

Managed autostart always supervises the server on loopback.

### Transport security

The application derives DNS-rebinding protection from the configured MCP resource URL:

- only HTTP(S) absolute URLs are accepted;
- embedded URL credentials are rejected;
- allowed host/origin values are pinned to the configured resource origin.

`doctor` already classifies:
- HTTPS transport as secure;
- localhost/127.0.0.1/::1 HTTP as acceptable loopback transport;
- non-loopback HTTP as unsafe.

### Existing documentation

Current docs already state:

- loopback is the safe default;
- internet-facing use requires HTTPS;
- a reverse proxy is the advanced public path;
- private OpenAI connectivity should prefer Secure MCP Tunnel;
- the tunnel is outbound-only and does not require an inbound Runner MCP port.

Official OpenAI documentation currently confirms Secure MCP Tunnel as an available outbound-only path for supported OpenAI products and private MCP servers.

## Demonstrated documentation drift / ambiguity

### 1. `security/CONNECTIVITY.md` still calls Secure MCP Tunnel a “preferred future connection”

That wording is stale relative to the current documented OpenAI product state and relative to Runner MCP's own README/Quickstart, which already describe it as usable for supported OpenAI products.

This is documentation drift only; no runtime defect is implied.

### 2. “Public mode” can be misread as “Runner MCP opens itself publicly”

The setup wizard's `public` mode only records an HTTPS resource/auth identity. It does not:
- bind to a public interface;
- configure TLS;
- configure DNS;
- configure a reverse proxy;
- modify a firewall;
- install a tunnel.

The Quickstart says the operator must already have an HTTPS endpoint, but the distinction should be stated next to the setup-mode explanation and in the connectivity document.

### 3. Reverse-proxy expectations are underspecified

Because Runner MCP pins allowed Host/Origin values to `RUNNER_MCP_RESOURCE_URL` and does not enable proxy-header trust, a guided reverse-proxy path should explicitly require:

- TLS termination outside Runner MCP;
- forwarding to Runner MCP over loopback/private networking;
- preserving an HTTP Host/origin shape compatible with the configured resource URL;
- no assumption that `X-Forwarded-*` headers will be trusted;
- no direct public bind as the normal guided path.

A proxy-specific vendor configuration should remain outside the core docs unless maintained as a separate example.

## Supported onboarding states

A future guide should present exactly these states.

### State A — local evaluation

Use when the client and Runner MCP are on the same controlled host.

- setup mode: `local`
- Runner MCP bind: loopback
- TLS: not required on loopback
- inbound firewall changes: none

This is the safest default and current five-minute path.

### State B — private tunnel

Preferred when a supported hosted AI product needs to reach a private Runner MCP instance.

- Runner MCP remains loopback/private;
- no inbound Runner MCP firewall port;
- tunnel client runs inside the same trusted network boundary;
- tunnel client initiates outbound HTTPS;
- tunnel credentials remain outside Runner MCP public configuration and output;
- Runner MCP does not install or own the external tunnel client;
- local/private MCP target remains explicit and fixed.

For OpenAI Secure MCP Tunnel, the current official product documentation should be treated as the source of truth for tunnel creation, permissions and client installation rather than copied verbatim into Runner MCP.

### State C — HTTPS reverse proxy

Use when an externally reachable HTTPS MCP endpoint is explicitly required.

- Runner MCP remains loopback/private by default;
- TLS terminates at a separately administered reverse proxy;
- the externally visible resource URL is HTTPS;
- the proxy forwards only the intended MCP/health traffic;
- no credentials are embedded in URLs;
- public DNS/certificates/firewall rules remain operator/infrastructure responsibilities;
- host/origin forwarding must remain compatible with Runner MCP's configured resource URL and DNS-rebinding protection.

### State D — direct non-loopback Runner MCP bind

This remains an advanced escape hatch, not a guided default.

- requires `--allow-public-bind`;
- does not provide TLS by itself;
- must never be presented as sufficient for internet-facing use;
- should not be enabled by setup/autostart automatically.

## Explicit non-goals for Runner MCP onboarding

Runner MCP should not automatically:

- request or renew public certificates;
- edit nginx, Apache, Caddy, Traefik or cloud load balancers;
- create DNS records;
- open firewall/security-group ports;
- install or authenticate third-party tunnel clients;
- store tunnel control-plane API keys in project YAML;
- alter operating-system trust stores;
- enable proxy-header trust globally;
- switch `serve` or autostart to a public bind;
- create a hosted relay/control plane;
- print real hostnames, tunnel IDs, credentials or private URLs in normal status/guide output.

These actions belong to the operator's chosen infrastructure boundary.

## Safe guided-onboarding contract

The smallest useful Runner MCP-owned guidance layer should remain read-only.

It may:

1. identify the configured connectivity category without printing the actual URL/hostname;
2. report one of:
   - `loopback`
   - `https_external_identity`
   - `unsafe_non_loopback_http`
3. explain the two recommended remote paths:
   - private tunnel;
   - external HTTPS reverse proxy;
4. remind the operator that setup does not create network exposure;
5. point to canonical current vendor documentation for an external tunnel product rather than hard-code vendor-specific install commands;
6. keep all examples placeholder-only;
7. direct the operator back to `runner-mcp doctor` after their external infrastructure change.

It must not mutate network state.

## Smallest recommended follow-up

Create one bounded documentation/CLI guidance task:

- reconcile `security/CONNECTIVITY.md`, README and Quickstart so “public mode” and tunnel availability are described consistently;
- remove the stale “future connection” wording;
- extend the existing `runner-mcp guide` output with a generic connectivity section based only on the configured resource URL category;
- never print the configured URL, hostname, port beyond the fixed local default, credentials or tunnel identifiers;
- give generic next steps for private tunnel vs HTTPS reverse proxy;
- preserve `serve` and autostart behavior unchanged;
- add tests proving guide output cannot leak a configured public hostname/resource URL or bearer token.

This is preferable to a new network-mutating `setup-tunnel` command.

## Acceptance criteria for the follow-up

- local config reports a safe loopback category;
- public HTTPS config reports only a generic external-HTTPS category;
- non-loopback HTTP remains a doctor failure and is never recommended;
- guide output contains no configured hostname/resource URL/auth issuer/token/private path;
- docs explicitly state public setup mode does not bind/expose Runner MCP;
- docs preserve outbound-only private-tunnel preference where supported;
- reverse-proxy guidance keeps TLS outside Runner MCP and does not enable proxy-header trust implicitly;
- no network/firewall/certificate/tunnel state is modified;
- no dependency or external service is added.

## Conclusion

No network-runtime change is required to preserve the current security posture.

The roadmap gap is best closed incrementally with a privacy-safe guided connectivity layer plus documentation reconciliation. Direct tunnel/proxy provisioning should remain outside Runner MCP unless a future separately reviewed infrastructure adapter is justified.
