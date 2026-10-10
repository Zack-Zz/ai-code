"""Strict local bundle integrity; historical bundles remain caller-trusted references."""

from io import BytesIO
import os
from pathlib import Path
import re
import stat
import zipfile

from .. import io
from ..io import DataError
from ..package_check import read_artifact
from ..registry import ID_PATTERN, HOSTS
from ..rendering import marketplace_path, manifest_path
from ..versions import VERSION_PATTERN, version_key

FIELDS = {"schema_version", "product_id", "version", "display_name", "mode", "tag", "source_revision",
          "working_tree_dirty", "source_tree_hash", "readiness", "files", "content_hash"}
HASH = re.compile(r"[0-9a-f]{64}")


def read_tree(root):
    root = Path(root).absolute()
    if root.is_symlink() or not root.is_dir():
        raise DataError("release bundle must be a real directory")
    files = {}
    def walk(directory):
        for entry in sorted(os.scandir(directory), key=lambda item: item.name):
            mode = entry.stat(follow_symlinks=False).st_mode
            path = Path(entry.path)
            if stat.S_ISDIR(mode):
                io.member(root, path.relative_to(root).as_posix(), directory=True)
                walk(path)
            elif stat.S_ISREG(mode):
                relative = path.relative_to(root).as_posix()
                files[relative] = io.read_file(root, relative, limit=256 * 1024 * 1024)
            else:
                raise DataError(f"release bundle has a symlink or special file: {path.relative_to(root)}")
    walk(root)
    return files


def pairs(value, what):
    if not isinstance(value, list):
        raise DataError(f"{what} must contain path/SHA256 pairs")
    result = {}
    for item in value:
        if not isinstance(item, list) or len(item) != 2 or not isinstance(item[1], str) or not HASH.fullmatch(item[1]):
            raise DataError(f"{what} has invalid path/SHA256 pair")
        name = io.relative_path(item[0], what=what)
        if name in result:
            raise DataError(f"{what} contains duplicate paths")
        result[name] = item[1]
    if value != sorted(value):
        raise DataError(f"{what} paths must be sorted")
    return result


def _json(files, relative):
    if relative not in files:
        raise DataError(f"required release file is missing: {relative}")
    return io.parse_json(files[relative], what=relative)


