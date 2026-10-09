# Control-plane authentication evidence freshness (issue #599)

This guard interprets the tunnel-client's **loopback-only**, read-only control-plane
health. A historical nonempty `details.last_success` is not current authentication
evidence.

## Source and bounded policy

The official tunnel-client configuration documents a default control-plane
long-poll wait of **30 seconds** and default deadline guardrail of **5 seconds**:
https://github.com/openai/tunnel-client/blob/master/docs/configuration.md

Runner-MCP requires the reported last successful poll to be a timezone-aware,
strict RFC3339 timestamp. It accepts no older than **90 seconds** (three nominal
default poll windows) and a maximum **5 seconds** of future clock skew against
the authorized host clock. Invalid, old, far-future, naive or overlong values
return **false**, not a successful authentication claim. Status `ok` and one of
`idle/polling/backpressured` remain prerequisites.

These values are a conservative **default-poll policy**, *not* a measurement of
the current tunnel-client process. Custom `CONTROL_PLANE_POLL_TIMEOUT` or
slow/backpressured operation can legitimately go longer than 90 seconds,
yielding **unknown/unproven authentication evidence**, not proof of an outage.
Do not increase the bound from public caller input or automatically restart
the tunnel when this check is false. Operator-owned source and configured
cadence must be reconciled separately for any future alternative policy.

Tests use an injected clock and synthetic loopback responses. They do not
change tunnel processes or perform real network authentication, credential
rotation or production diagnostics. The external ChatGPT connector remains
a separate qualification gate (#590).

## Regression expectations

- fresh within policy: accepted only if status and state gates hold;
- exactly 90 seconds ago: accepted; 91 seconds ago: rejected;
- 5 seconds future skew: tolerated; more than 5: rejected;
- malformed/empty/naive/invalid RFC3339: rejected;
- degraded/stopped/unknown statuses: rejected regardless of old success;
- operator must not infer remote routability from a successful poll alone.

