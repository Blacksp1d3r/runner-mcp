"""Fixed content-addressed staging for one Bewind OCR qualification source."""

from __future__ import annotations

import hashlib
import json
import os
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .operational_safety import ActionClass, OperatorSafetyGuard
from .secure_io import PrivateAtomicWriteError, atomic_replace_private

_CONFIG_ENV = "RUNNER_MCP_BEWIND_OCR_QUALIFICATION_SOURCE_JSON"
_SCHEMA = "runner-mcp/bewind-ocr-qualification-source/v1"
_RESULT_SCHEMA = "runner-mcp/bewind-ocr-qualification-stage-result/v1"
_RECEIPT_SCHEMA = "runner-mcp/bewind-ocr-qualification-stage-receipt/v1"
_CAPABILITY = "bewind-ocr-qualification-v1"
_WORKER_ID = "aifordable-lab"
_SOURCE_ID = "2026/02/03_1.pdf"
_MAX_SOURCE_BYTES = 64 * 1024 * 1024
_DIGEST_HEX_LENGTH = 64


class BewindOcrQualificationStagingError(RuntimeError):
    """Sanitized staging failure for the fixed qualification source."""


@dataclass(frozen=True, slots=True)
class StagedBewindOcrSource:
    source_sha256: str
    size_bytes: int
    staged_path: Path


