# Connectivity and ChatGPT integration

Runner MCP is self-hosted. The preferred architecture is to keep the MCP service private rather than exposing a general remote-control endpoint to the public internet.

## Preferred private architecture

For supported OpenAI products, the preferred private connection is OpenAI Secure MCP Tunnel:

```text
ChatGPT / OpenAI product
        |
OpenAI Secure MCP Tunnel service
        |
HTTPS outbound connection
        |
tunnel-client inside the controlled network
        |
Runner MCP on loopback/private network
        |
allow-listed projects and staging services
```

This model requires no inbound firewall port for Runner MCP. The tunnel client initiates the outbound HTTPS connection.

See the current [OpenAI Secure MCP Tunnel documentation](https://developers.openai.com/api/docs/guides/secure-mcp-tunnels) for tunnel creation, permissions and client operation. Runner MCP intentionally does not copy vendor-specific credentials or provisioning commands into its own setup flow.

Runner MCP itself should continue to bind to loopback/private networking unless there is a specific reviewed reason to expose it.

## What Runner MCP setup does — and does not do

The setup wizard has two identity modes:

- `local` records a loopback MCP resource/auth identity for same-host evaluation;
- `public` records an operator-supplied external HTTPS resource/auth identity.

The word `public` describes the configured external identity only. It does **not** make Runner MCP publicly reachable. Setup does not change the bind address, install or terminate TLS, create DNS records, edit a firewall/security group, configure a reverse proxy, or create/authenticate a tunnel.

Managed autostart continues to launch Runner MCP on loopback. Direct non-loopback `serve` remains an explicit advanced override and does not provide TLS by itself.

For remote connectivity, prefer one of two architectures:

1. **Private tunnel:** keep Runner MCP on loopback/private networking and let a supported tunnel client establish outbound HTTPS from the trusted network.
2. **External HTTPS reverse proxy:** keep Runner MCP on loopback/private networking and terminate TLS in separately administered infrastructure. The proxy must preserve host/origin behavior compatible with the configured resource URL. Runner MCP does not automatically trust proxy headers.

After changing external connectivity, run `runner-mcp doctor` again. `runner-mcp guide` reports only a generic connectivity category and never prints the configured external hostname, resource URL, auth issuer, bearer token or tunnel identifier.

## Transport security

Any external Runner MCP transport must use TLS. Plaintext internet-facing HTTP is prohibited.

Where supported and appropriate, mTLS may be added for control-plane authentication.

Application secrets, database credentials, private paths and bearer credentials must never be placed in public configuration or normal tool output.

## Hosted relay is optional and later

A public one-click service comparable to commercial remote MCP relays would require a separate hosted control plane: account authentication, device pairing, per-user routing, relay capacity, revocation, telemetry policy and abuse controls.

That hosted relay is not required for Runner MCP's self-hosted goal and is not part of the current MVP.

If a hosted mode is ever built, it must be a separate reviewed component rather than weakening the self-hosted security model.
