"""Begrensde Runner-Fabric-updateketen en alleen-lezen Release-controle.

De manager hergebruikt de bestaande Actions-, lokale custody- en vaste GitHub
Release-routes. Release-metadata is nooit automatisch installatiebevoegdheid:
alle activatie, herstel en hostherkomst blijven apart gekwalificeerde stappen.
"""

from __future__ import annotations

import base64
import hashlib
import io
import ipaddress
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import threading
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any
from uuid import uuid4

from .fabric_bootstrap import FabricBootstrapError, _private_env_value
from .fabric_release_assets import (
    FabricReleaseAdmissionError,
    FabricReleaseDigestError,
    ReleaseAdmission,
    inspect_exact_release,
)
from .fabric_release_private_custody import _promote_noreplace
from .operational_safety import OperatorSafetyGuard
from .secure_io import PrivateAtomicWriteError, atomic_replace_private

_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
_JOB_ID_RE = re.compile(r"^[0-9a-f]{32}$")
_REPOSITORY = "Blacksp1d3r/Runner-Fabric"
_WORKFLOW = "control-plane-update-bundle.yml"
_TOKEN_ENV = "RUNNER_MCP_GITHUB_TOKEN"
_JOB_SCHEMA = "runner-mcp/fabric-update-job/v1"
_MAX_JSON = 16_384
_MAX_API_RESPONSE = 2 * 1024 * 1024
_MAX_ARCHIVE = 256 * 1024 * 1024
_MAX_UNCOMPRESSED = 256 * 1024 * 1024
_MAX_ENTRY = 64 * 1024 * 1024
_MAX_FILES = 160
_RELEASE_RESOURCE_NOT_FOUND = "fabric_release_resource_not_found"
_TERMINAL = frozenset({"completed", "error", "interrupted"})


_LOCAL_CUSTODY_FAILURE_REASONS = frozenset(
    {
        "fabric_update_commit_invalid",
        "operator_stop",
        "runner_mcp_state_unavailable",
        "runner_mcp_self_update_active",
        "runner_mcp_restart_pending",
        "runner_mcp_install_recovery_pending",
        "fabric_launcher_unmanaged",
        "actions_run_unavailable",
        "fabric_bundle_storage_conflict",
        "fabric_bundle_invalid",
        "fabric_bundle_source_unavailable",
        "fabric_bundle_source_invalid",
        "fabric_bundle_secret_cleanup_failed",
        "fabric_bundle_build_failed",
    }
)


class FabricUpdateError(RuntimeError):
    """Bounded managed Runner Fabric update failure."""


def bounded_local_custody_failure_reason(
    error: FabricUpdateError,
) -> str | None:
    detail = str(error)
    return detail if detail in _LOCAL_CUSTODY_FAILURE_REASONS else None


_READINESS_FAILURE_REASONS = _LOCAL_CUSTODY_FAILURE_REASONS | frozenset(
    {
        "artifact_metadata_unavailable",
        "artifact_download_unavailable",
        "fabric_recovery_required",
        "fabric_transaction_invalid",
        "fabric_update_target_mismatch",
        "fabric_bundle_integrity_failed",
        "fabric_release_metadata_unavailable",
        "fabric_release_assets_unqualified",
        "release_not_published",
        "release_provider_unavailable",
        "release_digest_invalid",
    }
)


def bounded_fabric_readiness_failure(
    error: FabricUpdateError,
    *,
    source: str,
) -> dict[str, object]:
    """Expose only fixed safe reasons for an exact read-only update preflight.

    An error is NOT an artifact receipt, install permission or readiness proof.
    Do not include the requested commit, a private path or arbitrary error text.
    """
    if source not in {"github-actions", "local-custody", "github-release"}:
        raise ValueError("unsupported Fabric update source")
    reason = str(error) if type(error) is FabricUpdateError else ""
    code = (
        reason if reason in _READINESS_FAILURE_REASONS
        else "fabric_update_readiness_unavailable"
    )
    return {
        "state": "blocked",
        "reasonCode": code,
        "artifact_ready": False,
        "source": source,
    }


def read_alternative_release_metadata_after_actions_failure(
    manager: FabricUpdateManager,
    commit: str,
    actions_error: FabricUpdateError,
) -> dict[str, object] | None:
    """Explain an Actions metadata failure via existing Release inspection.

    This NEVER changes the original Actions-only update contract, never stages
    or downloads a wheel, and is not a host update readiness/approval result.
    A Release metadata match is still unsigned and not trusted local custody.
    """
    if (
        type(actions_error) is not FabricUpdateError
        or str(actions_error) != "actions_run_unavailable"
        or type(commit) is not str
        or _COMMIT_RE.fullmatch(commit) is None
    ):
        return None
    try:
        release = manager.release_assets_readiness(commit)
    except FabricUpdateError as exc:
        refusal = bounded_fabric_readiness_failure(
            exc, source="github-release",
        )
        return {
            "source": "github-release",
            "state": "blocked",
            "reasonCode": refusal["reasonCode"],
            "metadata_observed": False,
            "install_authorized": False,
            "download_performed": False,
        }
    except Exception:  # noqa: BLE001 - private provider faults must never leak
        return {
            "source": "github-release",
            "state": "blocked",
            "reasonCode": "release_metadata_probe_unavailable",
            "metadata_observed": False,
            "install_authorized": False,
            "download_performed": False,
        }
    # A stubbed or malformed provider must not claim metadata observation.
    if (
        type(release) is not dict
        or release.get("state") != "ready"
        or release.get("source") != "github-release"
        or release.get("commit") != commit
        or type(release.get("asset_count")) is not int
        or not 5 <= release["asset_count"] <= 160
        or type(release.get("project_wheel_sha256")) is not str
        or re.fullmatch(r"[a-f0-9]{64}", release["project_wheel_sha256"]) is None
        or release.get("mutation_authorized") is not False
        or release.get("download_performed") is not False
    ):
        return {
            "source": "github-release",
            "state": "blocked",
            "reasonCode": "release_metadata_probe_invalid",
            "metadata_observed": False,
            "install_authorized": False,
            "download_performed": False,
        }
    return {
        "source": "github-release",
        "state": "metadata_observed_unverified",
        "reasonCode": "exact_release_metadata_observed_not_installed",
        "metadata_observed": True,
        "install_authorized": False,
        "download_performed": False,
    }


class FabricUpdateState(StrEnum):
    QUEUED = "queued"
    FETCHING = "fetching"
    PREFLIGHT = "preflight"
    APPLYING = "applying"
    COMPLETED = "completed"
    ERROR = "error"
    INTERRUPTED = "interrupted"


