from __future__ import annotations

from runner_mcp.ci_runner_guest_enrollment import (
    CIRunnerGuestEnrollmentError,
    CIRunnerGuestSpec,
    CIRunnerGuestTransportResult,
    CIRunnerRegistrationSecret,
)
from runner_mcp.ci_runner_secret_handoff import (
    CIRunnerSecretHandoffError,
    CIRunnerSecretHandoffStore,
)
from runner_mcp.fabric_bridge import FabricBridgeClient, FabricBridgeError


class CIRunnerGuestFabricTransport:
    """Transport guest enrollment through an opaque single-use Fabric handoff."""

    def __init__(
        self,
        *,
        handoffs: CIRunnerSecretHandoffStore,
        fabric: FabricBridgeClient,
    ) -> None:
        if not isinstance(handoffs, CIRunnerSecretHandoffStore):
            raise TypeError("handoffs must be CIRunnerSecretHandoffStore")
        if not isinstance(fabric, FabricBridgeClient):
            raise TypeError("fabric must be FabricBridgeClient")
        self._handoffs = handoffs
        self._fabric = fabric

    def enroll(
        self,
        spec: CIRunnerGuestSpec,
        secret: CIRunnerRegistrationSecret,
    ) -> CIRunnerGuestTransportResult:
        if not isinstance(spec, CIRunnerGuestSpec):
            raise TypeError("spec must be CIRunnerGuestSpec")
        if not isinstance(secret, CIRunnerRegistrationSecret):
            raise TypeError("secret must be CIRunnerRegistrationSecret")

        try:
            handoff = self._handoffs.create(secret)
        except CIRunnerSecretHandoffError as exc:
            raise CIRunnerGuestEnrollmentError(
                "guest CI runner handoff is unavailable"
            ) from exc

        try:
            result = self._fabric.ci_runner_guest_enroll(
                handoff.handoff_id
            )
        except FabricBridgeError as exc:
            try:
                self._handoffs.discard(handoff.handoff_id)
            except CIRunnerSecretHandoffError:
                pass
            raise CIRunnerGuestEnrollmentError(
                "guest CI runner Fabric enrollment is unavailable"
            ) from exc

        if result["runner_name"] != spec.runner_name:
            raise CIRunnerGuestEnrollmentError(
                "guest CI runner Fabric identity did not converge"
            )
        if result["operation"] != "enroll":
            raise CIRunnerGuestEnrollmentError(
                "guest CI runner Fabric operation did not converge"
            )
        if result["state"] != "registered" or result["registered"] is not True:
            raise CIRunnerGuestEnrollmentError(
                "guest CI runner Fabric enrollment did not complete"
            )
        if result["running"] is not False:
            raise CIRunnerGuestEnrollmentError(
                "guest CI runner started before admission was restored"
            )

        return CIRunnerGuestTransportResult(
            state="registered",
            registered=True,
        )
