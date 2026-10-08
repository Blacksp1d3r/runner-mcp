"""Prepare one trusted pre-baked Bewind OCR-ready Incus VM image."""

from __future__ import annotations

import json
import re
import socket
import subprocess
import time
from collections.abc import Callable
from typing import Any

from .operational_safety import ActionClass, OperatorSafetyGuard

_WORKER_ID = "aifordable-lab"
_BASE_ALIAS = "aifordable/bewind-ocr-podman-v1"
_TARGET_ALIAS = "aifordable/bewind-ocr-runtime-v1"
_TARGET_PROFILE = "bewind-ocr-runtime-v1"
_TARGET_RUNTIME = "ocrmypdf-tesseract-nld-fra-deu-ready"
_TARGET_USER = "fabric:1000:1000"
_TARGET_BASE = "aifordable/bewind-ocr-podman-v1"
_TARGET_LANGUAGES = "nld+fra+deu"
_BUILDER = "rf-bewind-ocr-runtime-builder"
_INCUS = "/usr/bin/incus"
_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
_MAX_CAPTURE = 64 * 1024
_PACKAGES = (
    "ocrmypdf",
    "poppler-utils",
    "tesseract-ocr",
    "tesseract-ocr-nld",
    "tesseract-ocr-fra",
    "tesseract-ocr-deu",
)


class BewindOcrRuntimeImagePrepareError(RuntimeError):
    """Sanitized fixed OCR runtime image preparation failure."""