@dataclass(frozen=True)
class FabricUpdateJob:
    job_id: str
    commit: str
    state: FabricUpdateState
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error_category: str | None = None
    already_active: bool = False
    source: str = "github-actions"

    def __post_init__(self) -> None:
        if self.source not in {"github-actions", "local-custody"}:
            raise ValueError("fabric update source is invalid")

    def public_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "commit": self.commit,
            "state": self.state.value,
            "created_at": _iso(self.created_at),
            "started_at": _iso(self.started_at),
            "finished_at": _iso(self.finished_at),
            "error_category": self.error_category,
            "already_active": self.already_active,
            "source": self.source,
        }

    def persisted_dict(self) -> dict[str, Any]:
        return {"schemaVersion": _JOB_SCHEMA, **self.public_dict()}


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class FabricUpdateManager:
    def __init__(
        self,
        *,
        config_dir: Path,
        safety: OperatorSafetyGuard,
        self_update_status_provider: Callable[[], dict[str, Any]],
        runner=subprocess.run,
        opener: Any | None = None,
        home: Path | None = None,
    ) -> None:
        if not config_dir.is_absolute():
            raise FabricUpdateError("fabric_update_storage_invalid")
        try:
            self.config_dir = config_dir.resolve(strict=True)
        except OSError as exc:
            raise FabricUpdateError("fabric_update_storage_invalid") from exc
        self.safety = safety
        self._self_update_status_provider = self_update_status_provider
        self._runner = runner
        self._opener = opener or urllib.request.build_opener(_NoRedirect())
        self.home = (home or Path.home()).expanduser().resolve()
        self.jobs_root = _private_dir(self.config_dir / "fabric-update-jobs", create=True)
        self.state_root = _private_dir(
            self.home / ".local" / "state" / "runner-fabric" / "control-plane-update",
            create=True,
            parents=True,
        )
        self.bundle = self.state_root / "bundle"
        self.local_bundles_root = _private_dir(
            self.state_root / "local-bundles",
            create=True,
        )
        self.launcher = self.home / ".local" / "bin" / "runner-fabric"
        self.transaction = self.state_root / "transaction.json"
        self._lock = threading.RLock()
        self._jobs: dict[str, FabricUpdateJob] = {}
        self._load_existing()

    def runtime_status(self) -> dict[str, Any]:
        return {
            "fabric_update_active": any(
                job.state.value not in _TERMINAL for job in self._jobs.values()
            ),
        }

    def actions_readiness(self) -> dict[str, bool]:
        """Check only whether the configured credential can read Fabric Actions metadata."""
        token = self._github_token()
        owner, repo = _REPOSITORY.split("/", 1)
        payload = self._api_json(
            token,
            f"/repos/{owner}/{repo}/actions/workflows/{_WORKFLOW}/runs?per_page=1",
            category="actions_run_unavailable",
        )
        rows = payload.get("workflow_runs") if isinstance(payload, dict) else None
        if not isinstance(rows, list):
            raise FabricUpdateError("actions_run_unavailable")
        return {"configured": True, "actions_readable": True}

    def readiness(self, commit: str) -> dict[str, Any]:
        """Verify the exact canonical Actions run/artifact metadata without mutation."""
        _require_commit(commit)
        self._require_safe_runtime()
        self._assert_managed_launcher()
        token = self._github_token()
        self._resolve_exact_artifact(token, commit)
        return {"commit": commit, "artifact_ready": True}

    def release_assets_readiness(self, commit: str) -> dict[str, Any]:
        """Behoud de bestaande publieke, niet-autoriserende Release-status.

        De exacte onderliggende inspectie wordt gedeeld met een toekomstige
        ondertekende byte-import. Er wordt niets gedownload, opgeslagen,
        geïnstalleerd, geactiveerd of met een host geassocieerd.
        """
        return self._read_exact_release_admission(commit).public_dict()

    def _read_exact_release_admission(self, commit: str) -> ReleaseAdmission:
        """Houd het bestaande publieke, getypeerde Release-contract ongewijzigd."""
        admission, _ = self._read_exact_release_snapshot(commit)
        return admission

    def _read_exact_release_snapshot(
        self, commit: str,
    ) -> tuple[ReleaseAdmission, object]:
        """Lees exact de bestaande GitHub Release én tag-ref als één snapshot.

        Alleen een door deze bestaande manager verkregen getypeerd resultaat
        mag de volgende signed-byte-gate ingaan. De vaste repository, exacte
        commit/tag, beide responsen, SHA-256-inventaris en verschil tussen
        dubbele 404, providerstoring en tegenstrijdig bestaan blijven gelijk.

        Dit is uitsluitend read-only providerinformatie, NOOIT een
        onafhankelijke signer, hostbeheerder, releasebevoegdheid of ACK.
        """
        _require_commit(commit)
        self._require_safe_runtime()
        self._assert_managed_launcher()
        token = self._github_token()
        prefix = (
            "fabric-q7-bundle-"
            if commit == "b26822aeb6718bf339f0871df621c3e61fbf1e1c"
            else "fabric-update-bundle-"
        )
        tag = prefix + commit
        owner, repo = _REPOSITORY.split("/", 1)
        path = f"/repos/{owner}/{repo}"
        # Both fixed GitHub endpoints must return 404 before we may classify
        # this as not published. One 404 plus one present object is a
        # conflict, never proof that a new release may be created.
        absent = []
        records: list[dict[str, Any] | None] = []
        for suffix in (f"/releases/tags/{tag}", f"/git/ref/tags/{tag}"):
            try:
                records.append(self._api_json(
                    token,
                    path + suffix,
                    category="fabric_release_metadata_unavailable",
                ))
                absent.append(False)
            except FabricUpdateError as exc:
                if str(exc) != _RELEASE_RESOURCE_NOT_FOUND:
                    raise
                records.append(None)
                absent.append(True)
        if all(absent):
            # GitHub may deliberately conceal inaccessible resources as 404.
            # This is a diagnostic only, never publication/update authority.
            raise FabricUpdateError("release_not_published")
        if any(absent):
            raise FabricUpdateError("fabric_release_assets_unqualified")
        release, tag_ref = records
        try:
            admission = inspect_exact_release(commit, release, tag_ref)
        except FabricReleaseDigestError as exc:
            raise FabricUpdateError("release_digest_invalid") from exc
        except FabricReleaseAdmissionError as exc:
            raise FabricUpdateError("fabric_release_assets_unqualified") from exc
        # Beschrijving is onbetrouwbare providerdata, geen sleutelpins of
        # updatebevoegdheid. De private verbruiker valideert dit apart.
        return admission, release.get("body")

    def _read_exact_github_release_bytes(
        self,
        *,
        expected_commit: str,
        asset_reader: Callable[..., bytes] | None = None,
    ) -> dict[str, bytes]:
        """Bestaande private GitHub byte-API blijft ongewijzigd, uitsluitend RAM."""
        _, blobs = self._read_exact_github_release_candidate(
            expected_commit=expected_commit, asset_reader=asset_reader,
        )
        return blobs

    def _read_exact_github_release_candidate(
        self,
        *,
        expected_commit: str,
        expected_release_id: int | None = None,
        asset_reader: Callable[..., bytes] | None = None,
    ) -> tuple[ReleaseAdmission, dict[str, bytes]]:
        """Dezelfde 2 metadata-GETs en volle bytes, met optionele exacte ID-pin.

        Vóór enige asset-GET wordt een opgegeven Release-ID exact gecontroleerd.
        De aanroeper moet nog een eigen CI/bron-/host-policy leveren; inputpins
        of GitHub-hashes zijn op zichzelf nooit onafhankelijk eigenaarbewijs.
        """
        from .fabric_release_asset_bytes import (
            AssetBytesUnqualified,
            fetch_exact_github_release_bundle_bytes,
            fetch_pinned_asset_bytes,
        )

        _require_commit(expected_commit)
        if expected_release_id is not None and (
            type(expected_release_id) is not int or expected_release_id <= 0
        ):
            raise FabricUpdateError("fabric_release_assets_unqualified")
        admission = self._read_exact_release_admission(expected_commit)
        if (
            expected_release_id is not None
            and admission.release_id != expected_release_id
        ):
            raise FabricUpdateError("fabric_release_assets_unqualified")
        reader = fetch_pinned_asset_bytes if asset_reader is None else asset_reader
        token = self._github_token()
        try:
            bodies = fetch_exact_github_release_bundle_bytes(
                token=token,
                expected_commit=expected_commit,
                observed_metadata=admission,
                asset_reader=reader,
            )
        except (AssetBytesUnqualified, TypeError, ValueError) as exc:
            raise FabricUpdateError(
                "fabric_release_asset_bytes_unqualified"
            ) from exc
        return admission, bodies

    def _stage_github_release_inactive_once(
        self,
        *,
        expected_commit: str,
        expected_release_id: int,
        asset_reader: Callable[..., bytes] | None = None,
    ) -> dict[str, object]:
        """Zet GitHub-bytebewijs alleen in bestaand INACTIEF local-bundles.

        Geen ED-productiesleutel vereist. Hergebruik bestaande metadata +
        per-asset transport en dezelfde atomic 0700/0600 NOREPLACE custody
        van de vroegere signed-bron. Dit is PRIVATE SOURCE ONLY, geen MCP-
        tool, geen installatie-/rollbackbevoegdheid of client-ACK. De
        fysieke eigenaar-host + CI-sourcepolicy moeten later apart slagen.
        """
        from .fabric_release_inactive_custody import (
            InactiveSignedCustodyUnqualified,
            _stage_github_release_inactive_once,
        )

        admission, bodies = self._read_exact_github_release_candidate(
            expected_commit=expected_commit,
            expected_release_id=expected_release_id,
            asset_reader=asset_reader,
        )
        try:
            receipt = _stage_github_release_inactive_once(
                local_bundles_root=self.local_bundles_root,
                expected_commit=expected_commit,
                expected_release_id=expected_release_id,
                observed_metadata=admission,
                asset_bodies=bodies,
            )
        except InactiveSignedCustodyUnqualified as exc:
            raise FabricUpdateError(
                "fabric_release_inactive_custody_unqualified"
            ) from exc
        return {**receipt, "download_performed": True}

    def _read_verified_signed_release_bytes(
        self,
        *,
        expected_commit: str,
        expected_release_id: int,
        signed_document: bytes,
        signature: bytes,
        public_key: bytes,
        independently_trusted_key_sha256: str,
        asset_reader: Callable[..., bytes] | None = None,
    ) -> dict[str, bytes]:
        """Koppel twee BESTAANDE verificatiestappen zonder servermutatie.

        1. Weiger een ongeldige handtekening of onafhankelijke bron-/releasepin
           nog vóór het eerste GitHub-metadataverzoek.
        2. Hergebruik dezelfde getypeerde Release/tag-snapshot als de openbare
           `release_assets_readiness` van deze manager (vaste repository).
        3. Hergebruik de bestaande vastgepinde assetbyte-transport- én de
           complete manifest/ZIP/wheelcontroles; retourneer uitsluitend bytes
           in geheugen en nooit een gedeeltelijke release.

        De aanroeper moet de signer-sleutelvingerafdruk en bron-/release-ID
        vooraf van een onafhankelijke eigenaar/Fabric-policy ontvangen.
        Die autoriteit wordt hier NIET aangetoond door het aanleveren van de
        waarden. Daarom is dit een **interne bronvoorbereiding**, zonder MCP-
        tool, schijf-custody, BOOTSTRAP, install, `apply`, worker of ACK.
        `asset_reader` dient alleen voor offline synthetische testinjectie.
        """
        from .fabric_release_asset_bytes import (
            fetch_exact_signed_fabric_bundle_bytes,
            fetch_pinned_asset_bytes,
        )
        from .fabric_release_signed_roster import (
            SignedFabricRosterUnqualified,
            verify_signed_fabric_roster,
        )

        _require_commit(expected_commit)
        try:
            verify_signed_fabric_roster(
                signed_document=signed_document,
                signature=signature,
                public_key=public_key,
                independently_trusted_key_sha256=independently_trusted_key_sha256,
                expected_commit=expected_commit,
                expected_release_id=expected_release_id,
            )
        except SignedFabricRosterUnqualified as exc:
            raise FabricUpdateError(
                "fabric_signed_release_roster_unqualified"
            ) from exc

        # Het ontvangen Release-object is GitHub-metadata, nooit een nieuwe
        # trust anchor. Gebruik exact de bestaande managercontroles/2 endpoints.
        observed = self._read_exact_release_admission(expected_commit)
        token = self._github_token()
        reader = fetch_pinned_asset_bytes if asset_reader is None else asset_reader
        try:
            return fetch_exact_signed_fabric_bundle_bytes(
                token=token,
                signed_document=signed_document,
                signature=signature,
                public_key=public_key,
                independently_trusted_key_sha256=independently_trusted_key_sha256,
                expected_commit=expected_commit,
                expected_release_id=expected_release_id,
                observed_metadata=observed,
                asset_reader=reader,
            )
        except ValueError as exc:
            # Geen ruwe providertekst, tokens, bestandspaden of byte-inhoud
            # opnemen in een mogelijke volgende operator-/CI-foutmelding.
            raise FabricUpdateError(
                "fabric_release_asset_bytes_unqualified"
            ) from exc

    def _read_verified_signed_release_description_bytes(
        self,
        *,
        expected_commit: str,
        expected_release_id: int,
        independently_trusted_key_sha256: str,
        asset_reader: Callable[..., bytes] | None = None,
    ) -> dict[str, bytes]:
        """Behoud het bestaande interne broncontract: uitsluitend bytes in RAM.

        De verifiërende voorbereiding levert ook bewijsmateriaal voor de
        afzonderlijke inactieve opslag. Hier wordt NOOIT naar schijf geschreven.
        """
        _, _, _, _, bodies = (
            self._read_verified_signed_release_description_candidate(
                expected_commit=expected_commit,
                expected_release_id=expected_release_id,
                independently_trusted_key_sha256=independently_trusted_key_sha256,
                asset_reader=asset_reader,
            )
        )
        return bodies

    def _read_verified_signed_release_description_candidate(
        self,
        *,
        expected_commit: str,
        expected_release_id: int,
        independently_trusted_key_sha256: str,
        asset_reader: Callable[..., bytes] | None = None,
    ) -> tuple[ReleaseAdmission, bytes, bytes, bytes, dict[str, bytes]]:
        """Gebruik het bestaande Release/tag-GET als één getypeerde snapshot.

        Fabric #924 mag het ondertekende rooster in de Release-description
        vervoeren, maar de sleutel uit die beschrijving is nooit autoriteit.
        Alleen vooraf extern door eigenaar/Fabric vastgelegde commit,
        Release-ID en vertrouwde sleutelvingerafdruk komen in aanmerking.
        De bestaande signed-byte downloader controleert bovendien ALLE assets,
        BUNDLE/COMMIT/SHA256SUMS en de WHEEL/RECORD-inhoud. Er volgt geen
        schijfwrite, downloadtool-exposure, BOOTSTRAP, installatie of rollback.
        `asset_reader` is uitsluitend een synthetische testinjectie.
        """
        from .fabric_release_asset_bytes import (
            fetch_exact_signed_fabric_bundle_bytes,
            fetch_pinned_asset_bytes,
        )
        from .fabric_release_body_envelope import (
            SignedBodyEnvelopeUnqualified,
            verify_signed_release_body,
        )

        _require_commit(expected_commit)
        observed, body = self._read_exact_release_snapshot(expected_commit)
        try:
            document, signature, public_key = verify_signed_release_body(
                body=body,
                independently_trusted_key_sha256=independently_trusted_key_sha256,
                expected_commit=expected_commit,
                expected_release_id=expected_release_id,
                observed_metadata=observed,
            )
        except SignedBodyEnvelopeUnqualified as exc:
            raise FabricUpdateError(
                "fabric_signed_release_body_unqualified"
            ) from exc

        reader = fetch_pinned_asset_bytes if asset_reader is None else asset_reader
        token = self._github_token()
        try:
            bodies = fetch_exact_signed_fabric_bundle_bytes(
                token=token,
                signed_document=document,
                signature=signature,
                public_key=public_key,
                independently_trusted_key_sha256=independently_trusted_key_sha256,
                expected_commit=expected_commit,
                expected_release_id=expected_release_id,
                observed_metadata=observed,
                asset_reader=reader,
            )
        except ValueError as exc:
            # Negeer alle provider-/credentialdetails in eventuele fouttekst.
            raise FabricUpdateError(
                "fabric_release_asset_bytes_unqualified"
            ) from exc
        return observed, document, signature, public_key, bodies

    def _stage_signed_release_description_inactive_once(
        self,
        *,
        expected_commit: str,
        expected_release_id: int,
        independently_trusted_key_sha256: str,
        asset_reader: Callable[..., bytes] | None = None,
    ) -> dict[str, object]:
        """Voltooi exact signed Release->bestaande INACTIEVE local-bundles.

        Eerst twee vaste GitHub metadata-GETs, de onafhankelijke signer/
        source/release-pins, volledige pinned assetbytes en alle wheelchecks.
        PAS DAARNA schrijft de al aanwezige create-once/no-replace custody
        de gecontroleerde bytes in de bestaande eigenaar-private 0700 root.
        Dit is private, niet aan server/MCP tool gekoppelde bronvoorbereiding:
        ontvangen aanroeperpins bewijzen geen werkelijke operatorbevoegdheid.
        Geen actieve bundle, BOOTSTRAP, install, launcher, service of rollback.
        """
        from .fabric_release_inactive_custody import (
            InactiveSignedCustodyUnqualified,
            _stage_signed_release_inactive_once,
        )

        observed, document, signature, public_key, bodies = (
            self._read_verified_signed_release_description_candidate(
                expected_commit=expected_commit,
                expected_release_id=expected_release_id,
                independently_trusted_key_sha256=independently_trusted_key_sha256,
                asset_reader=asset_reader,
            )
        )
        try:
            receipt = _stage_signed_release_inactive_once(
                local_bundles_root=self.local_bundles_root,
                signed_document=document,
                signature=signature,
                public_key=public_key,
                independently_trusted_key_sha256=independently_trusted_key_sha256,
                expected_commit=expected_commit,
                expected_release_id=expected_release_id,
                observed_metadata=observed,
                asset_bodies=bodies,
            )
        except InactiveSignedCustodyUnqualified as exc:
            raise FabricUpdateError(
                "fabric_signed_inactive_custody_unqualified"
            ) from exc

        # Alleen na volledig download/verify/fsync/promotie is dit waar.
        # De echte eigenaar-/install-/rollbackbevoegdheid blijft FALSE.
        return {**receipt, "download_performed": True}

    def local_readiness(self, commit: str) -> dict[str, Any]:
        """Verify one exact locally-custodied Fabric bundle without mutation."""
        _require_commit(commit)
        self._require_safe_runtime()
        self._assert_managed_launcher()
        root = self._local_bundle_root(commit)
        self._validate_local_bundle_source(root)
        self._validated_bootstrap(commit, root=root, verify_wheel_records=True)
        return {
            "commit": commit,
            "artifact_ready": True,
            "source": "local-custody",
        }

    def stage_local_bundle(self, commit: str) -> dict[str, Any]:
        """Build and retain one exact canonical Runner Fabric update bundle."""

        _require_commit(commit)
        self._require_safe_runtime()
        self._assert_managed_launcher()

        target = self.local_bundles_root / commit
        if target.exists() or target.is_symlink():
            if target.is_symlink():
                raise FabricUpdateError("fabric_bundle_storage_conflict")
            root = self._local_bundle_root(commit)
            self._validate_local_bundle_source(root)
            self._validated_bootstrap(commit, root=root)
            return {
                "commit": commit,
                "staged": True,
                "bundleReady": True,
                "source": "canonical-source",
                "localCustody": True,
                "alreadyStaged": True,
            }

        work = self.local_bundles_root / f".incoming-{uuid4().hex}"
        source = work / "source"
        credential_config = work / "gitconfig"
        try:
            work.mkdir(mode=0o700)
            os.chmod(work, 0o700)
            token = self._github_token()
            encoded = base64.b64encode(f"x-access-token:{token}".encode()).decode("ascii")
            credential_config.write_text(
                '[http "https://github.com/"]\n'
                f"\textraHeader = AUTHORIZATION: basic {encoded}\n",
                encoding="utf-8",
            )
            os.chmod(credential_config, 0o600)

            git_env = {
                "HOME": str(self.home),
                "PATH": "/usr/local/bin:/usr/bin:/bin",
                "LANG": "C.UTF-8",
                "LC_ALL": "C.UTF-8",
                "GIT_CONFIG_NOSYSTEM": "1",
                "GIT_CONFIG_GLOBAL": str(credential_config),
                "GIT_TERMINAL_PROMPT": "0",
            }
            self._run_bundle_command(
                [
                    "/usr/bin/git",
                    "clone",
                    "--depth=64",
                    "--no-checkout",
                    "https://github.com/Blacksp1d3r/Runner-Fabric.git",
                    str(source),
                ],
                cwd=work,
                env=git_env,
                category="fabric_bundle_source_unavailable",
                timeout=180,
            )
            self._run_bundle_command(
                [
                    "/usr/bin/git",
                    "-C",
                    str(source),
                    "fetch",
                    "--depth=1",
                    "origin",
                    commit,
                ],
                cwd=work,
                env=git_env,
                category="fabric_bundle_source_unavailable",
                timeout=120,
            )
            self._run_bundle_command(
                [
                    "/usr/bin/git",
                    "-C",
                    str(source),
                    "checkout",
                    "--detach",
                    commit,
                ],
                cwd=work,
                env={
                    **git_env,
                    "GIT_CONFIG_GLOBAL": "/dev/null",
                },
                category="fabric_bundle_source_invalid",
                timeout=60,
            )
            observed = self._run_bundle_command(
                ["/usr/bin/git", "-C", str(source), "rev-parse", "HEAD"],
                cwd=work,
                env={
                    **git_env,
                    "GIT_CONFIG_GLOBAL": "/dev/null",
                },
                category="fabric_bundle_source_invalid",
                timeout=30,
                capture=True,
            )
            if observed.stdout.strip() != commit:
                raise FabricUpdateError("fabric_bundle_source_invalid")
            dirty = self._run_bundle_command(
                ["/usr/bin/git", "-C", str(source), "status", "--porcelain"],
                cwd=work,
                env={
                    **git_env,
                    "GIT_CONFIG_GLOBAL": "/dev/null",
                },
                category="fabric_bundle_source_invalid",
                timeout=30,
                capture=True,
            )
            if dirty.stdout.strip():
                raise FabricUpdateError("fabric_bundle_source_invalid")

            try:
                credential_config.unlink()
            except OSError as exc:
                raise FabricUpdateError("fabric_bundle_secret_cleanup_failed") from exc

            build_env = {
                "HOME": str(self.home),
                "PATH": "/usr/local/bin:/usr/bin:/bin",
                "LANG": "C.UTF-8",
                "LC_ALL": "C.UTF-8",
                "PIP_DISABLE_PIP_VERSION_CHECK": "1",
                "PIP_NO_INPUT": "1",
                "GIT_CONFIG_NOSYSTEM": "1",
                "GIT_TERMINAL_PROMPT": "0",
            }
            self._run_bundle_command(
                [sys.executable, "scripts/build_control_plane_update_bundle.py"],
                cwd=source,
                env=build_env,
                category="fabric_bundle_build_failed",
                timeout=900,
            )
            bundle = source / "bundle"
            self._validate_local_bundle_source(bundle)
            self._validated_bootstrap(commit, root=bundle)
            # `target.exists()` was only a momentopname. Two operators
            # could both pass it: os.replace could then overwrite an empty
            # destination created by the other staging operation. Use the
            # already-existing atomic Linux NOREPLACE promotion instead.
            _promote_inactive_bundle_noreplace(
                self.local_bundles_root, work.name, commit
            )
            self._validate_local_bundle_source(target)
            self._validated_bootstrap(commit, root=target)
        finally:
            shutil.rmtree(work, ignore_errors=True)

        return {
            "commit": commit,
            "staged": True,
            "bundleReady": True,
            "source": "canonical-source",
            "localCustody": True,
            "alreadyStaged": False,
        }

    def _run_bundle_command(
        self,
        argv: list[str],
        *,
        cwd: Path,
        env: dict[str, str],
        category: str,
        timeout: int,
        capture: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        try:
            completed = self._runner(
                argv,
                cwd=str(cwd),
                env=env,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE if capture else subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout,
                check=False,
                shell=False,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise FabricUpdateError(category) from exc
        if completed.returncode != 0:
            raise FabricUpdateError(category)
        return completed

    def start(self, commit: str) -> dict[str, Any]:
        return self._start(commit, source="github-actions")

    def start_local(self, commit: str) -> dict[str, Any]:
        self.local_readiness(commit)
        return self._start(commit, source="local-custody")

    def _start(self, commit: str, *, source: str) -> dict[str, Any]:
        _require_commit(commit)
        if source not in {"github-actions", "local-custody"}:
            raise FabricUpdateError("fabric_update_source_invalid")
        self._require_safe_runtime()
        with self._lock:
            active = [j for j in self._jobs.values() if j.state.value not in _TERMINAL]
            if active:
                if len(active) == 1 and active[0].commit == commit:
                    return active[0].public_dict()
                raise FabricUpdateError("fabric_update_active")
            active_commit = self._active_commit()
            if active_commit == commit:
                job = FabricUpdateJob(
                    job_id=uuid4().hex,
                    commit=commit,
                    state=FabricUpdateState.COMPLETED,
                    created_at=_now(),
                    finished_at=_now(),
                    already_active=True,
                    source=source,
                )
                self._persist(job)
                self._jobs[job.job_id] = job
                return job.public_dict()
            self._assert_managed_launcher()
            job = FabricUpdateJob(
                job_id=uuid4().hex,
                commit=commit,
                state=FabricUpdateState.QUEUED,
                created_at=_now(),
                source=source,
            )
            self._persist(job)
            self._jobs[job.job_id] = job
        worker = threading.Thread(
            target=self._run_job,
            args=(job.job_id,),
            name=f"runner-mcp-fabric-update-{job.job_id[:8]}",
            daemon=True,
        )
        try:
            worker.start()
        except RuntimeError as exc:
            self._finish(job.job_id, FabricUpdateState.ERROR, "worker_start_failed")
            raise FabricUpdateError("worker_start_failed") from exc
        return job.public_dict()

    def status(self, job_id: str) -> dict[str, Any]:
        if not isinstance(job_id, str) or _JOB_ID_RE.fullmatch(job_id) is None:
            raise FabricUpdateError("fabric_update_job_invalid")
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                raise FabricUpdateError("fabric_update_job_unknown")
            return job.public_dict()

    def rollback(self, commit: str) -> dict[str, str]:
        _require_commit(commit)
        self._require_safe_runtime()
        with self._lock:
            if any(job.state.value not in _TERMINAL for job in self._jobs.values()):
                raise FabricUpdateError("fabric_update_active")
            if self._active_commit() != commit:
                raise FabricUpdateError("fabric_update_target_mismatch")
            bootstrap = self._validated_bootstrap(commit)
            self._run_fixed(bootstrap, "rollback", "rollback_failed")
        return {"state": "completed", "commit": commit}

    def _require_safe_runtime(self) -> None:
        if self.safety.status().stop_active:
            raise FabricUpdateError("operator_stop")
        try:
            status = self._self_update_status_provider()
        except Exception as exc:
            raise FabricUpdateError("runner_mcp_state_unavailable") from exc
        for key, category in (
            ("active_update", "runner_mcp_self_update_active"),
            ("restart_pending", "runner_mcp_restart_pending"),
            ("install_recovery_pending", "runner_mcp_install_recovery_pending"),
        ):
            value = status.get(key)
            if not isinstance(value, bool):
                raise FabricUpdateError("runner_mcp_state_unavailable")
            if value:
                raise FabricUpdateError(category)

    def _assert_managed_launcher(self) -> None:
        if not self.launcher.is_symlink():
            raise FabricUpdateError("fabric_launcher_unmanaged")
        try:
            target = self.launcher.resolve(strict=True)
        except OSError as exc:
            raise FabricUpdateError("fabric_launcher_unmanaged") from exc
        slots = self.state_root / "slots"
        try:
            slots_root = slots.resolve(strict=True)
        except OSError as exc:
            raise FabricUpdateError("fabric_launcher_unmanaged") from exc
        if not target.is_relative_to(slots_root):
            raise FabricUpdateError("fabric_launcher_unmanaged")

    def _active_commit(self) -> str | None:
        if not self.transaction.exists():
            return None
        raw = _read_json(self.transaction, 32 * 1024, "fabric_transaction_invalid")
        if raw.get("schemaVersion") != "runner.fabric/control-plane-update-transaction/v1":
            raise FabricUpdateError("fabric_transaction_invalid")
        if raw.get("phase") != "active":
            raise FabricUpdateError("fabric_recovery_required")
        commit = raw.get("commitSha")
        if not isinstance(commit, str) or _COMMIT_RE.fullmatch(commit) is None:
            raise FabricUpdateError("fabric_transaction_invalid")
        return commit

    def _run_job(self, job_id: str) -> None:
        job = self._update(
            job_id,
            state=FabricUpdateState.FETCHING,
            started_at=_now(),
        )
        try:
            if job.source == "local-custody":
                staged = self._stage_local_bundle(job)
            else:
                archive = self._fetch_exact_artifact(job.commit)
                staged = self._extract_bundle(archive, job)
            previous = self._activate_bundle(staged, job)
            try:
                bootstrap = self._validated_bootstrap(
                    job.commit, verify_wheel_records=job.source == "local-custody",
                )
                self._update(job_id, state=FabricUpdateState.PREFLIGHT)
                self._run_fixed(bootstrap, "preflight", "fabric_preflight_failed")
                if self.safety.status().stop_active:
                    raise FabricUpdateError("operator_stop")
                self._update(job_id, state=FabricUpdateState.APPLYING)
                self._run_fixed(bootstrap, "apply", "fabric_apply_failed")
            except Exception:
                self._restore_bundle(previous)
                raise
            else:
                if previous is not None:
                    shutil.rmtree(previous, ignore_errors=True)
        except FabricUpdateError as exc:
            self._finish(job_id, FabricUpdateState.ERROR, _category(exc))
        except Exception:  # noqa: BLE001 - background update must fail closed
            self._finish(job_id, FabricUpdateState.ERROR, "fabric_update_failed")
        else:
            self._finish(job_id, FabricUpdateState.COMPLETED, None)

    def _local_bundle_root(self, commit: str) -> Path:
        root = self.local_bundles_root / commit
        return _private_dir(root, create=False)

    def _validate_local_bundle_source(self, root: Path) -> None:
        try:
            entries = tuple(root.iterdir())
        except OSError as exc:
            raise FabricUpdateError("fabric_bundle_invalid") from exc
        if not 1 <= len(entries) <= _MAX_FILES:
            raise FabricUpdateError("fabric_bundle_invalid")
        total = 0
        for entry in entries:
            if entry.is_symlink() or not entry.is_file():
                raise FabricUpdateError("fabric_bundle_invalid")
            try:
                info = entry.stat()
            except OSError as exc:
                raise FabricUpdateError("fabric_bundle_invalid") from exc
            if (
                info.st_uid != os.getuid()
                or info.st_nlink != 1
                or info.st_mode & 0o077
                or info.st_size <= 0
                or info.st_size > _MAX_ENTRY
            ):
                raise FabricUpdateError("fabric_bundle_invalid")
            total += info.st_size
        if total > _MAX_UNCOMPRESSED:
            raise FabricUpdateError("fabric_bundle_invalid")

    def _stage_local_bundle(self, job: FabricUpdateJob) -> Path:
        source = self._local_bundle_root(job.commit)
        self._validate_local_bundle_source(source)
        self._validated_bootstrap(job.commit, root=source, verify_wheel_records=True)
        staged = self.state_root / f".bundle-{job.job_id}"
        if staged.exists() or staged.is_symlink():
            raise FabricUpdateError("fabric_bundle_storage_conflict")
        staged.mkdir(mode=0o700)
        try:
            entries = tuple(source.iterdir())
            if not 1 <= len(entries) <= _MAX_FILES:
                raise FabricUpdateError("fabric_bundle_invalid")
            for entry in entries:
                if entry.is_symlink() or not entry.is_file():
                    raise FabricUpdateError("fabric_bundle_invalid")
                info = entry.stat()
                if info.st_uid != os.getuid() or info.st_nlink != 1:
                    raise FabricUpdateError("fabric_bundle_invalid")
                if info.st_mode & 0o077 or info.st_size > _MAX_ENTRY:
                    raise FabricUpdateError("fabric_bundle_invalid")
                target = staged / entry.name
                shutil.copyfile(entry, target)
                target.chmod(0o600)
            self._validated_bootstrap(job.commit, root=staged, verify_wheel_records=True)
        except Exception:
            shutil.rmtree(staged, ignore_errors=True)
            raise
        return staged

    def _fetch_exact_artifact(self, commit: str) -> bytes:
        token = self._github_token()
        artifact_id = self._resolve_exact_artifact(token, commit)
        return self._download_artifact(token, artifact_id)

    def _github_token(self) -> str:
        try:
            return _private_env_value(
                self.config_dir / "runner-mcp.env",
                _TOKEN_ENV,
            )
        except FabricBootstrapError as exc:
            raise FabricUpdateError("actions_run_unavailable") from exc

    def _resolve_exact_artifact(self, token: str, commit: str) -> int:
        owner, repo = _REPOSITORY.split("/", 1)
        runs = self._api_json(
            token,
            f"/repos/{owner}/{repo}/actions/workflows/{_WORKFLOW}/runs"
            f"?head_sha={commit}&status=success&per_page=100",
            category="actions_run_unavailable",
        )
        rows = runs.get("workflow_runs") if isinstance(runs, dict) else None
        if not isinstance(rows, list):
            raise FabricUpdateError("actions_run_unavailable")
        exact = [
            row for row in rows
            if isinstance(row, dict)
            and row.get("head_sha") == commit
            and row.get("conclusion") == "success"
            and row.get("head_branch") == "main"
            and row.get("event") in {"push", "workflow_dispatch"}
        ]
        pushed = [row for row in exact if row.get("event") == "push"]
        fallback = [row for row in exact if row.get("event") == "workflow_dispatch"]
        if len(pushed) == 1:
            selected = pushed[0]
        elif len(pushed) > 1 or len(fallback) != 1:
            raise FabricUpdateError("actions_run_unavailable")
        else:
            selected = fallback[0]
        if not isinstance(selected.get("id"), int):
            raise FabricUpdateError("actions_run_unavailable")
        run_id = selected["id"]
        artifacts = self._api_json(
            token,
            f"/repos/{owner}/{repo}/actions/runs/{run_id}/artifacts?per_page=100",
            category="artifact_metadata_unavailable",
        )
        rows = artifacts.get("artifacts") if isinstance(artifacts, dict) else None
        expected = f"runner-fabric-control-plane-update-{commit}"
        candidates = [
            row for row in (rows or [])
            if isinstance(row, dict)
            and row.get("name") == expected
            and row.get("expired") is False
            and isinstance(row.get("id"), int)
        ]
        if len(candidates) != 1:
            raise FabricUpdateError("artifact_metadata_unavailable")
        return candidates[0]["id"]

    def _api_json(
        self,
        token: str,
        path: str,
        *,
        category: str,
    ) -> dict[str, Any]:
        raw = self._request(
            f"https://api.github.com{path}",
            token=token,
            max_bytes=_MAX_API_RESPONSE,
            category=category,
        )
        try:
            value = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise FabricUpdateError(category) from exc
        if not isinstance(value, dict):
            raise FabricUpdateError(category)
        return value

    def _download_artifact(self, token: str, artifact_id: int) -> bytes:
        owner, repo = _REPOSITORY.split("/", 1)
        url = (
            f"https://api.github.com/repos/{owner}/{repo}/actions/artifacts/"
            f"{artifact_id}/zip"
        )
        redirect = self._request_redirect(url, token)
        return self._request(
            redirect,
            token=None,
            max_bytes=_MAX_ARCHIVE,
            category="artifact_download_unavailable",
        )

    def _request_redirect(self, url: str, token: str) -> str:
        request = urllib.request.Request(
            url,
            headers=self._headers(token),
            method="GET",
        )
        try:
            self._opener.open(request, timeout=30)
        except urllib.error.HTTPError as exc:
            if exc.code not in {301, 302, 303, 307, 308}:
                raise FabricUpdateError("artifact_download_unavailable") from exc
            location = exc.headers.get("Location", "")
        except (OSError, urllib.error.URLError) as exc:
            raise FabricUpdateError("artifact_download_unavailable") from exc
        else:
            raise FabricUpdateError("artifact_download_unavailable")
        parsed = urllib.parse.urlsplit(location)
        hostname = (parsed.hostname or "").lower()
        if (
            parsed.scheme != "https"
            or not hostname
            or parsed.username is not None
            or parsed.password is not None
            or parsed.fragment
            or hostname == "localhost"
            or hostname.endswith(".local")
        ):
            raise FabricUpdateError("artifact_download_unavailable")
        try:
            address = ipaddress.ip_address(hostname)
        except ValueError:
            address = None
        if address is not None and (
            address.is_private
            or address.is_loopback
            or address.is_link_local
            or address.is_reserved
            or address.is_unspecified
        ):
            raise FabricUpdateError("artifact_download_unavailable")
        return location

    def _request(
        self,
        url: str,
        *,
        token: str | None,
        max_bytes: int,
        category: str,
    ) -> bytes:
        request = urllib.request.Request(
            url,
            headers=self._headers(token),
            method="GET",
        )
        try:
            with self._opener.open(request, timeout=60) as response:
                raw = response.read(max_bytes + 1)
        except urllib.error.HTTPError as exc:
            if category == "fabric_release_metadata_unavailable":
                if exc.code == 404:
                    raise FabricUpdateError(_RELEASE_RESOURCE_NOT_FOUND) from exc
                raise FabricUpdateError("release_provider_unavailable") from exc
            raise FabricUpdateError(category) from exc
        except (OSError, urllib.error.URLError) as exc:
            if category == "fabric_release_metadata_unavailable":
                raise FabricUpdateError("release_provider_unavailable") from exc
            raise FabricUpdateError(category) from exc
        if len(raw) > max_bytes:
            raise FabricUpdateError(category)
        return raw

    @staticmethod
    def _headers(token: str | None) -> dict[str, str]:
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "runner-mcp",
        }
        if token is not None:
            headers["Authorization"] = f"Bearer {token}"
        return headers

    def _extract_bundle(self, archive: bytes, job: FabricUpdateJob) -> Path:
        staged = self.state_root / f".bundle-{job.job_id}"
        if staged.exists() or staged.is_symlink():
            raise FabricUpdateError("fabric_bundle_storage_conflict")
        staged.mkdir(mode=0o700)
        try:
            with zipfile.ZipFile(io.BytesIO(archive)) as zf:
                infos = zf.infolist()
                if not 1 <= len(infos) <= _MAX_FILES:
                    raise FabricUpdateError("fabric_bundle_invalid")
                if sum(info.file_size for info in infos) > _MAX_UNCOMPRESSED:
                    raise FabricUpdateError("fabric_bundle_invalid")
                names: set[str] = set()
                for info in infos:
                    name = info.filename
                    mode = info.external_attr >> 16
                    if (
                        not name
                        or name in names
                        or "/" in name
                        or "\\" in name
                        or info.is_dir()
                        or info.file_size > _MAX_ENTRY
                        or stat.S_ISLNK(mode)
                    ):
                        raise FabricUpdateError("fabric_bundle_invalid")
                    names.add(name)
                    target = staged / name
                    target.write_bytes(zf.read(info))
                    target.chmod(0o600)
        except (OSError, zipfile.BadZipFile, KeyError) as exc:
            shutil.rmtree(staged, ignore_errors=True)
            raise FabricUpdateError("fabric_bundle_invalid") from exc
        return staged

    def _activate_bundle(self, staged: Path, job: FabricUpdateJob) -> Path | None:
        previous = self.state_root / f".bundle-previous-{job.job_id}"
        try:
            if self.bundle.exists():
                if self.bundle.is_symlink() or not self.bundle.is_dir():
                    raise FabricUpdateError("fabric_bundle_storage_conflict")
                os.replace(self.bundle, previous)
            os.replace(staged, self.bundle)
        except OSError as exc:
            if previous.exists() and not self.bundle.exists():
                os.replace(previous, self.bundle)
            raise FabricUpdateError("fabric_bundle_storage_conflict") from exc
        return previous if previous.exists() else None

    def _restore_bundle(self, previous: Path | None) -> None:
        try:
            if self.bundle.exists():
                failed = self.state_root / ".bundle-failed"
                shutil.rmtree(failed, ignore_errors=True)
                os.replace(self.bundle, failed)
                shutil.rmtree(failed, ignore_errors=True)
            if previous is not None and previous.exists():
                os.replace(previous, self.bundle)
        except OSError as exc:
            raise FabricUpdateError("fabric_bundle_recovery_failed") from exc

    def _validated_bootstrap(
        self,
        commit: str,
        *,
        root: Path | None = None,
        verify_wheel_records: bool = False,
    ) -> Path:
        """Lees het bestaande bundle-formaat en, voor local-custody, ZIP/RECORD.

        De eerste SHA256SUMS-controle bewijst alleen lokale integriteit.
        Voor de bestaande inactieve lokale updatebron hergebruiken we daarna
        de al bestaande ZIP/METADATA/RECORD-parser op exact dezelfde bytes.
        Dit verifieert GEEN eigenaartrust, host of terugrolbevoegdheid.
        """
        bundle_root = self.bundle if root is None else root
        manifest = _read_json(
            bundle_root / "BUNDLE.json",
            32 * 1024,
            "fabric_bundle_invalid",
        )
        if (
            manifest.get("schemaVersion")
            != "runner.fabric/control-plane-update-bundle/v1"
            or manifest.get("commitSha") != commit
            or manifest.get("python") != "3.12"
        ):
            raise FabricUpdateError("fabric_bundle_invalid")

        project_wheel = manifest.get("projectWheel")
        wheel_count = manifest.get("wheelCount")
        bootstrap_sha = manifest.get("bootstrapSha256")
        if (
            not isinstance(project_wheel, str)
            or not project_wheel.startswith("runner_fabric-")
            or not project_wheel.endswith(".whl")
            or not isinstance(wheel_count, int)
            or isinstance(wheel_count, bool)
            or not 1 <= wheel_count <= _MAX_FILES
            or not isinstance(bootstrap_sha, str)
            or re.fullmatch(r"[0-9a-f]{64}", bootstrap_sha) is None
        ):
            raise FabricUpdateError("fabric_bundle_invalid")

        commit_file = bundle_root / "COMMIT_SHA"
        try:
            if (
                commit_file.is_symlink()
                or commit_file.read_text(encoding="ascii").strip() != commit
            ):
                raise FabricUpdateError("fabric_bundle_invalid")
        except (OSError, UnicodeDecodeError) as exc:
            raise FabricUpdateError("fabric_bundle_invalid") from exc

        sums = _parse_sums(
            _read_regular(
                bundle_root / "SHA256SUMS",
                128 * 1024,
                "fabric_bundle_invalid",
            )
        )
        bootstrap = bundle_root / "BOOTSTRAP.py"
        bootstrap_bytes = _read_regular(
            bootstrap,
            512 * 1024,
            "fabric_bundle_invalid",
        )
        if hashlib.sha256(bootstrap_bytes).hexdigest() != bootstrap_sha:
            raise FabricUpdateError("fabric_bundle_integrity_failed")

        try:
            wheels = sorted(bundle_root.glob("*.whl"))
            actual_entries = {entry.name for entry in bundle_root.iterdir()}
        except OSError as exc:
            raise FabricUpdateError("fabric_bundle_invalid") from exc
        if len(wheels) != wheel_count or project_wheel not in {w.name for w in wheels}:
            raise FabricUpdateError("fabric_bundle_invalid")

        payload_names = {"BOOTSTRAP.py", *(wheel.name for wheel in wheels)}
        expected_entries = payload_names | {
            "BUNDLE.json",
            "COMMIT_SHA",
            "SHA256SUMS",
        }
        if actual_entries != expected_entries or set(sums) != payload_names:
            raise FabricUpdateError("fabric_bundle_invalid")

        payloads = {"BOOTSTRAP.py": bootstrap_bytes}
        for wheel in wheels:
            payloads[wheel.name] = _read_regular(
                wheel,
                _MAX_ENTRY,
                "fabric_bundle_invalid",
            )
        for name, payload in payloads.items():
            if hashlib.sha256(payload).hexdigest() != sums[name]:
                raise FabricUpdateError("fabric_bundle_integrity_failed")
        if verify_wheel_records:
            from .fabric_release_wheelhouse import (
                WheelhouseUnqualified,
                _MAX_EXPANDED_TOTAL,
                _wheel_record_check,
            )

            try:
                expanded = 0
                for wheel in wheels:
                    expanded += _wheel_record_check(wheel.name, payloads[wheel.name])
                    if expanded > _MAX_EXPANDED_TOTAL:
                        raise WheelhouseUnqualified("expanded_wheelhouse_unqualified")
            except WheelhouseUnqualified as exc:
                # Gebruik de bestaande vaste foutcategorie, zonder ZIP-paden
                # of mogelijk gevoelige wheel-inhoud in de API te lekken.
                raise FabricUpdateError("fabric_bundle_integrity_failed") from exc
        return bootstrap

    def _run_fixed(self, bootstrap: Path, action: str, category: str) -> None:
        if action not in {"preflight", "apply", "rollback"}:
            raise FabricUpdateError("fabric_update_action_invalid")
        env = {
            "HOME": str(self.home),
            "PATH": "/usr/local/bin:/usr/bin:/bin",
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
            "PYTHONNOUSERSITE": "1",
        }
        try:
            completed = self._runner(
                [sys.executable, str(bootstrap), action],
                cwd=str(self.state_root),
                env=env,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=180,
                check=False,
                shell=False,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise FabricUpdateError(category) from exc
        if completed.returncode != 0:
            raise FabricUpdateError(category)

    def _persist(self, job: FabricUpdateJob) -> None:
        raw = (
            json.dumps(job.persisted_dict(), sort_keys=True, separators=(",", ":"))
            + "\n"
        ).encode("utf-8")
        if len(raw) > _MAX_JSON:
            raise FabricUpdateError("fabric_update_job_invalid")
        try:
            atomic_replace_private(self.jobs_root / f"{job.job_id}.json", raw)
        except PrivateAtomicWriteError as exc:
            raise FabricUpdateError("fabric_update_storage_invalid") from exc

    def _update(self, job_id: str, **changes: Any) -> FabricUpdateJob:
        with self._lock:
            job = replace(self._jobs[job_id], **changes)
            self._persist(job)
            self._jobs[job_id] = job
            return job

    def _finish(
        self,
        job_id: str,
        state: FabricUpdateState,
        category: str | None,
    ) -> None:
        self._update(
            job_id,
            state=state,
            finished_at=_now(),
            error_category=category,
        )

    def _load_existing(self) -> None:
        try:
            entries = tuple(self.jobs_root.iterdir())
        except OSError as exc:
            raise FabricUpdateError("fabric_update_storage_invalid") from exc
        for path in entries:
            if path.suffix != ".json" or _JOB_ID_RE.fullmatch(path.stem) is None:
                raise FabricUpdateError("fabric_update_storage_invalid")
            raw = _read_json(path, _MAX_JSON, "fabric_update_job_invalid")
            try:
                if raw.pop("schemaVersion") != _JOB_SCHEMA:
                    raise ValueError
                job = FabricUpdateJob(
                    job_id=raw["job_id"],
                    commit=raw["commit"],
                    state=FabricUpdateState(raw["state"]),
                    created_at=_parse(raw["created_at"]),
                    started_at=_parse_optional(raw["started_at"]),
                    finished_at=_parse_optional(raw["finished_at"]),
                    error_category=raw["error_category"],
                    already_active=raw["already_active"],
                    source=raw.get("source", "github-actions"),
                )
            except (KeyError, TypeError, ValueError) as exc:
                raise FabricUpdateError("fabric_update_job_invalid") from exc
            if job.job_id != path.stem or _COMMIT_RE.fullmatch(job.commit) is None:
                raise FabricUpdateError("fabric_update_job_invalid")
            if job.state.value not in _TERMINAL:
                job = replace(
                    job,
                    state=FabricUpdateState.INTERRUPTED,
                    finished_at=_now(),
                    error_category="runner_restart",
                )
                self._persist(job)
            self._jobs[job.job_id] = job


def _require_commit(commit: str) -> None:
    if not isinstance(commit, str) or _COMMIT_RE.fullmatch(commit) is None:
        raise FabricUpdateError("fabric_update_commit_invalid")



def _promote_inactive_bundle_noreplace(
    local_bundles_root: Path,
    incoming_name: str,
    commit: str,
) -> None:
    """Promoveer één reeds gevalideerde bundel zonder een ander slot te vervangen.

    Het bestaande `stage_local_bundle` bouwt eerst in
    `local-bundles/.incoming-<uuid>/source/bundle`. Deze functie doet alleen
    de atomaire *naamwijziging* naar `local-bundles/<commit>` en fsync; geen
    downloads, installer, BOOTSTRAP-aanroep, service- of actieve bundle-wijziging.
    Bij een gelijktijdig bestaande bestemming blijft die onaangeraakt.
    """
    _require_commit(commit)
    if (
        type(incoming_name) is not str
        or re.fullmatch(r"\.incoming-[0-9a-f]{32}", incoming_name) is None
        or not isinstance(local_bundles_root, Path)
        or not local_bundles_root.is_absolute()
    ):
        raise FabricUpdateError("fabric_bundle_storage_conflict")

    root_fd = -1
    incoming_fd = -1
    source_fd = -1
    bundle_fd = -1
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    try:
        # Root en werkboom komen uitsluitend uit de bestaande update-manager.
        # Open elk niveau met O_NOFOLLOW en houd directory descriptors vast.
        original = os.lstat(local_bundles_root)
        if (
            not stat.S_ISDIR(original.st_mode)
            or original.st_uid != os.geteuid()
            or stat.S_IMODE(original.st_mode) != 0o700
        ):
            raise FabricUpdateError("fabric_bundle_storage_conflict")
        root_fd = os.open(local_bundles_root, flags)
        pinned = os.fstat(root_fd)
        if (pinned.st_dev, pinned.st_ino) != (
            original.st_dev, original.st_ino
        ):
            raise FabricUpdateError("fabric_bundle_storage_conflict")
        incoming_fd = os.open(incoming_name, flags, dir_fd=root_fd)
        source_fd = os.open("source", flags, dir_fd=incoming_fd)
        bundle_fd = os.open("bundle", flags, dir_fd=source_fd)
        # .incoming is altijd door deze manager met 0700 aangemaakt.
        # Een gewone git clone maakt source soms met 0755 aan; dat is
        # veilig onder de privé-ouder zolang geen andere actor mag schrijven.
        for fd in (incoming_fd, source_fd, bundle_fd):
            item = os.fstat(fd)
            mode = stat.S_IMODE(item.st_mode)
            if item.st_uid != os.geteuid() or mode & 0o022:
                raise FabricUpdateError("fabric_bundle_storage_conflict")
            if fd == incoming_fd and mode != 0o700:
                raise FabricUpdateError("fabric_bundle_storage_conflict")

        # Reuse the same renameat2(RENAME_NOREPLACE) primitive as historical
        # Q7 custody. The source path is completely fixed below this private
        # root; a caller can never inject a path or a different destination.
        _promote_noreplace(
            root_fd, incoming_name + "/source/bundle", commit
        )
        os.fsync(root_fd)
    except (OSError, ValueError) as exc:
        raise FabricUpdateError("fabric_bundle_storage_conflict") from exc
    finally:
        for fd in (bundle_fd, source_fd, incoming_fd, root_fd):
            if fd >= 0:
                os.close(fd)


def _private_dir(path: Path, *, create: bool, parents: bool = False) -> Path:
    if not path.is_absolute() or path.is_symlink():
        raise FabricUpdateError("fabric_update_storage_invalid")
    try:
        if create:
            path.mkdir(mode=0o700, parents=parents, exist_ok=True)
            os.chmod(path, 0o700)
        resolved = path.resolve(strict=True)
        info = resolved.stat()
    except OSError as exc:
        raise FabricUpdateError("fabric_update_storage_invalid") from exc
    if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise FabricUpdateError("fabric_update_storage_invalid")
    return resolved


def _read_json(path: Path, max_bytes: int, category: str) -> dict[str, Any]:
    try:
        info = path.lstat()
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_uid != os.getuid()
            or info.st_size <= 0
            or info.st_size > max_bytes
        ):
            raise FabricUpdateError(category)
        raw = json.loads(path.read_text("utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise FabricUpdateError(category) from exc
    if not isinstance(raw, dict):
        raise FabricUpdateError(category)
    return raw



def _read_regular(path: Path, max_bytes: int, category: str) -> bytes:
    try:
        info = path.lstat()
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_uid != os.getuid()
            or info.st_nlink != 1
            or info.st_size <= 0
            or info.st_size > max_bytes
        ):
            raise FabricUpdateError(category)
        raw = path.read_bytes()
    except OSError as exc:
        raise FabricUpdateError(category) from exc
    if len(raw) > max_bytes:
        raise FabricUpdateError(category)
    return raw


def _parse_sums(raw: bytes) -> dict[str, str]:
    try:
        lines = raw.decode("ascii").splitlines()
    except UnicodeDecodeError as exc:
        raise FabricUpdateError("fabric_bundle_invalid") from exc
    rows: dict[str, str] = {}
    for line in lines:
        parts = line.split(maxsplit=1)
        if len(parts) != 2:
            raise FabricUpdateError("fabric_bundle_invalid")
        digest, name = parts
        if (
            re.fullmatch(r"[0-9a-f]{64}", digest) is None
            or not name
            or name in rows
            or "/" in name
            or "\\" in name
        ):
            raise FabricUpdateError("fabric_bundle_invalid")
        rows[name] = digest
    if not rows:
        raise FabricUpdateError("fabric_bundle_invalid")
    return rows

def _category(exc: FabricUpdateError) -> str:
    value = str(exc)
    allowed = {
        "operator_stop",
        "runner_mcp_state_unavailable",
        "runner_mcp_self_update_active",
        "runner_mcp_restart_pending",
        "runner_mcp_install_recovery_pending",
        "fabric_launcher_unmanaged",
        "fabric_recovery_required",
        "fabric_transaction_invalid",
        "fabric_artifact_unavailable",
        "actions_run_unavailable",
        "artifact_metadata_unavailable",
        "artifact_download_unavailable",
        "fabric_bundle_invalid",
        "fabric_bundle_integrity_failed",
        "fabric_bundle_storage_conflict",
        "fabric_bundle_recovery_failed",
        "fabric_preflight_failed",
        "fabric_apply_failed",
        "rollback_failed",
        "fabric_update_failed",
        "fabric_update_source_invalid",
    }
    return value if value in allowed else "fabric_update_failed"


def _now() -> datetime:
    return datetime.now(UTC)


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value is not None else None


def _parse(value: object) -> datetime:
    parsed = _parse_optional(value)
    if parsed is None:
        raise ValueError
    return parsed


def _parse_optional(value: object) -> datetime | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError
    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        raise ValueError
    return parsed.astimezone(UTC)
