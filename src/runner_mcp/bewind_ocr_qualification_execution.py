"""Fixed one-shot Bewind OCR qualification execution on the qualified worker."""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import subprocess
import time
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .bewind_ocr_qualification_staging import (
    BewindOcrQualificationStager,
    BewindOcrQualificationStagingError,
)
from .fabric_disposable_target import FabricDisposableTargetQualificationRunner
from .operational_safety import ActionClass, OperatorSafetyGuard

_WORKER_ID = "aifordable-lab"
_CAPABILITY = "bewind-ocr-qualification-v1"
_GENERATION = 1
_LANGUAGES = "nld+fra+deu"
_PIPELINE = "pre1997-ocrmypdf-sidecar-0.2.0"
_SOURCE_ID = "2026/02/03_1.pdf"
_REQUIRED_TERMS = (
    "Friedensgericht",
    "Bestellung eines Betreuers",
    "Schutzregelung der Vertretung",
)
_EXECUTION_ENV = "RUNNER_MCP_BEWIND_OCR_QUALIFICATION_EXECUTION_JSON"
_TARGET_ENV = "RUNNER_FABRIC_DISPOSABLE_TARGET_QUALIFICATION_CONFIG"
_EXECUTION_SCHEMA = "runner-mcp/bewind-ocr-qualification-execution/v1"
_RESULT_SCHEMA = "runner-mcp/bewind-ocr-qualification-result/v1"
_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_MAX_CAPTURE = 64 * 1024
_MAX_PAGES = 1000
_GUEST_INPUT = "/tmp/bewind-qualification.pdf"
_GUEST_SIDECAR = "/tmp/bewind-qualification-sidecar.txt"


class BewindOcrQualificationExecutionError(RuntimeError):
    """Sanitized fixed OCR qualification execution failure."""


class _QualificationFailure(RuntimeError):
    def __init__(self, category: str) -> None:
        super().__init__(category)
        self.category = category


