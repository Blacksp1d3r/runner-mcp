"""Regression for read-only diagnostics that must fail closed (#669/#341)."""

from __future__ import annotations

import pytest

from runner_mcp.bounded_status_read import bounded_status_object


def test_normal_categorical_status_is_preserved() -> None:
    observation = {"state": "wait", "self_update_ready": False}
    assert bounded_status_object(lambda: observation) is observation


@pytest.mark.parametrize(
    "error_type",
    [OSError, RuntimeError, ValueError, TypeError, AttributeError, KeyError],
)
def test_private_status_reader_error_is_not_leaked(error_type: type[Exception]) -> None:
    def unreadable() -> object:
        raise error_type("/private/secret token=DO-NOT-LEAK")

    assert bounded_status_object(unreadable) is None


@pytest.mark.parametrize(
    "bad", [None, "healthy", 1, True, ["healthy"], {"wait": True}]
)
def test_only_exact_status_dict_is_accepted(bad: object) -> None:
    if type(bad) is dict:
        assert bounded_status_object(lambda: bad) is bad
    else:
        assert bounded_status_object(lambda: bad) is None


def test_dict_subclass_cannot_override_status_semantics() -> None:
    class ForgedDict(dict):
        def get(self, key, default=None):
            return True

    assert bounded_status_object(lambda: ForgedDict(state="healthy")) is None


def test_normal_wait_remains_wait_without_upgrade_permission() -> None:
    result = bounded_status_object(
        lambda: {"state": "wait", "active_build_provenance_verified": False}
    )
    assert result is not None
    assert result["state"] == "wait"
    assert result["active_build_provenance_verified"] is False
