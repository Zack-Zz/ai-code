"""Repository market entries derived from trusted, fully verified distributions."""

from contextlib import contextmanager
from io import BytesIO
import base64
import binascii
import os
from pathlib import Path
import re
import stat
import subprocess
import tempfile
import zipfile
import uuid

from . import io
from .build import _verify_inputs, _verify_zip
from .io import ConflictError, DataError
from .package_check import check_package, read_artifact
from .registry import HOSTS, load_catalog
from .rendering import file_hashes, marketplace, marketplace_path, package_files

RECEIPT_PATH = "marketplaces.lock.json"
INITIALIZE_PATH = ".marketplace-initialize.json"


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
    return io.read_file(root, relative, limit=32 * 1024 * 1024)


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


def _sync_development_repository(root, check=False):
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


def read_public_files(root):
    """Read just publication paths; source files and their symlinks are out of scope."""
    from .distribution import NATIVE_PATHS
    from .release.integrity import read_tree
    root = Path(root).absolute()
    result = {}
    for path in NATIVE_PATHS:
        raw = _existing(root, path)
        if raw is not None:
            result[path] = raw
    published = root / "published"
    if published.exists() or published.is_symlink():
        io.member(root, "published", directory=True)
        result.update({"published/" + path: raw for path, raw in read_tree(published).items()})
    return result


def _git_read(root, *arguments):
    result = subprocess.run(["git", "-c", "core.hooksPath=/dev/null", *arguments], cwd=root,
                            capture_output=True, timeout=30)
    if result.returncode:
        raise DataError("published source or pinned installation commit is unavailable in Git")
    return result.stdout


def _source_snapshot(root, record, destination):
    """Read declarative frozen source; never import or execute code from that revision."""
    revision = record["source_revision"]
    catalog = io.parse_json(_git_read(root, "show", revision + ":catalog.json"), what="frozen catalog")
    if not isinstance(catalog, dict) or set(catalog) != {"schema_version", "plugins"} or \
            type(catalog["schema_version"]) is not int or catalog["schema_version"] != 1 or not isinstance(catalog["plugins"], list):
        raise DataError("invalid frozen source catalog")
    selected = None
    paths = set()
    for item in catalog["plugins"]:
        if not isinstance(item, dict) or set(item) != {"path"}:
            raise DataError("invalid frozen catalog registration")
        path = io.relative_path(item["path"])
        if not re.fullmatch(r"plugins/[a-z0-9][a-z0-9-]{0,63}", path) or path in paths:
            raise DataError("unsafe or duplicate frozen catalog registration")
        paths.add(path)
        product = io.parse_json(_git_read(root, "show", revision + ":" + path + "/product.json"), what="frozen product")
        if product.get("product_id") == record["product_id"]:
            if selected is not None:
                raise DataError("duplicate frozen product identity")
            selected = path
    if selected is None:
        raise DataError("published product was not registered in its frozen source")
    archive = _git_read(root, "archive", "--format=zip", revision, "--", selected)
    if len(archive) > 256 * 1024 * 1024:
        raise DataError("frozen source snapshot exceeds limit")
    with zipfile.ZipFile(BytesIO(archive)) as zipped:
        members = zipped.infolist()
        if len(members) > 20000 or sum(member.file_size for member in members) > 256 * 1024 * 1024:
            raise DataError("frozen source archive exceeds limit")
        for member in members:
            relative = io.relative_path(member.filename.rstrip("/"))
            if member.is_dir() and selected.startswith(relative + "/"):
                continue
            if not (relative == selected or relative.startswith(selected + "/")):
                raise DataError("frozen source archive escapes the registered plugin")
            mode = member.external_attr >> 16
            if member.is_dir():
                continue
            if stat.S_ISLNK(mode) or stat.S_ISFIFO(mode) or stat.S_ISSOCK(mode):
                raise DataError("frozen source contains an unsafe file")
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(zipped.read(member))
    (destination / "catalog.json").write_bytes(io.dump_json({"schema_version": 1, "plugins": [{"path": selected}]}))
    return load_catalog(destination)[0]