def record(files):
    manifest = _json(files, "release.json")
    if not isinstance(manifest, dict) or set(manifest) != FIELDS or type(manifest["schema_version"]) is not int or manifest["schema_version"] not in (1, 2):
        raise DataError("release manifest fields/schema are invalid")
    for key, pattern in (("product_id", ID_PATTERN), ("version", VERSION_PATTERN), ("source_tree_hash", HASH), ("content_hash", HASH)):
        if not isinstance(manifest[key], str) or not pattern.fullmatch(manifest[key]):
            raise DataError(f"invalid release manifest {key}")
    if not isinstance(manifest["display_name"], str) or not manifest["display_name"].strip() or manifest["mode"] not in {"draft", "stable"}:
        raise DataError("invalid release display name or mode")
    if type(manifest["working_tree_dirty"]) is not bool:
        raise DataError("release working_tree_dirty must be boolean")
    revision = manifest["source_revision"]
    if revision is not None and (not isinstance(revision, str) or not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", revision)):
        raise DataError("invalid release source revision")
    if manifest["tag"] not in (None, f"{manifest['product_id']}/v{manifest['version']}"):
        raise DataError("invalid release identity/version tag")
    if not isinstance(manifest["readiness"], dict):
        raise DataError("release readiness must be an object")
    declared = pairs(manifest["files"], "release files")
    actual = {name: io.sha256(data) for name, data in files.items() if name != "release.json"}
    if declared != actual or io.sha256(io.canonical_json(manifest["files"])) != manifest["content_hash"]:
        raise DataError("release files or content hash differ from actual bytes")
    expected_sums = "".join(f"{io.sha256(data)}  {name}\n" for name, data in sorted(files.items())
                            if name not in {"release.json", "SHA256SUMS"}).encode()
    if files.get("SHA256SUMS") != expected_sums:
        raise DataError("release SHA256SUMS differs from actual bytes")
    return manifest


def verify_zip(raw, expected, what):
    try:
        with zipfile.ZipFile(BytesIO(raw)) as archive:
            entries = archive.infolist()
            if [item.filename for item in entries] != sorted(expected):
                raise DataError(f"{what} archive has unexpected closure/order")
            for item in entries:
                io.relative_path(item.filename, what="ZIP member")
                payload = expected[item.filename]
                if not stat.S_ISREG(item.external_attr >> 16) or item.file_size != len(payload) or archive.read(item) != payload:
                    raise DataError(f"{what} archive content/type differs from trusted files")
    except (OSError, zipfile.BadZipFile, RuntimeError) as exc:
        raise DataError(f"invalid {what} ZIP: {exc}") from exc


def historical(previous):
    path = Path(previous).absolute()
    if path.is_symlink():
        raise DataError("previous release must not be a symlink")
    root = path.parent if path.name == "release.json" else path
    files = read_tree(root)
    release = record(files)
    identity, version = release["product_id"], release["version"]
    source = _json(files, "source-inputs.json")
    if not isinstance(source, dict) or source.get("schema_version") != 1 or type(source.get("schema_version")) is not int:
        raise DataError("previous source-inputs schema is invalid")
    for field in ("product_id", "version", "source_tree_hash"):
        if source.get(field) != release[field]:
            raise DataError(f"previous source-inputs {field} differs from release")
    product = source.get("product")
    if not isinstance(product, dict) or product.get("product_id") != identity or product.get("version") != version:
        raise DataError("previous product identity differs from release")
    hosts = product.get("hosts")
    if not isinstance(hosts, list) or not hosts or len(set(hosts)) != len(hosts) or set(hosts) - set(HOSTS):
        raise DataError("previous release hosts are invalid")
    source_pairs = pairs(source.get("source_files"), "previous source inputs")
    release_pairs = pairs(source.get("release_files"), "previous release inputs")
    if "product.json" not in source_pairs or "release.json" not in release_pairs:
        raise DataError("previous input snapshot is incomplete")
    index = _json(files, "packages/index.json")
    if not isinstance(index, dict) or type(index.get("schema_version")) is not int or index["schema_version"] != 2 or \
            set(index.get("plugins", {})) != {identity} or set(index.get("hosts", {})) != set(hosts):
        raise DataError("previous package index has invalid schema/identity/host closure")
    plugin = index["plugins"][identity]
    if plugin.get("version") != version or plugin.get("source_tree_hash") != release["source_tree_hash"] or set(plugin.get("hosts", {})) != set(hosts):
        raise DataError("previous package index differs from release")
    package_hashes = source.get("package_content_hashes")
    if not isinstance(package_hashes, dict) or set(package_hashes) != set(hosts):
        raise DataError("previous package hash inventory is incomplete")
    allowed = {"release.json", "release-notes.md", "SHA256SUMS", "source-inputs.json", "packages/index.json"}
    config = source.get("release_config")
    if not isinstance(config, dict) or not isinstance(config.get("readmes"), dict) or set(config["readmes"]) != {"en", "zh-CN"}:
        raise DataError("previous release readme bindings are invalid")
    for host in hosts:
        entry = plugin["hosts"][host]
        base = f"packages/{host}/{identity}/"
        if entry.get("package_dir") != f"{host}/{identity}" or entry.get("zip") != f"{host}/{identity}-{version}.zip":
            raise DataError("previous index has noncanonical package paths")
        artifact = read_artifact(root / base)
        for field, expected in (("product_id", identity), ("version", version), ("host", host),
                ("source_tree_hash", release["source_tree_hash"]), ("source_revision", release["source_revision"]),
                ("working_tree_dirty", release["working_tree_dirty"]), ("profiles", product.get("profiles", []))):
            if artifact[field] != expected:
                raise DataError(f"previous artifact {field} differs from release")
        package = {name.removeprefix(base): data for name, data in files.items() if name.startswith(base)}
        pairs_declared = pairs(artifact["files"], "previous package files")
        actual = {name: io.sha256(data) for name, data in package.items() if name != "artifact.json"}
        content_hash = io.sha256(io.canonical_json(artifact["files"]))
        if actual != pairs_declared or artifact["content_hash"] != content_hash or \
                entry.get("package_content_hash") != content_hash or package_hashes[host] != content_hash or \
                type(entry.get("files_count")) is not int or entry["files_count"] != len(actual):
            raise DataError("previous package bytes/hash/count are inconsistent")
        native = _json(package, manifest_path(host))
        if native.get("name") != identity or native.get("version") != version or native.get("author") != product.get("publisher"):
            raise DataError("previous native manifest identity/version/publisher is inconsistent")
        market_relative = f"packages/{host}/{marketplace_path(host)}"
        market = _json(files, market_relative)
        market_entry = index["hosts"][host]
        if market_entry.get("marketplace") != f"{host}/{marketplace_path(host)}" or market_entry.get("marketplace_sha256") != io.sha256(files[market_relative]):
            raise DataError("previous marketplace path/hash is inconsistent")
        if not isinstance(market, dict) or not isinstance(market.get("plugins"), list) or len(market["plugins"]) != 1:
            raise DataError("previous market must contain exactly one plugin")
        item = market["plugins"][0]
        expected_source = {"source": "local", "path": f"./{identity}"} if host == "codex" else f"./{identity}"
        if item.get("name") != identity or item.get("version") != version or item.get("source") != expected_source:
            raise DataError("previous market identity/version/source is inconsistent")
        raw_zip = f"packages/{entry['zip']}"
        if entry.get("zip_sha256") != io.sha256(files[raw_zip]):
            raise DataError("previous ZIP checksum is inconsistent")
        expected_zip = {f"{identity}/{name}": data for name, data in package.items()}
        expected_zip[marketplace_path(host)] = files[market_relative]
        verify_zip(files[raw_zip], expected_zip, "previous package")
        if release["schema_version"] == 2:
            installer = f"installers/{identity}-{version}-{host}-plugin.zip"
            if installer not in files:
                raise DataError(f"previous installer is missing: {installer}")
            verify_zip(files[installer], {f"{identity}/{name}": data for name, data in package.items()},
                       "previous installer")
            allowed.add(installer)
        download = f"downloads/{identity}-{version}-{host}.zip"
        if files.get(download) != files[raw_zip]:
            raise DataError("previous qualified download differs from package ZIP")
        channel = "openai" if host == "codex" else host
        source_base = f"submissions/{channel}/plugins/{identity}/"
        kit = {name.removeprefix(source_base): data for name, data in files.items() if name.startswith(source_base)}
        expected_kit = {name: data for name, data in package.items() if name != "artifact.json"}
        for name, locale in (("README.md", "en"), ("README_CN.md", "zh-CN")):
            if name not in kit or io.sha256(kit[name]) != release_pairs.get(config["readmes"][locale]):
                raise DataError("previous source-kit readme is not bound to release inputs")
            expected_kit[name] = kit[name]
        if kit != expected_kit:
            raise DataError("previous source-kit closure differs from package/readme inputs")
        submission = f"submissions/{channel}/{identity}-{version}.zip"
        verify_zip(files[submission], {f"{identity}/{name}": data for name, data in kit.items()}, "previous submission")
        registration = f"submissions/{channel}/{marketplace_path(host)}"
        source_market = _json(files, registration)
        expected_item = dict(item, source={"source": "local", "path": f"./plugins/{identity}"} if host == "codex" else f"./plugins/{identity}")
        if source_market != dict(market, plugins=[expected_item]):
            raise DataError("previous source-kit market differs from package identity/source")
        allowed.update(name for name in files if name.startswith(base) or name.startswith(source_base))
        allowed.update({market_relative, raw_zip, download, submission, registration})
    if set(files) != allowed:
        raise DataError("previous release contains unexpected file closure")
    return release, package_hashes


def compare_previous(spec, capture, previous):
    if previous is None:
        return
    old, hashes = historical(previous)
    if old["product_id"] != spec.product_id:
        raise DataError("previous release belongs to another plugin")
    old_version = version_key(old["version"])
    version = version_key(spec.version)
    if version < old_version:
        raise DataError("release version would downgrade the previous version")
    if version == old_version and (old["source_tree_hash"] != spec.source_tree_hash or hashes != capture.package_hashes):
        raise DataError("immutable release version was reused for different source/package content")
