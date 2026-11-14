"""#669: bind the existing wheel receipt to the serving Python generation.

This module REUSES artifact_receipt_preflight and serving_process_readonly.
It introduces no receipt writer, store, scheduler, signer, relay or updater.
The independent existing A7 owner must authenticate release provenance, PID,
start ticks, serving endpoint and the selected loaded-code digest. A caller
supplied callback, a wheel RECORD or a Python dataclass is never self-trust.
The old 0.1.88 one-time D-0037 admission remains outside this newer gate.
"""

from __future__ import annotations

import base64
import csv
import hashlib
import io
import marshal
import os
import re
import stat
import sys
import zipfile
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from types import CodeType, FunctionType, ModuleType

from .artifact_receipt_preflight import offline_artifact_receipt_preflight
from .serving_process_readonly import (
    _module_code_items,
    _normalized_code,
    observe_current_process_modules,
)

_REV = re.compile(r"[a-f0-9]{40}\Z")
_SHA = re.compile(r"[a-f0-9]{64}\Z")
_MAX_WHEEL = 100 * 1024 * 1024
_MAX_MEMBERS = 4096
_MAX_SOURCE_FILES = 4096
_MAX_ENTRY = 16 * 1024 * 1024
_SCHEMA = "runner-mcp/active-build-owner-challenge/v1"


@dataclass(frozen=True, slots=True)
class ActiveBuildOwnerChallenge:
    """In-process facts to be verified by the independent existing owner.

    Do NOT serialize to MCP: pid/startticks, private paths and owner controls
    must remain local. The owner must bind these to the live loopback server,
    executable/release slot and retained signed wheel/receipt; same-host input
    strings or a self-report cannot do that.
    """

    schema: str
    source_revision: str
    artifact_digest: str
    loaded_version: str
    serving_epoch: str
    pid: int
    start_ticks: int
    selected_loaded_code_sha256: str


@dataclass(frozen=True, slots=True)
class ActiveBuildOwnerInputs:
    """Inputs provisioned by existing privileged installer/A7 owner, NOT env.

    No new credential/store. The verifier MUST independently check the real
    process, connected socket identity, owner seal and published wheel source.
    """

    receipt: Path
    wheel: Path
    installed_package: Path
    independent_owner_verifier: Callable[[ActiveBuildOwnerChallenge], bool]


@dataclass(frozen=True, slots=True)
class QualifiedActiveBuild:
    """One authenticated serving-generation *candidate*, not release authority."""

    source_revision: str
    artifact_digest: str
    build_version: str
    serving_epoch: str
    selected_loaded_code_sha256: str


def _valid(value: object, regex: re.Pattern[str]) -> bool:
    return type(value) is str and regex.fullmatch(value) is not None


def _process_generation() -> tuple[int, int] | None:
    """Current Linux PID start ticks and conservative wall-time from procfs."""
    try:
        raw = Path("/proc/self/stat").read_text(encoding="ascii")
        tail = raw.rsplit(")", 1)[1].split()
        ticks = int(tail[19])  # field 22; tail begins at field 3
        hz = os.sysconf("SC_CLK_TCK")
        btime = next(
            int(line.split()[1]) for line in Path("/proc/stat").read_text(
                encoding="ascii"
            ).splitlines() if line.startswith("btime ")
        )
        started_ns = btime * 1_000_000_000 + ticks * 1_000_000_000 // hz
        return (ticks, started_ns) if ticks > 0 and started_ns > 0 else None
    except (OSError, IndexError, ValueError, StopIteration, ZeroDivisionError):
        return None


