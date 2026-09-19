import asyncio

from runner_mcp.server import StaticBearerVerifier


def test_static_bearer_verifier_accepts_only_expected_token() -> None:
    verifier = StaticBearerVerifier("a" * 32, "https://mcp.example.invalid/mcp")

    accepted = asyncio.run(verifier.verify_token("a" * 32))
    rejected = asyncio.run(verifier.verify_token("b" * 32))

    assert accepted is not None
    assert accepted.client_id == "runner-mcp-operator"
    assert rejected is None
