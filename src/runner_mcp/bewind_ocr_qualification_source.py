"""Provision the fixed Bewind OCR qualification source into private artifact custody."""

from __future__ import annotations

import hashlib
import json
import stat
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from urllib.error import URLError
from urllib.request import Request, urlopen

from .artifact_custody import ArtifactCustodyError, ContentAddressedArtifactCustody
from .operational_safety import ActionClass, OperatorSafetyGuard
from .secure_io import PrivateAtomicWriteError, atomic_replace_private

_WORKER_ID = "aifordable-lab"
_CAPABILITY = "bewind-ocr-qualification-v1"
_SOURCE_ID = "2026/02/03_1.pdf"
_SOURCE_URL = "https://www.ejustice.just.fgov.be/mopdf/2026/02/03_1.pdf"
_EXPECTED_SHA256 = "80a0fc4a561f26527aa7fb6dcc89209310f5af73a96e4e030f213faf76defa46"
_EXPECTED_SIZE_BYTES = 2_811_759
_BINDING_SCHEMA = "runner-mcp/bewind-ocr-qualification-source/v1"
_RESULT_SCHEMA = "runner-mcp/bewind-ocr-qualification-source-provision/v1"
_MAX_DOWNLOAD_BYTES = _EXPECTED_SIZE_BYTES + 1
_ALLOWED_HOST = "www.ejustice.just.fgov.be"


class BewindOcrQualificationSourceProvisionError(RuntimeError):
    """Sanitized failure from fixed source provisioning."""


class BewindOcrQualificationSourceProvisioner:
    """Fetch and bind exactly the canonical German sentinel."""

    def __init__(
        self,
        *,
        safety: OperatorSafetyGuard,
        config_dir: Path,
        custody: ContentAddressedArtifactCustody,
        opener=urlopen,
    ) -> None:
        self.safety = safety
        self.config_dir = config_dir.expanduser().resolve()
        self.custody = custody
        self._opener = opener
        self._binding = (
            self.config_dir
            / "bewind-ocr-qualification"
            / "source-binding.json"
        )

    def provision(self) -> dict[str, Any]:
        self.safety.assert_action_allowed(ActionClass.DEPLOY)

        try:
            artifact = self.custody.resolve(
                expected_sha256=_EXPECTED_SHA256,
                expected_size_bytes=_EXPECTED_SIZE_BYTES,
            )
            source_state = "hit"
        except ArtifactCustodyError:
            payload = self._download()
            try:
                artifact = self.custody.publish_bytes(
                    data=payload,
                    expected_sha256=_EXPECTED_SHA256,
                    expected_size_bytes=_EXPECTED_SIZE_BYTES,
                )
            except ArtifactCustodyError as exc:
                raise BewindOcrQualificationSourceProvisionError(
                    "qualification source custody publish failed"
                ) from exc
            source_state = artifact.cache_state

        self._write_binding(artifact.path)
        return {
            "schemaVersion": _RESULT_SCHEMA,
            "state": "ready",
            "workerId": _WORKER_ID,
            "capabilityProfile": _CAPABILITY,
            "sourceId": _SOURCE_ID,
            "sourceSha256": _EXPECTED_SHA256,
            "sizeBytes": _EXPECTED_SIZE_BYTES,
            "cache": source_state,
            "bindingReady": True,
            "normalActivationEnabled": False,
        }

    def _download(self) -> bytes:
        request = Request(
            _SOURCE_URL,
            headers={
                "User-Agent": (
                    "AIfordable-Runner-MCP/qualification "
                    "(fixed public legal-source sentinel)"
                ),
                "Accept": "application/pdf",
            },
            method="GET",
        )
        try:
            response = self._opener(request, timeout=60)
            with response:
                final_url = response.geturl()
                status = getattr(response, "status", None)
                if status != 200:
                    raise BewindOcrQualificationSourceProvisionError(
                        "qualification source download failed"
                    )
                parsed = urlparse(final_url)
                if parsed.scheme != "https" or parsed.hostname != _ALLOWED_HOST:
                    raise BewindOcrQualificationSourceProvisionError(
                        "qualification source redirect rejected"
                    )
                content_type = (
                    response.headers.get("Content-Type", "")
                    if response.headers is not None
                    else ""
                ).casefold()
                data = response.read(_MAX_DOWNLOAD_BYTES)
        except BewindOcrQualificationSourceProvisionError:
            raise
        except (OSError, URLError, ValueError) as exc:
            raise BewindOcrQualificationSourceProvisionError(
                "qualification source download unavailable"
            ) from exc

        if len(data) != _EXPECTED_SIZE_BYTES:
            raise BewindOcrQualificationSourceProvisionError(
                "qualification source download size mismatch"
            )
        if b"%PDF" not in data[:1024] and "pdf" not in content_type:
            raise BewindOcrQualificationSourceProvisionError(
                "qualification source download is not a PDF"
            )
        if hashlib.sha256(data).hexdigest() != _EXPECTED_SHA256:
            raise BewindOcrQualificationSourceProvisionError(
                "qualification source download digest mismatch"
            )
        return data

    def _write_binding(self, source_path: Path) -> None:
        parent = self._binding.parent
        if parent.is_symlink():
            raise BewindOcrQualificationSourceProvisionError(
                "qualification source binding directory is unsafe"
            )
        try:
            parent.mkdir(mode=0o700, exist_ok=True)
            parent.chmod(0o700)
            resolved_parent = parent.resolve(strict=True)
        except OSError as exc:
            raise BewindOcrQualificationSourceProvisionError(
                "qualification source binding directory unavailable"
            ) from exc
        if resolved_parent.parent != self.config_dir:
            raise BewindOcrQualificationSourceProvisionError(
                "qualification source binding directory is unsafe"
            )
        if resolved_parent.stat().st_mode & 0o777 != 0o700:
            raise BewindOcrQualificationSourceProvisionError(
                "qualification source binding directory is unsafe"
            )

        binding = {
            "schemaVersion": _BINDING_SCHEMA,
            "worker_id": _WORKER_ID,
            "capability_profile": _CAPABILITY,
            "source_id": _SOURCE_ID,
            "source_path": str(source_path),
            "expected_sha256": _EXPECTED_SHA256,
            "expected_size_bytes": _EXPECTED_SIZE_BYTES,
        }
        try:
            atomic_replace_private(
                self._binding,
                (
                    json.dumps(
                        binding,
                        sort_keys=True,
                        separators=(",", ":"),
                        ensure_ascii=True,
                        allow_nan=False,
                    )
                    + "\n"
                ).encode("utf-8"),
            )
        except PrivateAtomicWriteError as exc:
            raise BewindOcrQualificationSourceProvisionError(
                "qualification source binding persist failed"
            ) from exc

        try:
            metadata = self._binding.lstat()
        except OSError as exc:
            raise BewindOcrQualificationSourceProvisionError(
                "qualification source binding unavailable"
            ) from exc
        if (
            not stat.S_ISREG(metadata.st_mode)
            or self._binding.is_symlink()
            or metadata.st_mode & 0o077
        ):
            raise BewindOcrQualificationSourceProvisionError(
                "qualification source binding is unsafe"
            )
