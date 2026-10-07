"""Small, bounded, no-follow file operations for declarative plugin inputs."""

from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import re
import stat


class ToolError(Exception):
    exit_code = 1


class DataError(ToolError):
    exit_code = 2


class ConflictError(ToolError):
    exit_code = 3


def canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def dump_json(value):
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=True) + "\n").encode()


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def relative_path(value, *, what="path"):
    if (not isinstance(value, str) or not value or value.startswith("/") or
            "\\" in value or re.match(r"^[A-Za-z]:", value) or "\x00" in value or
            any(part in ("", ".", "..") for part in value.split("/"))):
        raise DataError(f"invalid {what}: canonical relative path required: {value!r}")
    return value


def _scope(root, relative, boundary_root):
    """Keep catalog children anchored to the user-selected repository root."""
    root = Path(root)
    relative_path(relative)
    if boundary_root is None:
        return root, relative
    boundary_root = Path(boundary_root)
    try:
        prefix = root.relative_to(boundary_root).as_posix()
    except ValueError as exc:
        raise DataError(f"source root is outside its repository boundary: {root}") from exc
    if prefix != ".":
        relative = relative_path(f"{prefix}/{relative}")
    return boundary_root, relative


def member(root, relative, *, directory=False, boundary_root=None):
    """Inspect every component below a user-selected root without following links."""
    path, relative = _scope(root, relative, boundary_root)
    try:
        mode = path.lstat().st_mode
    except OSError as exc:
        raise DataError(f"cannot inspect root path {path}: {exc}") from exc
    if stat.S_ISLNK(mode):
        raise DataError(f"symlinked root path rejected: {path}")
    if not stat.S_ISDIR(mode):
        raise DataError(f"root path is not a directory: {path}")
    parts = relative_path(relative).split("/")
    for index, part in enumerate(parts):
        path = path / part
        try:
            mode = path.lstat().st_mode
        except OSError as exc:
            raise DataError(f"cannot inspect path {path}: {exc}") from exc
        if stat.S_ISLNK(mode):
            raise DataError(f"symlinked path rejected: {path}")
        if index < len(parts) - 1 or directory:
            if not stat.S_ISDIR(mode):
                raise DataError(f"path is not a directory: {path}")
        elif not stat.S_ISREG(mode):
            raise DataError(f"path is not a regular file: {path}")
    return path


@contextmanager
def parent_handle(root, relative, *, boundary_root=None):
    """Hold each traversed directory so a concurrent path swap cannot redirect reads."""
    root, relative = _scope(root, relative, boundary_root)
    parts = relative_path(relative).split("/")
    descriptor = None
    try:
        descriptor = os.open(Path(root), os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        for part in parts[:-1]:
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        yield descriptor, parts[-1]
    except OSError as exc:
        raise DataError(f"unsafe or inaccessible path {relative}: {exc}") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)


def read_file(root, relative, *, limit=32 * 1024 * 1024, boundary_root=None):
    member(root, relative, boundary_root=boundary_root)
    with parent_handle(root, relative, boundary_root=boundary_root) as (parent, name):
        fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=parent)
        with os.fdopen(fd, "rb") as handle:
            info = os.fstat(handle.fileno())
            if not stat.S_ISREG(info.st_mode):
                raise DataError(f"path is not a regular file: {relative}")
            if info.st_size > limit:
                raise DataError(f"input exceeds byte limit: {relative}")
            payload = handle.read(limit + 1)
            if len(payload) > limit:
                raise DataError(f"input exceeds byte limit: {relative}")
            return payload


def _unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise DataError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def parse_json(raw, *, what):
    try:
        return json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_keys)
    except (ValueError, UnicodeDecodeError) as exc:
        raise DataError(f"invalid JSON in {what}: {exc}") from exc


def read_json(root, relative, *, boundary_root=None):
    raw = read_file(root, relative, limit=1024 * 1024, boundary_root=boundary_root)
    return parse_json(raw, what=relative), raw
