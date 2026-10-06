from __future__ import annotations

from pathlib import Path

import pytest

from runner_mcp.tunnel_topology_heartbeat import (
    DEFAULT_HEARTBEAT_SECONDS,
    run_topology_heartbeat_forever,
    run_topology_heartbeat_once,
)
from runner_mcp.tunnel_topology_refresh import TunnelTopologyRefreshError


def test_once_returns_secret_free_qualified_outcome(tmp_path: Path) -> None:
    outcome = run_topology_heartbeat_once(
        tmp_path,
        refresh=lambda _path: {
            "state": "qualified",
            "reason": "topology_unique_primary",
            "qualified": True,
        },
    )

    assert outcome.public_dict() == {
        "healthy": True,
        "state": "qualified",
        "reason": "topology_unique_primary",
        "qualified": True,
    }


def test_once_converts_refresh_failure_to_safe_unavailable(tmp_path: Path) -> None:
    def fail(_path: Path):
        raise TunnelTopologyRefreshError("private endpoint failed")

    outcome = run_topology_heartbeat_once(tmp_path, refresh=fail)

    assert outcome.public_dict() == {
        "healthy": False,
        "state": "unavailable",
        "reason": "topology_refresh_unavailable",
        "qualified": False,
    }
    assert "private" not in str(outcome.public_dict())


def test_once_fails_closed_on_invalid_refresh_shape(tmp_path: Path) -> None:
    outcome = run_topology_heartbeat_once(
        tmp_path,
        refresh=lambda _path: {
            "state": "qualified",
            "reason": "topology_unique_primary",
            "qualified": "yes",
        },
    )

    assert outcome.public_dict() == {
        "healthy": False,
        "state": "invalid",
        "reason": "topology_refresh_invalid",
        "qualified": False,
    }


def test_forever_retries_after_transient_failure_at_fixed_cadence(
    tmp_path: Path,
) -> None:
    calls: list[int] = []
    sleeps: list[float] = []

    def refresh(_path: Path):
        calls.append(len(calls) + 1)
        if len(calls) == 1:
            raise TunnelTopologyRefreshError("transient")
        return {
            "state": "qualified",
            "reason": "topology_unique_primary",
            "qualified": True,
        }

    def sleep(value: float) -> None:
        sleeps.append(value)
        if len(sleeps) == 2:
            raise KeyboardInterrupt

    with pytest.raises(KeyboardInterrupt):
        run_topology_heartbeat_forever(
            tmp_path,
            refresh=refresh,
            sleep=sleep,
        )

    assert calls == [1, 2]
    assert sleeps == [
        DEFAULT_HEARTBEAT_SECONDS,
        DEFAULT_HEARTBEAT_SECONDS,
    ]


@pytest.mark.parametrize("value", [0, 4.9, 30.1, True])
def test_forever_rejects_unbounded_interval(tmp_path: Path, value) -> None:
    with pytest.raises(ValueError, match="interval"):
        run_topology_heartbeat_forever(
            tmp_path,
            interval_seconds=value,
        )