def _wheel_record_matches(wheel: Path, expected_digest: str) -> bool:
    """Validate complete wheel RECORD against bytes, bounded in one read.

    The existing private capture pins wheel inode and raw hash. This secondary
    read is only a consistency check, never an independent publisher signature.
    """
    try:
        info = wheel.lstat()
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_nlink != 1
            or info.st_size > _MAX_WHEEL
            or info.st_size < 100
            or info.st_mode & 0o022
        ):
            return False
        if not hasattr(os, "O_NOFOLLOW"):
            return False
        flags = os.O_RDONLY | os.O_NOFOLLOW
        if hasattr(os, "O_CLOEXEC"):
            flags |= os.O_CLOEXEC
        with os.fdopen(os.open(wheel, flags), "rb") as handle:
            opened = os.fstat(handle.fileno())
            if (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns) != (
                opened.st_dev, opened.st_ino, opened.st_size, opened.st_mtime_ns, opened.st_ctime_ns
            ):
                return False
            raw = handle.read(_MAX_WHEEL + 1)
            if len(raw) != info.st_size or hashlib.sha256(raw).hexdigest() != expected_digest:
                return False
            after = os.fstat(handle.fileno())
            now = wheel.lstat()
            for newer in (after, now):
                if (newer.st_dev, newer.st_ino, newer.st_size, newer.st_mtime_ns, newer.st_ctime_ns) != (
                    info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns
                ):
                    return False
        with zipfile.ZipFile(io.BytesIO(raw)) as archive:
            members = archive.namelist()
            if len(members) > _MAX_MEMBERS or len(members) != len(set(members)):
                return False
            record_files = [p for p in members if p.endswith(".dist-info/RECORD")]
            if len(record_files) != 1:
                return False
            record = record_files[0]
            rows = list(csv.reader(io.StringIO(archive.read(record).decode("utf-8"))))
            if len(rows) != len(members) or len(rows) > _MAX_MEMBERS:
                return False
            seen: set[str] = set()
            total_expanded = 0
            for row in rows:
                if len(row) != 3:
                    return False
                name, hashed, size = row
                if (
                    name in seen or name not in members or name.startswith("/")
                    or ".." in Path(name).parts or "\\" in name
                ):
                    return False
                seen.add(name)
                entry = archive.getinfo(name)
                total_expanded += entry.file_size
                if (
                    entry.is_dir() or entry.file_size > _MAX_ENTRY
                    or total_expanded > _MAX_WHEEL
                    or stat.S_IFMT(entry.external_attr >> 16) == stat.S_IFLNK
                ):
                    return False
                if name == record:
                    if hashed or size:
                        return False
                    continue
                if not hashed.startswith("sha256=") or not size.isascii() or not size.isdecimal():
                    return False
                content = archive.read(name)
                checksum = base64.urlsafe_b64encode(hashlib.sha256(content).digest()).rstrip(b"=").decode("ascii")
                if hashed != "sha256=" + checksum or int(size) != len(content):
                    return False
            return seen == set(members)
    except (OSError, UnicodeError, ValueError, RuntimeError, KeyError, zipfile.BadZipFile, zipfile.LargeZipFile):
        return False


def _installed_files_predate_process(installed_package: Path, process_started_ns: int) -> bool:
    """Deny an in-place pip upgrade under old imports, even same version.

    Linux ctime is not a provenance signature. It is a necessary, conservative
    *anti-stale-process* check; the independent owner still verifies PID,
    executable and socket generation. Reject symlinks and unknown native code.
    """
    try:
        root = installed_package.resolve(strict=True)
        if installed_package.is_symlink() or root != installed_package:
            return False
        count = 0
        for current, dirs, files in os.walk(root, followlinks=False):
            for name in (*dirs, *files):
                candidate = Path(current) / name
                info = candidate.lstat()
                count += 1
                if count > _MAX_SOURCE_FILES * 3 or stat.S_ISLNK(info.st_mode):
                    return False
                if name.endswith((".so", ".pyd", ".dll", ".dylib")):
                    return False
                # Python may create __pycache__ during import AFTER boot.
                # Only the installed executable .py source, not ephemeral
                # bytecode caches or directory ctimes, must predate the PID.
                if name.endswith(".py") and (
                    not stat.S_ISREG(info.st_mode)
                    or info.st_ctime_ns > process_started_ns
                ):
                    return False
        return count > 0
    except (OSError, ValueError):
        return False


