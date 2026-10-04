from dataclasses import dataclass

import pytest

from runner_mcp.ci_runner_guest_enrollment import (
    CIRunnerGuestEnrollmentError,
    CIRunnerGuestEnrollmentManager,
    CIRunnerGuestSpec,
    CIRunnerGuestTransportResult,
    CIRunnerRegistrationSecret,
)


@dataclass(frozen=True)
class Token:
    value: str


@dataclass(frozen=True)
class Remote:
    online: bool
    busy: bool
    custom_labels: tuple[str, ...]


class FakeGitHub:
    def __init__(self) -> None:
        self.states = [None, Remote(True, False, ("aifordable-ci",))]
        self.token_requests = 0

    def status(self, spec):
        assert spec.alias == "aifordable-lab-ci"
        return self.states.pop(0) if self.states else Remote(
            True,
            False,
            ("aifordable-ci",),
        )

    def create_registration_token(self, spec):
        assert spec.repository == "Blacksp1d3r/AIfordable"
        self.token_requests += 1
        return Token("short-lived-registration-secret")


class FakeTransport:
    def __init__(self) -> None:
        self.calls = []

    def enroll(self, spec, secret):
        self.calls.append((spec, secret))
        assert isinstance(secret, CIRunnerRegistrationSecret)
        assert secret.value == "short-lived-registration-secret"
        return CIRunnerGuestTransportResult(
            state="registered",
            registered=True,
        )


def spec(**overrides):
    values = {
        "alias": "aifordable-lab-ci",
        "repository": "Blacksp1d3r/AIfordable",
        "runner_name": "aifordable-lab-ci",
        "labels": ("aifordable-ci",),
        "transport_binding_key": "aifordable-lab-ci",
    }
    values.update(overrides)
    return CIRunnerGuestSpec(**values)


def test_guest_enrollment_delegates_secret_without_host_paths() -> None:
    github = FakeGitHub()
    transport = FakeTransport()
    manager = CIRunnerGuestEnrollmentManager(
        github=github,
        transport=transport,
        sleeper=lambda _seconds: None,
    )

    result = manager.enroll(spec())

    assert result.state == "registered"
    assert result.alias == "aifordable-lab-ci"
    assert result.online is True
    assert result.busy is False
    assert result.custom_labels == ("aifordable-ci",)
    assert github.token_requests == 1
    assert len(transport.calls) == 1

    rendered = repr(result.to_payload())
    assert "short-lived-registration-secret" not in rendered
    assert "runner_root" not in rendered
    assert "work_root" not in rendered
    assert "transport_binding_key" not in rendered


def test_registration_secret_repr_is_always_redacted() -> None:
    secret = CIRunnerRegistrationSecret(
        "short-lived-registration-secret"
    )

    assert repr(secret) == "<CIRunnerRegistrationSecret redacted>"
    assert secret.value not in repr(secret)


def test_existing_remote_runner_is_idempotent_without_token_or_transport() -> None:
    remote = Remote(True, False, ("aifordable-ci",))

    class ExistingGitHub:
        def status(self, _spec):
            return remote

        def create_registration_token(self, _spec):
            raise AssertionError("token must not be requested")

    class NoTransport:
        def enroll(self, _spec, _secret):
            raise AssertionError("transport must not run")

    result = CIRunnerGuestEnrollmentManager(
        github=ExistingGitHub(),
        transport=NoTransport(),
    ).enroll(spec())

    assert result.state == "already-registered"
    assert result.registered is True


def test_staging_label_is_forbidden() -> None:
    with pytest.raises(
        CIRunnerGuestEnrollmentError,
        match="forbidden",
    ):
        spec(labels=("aifordable-staging",))


def test_failed_label_convergence_is_rejected() -> None:
    class WrongLabelGitHub(FakeGitHub):
        def status(self, spec):
            assert spec.alias == "aifordable-lab-ci"
            if self.states:
                self.states.pop(0)
                return None
            return Remote(True, False, ("wrong-label",))

    with pytest.raises(
        CIRunnerGuestEnrollmentError,
        match="labels did not converge",
    ):
        CIRunnerGuestEnrollmentManager(
            github=WrongLabelGitHub(),
            transport=FakeTransport(),
            sleeper=lambda _seconds: None,
        ).enroll(spec())


def test_invalid_transport_binding_is_rejected() -> None:
    with pytest.raises(
        CIRunnerGuestEnrollmentError,
        match="transport binding",
    ):
        spec(transport_binding_key="../guest")


@pytest.mark.parametrize(
    "value",
    [
        "x" * 15,
        "x" * 4097,
        "safe-but has-space" + "x" * 8,
        "unsafe\n" + "x" * 16,
        "unsafe\x00" + "x" * 16,
        "é" * 20,
    ],
)
def test_registration_secret_rejects_unsafe_values(value: str) -> None:
    with pytest.raises(
        CIRunnerGuestEnrollmentError,
        match="registration secret is invalid",
    ):
        CIRunnerRegistrationSecret(value)
