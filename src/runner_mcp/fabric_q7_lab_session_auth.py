"""Short-lived Black-only Q7 lab token reuse in the existing Linux user runtime.

Only the explicit `lab-login` operator action creates a credential file.
It lives in the owner-private /run/user/$UID tmpfs, NOT repo/home or an env.
Lab credential reuse never authorizes signed release, install, worker or ACK.
"""
from __future__ import annotations

import os
import re
import stat
import time
from pathlib import Path

_TTL_SECONDS = 3600
_DIR_NAME = "runner-mcp-q7-lab-login"
_TOKEN_NAME = "contents-read-token"
_TOKEN_RE = re.compile(r"[\x21-\x7e]{8,512}\Z")


class Q7LabLoginDenied(ValueError):
    """No sensitive data may appear in an error."""


def _deny() -> None:
    raise Q7LabLoginDenied("q7_lab_login_unqualified")


def _root() -> Path:
    return Path("/run/user") / str(os.geteuid())


def _directory_fd(*, create: bool = False) -> int:
    root = _root()
    if os.environ.get("XDG_RUNTIME_DIR") != str(root):
        _deny()
    try:
        st = root.lstat()
        if (not stat.S_ISDIR(st.st_mode) or st.st_uid != os.geteuid()
                or stat.S_IMODE(st.st_mode) != 0o700):
            _deny()
        fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            if create:
                try:
                    os.mkdir(_DIR_NAME, mode=0o700, dir_fd=fd)
                    os.fsync(fd)
                except FileExistsError:
                    pass
            nested = os.open(
                _DIR_NAME, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                dir_fd=fd,
            )
            try:
                st = os.fstat(nested)
                if (st.st_uid != os.geteuid()
                        or stat.S_IMODE(st.st_mode) != 0o700):
                    _deny()
            except BaseException:
                os.close(nested)
                raise
            return nested
        finally:
            os.close(fd)
    except (OSError, ValueError):
        _deny()


def _verify_token(token: str) -> bytes:
    if type(token) is not str or _TOKEN_RE.fullmatch(token) is None:
        _deny()
    return token.encode("ascii")


def _existing(fd: int) -> tuple[int, os.stat_result] | None:
    try:
        handle = os.open(
            _TOKEN_NAME, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
            dir_fd=fd,
        )
    except FileNotFoundError:
        return None
    except OSError:
        _deny()
    st = os.fstat(handle)
    if (not stat.S_ISREG(st.st_mode) or st.st_uid != os.geteuid()
            or st.st_nlink != 1 or stat.S_IMODE(st.st_mode) != 0o600
            or not 8 <= st.st_size <= 512):
        os.close(handle)
        _deny()
    return handle, st


def read_lab_login() -> str | None:
    """Read only fresh correct-owner 0600 cached token; no network or mutation."""
    try:
        fd = _directory_fd()
    except Q7LabLoginDenied:
        return None
    try:
        pair = _existing(fd)
        if pair is None:
            return None
        handle, st = pair
        try:
            age = time.time() - st.st_mtime
            if age < 0 or age >= _TTL_SECONDS:
                return None
            raw = os.read(handle, 513)
            if len(raw) != st.st_size:
                _deny()
            try:
                result = raw.decode("ascii")
            except UnicodeDecodeError:
                _deny()
            _verify_token(result)
            return result
        finally:
            os.close(handle)
    finally:
        os.close(fd)


def clear_lab_login() -> None:
    """Remove only the exact existing validated owned token; keep runtime root."""
    try:
        fd = _directory_fd()
    except Q7LabLoginDenied:
        return
    try:
        pair = _existing(fd)
        if pair is None:
            return
        handle, st = pair
        try:
            # Refuse races with a swapped or symlinked source.
            current = os.stat(_TOKEN_NAME, dir_fd=fd, follow_symlinks=False)
            if (current.st_ino, current.st_dev) != (st.st_ino, st.st_dev):
                _deny()
            os.unlink(_TOKEN_NAME, dir_fd=fd)
            os.fsync(fd)
        finally:
            os.close(handle)
    finally:
        os.close(fd)


def save_lab_login(token: str) -> None:
    """Explicit user-approved login only; never overwrite another credential."""
    raw = _verify_token(token)
    fd = _directory_fd(create=True)
    try:
        pair = _existing(fd)
        if pair is not None:
            os.close(pair[0])
            _deny()
        target = os.open(
            _TOKEN_NAME, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            0o600, dir_fd=fd,
        )
        try:
            sent = 0
            while sent < len(raw):
                wrote = os.write(target, raw[sent:])
                if wrote <= 0:
                    _deny()
                sent += wrote
            os.fsync(target)
        finally:
            os.close(target)
        os.fsync(fd)
    except OSError:
        _deny()
    finally:
        os.close(fd)