def _current_python_imports_are_installed(
    installed_package: Path, modules: Mapping[str, object],
) -> bool:
    """Every observed runner_mcp import must originate in the fixed package.

    Python metadata alone is insufficient: this checks the modules currently
    imported inside the actual server, not another interpreter's dist-info.
    """
    try:
        root = installed_package.resolve(strict=True)
        names = [name for name in modules if name == "runner_mcp" or name.startswith("runner_mcp.")]
        if not names or len(names) > _MAX_SOURCE_FILES:
            return False
        for name in names:
            module = modules[name]
            if type(module) is not ModuleType or module.__name__ != name:
                return False
            rel = name.split(".")[1:]
            file = Path(getattr(module, "__file__", ""))
            spec = getattr(module, "__spec__", None)
            origin = getattr(spec, "origin", None)
            if not file.is_absolute() or not file.is_file() or file.is_symlink():
                return False
            if origin != str(file):
                return False
            source = root.joinpath(*rel)
            if (file != source.with_suffix(".py") and file != source / "__init__.py"):
                return False
            if file.resolve(strict=True) != file:
                return False
        return True
    except (OSError, TypeError, ValueError, AttributeError):
        return False


def _loaded_code_matches_installed_sources(
    installed_package: Path, modules: Mapping[str, object],
) -> bool:
    """Reject stale loaded function/method code, including same-version .pyc.

    Compare in-memory code objects with this interpreter's fresh compilation of
    source already checked against the wheel. Static module/class code only;
    arbitrary generated/decorated code fails closed except standard dataclass
    methods with stdlib-generated <string> code. Even a PASS does not prove
    import-time mutable globals or an independent authenticated owner.
    """
    try:
        for name, module in modules.items():
            if name != "runner_mcp" and not name.startswith("runner_mcp."):
                continue
            if type(module) is not ModuleType:
                return False
            path = Path(module.__file__)
            source = path.read_bytes()
            compiled = compile(source, str(path), "exec")
            expected: dict[str, CodeType] = {}

            def collect(code: CodeType, *, depth: int = 0) -> bool:
                if depth > 48:
                    return False
                for nested in code.co_consts:
                    if type(nested) is not CodeType:
                        continue
                    if nested.co_qualname in expected:
                        return False
                    expected[nested.co_qualname] = nested
                    if not collect(nested, depth=depth + 1):
                        return False
                return True

            if not collect(compiled):
                return False
            seen: set[str] = set()
            for symbol, actual in _module_code_items(name, module):
                if symbol in seen:
                    return False
                seen.add(symbol)
                on_source = expected.get(symbol)
                if on_source is None:
                    # dataclasses creates these methods at runtime; their
                    # contents are covered by the existing in-memory digest
                    # only, and owner separately qualifies the interpreter.
                    clsname, sep, member = symbol.partition(".")
                    cls = vars(module).get(clsname)
                    if not (
                        sep and type(cls) is type
                        and hasattr(cls, "__dataclass_fields__")
                        and member in {
                            "__init__", "__repr__", "__eq__", "__hash__",
                            "__setattr__", "__delattr__", "__lt__", "__le__",
                            "__gt__", "__ge__",
                        }
                        and actual.co_filename == "<string>"
                    ):
                        return False
                    continue
                if marshal.dumps(_normalized_code(actual)) != marshal.dumps(
                    _normalized_code(on_source)
                ):
                    return False
            # property getters and setters are function objects held by a
            # descriptor, not exposed by _module_code_items. Check them too.
            for clsname, cls in vars(module).items():
                if type(cls) is not type or cls.__module__ != name:
                    continue
                for member, descriptor in vars(cls).items():
                    if type(descriptor) is not property:
                        continue
                    for function in (descriptor.fget, descriptor.fset, descriptor.fdel):
                        if function is None:
                            continue
                        if type(function) is not FunctionType:
                            return False
                        matching = expected.get(function.__code__.co_qualname)
                        if matching is None or marshal.dumps(_normalized_code(
                            function.__code__
                        )) != marshal.dumps(_normalized_code(matching)):
                            return False
        return True
    except (
        OSError, TypeError, ValueError, AttributeError, RuntimeError,
        OverflowError, RecursionError, KeyError,
    ):
        return False


