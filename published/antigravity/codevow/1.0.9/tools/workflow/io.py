"""Controlled JSON and path operations shared by every workflow tool.

Policy: fixed-structure validation instead of a generic schema engine;
duplicate JSON keys, oversized inputs, path escapes, symlink bypass and
non-regular files are rejected with specific, stable error messages.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

MAX_JSON_BYTES = 1024 * 1024  # 1 MiB structural input cap


class ToolError(Exception):
    """Base class with a stable exit code."""

    exit_code = 1


class DataError(ToolError):
    """Malformed data or arguments."""

    exit_code = 2


class ConflictError(ToolError):
    """Content/revision conflict, or a lock held elsewhere."""

    exit_code = 3


class InvalidStateError(ToolError):
    """Workspace identity mismatch or invalidated evidence."""

    exit_code = 4


class HostUnavailableError(ToolError):
    """A required host environment is not available."""

    exit_code = 5


def is_strict_int(value) -> bool:
    """True only for real ints — bool is an int subclass and must be excluded."""
    return isinstance(value, int) and not isinstance(value, bool)


def canonical_json(obj) -> bytes:
    """Canonical byte form used for every content hash in this product."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def now_rfc3339() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _reject_duplicate_keys(pairs):
    seen = {}
    for key, value in pairs:
        if key in seen:
            raise DataError(f"duplicate JSON key: {key!r}")
        seen[key] = value
    return seen


