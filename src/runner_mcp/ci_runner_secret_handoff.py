from __future__ import annotations

import os
import re
import secrets
import stat
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from .ci_runner_guest_enrollment import CIRunnerRegistrationSecret

_HANDOFF_RE = re.compile(r"^[0-9a-f]{32}$")
_MAX_SECRET_BYTES = 4096
_DEFAULT_TTL_SECONDS = 300


class CIRunnerSecretHandoffError(RuntimeError):
    """Bounded handoff failure without secret or private-path disclosure."""


@dataclass(frozen=True, slots=True)
class CIRunnerSecretHandoff:
    handoff_id: str
    expires_at: int

    def __post_init__(self) -> None:
        if _HANDOFF_RE.fullmatch(self.handoff_id) is None:
            raise CIRunnerSecretHandoffError("handoff id is invalid")
        if isinstance(self.expires_at, bool) or not isinstance(
            self.expires_at,
            int,
        ):
            raise CIRunnerSecretHandoffError("handoff expiry is invalid")

    def to_payload(self) -> dict[str, object]:
        return {
            "handoff_id": self.handoff_id,
            "expires_at": self.expires_at,
        }


Now = Callable[[], float]
RandomBytes = Callable[[int], bytes]


class CIRunnerSecretHandoffStore:
    """Create opaque single-use handoff records under one private fixed root."""

    def __init__(
        self,
        *,
        root: Path,
        ttl_seconds: int = _DEFAULT_TTL_SECONDS,
        now: Now = time.time,
        random_bytes: RandomBytes = secrets.token_bytes,
    ) -> None:
        if not isinstance(root, Path) or not root.is_absolute():
            raise CIRunnerSecretHandoffError(
                "handoff root must be an absolute path"
            )
        if isinstance(ttl_seconds, bool) or not isinstance(
            ttl_seconds,
            int,
        ):
            raise CIRunnerSecretHandoffError(
                "handoff TTL must be an integer"
            )
        if not 30 <= ttl_seconds <= 900:
            raise CIRunnerSecretHandoffError(
                "handoff TTL is outside policy"
            )
        if not callable(now) or not callable(random_bytes):
            raise TypeError("handoff providers must be callable")
        self._root = root
        self._ttl_seconds = ttl_seconds
        self._now = now
        self._random_bytes = random_bytes

    def create(
        self,
        secret: CIRunnerRegistrationSecret,
    ) -> CIRunnerSecretHandoff:
        if not isinstance(secret, CIRunnerRegistrationSecret):
            raise TypeError(
                "secret must be CIRunnerRegistrationSecret"
            )
        self._validate_root()

        raw = secret.value.encode("ascii")
        if not 16 <= len(raw) <= _MAX_SECRET_BYTES:
            raise CIRunnerSecretHandoffError(
                "registration secret is outside policy"
            )

        for _attempt in range(4):
            handoff_id = self._random_bytes(16).hex()
            if _HANDOFF_RE.fullmatch(handoff_id) is None:
                raise CIRunnerSecretHandoffError(
                    "handoff randomness is invalid"
                )
            path = self._root / handoff_id
            flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
            if hasattr(os, "O_NOFOLLOW"):
                flags |= os.O_NOFOLLOW
            try:
                fd = os.open(path, flags, 0o600)
            except FileExistsError:
                continue
            except OSError as exc:
                raise CIRunnerSecretHandoffError(
                    "handoff record could not be created"
                ) from exc

            try:
                os.fchmod(fd, 0o600)
                written = os.write(fd, raw)
                if written != len(raw):
                    raise CIRunnerSecretHandoffError(
                        "handoff record write was incomplete"
                    )
                os.fsync(fd)
            except BaseException:
                try:
                    os.close(fd)
                finally:
                    try:
                        path.unlink()
                    except OSError:
                        pass
                raise
            else:
                os.close(fd)

            created_at = int(self._now())
            try:
                os.utime(path, (created_at, created_at), follow_symlinks=False)
            except OSError as exc:
                try:
                    path.unlink()
                except OSError:
                    pass
                raise CIRunnerSecretHandoffError(
                    "handoff timestamp could not be set"
                ) from exc

            return CIRunnerSecretHandoff(
                handoff_id=handoff_id,
                expires_at=created_at + self._ttl_seconds,
            )

        raise CIRunnerSecretHandoffError(
            "handoff id collision limit exceeded"
        )

    def reap_expired(self) -> int:
        self._validate_root()
        now = self._now()
        removed = 0
        try:
            entries = list(self._root.iterdir())
        except OSError as exc:
            raise CIRunnerSecretHandoffError(
                "handoff root could not be inspected"
            ) from exc

        for path in entries:
            if _HANDOFF_RE.fullmatch(path.name) is None:
                continue
            try:
                info = path.lstat()
            except OSError:
                continue
            if (
                not stat.S_ISREG(info.st_mode)
                or info.st_uid != os.geteuid()
                or stat.S_IMODE(info.st_mode) != 0o600
            ):
                continue
            if now - info.st_mtime <= self._ttl_seconds:
                continue
            try:
                path.unlink()
            except OSError:
                continue
            removed += 1
        return removed

    def _validate_root(self) -> None:
        try:
            info = self._root.lstat()
        except OSError as exc:
            raise CIRunnerSecretHandoffError(
                "handoff root is unavailable"
            ) from exc
        if self._root.is_symlink() or not stat.S_ISDIR(info.st_mode):
            raise CIRunnerSecretHandoffError(
                "handoff root is unsafe"
            )
        if info.st_uid != os.geteuid():
            raise CIRunnerSecretHandoffError(
                "handoff root ownership is unsafe"
            )
        if stat.S_IMODE(info.st_mode) != 0o700:
            raise CIRunnerSecretHandoffError(
                "handoff root permissions are unsafe"
            )


def validate_handoff_id(value: object) -> str:
    if not isinstance(value, str) or _HANDOFF_RE.fullmatch(value) is None:
        raise CIRunnerSecretHandoffError("handoff id is invalid")
    return value
