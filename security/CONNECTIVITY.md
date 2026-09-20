# Connectivity and ChatGPT integration

Runner MCP is self-hosted. The preferred architecture is to keep the MCP service private rather than exposing a general remote-control endpoint to the public internet.

## Preferred private architecture

For supported OpenAI products, the preferred future connection is:

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

Runner MCP itself should continue to bind to loopback/private networking unless there is a specific reviewed reason to expose it.

## Transport security

Any external Runner MCP transport must use TLS. Plaintext internet-facing HTTP is prohibited.

Where supported and appropriate, mTLS may be added for control-plane authentication.

Application secrets, database credentials, private paths and bearer credentials must never be placed in public configuration or normal tool output.

## Hosted relay is optional and later

A public one-click service comparable to commercial remote MCP relays would require a separate hosted control plane: account authentication, device pairing, per-user routing, relay capacity, revocation, telemetry policy and abuse controls.

That hosted relay is not required for Runner MCP's self-hosted goal and is not part of the current MVP.

If a hosted mode is ever built, it must be a separate reviewed component rather than weakening the self-hosted security model.