def qualify_serving_build(
    *,
    receipt: Path,
    wheel: Path,
    installed_package: Path,
    loaded_version: str,
    installed_version: str,
    serving_epoch: str,
    independent_owner_verifier: Callable[[ActiveBuildOwnerChallenge], bool] | None,
    modules: Mapping[str, object] | None = None,
) -> QualifiedActiveBuild | None:
    """Read existing bytes and live code, then demand an independent owner.

    The external verifier is NOT instantiated from environment/user messages;
    it must be the already privileged original A7 owner bound to this exact
    process/socket/executable and trusted wheel source provenance. Default
    None and any missing, stale, corrupt or ambiguous evidence => DENY.
    """
    try:
        if not callable(independent_owner_verifier):
            return None
        if not all(isinstance(p, Path) and p.is_absolute() for p in (receipt, wheel, installed_package)):
            return None
        if (
            type(loaded_version) is not str or loaded_version != installed_version
            or not loaded_version or len(loaded_version) > 64
            or not _valid(serving_epoch, re.compile(r"[a-f0-9]{32}\Z"))
        ):
            return None
        generation = _process_generation()
        if generation is None:
            return None
        ticks, process_started_ns = generation
        receipt_state = offline_artifact_receipt_preflight(receipt, wheel, installed_package)
        if receipt_state.get("state") != "offline_bytes_match":
            return None
        import json
        saved = json.loads(receipt.read_text(encoding="utf-8"))
        source_revision, wheel_sha = saved["source_revision"], saved["wheel_sha256"]
        if not _valid(source_revision, _REV) or not _valid(wheel_sha, _SHA):
            return None
        if not _wheel_record_matches(wheel, wheel_sha):
            return None
        if not _installed_files_predate_process(installed_package, process_started_ns):
            return None
        current = sys.modules if modules is None else modules
        if not _current_python_imports_are_installed(installed_package, current):
            return None
        if not _loaded_code_matches_installed_sources(installed_package, current):
            return None
        observation = observe_current_process_modules(
            imported_version=loaded_version,
            installed_distribution_version=installed_version,
            modules=current,
        )
        digest = observation.get("loadedCodeObjectDigest")
        if (
            observation.get("loadedCodeObservationComplete") is not True
            or observation.get("moduleRosterComplete") is not True
            or observation.get("loadedVersionMatchesInstalled") is not True
            or not _valid(digest, _SHA)
        ):
            return None
        challenge = ActiveBuildOwnerChallenge(
            schema=_SCHEMA, source_revision=source_revision,
            artifact_digest=wheel_sha, loaded_version=loaded_version,
            serving_epoch=serving_epoch, pid=os.getpid(), start_ticks=ticks,
            selected_loaded_code_sha256=digest,
        )
        if independent_owner_verifier(challenge) is not True:
            return None
        # Fail closed if wheel/receipt or source generation drifted during the
        # external owner check; post-update in-place writes need a fresh boot.
        if (offline_artifact_receipt_preflight(receipt, wheel, installed_package).get("state")
                != "offline_bytes_match"
                or not _installed_files_predate_process(installed_package, process_started_ns)
                or not _loaded_code_matches_installed_sources(installed_package, current)):
            return None
        return QualifiedActiveBuild(
            source_revision=source_revision, artifact_digest=wheel_sha,
            build_version=loaded_version, serving_epoch=serving_epoch,
            selected_loaded_code_sha256=digest,
        )
    except (OSError, RuntimeError, KeyError, TypeError, ValueError, OverflowError, AttributeError):
        return None


def observe_owner_qualified_serving_build(
    owner: ActiveBuildOwnerInputs | None, *, loaded_version: str,
    installed_version: str, serving_epoch: str,
) -> QualifiedActiveBuild | None:
    """Single existing owner readback invoked by build_identity and status.

    The 0.1.88 D-0037 bootstrap does NOT require this new implementation.
    A newly activated release must pass it on its CURRENT serving generation.
    """
    if type(owner) is not ActiveBuildOwnerInputs:
        return None
    return qualify_serving_build(
        receipt=owner.receipt, wheel=owner.wheel,
        installed_package=owner.installed_package,
        loaded_version=loaded_version, installed_version=installed_version,
        serving_epoch=serving_epoch,
        independent_owner_verifier=owner.independent_owner_verifier,
    )