class BewindOcrRuntimeImagePreparer:
    """Create exactly one local OCR-ready VM image from the trusted Podman base."""

    def __init__(
        self,
        *,
        safety: OperatorSafetyGuard,
        hostname_provider: Callable[[], str] = socket.gethostname,
        runner=subprocess.run,
        sleep=time.sleep,
    ) -> None:
        self.safety = safety
        self.hostname_provider = hostname_provider
        self._runner = runner
        self._sleep = sleep

    def prepare(self) -> dict[str, Any]:
        self.safety.assert_action_allowed(ActionClass.DEPLOY)
        if self.hostname_provider().strip().casefold() != _WORKER_ID:
            raise BewindOcrRuntimeImagePrepareError(
                "bewind_ocr_runtime_image_host_mismatch"
            )

        existing = self._trusted_target_images()
        if len(existing) == 1:
            return self._result(existing[0], state="ready", cache="hit")
        if len(existing) > 1:
            raise BewindOcrRuntimeImagePrepareError(
                "bewind_ocr_runtime_image_ambiguous"
            )

        if self._instance_exists(_BUILDER):
            raise BewindOcrRuntimeImagePrepareError(
                "bewind_ocr_runtime_image_builder_not_clean"
            )

        cleanup_ok = True
        published = False
        try:
            self._require_ok(
                ("launch", f"local:{_BASE_ALIAS}", _BUILDER, "--vm"),
                category="builder-create-failed",
                timeout=180,
            )
            self._wait_guest()

            self._require_ok(
                (
                    "exec",
                    _BUILDER,
                    "--",
                    "/usr/bin/env",
                    "DEBIAN_FRONTEND=noninteractive",
                    "apt-get",
                    "update",
                ),
                category="runtime-install-failed",
                timeout=300,
            )
            self._require_ok(
                (
                    "exec",
                    _BUILDER,
                    "--",
                    "/usr/bin/env",
                    "DEBIAN_FRONTEND=noninteractive",
                    "apt-get",
                    "install",
                    "-y",
                    "--no-install-recommends",
                    *_PACKAGES,
                ),
                category="runtime-install-failed",
                timeout=600,
            )
            self._validate_guest_runtime()

            self._require_ok(
                ("stop", _BUILDER, "--timeout", "60"),
                category="builder-stop-failed",
                timeout=120,
            )
            self._require_ok(
                ("publish", _BUILDER, "--alias", _TARGET_ALIAS),
                category="image-publish-failed",
                timeout=600,
            )
            published = True
            for key, value in (
                ("os", "Ubuntu"),
                ("release", "noble"),
                ("aifordable.profile", _TARGET_PROFILE),
                ("aifordable.runtime", _TARGET_RUNTIME),
                ("aifordable.user", _TARGET_USER),
                ("aifordable.base", _TARGET_BASE),
                ("aifordable.languages", _TARGET_LANGUAGES),
            ):
                self._require_ok(
                    ("image", "set-property", _TARGET_ALIAS, key, value),
                    category="image-metadata-failed",
                )
        finally:
            if self._instance_exists(_BUILDER):
                result = self._incus(
                    ("delete", _BUILDER, "--force"),
                    timeout=120,
                )
                cleanup_ok = result.returncode == 0

        if not cleanup_ok:
            raise BewindOcrRuntimeImagePrepareError(
                "bewind_ocr_runtime_image_cleanup_failed"
            )

        images = self._trusted_target_images()
        if len(images) != 1:
            if published:
                raise BewindOcrRuntimeImagePrepareError(
                    "bewind_ocr_runtime_image_publish_verification_failed"
                )
            raise BewindOcrRuntimeImagePrepareError(
                "bewind_ocr_runtime_image_unavailable"
            )
        return self._result(images[0], state="prepared", cache="miss")

    def _validate_guest_runtime(self) -> None:
        self._require_ok(
            ("exec", _BUILDER, "--", "ocrmypdf", "--version"),
            category="runtime-validation-failed",
        )
        self._require_ok(
            ("exec", _BUILDER, "--", "pdfinfo", "-v"),
            category="runtime-validation-failed",
        )
        langs = self._require_ok(
            ("exec", _BUILDER, "--", "tesseract", "--list-langs"),
            category="runtime-validation-failed",
        ).stdout.splitlines()
        available = {line.strip() for line in langs}
        if not {"nld", "fra", "deu"}.issubset(available):
            raise BewindOcrRuntimeImagePrepareError(
                "bewind_ocr_runtime_image_language_validation_failed"
            )

    def _wait_guest(self) -> None:
        for _ in range(30):
            probe = self._incus(
                ("exec", _BUILDER, "--", "true"),
                timeout=10,
            )
            if probe.returncode == 0:
                return
            self._sleep(1)
        raise BewindOcrRuntimeImagePrepareError(
            "bewind_ocr_runtime_image_guest_not_ready"
        )

    def _trusted_target_images(self) -> list[str]:
        payload = self._image_inventory()
        matches: list[str] = []
        for item in payload:
            if not isinstance(item, dict):
                continue
            fingerprint = item.get("fingerprint")
            aliases = item.get("aliases")
            properties = item.get("properties")
            if (
                str(item.get("type", "")).strip().casefold() != "virtual-machine"
                or not isinstance(fingerprint, str)
                or _HEX64_RE.fullmatch(fingerprint) is None
                or not isinstance(aliases, list)
                or not isinstance(properties, dict)
            ):
                continue
            alias_names = {
                str(alias.get("name", "")).strip()
                for alias in aliases
                if isinstance(alias, dict)
            }
            if _TARGET_ALIAS not in alias_names:
                continue
            if (
                str(properties.get("aifordable.profile", "")).strip()
                != _TARGET_PROFILE
                or str(properties.get("aifordable.runtime", "")).strip()
                != _TARGET_RUNTIME
                or str(properties.get("aifordable.user", "")).strip()
                != _TARGET_USER
                or str(properties.get("aifordable.base", "")).strip()
                != _TARGET_BASE
                or str(properties.get("aifordable.languages", "")).strip()
                != _TARGET_LANGUAGES
            ):
                raise BewindOcrRuntimeImagePrepareError(
                    "bewind_ocr_runtime_image_metadata_mismatch"
                )
            matches.append(fingerprint)
        return matches

    def _image_inventory(self) -> list[Any]:
        result = self._require_ok(
            ("image", "list", "--format=json"),
            category="image-inventory-unavailable",
        )
        try:
            payload = json.loads(result.stdout or "[]")
        except json.JSONDecodeError as exc:
            raise BewindOcrRuntimeImagePrepareError(
                "bewind_ocr_runtime_image_inventory_invalid"
            ) from exc
        if not isinstance(payload, list):
            raise BewindOcrRuntimeImagePrepareError(
                "bewind_ocr_runtime_image_inventory_invalid"
            )
        return payload

    def _instance_exists(self, name: str) -> bool:
        result = self._require_ok(
            ("list", "--format=json"),
            category="builder-state-unavailable",
        )
        try:
            payload = json.loads(result.stdout or "[]")
        except json.JSONDecodeError as exc:
            raise BewindOcrRuntimeImagePrepareError(
                "bewind_ocr_runtime_image_builder_state_invalid"
            ) from exc
        if not isinstance(payload, list):
            raise BewindOcrRuntimeImagePrepareError(
                "bewind_ocr_runtime_image_builder_state_invalid"
            )
        return any(
            isinstance(item, dict) and item.get("name") == name
            for item in payload
        )

    def _incus(
        self,
        args: tuple[str, ...],
        *,
        timeout: int = 120,
    ) -> subprocess.CompletedProcess[str]:
        try:
            result = self._runner(
                (_INCUS, *args),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=timeout,
                check=False,
                shell=False,
                cwd="/",
                env={"LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"},
            )
        except (OSError, subprocess.SubprocessError) as exc:
            raise BewindOcrRuntimeImagePrepareError(
                "bewind_ocr_runtime_image_incus_unavailable"
            ) from exc
        stdout = result.stdout if isinstance(result.stdout, str) else ""
        stderr = result.stderr if isinstance(result.stderr, str) else ""
        if (
            len(stdout.encode(errors="replace")) > _MAX_CAPTURE
            or len(stderr.encode(errors="replace")) > _MAX_CAPTURE
        ):
            raise BewindOcrRuntimeImagePrepareError(
                "bewind_ocr_runtime_image_output_exceeded"
            )
        return result

    def _require_ok(
        self,
        args: tuple[str, ...],
        *,
        category: str,
        timeout: int = 120,
    ) -> subprocess.CompletedProcess[str]:
        result = self._incus(args, timeout=timeout)
        if result.returncode != 0:
            raise BewindOcrRuntimeImagePrepareError(
                f"bewind_ocr_runtime_image_{category}"
            )
        return result

    @staticmethod
    def _result(
        fingerprint: str,
        *,
        state: str,
        cache: str,
    ) -> dict[str, Any]:
        return {
            "schemaVersion": "runner-mcp/bewind-ocr-runtime-image/v1",
            "state": state,
            "imageFingerprint": fingerprint,
            "profile": _TARGET_PROFILE,
            "runtime": _TARGET_RUNTIME,
            "languages": _TARGET_LANGUAGES,
            "cache": cache,
            "builderClean": True,
            "normalActivationEnabled": False,
        }
