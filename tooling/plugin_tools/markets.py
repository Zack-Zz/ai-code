"""Repository market entries derived from trusted, fully verified distributions."""

from contextlib import contextmanager
from io import BytesIO
import os
from pathlib import Path
import re
import stat
import uuid

from . import io
from .build import _verify_inputs, _verify_zip
from .io import ConflictError, DataError
from .package_check import check_package, read_artifact
from .registry import HOSTS, load_catalog
from .rendering import file_hashes, marketplace, marketplace_path, package_files

RECEIPT_PATH = "marketplaces.lock.json"


def _project_market(specs, host):
    data = marketplace([spec for spec in specs if host in spec.hosts], host)
    for entry in data["plugins"]:
        source = f"./dist/{host}/{entry['name']}"
        if host == "codex":
            entry["source"]["path"] = source
        else:
            entry["source"] = source
    return data


def _dist_files(root, relative="dist"):
    io.member(root, relative, directory=True)
    for entry in sorted(os.scandir(root / relative), key=lambda item: item.name):
        child = f"{relative}/{entry.name}"
        mode = entry.stat(follow_symlinks=False).st_mode
        if stat.S_ISDIR(mode):
            yield from _dist_files(root, child)
        else:
            yield child, io.read_file(root, child)


def _validate_dist(root, specs):
    index, raw = io.read_json(root, "dist/index.json")
    fields = {"schema_version", "plugins", "hosts", "source_revision", "working_tree_dirty"}
    if not isinstance(index, dict) or set(index) != fields or type(index["schema_version"]) is not int or index["schema_version"] != 2:
        raise DataError("dist/index.json must match distribution schema 2")
    identities = {spec.product_id for spec in specs}
    hosts = {host for spec in specs for host in spec.hosts}
    if not isinstance(index["plugins"], dict) or set(index["plugins"]) != identities:
        raise DataError("distribution plugin inventory differs from trusted catalog")
    if not isinstance(index["hosts"], dict) or set(index["hosts"]) != hosts:
        raise DataError("distribution host inventory differs from declared source hosts")
    validated = {"dist/index.json": raw}
    for host in hosts:
        relative = f"dist/{host}/{marketplace_path(host)}"
        entry = index["hosts"][host]
        if not isinstance(entry, dict) or set(entry) != {"marketplace", "marketplace_sha256"} or entry["marketplace"] != relative.removeprefix("dist/"):
            raise DataError(f"invalid distribution marketplace registration: {host}")
        payload = io.read_file(root, relative)
        expected = io.dump_json(marketplace([spec for spec in specs if host in spec.hosts], host))
        if payload != expected or io.sha256(payload) != entry["marketplace_sha256"]:
            raise DataError(f"distribution marketplace differs from trusted source: {host}")
        validated[relative] = expected
    for spec in specs:
        plugin = index["plugins"][spec.product_id]
        if (not isinstance(plugin, dict) or set(plugin) != {"version", "source_tree_hash", "hosts"} or
                plugin["version"] != spec.version or plugin["source_tree_hash"] != spec.source_tree_hash or
                not isinstance(plugin["hosts"], dict) or set(plugin["hosts"]) != set(spec.hosts)):
            raise DataError(f"distribution identity/version/source differs from trusted plugin: {spec.product_id}")
        for host in spec.hosts:
            entry = plugin["hosts"][host]
            package_rel = f"dist/{host}/{spec.product_id}"
            archive_rel = f"dist/{host}/{spec.product_id}-{spec.version}.zip"
            required = {"package_dir", "package_content_hash", "zip", "zip_sha256", "files_count"}
            if (not isinstance(entry, dict) or set(entry) != required or
                    entry["package_dir"] != package_rel.removeprefix("dist/") or
                    entry["zip"] != archive_rel.removeprefix("dist/")):
                raise DataError(f"invalid distribution package/archive path: {spec.product_id}/{host}")
            package = io.member(root, package_rel, directory=True)
            report = check_package(package, host, spec)
            if not report["ok"] or report["content_hash"] != entry["package_content_hash"] or type(entry["files_count"]) is not int or report["files_checked"] != entry["files_count"]:
                raise DataError(f"distribution package failed trusted checking: {spec.product_id}/{host}: {report['problems']}")
            artifact = read_artifact(package)
            for field in ("source_revision", "working_tree_dirty"):
                if type(index[field]) is not type(artifact[field]) or index[field] != artifact[field]:
                    raise DataError(f"distribution provenance differs from package: {field}")
            trusted_files = package_files(spec, host)
            trusted_artifact = {
                "schema_version": 1, "product_id": spec.product_id, "version": spec.version,
                "host": host, "profiles": spec.profiles,
                "source_revision": index["source_revision"], "working_tree_dirty": index["working_tree_dirty"],
                "source_tree_hash": spec.source_tree_hash, "files": file_hashes(trusted_files),
                "content_hash": report["content_hash"],
            }
            payload = io.read_file(root, archive_rel)
            if io.sha256(payload) != entry["zip_sha256"]:
                raise DataError(f"distribution archive checksum mismatch: {spec.product_id}/{host}")
            _verify_zip(BytesIO(payload), spec, host, trusted_artifact)
            validated.update({f"{package_rel}/{relative}": content for relative, content in trusted_files.items()})
            validated[f"{package_rel}/artifact.json"] = io.dump_json(trusted_artifact)
            validated[archive_rel] = payload
    captured = dict(_dist_files(root))
    if set(captured) != set(validated):
        raise DataError("distribution contains extra/missing files or changed index bytes")
    for relative, expected in validated.items():
        if captured[relative] != expected:
            raise DataError(f"distribution bytes changed or differ from trusted validation: {relative}")
    return hosts, captured