def verify_public_sources(root, records, files):
    """Independently bind records to actual Git source and pinned installation bytes."""
    from .release.layout import package_outputs, zip_bytes
    from .rendering import marketplace_entry
    for record in records.values():
        _git_read(root, "merge-base", "--is-ancestor", record["source_revision"], "HEAD")
        if _git_read(root, "rev-parse", record["tag"] + "^{commit}").decode().strip() != record["source_revision"]:
            raise DataError("published source tag moved")
        if record["codex_revision"] is not None:
            prefix = f"published/codex/{record['product_id']}/{record['version']}/"
            entries = _git_read(root, "ls-tree", "-r", "-z", record["codex_revision"], "--", prefix).split(b"\0")
            pinned = {}
            for entry in entries:
                if not entry:
                    continue
                metadata, path = entry.split(b"\t", 1)
                mode, kind, blob = metadata.split()
                if mode not in (b"100644", b"100755") or kind != b"blob":
                    raise DataError("pinned Codex package contains a nonregular file")
                name = path.decode()
                pinned[name] = _git_read(root, "cat-file", "blob", blob.decode())
            if pinned != {name: files[name] for name in record["codex_files"]}:
                raise DataError("pinned Codex commit differs from its public record")
        with tempfile.TemporaryDirectory(prefix="ai-published-source-") as temporary:
            snapshot = Path(temporary)
            spec = _source_snapshot(root, record, snapshot)
            if spec.version != record["version"] or spec.source_tree_hash != record["source_tree_hash"] or set(spec.hosts) != set(record["hosts"]):
                raise DataError("published identity/version/hosts/hash differs from frozen source")
            # Live acceptance was checked before publication. A public checkout
            # must never need private records/logs again or invent a fresh pass.
            release_config, _ = io.read_json(spec.root, "release.json")
            acceptance = release_config.get("acceptance")
            if not isinstance(acceptance, dict) or set(acceptance) != set(spec.hosts) or any(
                    not isinstance(value, str) or not value for value in acceptance.values()):
                raise DataError("frozen source did not declare evidence for every published host")
            outputs = package_outputs(spec, {"source_revision": record["source_revision"],
                                              "working_tree_dirty": False})
            for host in spec.hosts:
                entry = marketplace_entry(spec, host)
                del entry["source"]
                artifact = io.parse_json(outputs[f"{host}/{spec.product_id}/artifact.json"], what="source artifact")
                if entry != record["hosts"][host]["entry"] or artifact["content_hash"] != record["hosts"][host]["package_content_hash"]:
                    raise DataError("published metadata/package hash differs from frozen source")
                base = f"{host}/{spec.product_id}/"
                installer = zip_bytes({f"{spec.product_id}/{name.removeprefix(base)}": raw
                    for name, raw in outputs.items() if name.startswith(base)})
                asset = record["hosts"][host]["asset"]
                if asset["sha256"] != io.sha256(installer) or asset["size"] != len(installer):
                    raise DataError("published installer digest/size differs from frozen source")
            if "codex" in spec.hosts:
                original = f"codex/{spec.product_id}/"
                published = f"published/codex/{spec.product_id}/{spec.version}/"
                expected = {published + name.removeprefix(original): raw
                            for name, raw in outputs.items() if name.startswith(original)}
                if expected != {name: files[name] for name in record["codex_files"]}:
                    raise DataError("public Codex package differs from frozen source")


def check_public_markets(root):
    from .distribution import _existing as validate, bootstrap_files, load_config, repository_url
    root = Path(root).absolute()
    if _existing(root, INITIALIZE_PATH) is not None:
        raise ConflictError("market initialization is incomplete; resume marketplace initialize")
    load_config(root)
    specs = load_catalog(root)
    repository = repository_url(specs[0].manifest["repository"])
    files = read_public_files(root)
    records, _, _ = validate(files, "stable", repository)
    if not files:
        return {"ok": False, "check": True, "problems": ["public market has not been initialized"],
                "files": sorted(bootstrap_files())}
    verify_public_sources(root, records, files)
    return {"ok": True, "check": True, "files": sorted(files), "problems": []}


def _initial_snapshot(current, expected, legacy, receipt_raw, migrate):
    if set(current) - set(expected):
        raise ConflictError("unknown initialization destinations")
    if receipt_raw is not None or any(current.get(path) not in (None, raw) for path, raw in expected.items()):
        receipt = io.parse_json(receipt_raw, what="legacy receipt") if receipt_raw is not None else None
        if not migrate or current != legacy or not isinstance(receipt, dict) or \
                type(receipt.get("schema_version")) is not int or receipt != {"schema_version": 1,
                "files": {path: io.sha256(raw) for path, raw in legacy.items()}}:
            raise ConflictError("existing root marketplace is not the exact owned development snapshot")