class BewindOcrQualificationRunner:
    """Execute exactly one canonical OCR qualification unit and clean all state."""

    def __init__(
        self,
        *,
        safety: OperatorSafetyGuard,
        environment: Mapping[str, str],
        config_dir: Path,
        stager: BewindOcrQualificationStager,
        disposable_qualifier: FabricDisposableTargetQualificationRunner,
        readiness_provider: Callable[[], Mapping[str, Any]],
        command_runner=subprocess.run,
        monotonic=time.monotonic,
        loadavg=os.getloadavg,
    ) -> None:
        self.safety = safety
        self.environment = environment
        self.config_dir = config_dir.expanduser().resolve()
        self.stager = stager
        self.disposable_qualifier = disposable_qualifier
        self.readiness_provider = readiness_provider
        self._command_runner = command_runner
        self._monotonic = monotonic
        self._loadavg = loadavg

    def run(self) -> dict[str, Any]:
        self.safety.assert_action_allowed(ActionClass.DEPLOY)
        try:
            execution = self._execution_config()
            self._require_fabric_revision(execution["fabric_revision"])
            self._require_worker_readiness()

            qualification = self.disposable_qualifier.run()
            if (
                qualification.get("qualificationPassed") is not True
                or qualification.get("finalState") != "destroyed"
                or qualification.get("normalActivationEnabled") is not False
            ):
                raise BewindOcrQualificationExecutionError(
                    "bewind_ocr_qualification_preflight_failed"
                )

            staged = self.stager.require_staged()
            target = self._target_config()
        except BewindOcrQualificationExecutionError as exc:
            reason_map = {
                "bewind_ocr_qualification_execution_authority_unavailable": (
                    "execution-authority-unavailable"
                ),
                "bewind_ocr_qualification_execution_authority_invalid": (
                    "execution-authority-invalid"
                ),
                "bewind_ocr_qualification_fabric_revision_unavailable": (
                    "fabric-revision-unavailable"
                ),
                "bewind_ocr_qualification_fabric_revision_mismatch": (
                    "fabric-revision-mismatch"
                ),
                "bewind_ocr_qualification_readiness_unavailable": (
                    "readiness-unavailable"
                ),
                "bewind_ocr_qualification_readiness_blocked": (
                    "readiness-blocked"
                ),
                "bewind_ocr_qualification_preflight_failed": (
                    "disposable-preflight-failed"
                ),
                "bewind_ocr_qualification_target_unavailable": (
                    "target-unavailable"
                ),
                "bewind_ocr_qualification_target_invalid": "target-invalid",
                "bewind_ocr_qualification_target_expired": "target-expired",
            }
            return {
                "schemaVersion": "runner-mcp/bewind-ocr-qualification-preflight/v1",
                "state": "blocked",
                "reasonCode": reason_map.get(
                    str(exc),
                    "execution-preflight-unavailable",
                ),
                "normalActivationEnabled": False,
            }
        except BewindOcrQualificationStagingError as exc:
            reason_map = {
                "qualification staging state is unavailable": (
                    "staging-state-unavailable"
                ),
                "qualification staging state is unsafe": (
                    "staging-state-unsafe"
                ),
                "qualification staging receipt is invalid": (
                    "staging-receipt-invalid"
                ),
                "staged qualification source is unavailable": (
                    "staged-source-unavailable"
                ),
                "staged qualification source size does not match": (
                    "staged-source-size-mismatch"
                ),
                "staged qualification source digest does not match": (
                    "staged-source-digest-mismatch"
                ),
            }
            return {
                "schemaVersion": "runner-mcp/bewind-ocr-qualification-preflight/v1",
                "state": "blocked",
                "reasonCode": reason_map.get(
                    str(exc),
                    "staging-preflight-unavailable",
                ),
                "normalActivationEnabled": False,
            }
        started = self._monotonic()
        start_load = self._bounded_load()
        sidecar_path = self.config_dir / "bewind-ocr-qualification" / "result-sidecar.txt"
        page_hashes: tuple[str, ...] = ()
        output_sha = None
        pages = None
        cpu_seconds_per_page = None
        failure_category = None
        target_cleanup = False
        staging_cleanup = False

        try:
            self._require_clean_start(target)
            self._create_target(target)
            self._require_guest_runtime(target)
            self._push_source(
                target,
                staged.staged_path,
                expected_sha=staged.source_sha256,
                expected_size=staged.size_bytes,
            )
            pages = self._page_count(target)
            cpu_before = self._guest_cpu_seconds(target)
            self._execute_ocr(target)
            cpu_after = self._guest_cpu_seconds(target)
            cpu_seconds_per_page = round(
                max(0.0, cpu_after - cpu_before) / pages,
                6,
            )
            self._pull_sidecar(target, sidecar_path)
            page_hashes, output_sha = self._validate_output(
                sidecar_path,
                expected_pages=pages,
                expected_source_sha=staged.source_sha256,
            )
        except _QualificationFailure as exc:
            failure_category = exc.category
        except (OSError, subprocess.SubprocessError, ValueError):
            failure_category = "runtime-unavailable"
        finally:
            try:
                target_cleanup = self._cleanup_target(target)
            except (
                OSError,
                subprocess.SubprocessError,
                ValueError,
                _QualificationFailure,
            ):
                target_cleanup = False
            try:
                self.stager.cleanup()
                staging_cleanup = True
            except BewindOcrQualificationStagingError:
                staging_cleanup = False
            try:
                if sidecar_path.exists() or sidecar_path.is_symlink():
                    sidecar_path.unlink()
            except OSError:
                target_cleanup = False

        elapsed = round(max(0.0, self._monotonic() - started), 3)
        cleanup_ok = target_cleanup and staging_cleanup
        if failure_category is None and not cleanup_ok:
            failure_category = "cleanup-failed"

        if failure_category is not None:
            return {
                "schemaVersion": _RESULT_SCHEMA,
                "state": "failed" if cleanup_ok else "recovery-required",
                "workerId": _WORKER_ID,
                "capabilityProfile": _CAPABILITY,
                "generation": _GENERATION,
                "bewindRevision": execution["bewind_revision"],
                "fabricRevision": execution["fabric_revision"],
                "pipeline": _PIPELINE,
                "languages": _LANGUAGES,
                "sourceId": _SOURCE_ID,
                "sourceSha256": staged.source_sha256,
                "failureCategory": failure_category,
                "cleanupReceipt": {
                    "targetDestroyed": target_cleanup,
                    "stagedInputRemoved": staging_cleanup,
                },
                "normalActivationEnabled": False,
            }

        return {
            "schemaVersion": _RESULT_SCHEMA,
            "state": "qualified",
            "workerId": _WORKER_ID,
            "capabilityProfile": _CAPABILITY,
            "generation": _GENERATION,
            "bewindRevision": execution["bewind_revision"],
            "fabricRevision": execution["fabric_revision"],
            "pipeline": _PIPELINE,
            "languages": _LANGUAGES,
            "sourceId": _SOURCE_ID,
            "sourceSha256": staged.source_sha256,
            "pageCount": pages,
            "pageSha256": list(page_hashes),
            "outputSha256": output_sha,
            "germanSentinelVerified": True,
            "elapsedWallSeconds": elapsed,
            "cpuSecondsPerPage": cpu_seconds_per_page,
            "loadSummary": {
                "start": start_load,
                "end": self._bounded_load(),
            },
            "failureCategory": None,
            "cleanupReceipt": {
                "targetDestroyed": True,
                "stagedInputRemoved": True,
            },
            "normalActivationEnabled": False,
        }

    def _execution_config(self) -> dict[str, str]:
        raw = self.environment.get(_EXECUTION_ENV)
        if not isinstance(raw, str) or not raw.strip() or len(raw.encode()) > 8192:
            raise BewindOcrQualificationExecutionError(
                "bewind_ocr_qualification_execution_authority_unavailable"
            )
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise BewindOcrQualificationExecutionError(
                "bewind_ocr_qualification_execution_authority_invalid"
            ) from exc
        if not isinstance(payload, dict) or set(payload) != {
            "schemaVersion",
            "worker_id",
            "capability_profile",
            "generation",
            "fabric_revision",
            "bewind_revision",
        }:
            raise BewindOcrQualificationExecutionError(
                "bewind_ocr_qualification_execution_authority_invalid"
            )
        if (
            payload["schemaVersion"] != _EXECUTION_SCHEMA
            or payload["worker_id"] != _WORKER_ID
            or payload["capability_profile"] != _CAPABILITY
            or payload["generation"] != _GENERATION
            or not isinstance(payload["fabric_revision"], str)
            or _COMMIT_RE.fullmatch(payload["fabric_revision"]) is None
            or not isinstance(payload["bewind_revision"], str)
            or _COMMIT_RE.fullmatch(payload["bewind_revision"]) is None
        ):
            raise BewindOcrQualificationExecutionError(
                "bewind_ocr_qualification_execution_authority_invalid"
            )
        return payload

    def _require_fabric_revision(self, expected: str) -> None:
        home = Path.home().resolve()
        launcher = home / ".local/bin/runner-fabric"
        try:
            metadata = launcher.lstat()
            if not stat.S_ISLNK(metadata.st_mode):
                raise OSError
            resolved = launcher.resolve(strict=True)
            slot = (
                home
                / ".local/state/runner-fabric/control-plane-update/slots"
                / expected
            ).resolve(strict=True)
        except OSError as exc:
            raise BewindOcrQualificationExecutionError(
                "bewind_ocr_qualification_fabric_revision_unavailable"
            ) from exc
        if not resolved.is_relative_to(slot):
            raise BewindOcrQualificationExecutionError(
                "bewind_ocr_qualification_fabric_revision_mismatch"
            )

    def _require_worker_readiness(self) -> None:
        try:
            readiness = self.readiness_provider()
        except Exception as exc:
            raise BewindOcrQualificationExecutionError(
                "bewind_ocr_qualification_readiness_unavailable"
            ) from exc
        generation = readiness.get("currentGeneration")
        if (
            readiness.get("activationReady") is not True
            or generation != _GENERATION
        ):
            raise BewindOcrQualificationExecutionError(
                "bewind_ocr_qualification_readiness_blocked"
            )

    def _target_config(self) -> dict[str, Any]:
        raw_path = self.environment.get(_TARGET_ENV)
        if not isinstance(raw_path, str) or not raw_path or "\x00" in raw_path:
            raise BewindOcrQualificationExecutionError(
                "bewind_ocr_qualification_target_unavailable"
            )
        path = Path(raw_path)
        if not path.is_absolute():
            raise BewindOcrQualificationExecutionError(
                "bewind_ocr_qualification_target_unavailable"
            )
        try:
            metadata = path.lstat()
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise BewindOcrQualificationExecutionError(
                "bewind_ocr_qualification_target_unavailable"
            ) from exc
        if (
            not stat.S_ISREG(metadata.st_mode)
            or path.is_symlink()
            or metadata.st_mode & 0o077
            or not isinstance(payload, dict)
        ):
            raise BewindOcrQualificationExecutionError(
                "bewind_ocr_qualification_target_unavailable"
            )
        required = {
            "project_name",
            "instance_name",
            "network_name",
            "storage_pool_name",
            "image_remote",
            "image_fingerprint",
            "cpu_count",
            "memory_mib",
            "root_disk_gib",
            "binding_expires_at",
            "incus_executable",
        }
        if not required.issubset(payload):
            raise BewindOcrQualificationExecutionError(
                "bewind_ocr_qualification_target_invalid"
            )
        if payload["incus_executable"] != "/usr/bin/incus":
            raise BewindOcrQualificationExecutionError(
                "bewind_ocr_qualification_target_invalid"
            )
        fingerprint = payload["image_fingerprint"]
        if not isinstance(fingerprint, str) or _SHA256_RE.fullmatch(fingerprint) is None:
            raise BewindOcrQualificationExecutionError(
                "bewind_ocr_qualification_target_invalid"
            )
        try:
            expires = datetime.fromisoformat(payload["binding_expires_at"])
        except (TypeError, ValueError) as exc:
            raise BewindOcrQualificationExecutionError(
                "bewind_ocr_qualification_target_invalid"
            ) from exc
        if (
            expires.tzinfo is None
            or datetime.now(UTC) >= expires.astimezone(UTC)
        ):
            raise BewindOcrQualificationExecutionError(
                "bewind_ocr_qualification_target_expired"
            )
        return payload

    def _incus(
        self,
        args: tuple[str, ...],
        *,
        timeout: int = 120,
    ) -> subprocess.CompletedProcess[str]:
        try:
            result = self._command_runner(
                ("/usr/bin/incus", *args),
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
            raise _QualificationFailure("incus-unavailable") from exc
        stdout = result.stdout if isinstance(result.stdout, str) else ""
        stderr = result.stderr if isinstance(result.stderr, str) else ""
        if len(stdout.encode(errors="replace")) > _MAX_CAPTURE or len(
            stderr.encode(errors="replace")
        ) > _MAX_CAPTURE:
            raise _QualificationFailure("bounded-output-exceeded")
        return result

    def _require_ok(
        self,
        args: tuple[str, ...],
        *,
        timeout: int = 120,
        category: str,
    ) -> subprocess.CompletedProcess[str]:
        result = self._incus(args, timeout=timeout)
        if result.returncode != 0:
            raise _QualificationFailure(category)
        return result

    def _json_names(self, args: tuple[str, ...], *, category: str) -> set[str]:
        result = self._require_ok(args, category=category)
        try:
            payload = json.loads(result.stdout or "[]")
        except json.JSONDecodeError as exc:
            raise _QualificationFailure(category) from exc
        if not isinstance(payload, list):
            raise _QualificationFailure(category)
        return {
            str(item.get("name"))
            for item in payload
            if isinstance(item, dict) and isinstance(item.get("name"), str)
        }

    def _require_clean_start(self, target: Mapping[str, Any]) -> None:
        projects = self._json_names(
            ("project", "list", "--format=json"),
            category="clean-start-unavailable",
        )
        networks = self._json_names(
            ("--project", "default", "network", "list", "--format=json"),
            category="clean-start-unavailable",
        )
        if (
            target["project_name"] in projects
            or target["network_name"] in networks
        ):
            raise _QualificationFailure("clean-start-not-empty")

    def _create_target(self, target: Mapping[str, Any]) -> None:
        p = str(target["project_name"])
        n = str(target["network_name"])
        i = str(target["instance_name"])
        self._require_ok(
            (
                "project", "create", p,
                "--config", "features.images=false",
                "--config", "features.profiles=false",
                "--config", "features.networks=false",
                "--config", "features.storage.volumes=true",
                "--config", "limits.instances=1",
                "--config", "limits.virtual-machines=1",
            ),
            category="target-create-failed",
        )
        self._require_ok(
            (
                "--project", "default", "network", "create", n,
                "--type", "bridge",
                "ipv4.address=auto",
                "ipv4.nat=false",
                "ipv4.routing=false",
                "ipv6.address=none",
                "dns.mode=none",
                "raw.dnsmasq=dhcp-option=3",
            ),
            category="target-create-failed",
        )
        image = f"{target['image_remote']}:{target['image_fingerprint']}"
        self._require_ok(
            (
                "--project", p, "create", image, i, "--vm", "--no-profiles",
                "--storage", str(target["storage_pool_name"]),
                "--network", n,
                "--config", f"limits.cpu={int(target['cpu_count'])}",
                "--config", f"limits.memory={int(target['memory_mib'])}MiB",
                "--config", "boot.autostart=false",
                "--device", f"root,size={int(target['root_disk_gib'])}GiB",
            ),
            category="target-create-failed",
        )
        self._require_ok(
            ("--project", p, "start", i),
            category="target-create-failed",
        )
        for _ in range(12):
            probe = self._incus(
                ("--project", p, "exec", i, "--", "true"),
                timeout=10,
            )
            if probe.returncode == 0:
                return
            time.sleep(1)
        raise _QualificationFailure("guest-agent-not-ready")

    def _require_guest_runtime(self, target: Mapping[str, Any]) -> None:
        p = str(target["project_name"])
        i = str(target["instance_name"])
        self._require_ok(
            ("--project", p, "exec", i, "--", "ocrmypdf", "--version"),
            category="ocr-runtime-unavailable",
        )
        langs = self._require_ok(
            ("--project", p, "exec", i, "--", "tesseract", "--list-langs"),
            category="ocr-runtime-unavailable",
        ).stdout.splitlines()
        available = {line.strip() for line in langs}
        if not {"nld", "fra", "deu"}.issubset(available):
            raise _QualificationFailure("ocr-language-set-unavailable")
        default_route = self._incus(
            ("--project", p, "exec", i, "--", "ip", "route", "show", "default")
        )
        if default_route.returncode != 0 or default_route.stdout.strip():
            raise _QualificationFailure("isolation-default-route")
        for socket_path in ("/var/lib/incus/unix.socket", "/var/lib/lxd/unix.socket"):
            probe = self._incus(
                ("--project", p, "exec", i, "--", "stat", socket_path)
            )
            if probe.returncode == 0:
                raise _QualificationFailure("isolation-management-authority")

    def _push_source(
        self,
        target: Mapping[str, Any],
        staged_path: Path,
        *,
        expected_sha: str,
        expected_size: int,
    ) -> None:
        p = str(target["project_name"])
        i = str(target["instance_name"])
        self._require_ok(
            (
                "--project", p, "file", "push", str(staged_path),
                f"{i}{_GUEST_INPUT}",
            ),
            category="source-transfer-failed",
        )
        digest = self._require_ok(
            (
                "--project",
                p,
                "exec",
                i,
                "--",
                "sha256sum",
                _GUEST_INPUT,
            ),
            category="source-transfer-verification-failed",
        ).stdout.split()
        if (
            len(digest) < 1
            or _SHA256_RE.fullmatch(digest[0]) is None
            or digest[0] != expected_sha
        ):
            raise _QualificationFailure("source-transfer-verification-failed")

        size_result = self._require_ok(
            (
                "--project",
                p,
                "exec",
                i,
                "--",
                "stat",
                "-c",
                "%s",
                _GUEST_INPUT,
            ),
            category="source-transfer-verification-failed",
        )
        try:
            observed_size = int(size_result.stdout.strip())
        except ValueError as exc:
            raise _QualificationFailure(
                "source-transfer-verification-failed"
            ) from exc
        if observed_size != expected_size:
            raise _QualificationFailure("source-transfer-verification-failed")

    def _page_count(self, target: Mapping[str, Any]) -> int:
        p = str(target["project_name"])
        i = str(target["instance_name"])
        result = self._require_ok(
            ("--project", p, "exec", i, "--", "pdfinfo", _GUEST_INPUT),
            category="source-inspection-failed",
        )
        for line in result.stdout.splitlines():
            if line.startswith("Pages:"):
                try:
                    pages = int(line.split(":", 1)[1].strip())
                except ValueError as exc:
                    raise _QualificationFailure("source-inspection-failed") from exc
                if 1 <= pages <= _MAX_PAGES:
                    return pages
        raise _QualificationFailure("source-inspection-failed")

    def _guest_cpu_seconds(self, target: Mapping[str, Any]) -> float:
        p = str(target["project_name"])
        i = str(target["instance_name"])
        tick_result = self._require_ok(
            (
                "--project",
                p,
                "exec",
                i,
                "--",
                "getconf",
                "CLK_TCK",
            ),
            category="cpu-measurement-unavailable",
        )
        try:
            ticks_per_second = int(tick_result.stdout.strip())
        except ValueError as exc:
            raise _QualificationFailure(
                "cpu-measurement-unavailable"
            ) from exc
        if not 1 <= ticks_per_second <= 1_000_000:
            raise _QualificationFailure("cpu-measurement-unavailable")

        stat_result = self._require_ok(
            (
                "--project",
                p,
                "exec",
                i,
                "--",
                "cat",
                "/proc/stat",
            ),
            category="cpu-measurement-unavailable",
        )
        cpu_line = next(
            (
                line
                for line in stat_result.stdout.splitlines()
                if line.startswith("cpu ")
            ),
            None,
        )
        if cpu_line is None:
            raise _QualificationFailure("cpu-measurement-unavailable")
        fields = cpu_line.split()[1:]
        if len(fields) < 8:
            raise _QualificationFailure("cpu-measurement-unavailable")
        try:
            ticks = [int(value) for value in fields[:8]]
        except ValueError as exc:
            raise _QualificationFailure(
                "cpu-measurement-unavailable"
            ) from exc
        if any(value < 0 for value in ticks):
            raise _QualificationFailure("cpu-measurement-unavailable")

        # Linux /proc/stat fields: user nice system idle iowait irq softirq steal.
        # Exclude idle + iowait; the VM is dedicated to this one bounded run.
        busy_ticks = sum(ticks[index] for index in (0, 1, 2, 5, 6, 7))
        return busy_ticks / ticks_per_second

    def _execute_ocr(self, target: Mapping[str, Any]) -> None:
        p = str(target["project_name"])
        i = str(target["instance_name"])
        self._require_ok(
            (
                "--project", p, "exec", i, "--",
                "ocrmypdf",
                "--force-ocr",
                "--output-type", "none",
                "--sidecar", _GUEST_SIDECAR,
                "--jobs", "4",
                "--tesseract-pagesegmode", "3",
                "-l", _LANGUAGES,
                _GUEST_INPUT,
                "-",
            ),
            timeout=600,
            category="ocr-execution-failed",
        )

    def _pull_sidecar(self, target: Mapping[str, Any], destination: Path) -> None:
        p = str(target["project_name"])
        i = str(target["instance_name"])
        destination.parent.mkdir(mode=0o700, exist_ok=True)
        destination.parent.chmod(0o700)
        if destination.exists():
            destination.unlink()
        self._require_ok(
            (
                "--project", p, "file", "pull",
                f"{i}{_GUEST_SIDECAR}",
                str(destination),
            ),
            category="ocr-output-unavailable",
        )
        try:
            destination.chmod(0o600)
        except OSError as exc:
            raise _QualificationFailure("ocr-output-unavailable") from exc

    def _validate_output(
        self,
        sidecar: Path,
        *,
        expected_pages: int,
        expected_source_sha: str,
    ) -> tuple[tuple[str, ...], str]:
        try:
            data = sidecar.read_bytes()
            text = data.decode("utf-8", errors="replace")
        except OSError as exc:
            raise _QualificationFailure("ocr-output-unavailable") from exc
        if not data:
            raise _QualificationFailure("ocr-output-empty")
        pages = text.split("\f")
        if len(pages) == expected_pages + 1 and not pages[-1].strip():
            pages.pop()
        if len(pages) != expected_pages:
            raise _QualificationFailure("ocr-page-count-mismatch")
        normalized = " ".join(text.casefold().split())
        if not all(
            " ".join(term.casefold().split()) in normalized
            for term in _REQUIRED_TERMS
        ):
            raise _QualificationFailure("german-sentinel-missing")
        page_hashes = tuple(
            hashlib.sha256((page.rstrip() + "\n").encode("utf-8")).hexdigest()
            for page in pages
        )
        if len(page_hashes) != expected_pages:
            raise _QualificationFailure("ocr-page-count-mismatch")
        if _SHA256_RE.fullmatch(expected_source_sha) is None:
            raise _QualificationFailure("source-digest-invalid")
        return page_hashes, hashlib.sha256(data).hexdigest()

    def _cleanup_target(self, target: Mapping[str, Any]) -> bool:
        p = str(target["project_name"])
        i = str(target["instance_name"])
        n = str(target["network_name"])
        ok = True
        instances = self._json_names(
            ("--project", p, "list", "--format=json"),
            category="cleanup-failed",
        ) if self._project_exists(p) else set()
        if (
            i in instances
            and self._incus(("--project", p, "delete", i, "--force")).returncode
            != 0
        ):
            ok = False
        if (
            self._project_exists(p)
            and self._incus(("project", "delete", p)).returncode != 0
        ):
            ok = False
        networks = self._json_names(
            ("--project", "default", "network", "list", "--format=json"),
            category="cleanup-failed",
        )
        if (
            n in networks
            and self._incus(
                ("--project", "default", "network", "delete", n)
            ).returncode
            != 0
        ):
            ok = False
        return ok and not self._project_exists(p) and n not in self._json_names(
            ("--project", "default", "network", "list", "--format=json"),
            category="cleanup-failed",
        )

    def _project_exists(self, project: str) -> bool:
        try:
            return project in self._json_names(
                ("project", "list", "--format=json"),
                category="cleanup-failed",
            )
        except _QualificationFailure:
            return True

    def _bounded_load(self) -> dict[str, float | int]:
        try:
            load1, load5, load15 = self._loadavg()
        except OSError:
            load1 = load5 = load15 = 0.0
        return {
            "logicalCpus": os.cpu_count() or 1,
            "load1m": round(float(load1), 3),
            "load5m": round(float(load5), 3),
            "load15m": round(float(load15), 3),
        }