class BewindOcrQualificationStager:
    """Stage and consume exactly one trusted Bewind qualification source."""

    def __init__(
        self,
        *,
        safety: OperatorSafetyGuard,
        environment: dict[str, str] | Any,
        config_dir: Path,
    ) -> None:
        self.safety = safety
        self.environment = environment
        self.config_dir = config_dir.expanduser().resolve()
        self._root = self.config_dir / "bewind-ocr-qualification"
        self._stage_dir = self._root / "staged"
        self._receipt = self._root / "stage-receipt.json"
        self._source_binding = self._root / "source-binding.json"

    def stage(self) -> dict[str, Any]:
        self.safety.assert_action_allowed(ActionClass.DEPLOY)
        config = self._private_config()
        source = Path(config["source_path"]).expanduser()
        expected_sha = config["expected_sha256"]
        expected_size = config["expected_size_bytes"]

        data = self._read_source(
            source,
            expected_sha=expected_sha,
            expected_size=expected_size,
        )
        self._ensure_private_dir(self._root, self.config_dir)
        self._ensure_private_dir(self._stage_dir, self._root)

        staged_path = self._stage_dir / f"{expected_sha}.pdf"
        if staged_path.exists():
            self._verify_staged(
                staged_path,
                expected_sha=expected_sha,
                expected_size=expected_size,
            )
        else:
            try:
                atomic_replace_private(staged_path, data)
            except PrivateAtomicWriteError as exc:
                raise BewindOcrQualificationStagingError(
                    "qualification source could not be staged"
                ) from exc
            self._verify_staged(
                staged_path,
                expected_sha=expected_sha,
                expected_size=expected_size,
            )

        receipt = {
            "schemaVersion": _RECEIPT_SCHEMA,
            "workerId": _WORKER_ID,
            "capabilityProfile": _CAPABILITY,
            "sourceId": _SOURCE_ID,
            "sourceSha256": expected_sha,
            "sizeBytes": expected_size,
            "singleUse": True,
            "normalActivationEnabled": False,
        }
        try:
            atomic_replace_private(
                self._receipt,
                (
                    json.dumps(
                        receipt,
                        sort_keys=True,
                        separators=(",", ":"),
                        ensure_ascii=True,
                        allow_nan=False,
                    )
                    + "\n"
                ).encode("utf-8"),
            )
        except PrivateAtomicWriteError as exc:
            self._safe_unlink(staged_path)
            raise BewindOcrQualificationStagingError(
                "qualification staging receipt could not be written"
            ) from exc
        self._require_private_file(self._receipt)

        return {
            "schemaVersion": _RESULT_SCHEMA,
            "state": "ready",
            "reasonCode": "qualification-source-staged",
            "workerId": _WORKER_ID,
            "capabilityProfile": _CAPABILITY,
            "sourceId": _SOURCE_ID,
            "sourceSha256": expected_sha,
            "sizeBytes": expected_size,
            "singleUse": True,
            "normalActivationEnabled": False,
        }

    def require_staged(self) -> StagedBewindOcrSource:
        receipt = self._load_receipt()
        expected_sha = receipt["sourceSha256"]
        expected_size = receipt["sizeBytes"]
        staged_path = self._stage_dir / f"{expected_sha}.pdf"
        self._verify_staged(
            staged_path,
            expected_sha=expected_sha,
            expected_size=expected_size,
        )
        return StagedBewindOcrSource(
            source_sha256=expected_sha,
            size_bytes=expected_size,
            staged_path=staged_path,
        )

    def cleanup(self) -> dict[str, Any]:
        removed = False
        receipt = None
        try:
            receipt = self._load_receipt()
        except BewindOcrQualificationStagingError:
            if self._receipt.exists():
                self._safe_unlink(self._receipt)
            return {
                "state": "clean",
                "stagedInputPresent": False,
                "receiptPresent": False,
            }

        staged_path = self._stage_dir / f"{receipt['sourceSha256']}.pdf"
        if staged_path.exists():
            self._safe_unlink(staged_path)
            removed = True
        self._safe_unlink(self._receipt)
        return {
            "state": "clean",
            "stagedInputPresent": False,
            "receiptPresent": False,
            "removed": removed,
        }

    def _private_config(self) -> dict[str, Any]:
        raw = self.environment.get(_CONFIG_ENV)
        if isinstance(raw, str) and raw.strip():
            if len(raw.encode("utf-8")) > 16 * 1024:
                raise BewindOcrQualificationStagingError(
                    "qualification source authority is invalid"
                )
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise BewindOcrQualificationStagingError(
                    "qualification source authority is invalid"
                ) from exc
        else:
            self._require_private_file(self._source_binding)
            try:
                if self._source_binding.stat().st_size > 16 * 1024:
                    raise BewindOcrQualificationStagingError(
                        "qualification source authority is invalid"
                    )
                payload = json.loads(
                    self._source_binding.read_text(encoding="utf-8")
                )
            except (OSError, json.JSONDecodeError) as exc:
                raise BewindOcrQualificationStagingError(
                    "qualification source authority is unavailable"
                ) from exc
        if not isinstance(payload, dict) or set(payload) != {
            "schemaVersion",
            "worker_id",
            "capability_profile",
            "source_id",
            "source_path",
            "expected_sha256",
            "expected_size_bytes",
        }:
            raise BewindOcrQualificationStagingError(
                "qualification source authority is invalid"
            )
        if (
            payload["schemaVersion"] != _SCHEMA
            or payload["worker_id"] != _WORKER_ID
            or payload["capability_profile"] != _CAPABILITY
            or payload["source_id"] != _SOURCE_ID
        ):
            raise BewindOcrQualificationStagingError(
                "qualification source authority is invalid"
            )
        source_path = payload["source_path"]
        if not isinstance(source_path, str) or not source_path:
            raise BewindOcrQualificationStagingError(
                "qualification source authority is invalid"
            )
        if not Path(source_path).is_absolute():
            raise BewindOcrQualificationStagingError(
                "qualification source authority is invalid"
            )
        expected_sha = payload["expected_sha256"]
        if (
            not isinstance(expected_sha, str)
            or len(expected_sha) != _DIGEST_HEX_LENGTH
            or any(ch not in "0123456789abcdef" for ch in expected_sha)
        ):
            raise BewindOcrQualificationStagingError(
                "qualification source authority is invalid"
            )
        expected_size = payload["expected_size_bytes"]
        if (
            isinstance(expected_size, bool)
            or not isinstance(expected_size, int)
            or not 1 <= expected_size <= _MAX_SOURCE_BYTES
        ):
            raise BewindOcrQualificationStagingError(
                "qualification source authority is invalid"
            )
        return payload

    def _read_source(
        self,
        path: Path,
        *,
        expected_sha: str,
        expected_size: int,
    ) -> bytes:
        try:
            metadata = path.lstat()
        except OSError as exc:
            raise BewindOcrQualificationStagingError(
                "qualification source is unavailable"
            ) from exc
        if not stat.S_ISREG(metadata.st_mode) or path.is_symlink():
            raise BewindOcrQualificationStagingError(
                "qualification source is unavailable"
            )
        if metadata.st_size != expected_size or metadata.st_size > _MAX_SOURCE_BYTES:
            raise BewindOcrQualificationStagingError(
                "qualification source size does not match"
            )
        try:
            data = path.read_bytes()
        except OSError as exc:
            raise BewindOcrQualificationStagingError(
                "qualification source is unavailable"
            ) from exc
        if len(data) != expected_size:
            raise BewindOcrQualificationStagingError(
                "qualification source size does not match"
            )
        digest = hashlib.sha256(data).hexdigest()
        if digest != expected_sha:
            raise BewindOcrQualificationStagingError(
                "qualification source digest does not match"
            )
        return data

    def _load_receipt(self) -> dict[str, Any]:
        self._require_private_file(self._receipt)
        try:
            payload = json.loads(self._receipt.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise BewindOcrQualificationStagingError(
                "qualification staging receipt is invalid"
            ) from exc
        if (
            not isinstance(payload, dict)
            or payload.get("schemaVersion") != _RECEIPT_SCHEMA
            or payload.get("workerId") != _WORKER_ID
            or payload.get("capabilityProfile") != _CAPABILITY
            or payload.get("sourceId") != _SOURCE_ID
            or payload.get("singleUse") is not True
            or payload.get("normalActivationEnabled") is not False
        ):
            raise BewindOcrQualificationStagingError(
                "qualification staging receipt is invalid"
            )
        digest = payload.get("sourceSha256")
        size = payload.get("sizeBytes")
        if (
            not isinstance(digest, str)
            or len(digest) != _DIGEST_HEX_LENGTH
            or any(ch not in "0123456789abcdef" for ch in digest)
            or isinstance(size, bool)
            or not isinstance(size, int)
            or not 1 <= size <= _MAX_SOURCE_BYTES
        ):
            raise BewindOcrQualificationStagingError(
                "qualification staging receipt is invalid"
            )
        return payload

    def _verify_staged(
        self,
        path: Path,
        *,
        expected_sha: str,
        expected_size: int,
    ) -> None:
        self._require_private_file(path)
        try:
            data = path.read_bytes()
        except OSError as exc:
            raise BewindOcrQualificationStagingError(
                "staged qualification source is unavailable"
            ) from exc
        if len(data) != expected_size:
            raise BewindOcrQualificationStagingError(
                "staged qualification source size does not match"
            )
        if hashlib.sha256(data).hexdigest() != expected_sha:
            raise BewindOcrQualificationStagingError(
                "staged qualification source digest does not match"
            )

    @staticmethod
    def _ensure_private_dir(path: Path, parent: Path) -> None:
        if path.is_symlink():
            raise BewindOcrQualificationStagingError(
                "qualification staging directory is unsafe"
            )
        try:
            path.mkdir(mode=0o700, exist_ok=True)
            os.chmod(path, 0o700)
            resolved = path.resolve(strict=True)
        except OSError as exc:
            raise BewindOcrQualificationStagingError(
                "qualification staging directory is unavailable"
            ) from exc
        if resolved.parent != parent.resolve():
            raise BewindOcrQualificationStagingError(
                "qualification staging directory is unsafe"
            )
        if resolved.stat().st_mode & 0o777 != 0o700:
            raise BewindOcrQualificationStagingError(
                "qualification staging directory is unsafe"
            )

    @staticmethod
    def _require_private_file(path: Path) -> None:
        try:
            metadata = path.lstat()
        except OSError as exc:
            raise BewindOcrQualificationStagingError(
                "qualification staging state is unavailable"
            ) from exc
        if (
            not stat.S_ISREG(metadata.st_mode)
            or path.is_symlink()
            or metadata.st_mode & 0o077
        ):
            raise BewindOcrQualificationStagingError(
                "qualification staging state is unsafe"
            )

    @staticmethod
    def _safe_unlink(path: Path) -> None:
        try:
            if path.exists() or path.is_symlink():
                path.unlink()
        except OSError as exc:
            raise BewindOcrQualificationStagingError(
                "qualification staging cleanup failed"
            ) from exc