def _initial_bytes(value):
    if value is None:
        return None
    if not isinstance(value, str):
        raise DataError("invalid initialization journal bytes")
    try:
        return base64.b64decode(value, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise DataError("invalid initialization journal bytes") from exc


def _unlink_owned(root, path, previous):
    if _existing(root, path) != previous:
        raise ConflictError(f"initialization input changed: {path}")
    with io.parent_handle(root, path) as (parent, name):
        os.unlink(name, dir_fd=parent)


def initialize_public_market(root, *, migrate=False):
    """Resume a byte-bound migration; never adopt a later human edit as the baseline."""
    from .distribution import bootstrap_files, load_config
    root = Path(root).absolute()
    load_config(root)
    expected = bootstrap_files()
    journal_raw = _existing(root, INITIALIZE_PATH)
    current = read_public_files(root)
    if journal_raw is None and any(path.startswith("published/") for path in current):
        return check_public_markets(root)
    specs = load_catalog(root)
    legacy = {marketplace_path(host): io.dump_json(_project_market(specs, host))
              for host in HOSTS if any(host in spec.hosts for spec in specs)}
    if journal_raw is None:
        _, old_raw = _receipt(root)
        _initial_snapshot(current, expected, legacy, old_raw, migrate)
        baseline = {path: current.get(path) for path in expected}
        encode = lambda value: base64.b64encode(value).decode() if value is not None else None
        journal_raw = io.dump_json({"schema_version": 1,
            "previous": {path: encode(raw) for path, raw in baseline.items()},
            "legacy_receipt": encode(old_raw)})
        _write_market(root, INITIALIZE_PATH, journal_raw, None)
    else:
        journal = io.parse_json(journal_raw, what="initialization journal")
        if not isinstance(journal, dict) or set(journal) != {"schema_version", "previous", "legacy_receipt"} or \
                type(journal["schema_version"]) is not int or journal["schema_version"] != 1 or \
                not isinstance(journal["previous"], dict) or set(journal["previous"]) != set(expected):
            raise DataError("invalid initialization journal")
        baseline = {path: _initial_bytes(raw) for path, raw in journal["previous"].items()}
        old_raw = _initial_bytes(journal["legacy_receipt"])
        _initial_snapshot({path: raw for path, raw in baseline.items() if raw is not None},
                          expected, legacy, old_raw, migrate)
    if set(current) - set(expected) or any(current.get(path) not in (baseline[path], raw)
                                         for path, raw in expected.items()):
        raise ConflictError("marketplace changed after the reviewed initialization snapshot")
    receipt_now = _existing(root, RECEIPT_PATH)
    complete = all(current.get(path) == raw for path, raw in expected.items())
    if receipt_now != old_raw and not (receipt_now is None and complete):
        raise ConflictError("legacy ownership receipt changed during migration")
    changed = []
    for path, raw in expected.items():
        previous = current.get(path)
        if previous != raw:
            _write_market(root, path, raw, previous)
            changed.append(path)
    if read_public_files(root) != expected:
        raise ConflictError("initialized marketplace changed before completion; recovery journal retained")
    if old_raw is not None and receipt_now is not None:
        _unlink_owned(root, RECEIPT_PATH, old_raw)
    _unlink_owned(root, INITIALIZE_PATH, journal_raw)
    return {"ok": True, "files": sorted(expected), "changed": changed, "problems": []}


def sync_markets(root, check=False, *, output=None):
    """Explicit scratch development output; configured public roots cannot be overwritten."""
    root = Path(root).absolute()
    if output is not None:
        if check:
            raise DataError("development generation uses --output; public verification uses marketplace check")
        from .build import build_plugins
        result = build_plugins(root, load_catalog(root), output, HOSTS)
        return dict(result, output=str(Path(output).absolute()), kind="development")
    if (root / "distribution.json").exists() or (root / "published").exists():
        if check:
            return check_public_markets(root)
        raise DataError("development market requires an explicit --output; public root is protected")
    # Compatibility for callers operating on isolated scratch repositories only.
    return _sync_development_repository(root, check=check)
