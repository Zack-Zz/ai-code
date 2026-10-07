"""Verify packages against trusted repository inputs, never package declarations alone."""

import os
from pathlib import Path
import re
import stat

from . import io
from .io import DataError
from .registry import ID_PATTERN, VERSION_PATTERN
from .rendering import file_hashes, marketplace_entry, marketplace_path, package_files

ARTIFACT_FIELDS = {"schema_version", "product_id", "version", "host", "profiles", "source_revision",
                   "working_tree_dirty", "source_tree_hash", "files", "content_hash"}
HASH_PATTERN = re.compile(r"[0-9a-f]{64}")


def read_artifact(package):
    artifact, _ = io.read_json(package, "artifact.json")
    if not isinstance(artifact, dict) or set(artifact) != ARTIFACT_FIELDS:
        raise DataError("artifact.json fields do not match its contract")
    if type(artifact["schema_version"]) is not int or artifact["schema_version"] != 1:
        raise DataError("artifact schema_version must be integer 1")
    for key, pattern in (("product_id", ID_PATTERN), ("version", VERSION_PATTERN),
                         ("content_hash", HASH_PATTERN), ("source_tree_hash", HASH_PATTERN)):
        if not isinstance(artifact[key], str) or not pattern.fullmatch(artifact[key]):
            raise DataError(f"invalid artifact {key}")
    if artifact["host"] not in ("codex", "zcode"):
        raise DataError("invalid artifact host")
    if (not isinstance(artifact["profiles"], list) or
            not all(isinstance(value, str) for value in artifact["profiles"])):
        raise DataError("artifact profiles must be a list of strings")
    if type(artifact["working_tree_dirty"]) is not bool:
        raise DataError("artifact working_tree_dirty must be boolean")
    revision = artifact["source_revision"]
    if revision is not None and (not isinstance(revision, str) or
                                 not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", revision)):
        raise DataError("artifact source_revision must be Git object ID or null")
    if not isinstance(artifact["files"], list):
        raise DataError("artifact files must be a list")
    for entry in artifact["files"]:
        if not isinstance(entry, list) or len(entry) != 2:
            raise DataError("artifact files must contain path/hash pairs")
        io.relative_path(entry[0], what="artifact file path")
        if not isinstance(entry[1], str) or not HASH_PATTERN.fullmatch(entry[1]):
            raise DataError("artifact file hash must be SHA256 hex")
    return artifact


def _walk(root):
    for entry in sorted(os.scandir(root), key=lambda entry: entry.name):
        path = Path(entry.path)
        mode = entry.stat(follow_symlinks=False).st_mode
        if stat.S_ISDIR(mode):
            yield from _walk(path)
        else:
            yield path, mode


def check_package(package_root, host, spec):
    package_root = Path(package_root).absolute()
    if host not in ("codex", "zcode"):
        raise DataError(f"unknown host: {host}")
    artifact = read_artifact(package_root)
    expected = package_files(spec, host)
    expected_pairs = file_hashes(expected)
    expected_hash = io.sha256(io.canonical_json(expected_pairs))
    problems = []
    caches = []
    for key, value in (("product_id", spec.product_id), ("version", spec.version), ("host", host),
                       ("profiles", spec.profiles), ("source_tree_hash", spec.source_tree_hash)):
        if artifact[key] != value:
            problems.append(f"artifact {key} differs from trusted plugin: {artifact[key]!r} != {value!r}")
    if package_root.name != spec.product_id:
        problems.append("package directory name differs from trusted product_id")
    registered = dict(artifact["files"])
    if len(registered) != len(artifact["files"]):
        problems.append("duplicate artifact file entries")
    if artifact["files"] != sorted(artifact["files"]):
        problems.append("artifact files are not sorted")
    for relative in sorted(set(expected) - set(registered)):
        problems.append(f"required trusted resource missing from artifact: {relative}")
    for relative in sorted(set(registered) - set(expected)):
        problems.append(f"untrusted resource registered in artifact: {relative}")
    if io.sha256(io.canonical_json(artifact["files"])) != artifact["content_hash"]:
        problems.append("artifact content_hash differs from its files list")
    if artifact["content_hash"] != expected_hash:
        problems.append("artifact content_hash differs from trusted package inputs")
    for relative, payload in expected.items():
        try:
            actual = io.read_file(package_root, relative)
        except DataError as exc:
            problems.append(f"missing or unsafe trusted resource {relative}: {exc}")
            continue
        if actual != payload:
            problems.append(f"resource content differs from trusted inputs: {relative}")
        if relative in registered and io.sha256(actual) != registered[relative]:
            problems.append(f"artifact file hash mismatch: {relative}")
    for path, mode in _walk(package_root):
        relative = path.relative_to(package_root).as_posix()
        if relative == "artifact.json":
            continue
        if relative in expected:
            if not stat.S_ISREG(mode):
                problems.append(f"trusted resource is not a regular file: {relative}")
            continue
        # CPython caches are executable inputs. Matching a trusted source's
        # basename, timestamp and size does not authenticate their bytecode.
        problems.append(f"extra active file outside trusted closure: {relative}")
    try:
        market, _ = io.read_json(package_root.parent, marketplace_path(host))
        if not isinstance(market, dict) or set(market) != {"name", "plugins"} or market["name"] != "ai-code-local":
            raise DataError("marketplace must be ai-code-local with name/plugins fields")
        entries = market["plugins"]
        if not isinstance(entries, list) or not all(isinstance(entry, dict) for entry in entries):
            raise DataError("marketplace plugins must be a list of entries")
        names = [entry.get("name") for entry in entries]
        if not all(isinstance(name, str) for name in names) or len(set(names)) != len(names):
            raise DataError("marketplace contains duplicate or invalid plugin identities")
        matches = [entry for entry in entries if entry.get("name") == spec.product_id]
        if matches != [marketplace_entry(spec, host)]:
            problems.append("marketplace entry differs from trusted plugin identity/version/source")
    except DataError as exc:
        problems.append(f"invalid marketplace: {exc}")
    return {"ok": not problems, "product_id": artifact["product_id"], "version": artifact["version"],
            "host": host, "content_hash": artifact["content_hash"],
            "source_tree_hash": artifact["source_tree_hash"], "files_checked": len(expected),
            "problems": problems, "caches": caches}