def _existing(root, relative):
    """Inspect missing write paths too, refusing every existing unsafe component."""
    path = root
    parts = io.relative_path(relative).split("/")
    for position, part in enumerate(parts):
        path = path / part
        try:
            mode = path.lstat().st_mode
        except FileNotFoundError:
            return None
        if stat.S_ISLNK(mode):
            raise DataError(f"symlinked market destination rejected: {relative}")
        if position < len(parts) - 1:
            if not stat.S_ISDIR(mode):
                raise DataError(f"market destination parent is not a directory: {relative}")
        elif not stat.S_ISREG(mode):
            raise DataError(f"market destination is not a regular file: {relative}")
    return io.read_file(root, relative, limit=1024 * 1024)


def _receipt(root):
    raw = _existing(root, RECEIPT_PATH)
    if raw is None:
        return {"schema_version": 1, "files": {}}, None
    receipt = io.parse_json(raw, what=RECEIPT_PATH)
    if (not isinstance(receipt, dict) or set(receipt) != {"schema_version", "files"} or
            type(receipt["schema_version"]) is not int or receipt["schema_version"] != 1 or
            not isinstance(receipt["files"], dict)):
        raise DataError("marketplaces.lock.json requires schema_version 1 and files only")
    allowed = {marketplace_path(host) for host in HOSTS}
    for relative, digest in receipt["files"].items():
        if relative not in allowed or not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise DataError(f"invalid marketplace ownership receipt entry: {relative}")
    return receipt, raw


@contextmanager
def _write_parent(root, relative):
    parts = relative.split("/")
    descriptor = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for part in parts[:-1]:
            try:
                os.mkdir(part, 0o755, dir_fd=descriptor)
            except FileExistsError:
                pass
            child = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        yield descriptor, parts[-1]
    except OSError as exc:
        raise DataError(f"unsafe or inaccessible market write: {relative}: {exc}") from exc
    finally:
        os.close(descriptor)


def _write_market(root, relative, payload, previous):
    with _write_parent(root, relative) as (parent, name):
        temporary = f".{name}.{uuid.uuid4().hex}.tmp"
        try:
            fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o644, dir_fd=parent)
            with os.fdopen(fd, "wb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            if _existing(root, relative) != previous:
                raise ConflictError(f"market destination changed during synchronization: {relative}")
            os.replace(temporary, name, src_dir_fd=parent, dst_dir_fd=parent)
        finally:
            try:
                os.unlink(temporary, dir_fd=parent)
            except FileNotFoundError:
                pass


def sync_markets(root, check=False):
    root = Path(root).absolute()
    if root.is_symlink() or not stat.S_ISDIR(root.lstat().st_mode):
        raise DataError("repository market root must be a real directory")
    root = root.resolve()
    catalog_bytes = io.read_file(root, "catalog.json", limit=1024 * 1024)
    specs = load_catalog(root)
    hosts, captured = _validate_dist(root, specs)
    expected = {marketplace_path(host): io.dump_json(_project_market(specs, host)) for host in HOSTS if host in hosts}
    previous = {marketplace_path(host): _existing(root, marketplace_path(host)) for host in HOSTS}
    receipt, receipt_bytes = _receipt(root)
    problems = [f"missing or stale repository market: {relative}" for relative, payload in expected.items() if previous[relative] != payload]
    problems.extend(f"unexpected repository market for undeclared host: {relative}" for relative in previous if relative not in expected and previous[relative] is not None)
    for relative, digest in receipt["files"].items():
        if previous[relative] is None or io.sha256(previous[relative]) != digest:
            problems.append(f"repository market differs from ownership receipt: {relative}")
    if check:
        return {"ok": not problems, "check": True, "files": sorted(expected), "changed": [], "problems": problems}
    for relative, payload in previous.items():
        if payload is not None and payload != expected.get(relative) and (
                relative not in expected or receipt["files"].get(relative) != io.sha256(payload)):
            raise ConflictError(f"existing repository market conflicts with generated content; preserved: {relative}")
    _verify_inputs(specs)
    if io.read_file(root, "catalog.json", limit=1024 * 1024) != catalog_bytes:
        raise DataError("catalog input changed during market synchronization")
    for relative, payload in captured.items():
        if io.read_file(root, relative) != payload:
            raise DataError(f"distribution input changed during market synchronization: {relative}")
    changed = []
    for relative, payload in expected.items():
        # Per-file atomic writes and immediate ownership updates preserve prior
        # successes when a later destination conflicts. POSIX cannot atomically
        # publish all three native paths together or lock out external writers.
        if previous[relative] != payload:
            _write_market(root, relative, payload, previous[relative])
            changed.append(relative)
        receipt["files"][relative] = io.sha256(payload)
        updated_receipt = io.dump_json(receipt)
        if updated_receipt != receipt_bytes:
            _write_market(root, RECEIPT_PATH, updated_receipt, receipt_bytes)
            receipt_bytes = updated_receipt
    return {"ok": True, "check": False, "files": sorted(expected), "changed": changed, "problems": []}