def read_json_snapshot(path: Path, *, root: Path | None = None):
    """Parse exactly the bounded bytes read through one no-follow file handle.

    A workspace caller supplies its root so every parent below it is checked.
    Nonblocking open rejects FIFOs without waiting for a writer; fstat checks
    the opened inode and the read cap also covers growth after that check.
    """
    path = Path(path)
    try:
        with parent_handle(path, root=root) as (parent, name):
            fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
            with os.fdopen(fd, "rb") as handle:
                info = os.fstat(handle.fileno())
                if not stat.S_ISREG(info.st_mode):
                    raise DataError(f"not a regular JSON file: {path}")
                if info.st_size > MAX_JSON_BYTES:
                    raise DataError(f"JSON input exceeds 1 MiB cap: {path}")
                raw = handle.read(MAX_JSON_BYTES + 1)
                if len(raw) > MAX_JSON_BYTES:
                    raise DataError(f"JSON input exceeds 1 MiB cap: {path}")
        text = raw.decode("utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise DataError(f"cannot read {path}: {exc}") from exc
    try:
        return json.loads(text, object_pairs_hook=_reject_duplicate_keys), raw
    except DataError:
        raise
    except json.JSONDecodeError as exc:
        raise DataError(f"invalid JSON in {path}: {exc}") from exc


def load_json(path: Path, *, root: Path | None = None):
    """Load a bounded JSON document with unique object keys."""
    return read_json_snapshot(path, root=root)[0]


_REL_FORBIDDEN = re.compile(r"(^|/)(\.|\.\.)(/|$)")


def check_relative(rel: str, *, what: str = "path") -> str:
    """Validate a normalized relative path usable inside a controlled root."""
    if not isinstance(rel, str) or not rel:
        raise DataError(f"invalid {what}: empty or not a string")
    if rel.startswith("/") or os.path.isabs(rel) or "\\" in rel or re.match(r"^[A-Za-z]:", rel):
        raise DataError(f"invalid {what}: absolute paths are not allowed: {rel!r}")
    if _REL_FORBIDDEN.search(rel) or "//" in rel or rel.endswith("/"):
        raise DataError(f"invalid {what}: path escape or unnormalized segment rejected: {rel!r}")
    return rel


def resolve_member(root: Path, relative: str, *, must_exist: bool = True,
                   allow_directory: bool = False) -> Path:
    """Resolve a controlled path under root.

    Rejects path escapes, symlinked components and (by default) non-regular
    files. When must_exist is False a missing final component is allowed as a
    planned write target, but its existing parent chain is still checked.
    """
    root = Path(root)
    rel = check_relative(relative)
    current = root
    parts = rel.split("/")
    for index, part in enumerate(parts):
        current = current / part
        try:
            info = os.lstat(current)
        except FileNotFoundError:
            if index == len(parts) - 1:
                if must_exist:
                    raise DataError(f"path does not exist: {current}")
                return current
            if must_exist:
                raise DataError(f"path does not exist: {current}")
            # Missing intermediate directory for a planned target: keep the
            # controlled path; creation happens under the caller's lock.
            continue
        except OSError as exc:
            raise DataError(f"cannot inspect {current}: {exc}") from exc
        if stat.S_ISLNK(info.st_mode):
            raise DataError(f"symlinked path component rejected: {current}")
        if index == len(parts) - 1:
            if stat.S_ISDIR(info.st_mode):
                if not allow_directory:
                    raise DataError(f"not a regular file: {current}")
            elif not stat.S_ISREG(info.st_mode):
                raise DataError(f"not a regular file: {current}")
    return current


@contextmanager
def parent_handle(path: Path, *, root: Path | None = None, create=False):
    """Walk beneath an explicit trusted root using no-follow directory handles.

    Callers managing a workspace must supply that workspace as root. Without
    it, only the immediate parent is the boundary (for standalone writes).
    Canonicalizing the user-selected root permits OS aliases such as /var;
    no component below that root is resolved through a link.
    """
    path = Path(path).absolute()
    anchor = Path(root).absolute() if root is not None else path.parent
    try:
        relative = path.relative_to(anchor)
    except ValueError as exc:
        raise DataError(f"write target is outside root {anchor}: {path}") from exc
    check_relative(relative.as_posix())
    if not hasattr(os, "O_NOFOLLOW") or not hasattr(os, "O_DIRECTORY"):
        raise DataError("safe directory-handle writes are unsupported on this platform")
    fd = None
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    try:
        fd = os.open(str(anchor.resolve()), flags)
        for part in relative.parts[:-1]:
            try:
                child = os.open(part, flags, dir_fd=fd)
            except FileNotFoundError:
                if not create:
                    raise
                try:
                    os.mkdir(part, 0o755, dir_fd=fd)
                except FileExistsError:
                    pass
                child = os.open(part, flags, dir_fd=fd)
            os.close(fd)
            fd = child
        yield fd, relative.name
    except OSError as exc:
        raise DataError(f"unsafe or inaccessible path {path}: {exc}") from exc
    finally:
        if fd is not None:
            os.close(fd)


def ensure_directory(root: Path, relative: str) -> None:
    """Create checked directories below root, without following links."""
    check_relative(relative)
    with parent_handle(Path(root) / relative / ".directory-probe", root=root, create=True):
        pass


def _read_at(fd: int, name: str):
    try:
        file_fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
    except FileNotFoundError:
        return None, None
    with os.fdopen(file_fd, "rb") as handle:
        info = os.fstat(handle.fileno())
        if not stat.S_ISREG(info.st_mode):
            raise DataError(f"not a regular file: {name}")
        return handle.read(), info


def read_owned(path: Path, *, root: Path) -> bytes | None:
    with parent_handle(path, root=root) as (fd, name):
        return _read_at(fd, name)[0]


def _recheck_parent(path: Path, root, fd):
    with parent_handle(path, root=root) as (fresh, _):
        before, after = os.fstat(fd), os.fstat(fresh)
        if (before.st_dev, before.st_ino) != (after.st_dev, after.st_ino):
            raise ConflictError(f"parent directory changed during write: {path}")


def atomic_write(path: Path, data: bytes, *, expected_before: bytes | None,
                 root: Path | None = None) -> None:
    """Locked compare/recheck/replace; existing files still require cooperation.

    Late creates are rejected atomically. POSIX provides no content-CAS for
    replacement: an unrelated editor can race the final recheck/rename. This
    is not an OS sandbox; the caller's lock covers cooperating tool writers.
    """
    with parent_handle(path, root=root) as (parent, name):
        current, info = _read_at(parent, name)
        if current != expected_before:
            raise ConflictError(f"content conflict: {path} no longer matches expected content")
        temp = f".{name}.{uuid.uuid4().hex}.tmp"
        fd = os.open(temp, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW,
                     0o600, dir_fd=parent)
        try:
            with os.fdopen(fd, "wb") as handle:
                os.fchmod(handle.fileno(), info.st_mode & 0o7777 if info else 0o644)
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            _recheck_parent(path, root, parent)
            latest, _ = _read_at(parent, name)
            if latest != expected_before:
                raise ConflictError(f"content conflict during write: {path}")
            if expected_before is None:
                try:
                    os.link(temp, name, src_dir_fd=parent, dst_dir_fd=parent,
                            follow_symlinks=False)
                except FileExistsError as exc:
                    raise ConflictError(f"create target appeared during write: {path}") from exc
            else:
                os.replace(temp, name, src_dir_fd=parent, dst_dir_fd=parent)
            try:
                os.fsync(parent)
            except OSError:
                pass  # Some filesystems cannot fsync directories.
        finally:
            try:
                os.unlink(temp, dir_fd=parent)
            except FileNotFoundError:
                pass


def delete_owned(path: Path, *, root: Path, expected_before: bytes) -> None:
    with parent_handle(path, root=root) as (fd, name):
        current, _ = _read_at(fd, name)
        if current != expected_before:
            raise ConflictError(f"content conflict before deletion: {path}")
        _recheck_parent(path, root, fd)
        os.unlink(name, dir_fd=fd)


def acquire_lock(lock_path: Path, operation_id: str, *, root: Path | None = None) -> None:
    """Take an exclusive O_CREAT|O_EXCL advisory lock for one operation."""
    lock_path = Path(lock_path)
    payload = canonical_json({
        "operation_id": operation_id,
        "pid": os.getpid(),
        "created_at": now_rfc3339(),
    })
    try:
        with parent_handle(lock_path, root=root) as (parent, name):
            try:
                fd = os.open(name, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW,
                             0o644, dir_fd=parent)
            except FileExistsError as exc:
                raise ConflictError(f"write lock exists: {lock_path}") from exc
    except FileExistsError as exc:
        raise ConflictError(f"write lock exists: {lock_path}") from exc
    except OSError as exc:
        raise DataError(f"cannot create lock {lock_path}: {exc}") from exc
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    except BaseException:
        # Never leave a half-written lock behind: it would be unparseable and
        # block every later operation until manual cleanup.
        try:
            with parent_handle(lock_path, root=root) as (parent, name):
                os.unlink(name, dir_fd=parent)
        except OSError:
            pass
        raise


def release_lock(lock_path: Path, operation_id: str, *, root: Path | None = None) -> None:
    """Release the lock only when it still belongs to this operation."""
    lock_path = Path(lock_path)
    try:
        with parent_handle(lock_path, root=root) as (parent, name):
            raw = _read_at(parent, name)[0]
            if raw is None:
                return
            try:
                owner = json.loads(raw, object_pairs_hook=_reject_duplicate_keys)
            except DataError as exc:
                raise ConflictError(
                    f"lock file {lock_path} has ambiguous owner keys; verify no writer is active, "
                    "then remove it manually") from exc
    except FileNotFoundError:
        return
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ConflictError(
            f"lock file {lock_path} is not parseable (likely a torn write from a "
            f"crashed process); verify no writer is active, then remove it manually"
        ) from exc
    except OSError as exc:
        raise ConflictError(f"cannot inspect lock {lock_path}: {exc}") from exc
    if not isinstance(owner, dict):
        raise ConflictError(
            f"lock file {lock_path} is not an owner object; verify no writer is active, "
            "then remove it manually")
    if owner.get("operation_id") != operation_id:
        raise ConflictError(
            f"lock {lock_path} is owned by another operation "
            f"({owner.get('operation_id')!r})")
    try:
        delete_owned(lock_path, root=root or lock_path.parent, expected_before=raw)
    except OSError as exc:
        raise DataError(f"cannot release lock {lock_path}: {exc}") from exc
