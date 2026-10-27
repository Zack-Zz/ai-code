"""Pure local hosted-market planning; never writes Git or network state.

Every plan is review data. Callers must regenerate it from trusted source and
actually downloaded release assets before using its hash as a deployment lease.
"""

import base64
import binascii
import copy
from datetime import datetime
import re
from urllib.parse import quote

from . import io
from .io import ConflictError, DataError
from .versions import release_kind, version_key
from .registry import HOSTS, ID_PATTERN, VERSION_PATTERN, load_catalog
from .release import verify_release
from .release import integrity, metadata, source_git
from .rendering import marketplace_entry, marketplace_path
from .listings import validate_icon_url

HASH = re.compile(r"[0-9a-f]{64}")
REVISION = re.compile(r"[0-9a-f]{40}|[0-9a-f]{64}")
LEGACY_TRANSPORTS = {"claude": "archive", "codex": "git-subdir", "zcode": "url-zip"}
TRANSPORTS = dict(LEGACY_TRANSPORTS, dsh="git-subdir")
GIT_HOSTS = {"codex", "dsh"}
MARKETPLACE = {"branch": "main", "name": "ai-code", "version_policy": "latest-stable"}
INDEX_PATH = "published/index.json"
LOCK_PATH = "published/marketplaces.lock.json"
LEGACY_NATIVE_PATHS = {".claude-plugin/marketplace.json", ".agents/plugins/marketplace.json", "marketplace.json"}
NATIVE_PATHS = LEGACY_NATIVE_PATHS | {"published/dsh/index.json"}
LEGACY_RECORD_FIELDS = {"schema_version", "channel", "product_id", "version", "repository", "source_revision",
                 "source_tree_hash", "tag", "release_id", "release_url", "mode", "readiness", "hosts",
                 "codex_revision", "codex_files"}
LEGACY_PLAN_FIELDS = {"schema_version", "status", "channel", "branch", "marketplace_name", "base_commit",
               "repository", "product_id", "version", "source_revision", "release_id", "release_tag",
               "bootstrap", "previous_version", "record", "existing_files", "codex_files", "config_hash", "plan_hash"}
RECORD_FIELDS = LEGACY_RECORD_FIELDS - {"codex_revision", "codex_files"} | {"git_installs", "release_published_at"}
PLAN_FIELDS = LEGACY_PLAN_FIELDS - {"codex_files"} | {"git_install_files", "config"}
RECEIPT_FIELDS = {"schema_version", "record", "base_commit", "config_hash", "plan_hash"}
HOST_FIELDS = {"asset", "package_content_hash", "entry"}
ASSET_FIELDS = {"id", "name", "size", "browser_download_url", "sha256"}
READINESS_FIELDS = {"publication_ready", "pending_acceptance", "accepted_hosts", "package_content_hashes", "limitations"}


def _object(value, fields, what):
    if not isinstance(value, dict) or set(value) != fields:
        raise DataError(f"{what} requires exactly {sorted(fields)}")


def _schema(value, what, version=1):
    if type(value) is not int or value != version:
        raise DataError(f"{what} requires schema {version}")


def _hash(value, what):
    if not isinstance(value, str) or not HASH.fullmatch(value):
        raise DataError(f"invalid {what}: SHA256 required")


def _revision(value, what, nullable=False):
    if nullable and value is None:
        return
    if not isinstance(value, str) or not REVISION.fullmatch(value):
        raise DataError(f"invalid {what}: Git revision required")


def _repository(value):
    if not isinstance(value, str) or not re.fullmatch(r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:\.git)?/?", value):
        raise DataError("distribution repository must be a canonical HTTPS GitHub repository")
    value = value.rstrip("/").removesuffix(".git")
    if any(part in {".", ".."} for part in value.split("/")[-2:]):
        raise DataError("invalid GitHub repository identity")
    return value


def repository_url(value):
    """Canonical public GitHub identity shared by planners and remote adapters."""
    return _repository(value)


def validate_config(config):
    version = config.get("schema_version") if isinstance(config, dict) else None
    fields = {"schema_version", "source_branch", "marketplace", "transports"}
    if version == 3:
        fields.add("identity_replacements")
    _object(config, fields, "distribution config")
    if type(version) is not int or version not in (2, 3):
        raise DataError("distribution config requires schema 2 or 3")
    if config["transports"] != (TRANSPORTS if version == 3 else LEGACY_TRANSPORTS):
        raise DataError("unsupported distribution transports")
    if config["source_branch"] != "main" or config["marketplace"] != MARKETPLACE:
        raise DataError("distribution requires main and one latest-stable marketplace")
    replacements = config.get("identity_replacements", {})
    if not isinstance(replacements, dict) or any(not isinstance(value, str) or not ID_PATTERN.fullmatch(value)
            for pair in replacements.items() for value in pair):
        raise DataError("invalid identity replacements")
    if set(replacements) & set(replacements.values()) or len(set(replacements.values())) != len(replacements):
        raise DataError("identity replacements must be one-to-one without chains, cycles or identity overlap")
    return config


def load_config(root):
    config, _ = io.read_json(root, "distribution.json")
    return validate_config(config)


def git_installs(record):
    """Normalize legacy Codex fields in memory; historical bytes stay untouched."""
    if "git_installs" in record:
        return copy.deepcopy(record["git_installs"])
    if record.get("codex_files"):
        return {"codex": {"revision": record["codex_revision"], "files": copy.deepcopy(record["codex_files"])}}
    return {}


def _git_prefix(host, identity, version):
    return f"published/{host}/{identity}/{version}/"


def _stage_path(identity, version):
    return f"published/staged/{identity}/{version}.json"


def _timestamp(value):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z", value):
        raise DataError("Release published_at must be an actual UTC timestamp")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise DataError("invalid Release published_at") from exc
    if parsed.year < 2008:
        raise DataError("invalid Release published_at")
    return int(parsed.timestamp())


def _candidate_record(record):
    result = copy.deepcopy(record)
    for entry in result.get("git_installs", {}).values():
        entry["revision"] = None
    if "codex_revision" in result:
        result["codex_revision"] = None
    return result


def _asset(asset, repository, tag, name=None):
    _object(asset, ASSET_FIELDS, "Release asset")
    if type(asset["id"]) is not int or asset["id"] <= 0 or type(asset["size"]) is not int or asset["size"] <= 0:
        raise DataError("Release asset needs a positive integer ID and size")
    relative = io.relative_path(asset["name"], what="Release asset name")
    if "/" in relative or name is not None and relative != name:
        raise DataError("Release installer asset name differs from expected identity/version/host")
    expected = f"{repository}/releases/download/{quote(tag, safe='')}/{quote(relative, safe='')}"
    if asset["browser_download_url"] != expected:
        raise DataError("Release asset URL must bind this GitHub repository and encoded canonical tag")
    _hash(asset["sha256"], "Release asset digest")


def _encode(files):
    return {name: {"encoding": "base64", "data": base64.b64encode(data).decode("ascii"), "sha256": io.sha256(data)}
            for name, data in sorted(files.items())}


def _decode(files):
    if not isinstance(files, dict):
        raise DataError("plan file inventory must be an object")
    result = {}
    for name, entry in files.items():
        io.relative_path(name)
        _object(entry, {"encoding", "data", "sha256"}, "encoded plan file")
        if entry["encoding"] != "base64" or not isinstance(entry["data"], str):
            raise DataError("plan files require explicit base64 encoding")
        try:
            payload = base64.b64decode(entry["data"], validate=True)
        except (ValueError, binascii.Error) as exc:
            raise DataError("invalid base64 plan file") from exc
        if base64.b64encode(payload).decode("ascii") != entry["data"] or io.sha256(payload) != entry["sha256"]:
            raise DataError(f"plan file bytes differ from digest: {name}")
        result[name] = payload
    return result


def in_scope(path):
    io.relative_path(path)
    return path in NATIVE_PATHS or path.startswith("published/")


def _record_path(identity, version):
    return f"published/releases/{identity}/{version}.json"


def _codex_prefix(identity, version):
    return f"published/codex/{identity}/{version}/"


def _snapshot(record, *, legacy=False):
    result = {"version": record["version"], "release_id": record["release_id"],
              "source_revision": record["source_revision"], "source_tree_hash": record["source_tree_hash"],
              "installers": {host: item["asset"]["sha256"] for host, item in sorted(record["hosts"].items())}}
    if legacy:
        result["codex_revision"] = record["codex_revision"]
    else:
        result["git_revisions"] = {host: item["revision"] for host, item in sorted(git_installs(record).items())}
    return result


def _entry(record, host):
    entry = copy.deepcopy(record["hosts"][host]["entry"])
    asset = record["hosts"][host]["asset"]
    if host == "dsh":
        engines = entry.pop("engines")
        icon = entry.pop("icon", None)
        revision = git_installs(record)[host]["revision"]
        if icon is not None:
            entry["icon"] = record["repository"].replace("https://github.com/", "https://raw.githubusercontent.com/") + f"/{revision}/published/dsh/{record['product_id']}/{record['version']}/{icon}"
        entry["versions"] = [{"version": record["version"], "publishTimestamp": _timestamp(record["release_published_at"]),
            "engines": engines, "source": {"type": "git", "url": record["repository"], "commit": revision,
            "path": f"published/dsh/{record['product_id']}/{record['version']}"}}]
    elif host == "codex":
        entry["source"] = {"source": "git-subdir", "url": record["repository"] + ".git",
                           "path": f"./published/codex/{record['product_id']}/{record['version']}",
                           "sha": git_installs(record)[host]["revision"]}
    else:
        source = {"source": "archive" if host == "claude" else "url", "url": asset["browser_download_url"], "sha256": asset["sha256"]}
        if host == "zcode":
            source.update(type="zip", path=record["product_id"])
        entry["source"] = source
    return entry


def _markets(channel, records, pointers, *, legacy=False):
    result = {}
    for host in (tuple(LEGACY_TRANSPORTS) if legacy else tuple(TRANSPORTS)):
        entries = []
        for identity, pointer in sorted(pointers.items()):
            record = records[_record_path(identity, pointer["version"])]
            if host in record["hosts"]:
                entries.append(_entry(record, host))
        market = {"format": 1, "title": {"en": "ai-code", "zh": "ai-code"}, "plugins": entries} if host == "dsh" else {"name": MARKETPLACE["name"], "plugins": entries}
        if host == "claude":
            market["owner"] = {"name": "ai-code"}
        result[marketplace_path(host)] = io.dump_json(market)
    return result


def _record(record, channel, repository, *, staged=False):
    _object(record, RECORD_FIELDS if isinstance(record, dict) and record.get("schema_version") == 3 else LEGACY_RECORD_FIELDS, "distribution record")
    if type(record["schema_version"]) is not int or record["schema_version"] not in (2, 3):
        raise DataError("distribution record requires schema 2 or 3")
    if record["schema_version"] == 3:
        _timestamp(record["release_published_at"])
    identity, version = record["product_id"], record["version"]
    if not isinstance(identity, str) or not ID_PATTERN.fullmatch(identity) or not isinstance(version, str) or not VERSION_PATTERN.fullmatch(version):
        raise DataError("record identity/version is invalid")
    tag = f"{identity}/v{version}"
    if record["channel"] != channel or record["repository"] != repository or record["tag"] != tag or record["mode"] != "stable" or channel != "stable" or release_kind(version) != "stable":
        raise DataError("record channel/repository/tag/mode binding differs")
    if type(record["release_id"]) is not int or record["release_id"] <= 0 or record["release_url"] != f"{repository}/releases/tag/{quote(tag, safe='')}":
        raise DataError("record Release identity/URL differs")
    _revision(record["source_revision"], "record source revision")
    _hash(record["source_tree_hash"], "record source hash")
    readiness = record["readiness"]
    _object(readiness, READINESS_FIELDS, "record readiness")
    if type(readiness["publication_ready"]) is not bool or channel == "stable" and not readiness["publication_ready"]:
        raise DataError("stable record must be publication-ready")
    hosts = record["hosts"]
    if not isinstance(hosts, dict) or not hosts or not set(hosts) <= set(HOSTS):
        raise DataError("record hosts must be a nonempty supported subset")
    for field in ("pending_acceptance", "accepted_hosts"):
        value = readiness[field]
        if not isinstance(value, list) or len(value) != len(set(value)) or not set(value) <= set(hosts):
            raise DataError("invalid record host acceptance inventory")
    if set(readiness["pending_acceptance"]) & set(readiness["accepted_hosts"]) or set(readiness["pending_acceptance"] + readiness["accepted_hosts"]) != set(hosts):
        raise DataError("record acceptance must partition all declared hosts")
    if not isinstance(readiness["limitations"], list) or not all(isinstance(item, str) for item in readiness["limitations"]):
        raise DataError("invalid readiness limitations")
    if not isinstance(readiness["package_content_hashes"], dict) or set(readiness["package_content_hashes"]) != set(hosts):
        raise DataError("readiness package inventory differs from hosts")
    for host, item in hosts.items():
        _object(item, HOST_FIELDS | ({"installer_format"} if record["schema_version"] == 3 else set()), "record host")
        if record["schema_version"] == 3 and item["installer_format"] != ("npm-tgz" if host == "dsh" else "zip"):
            raise DataError("record installer format differs from native host")
        _asset(item["asset"], repository, tag, f"{identity}-{version}-{host}-plugin.{'tgz' if host == 'dsh' else 'zip'}")
        _hash(item["package_content_hash"], "package content hash")
        if readiness["package_content_hashes"][host] != item["package_content_hash"]:
            raise DataError("record readiness/package hashes differ")
        entry = item["entry"]
        fields = {"name", "title", "description", "engines"} | ({"icon"} if isinstance(entry, dict) and "icon" in entry else set()) if host == "dsh" else ({"name", "version", "policy", "category"} if host == "codex" else {"name", "version", "description"})
        if isinstance(entry, dict):
            if host == "claude" and "displayName" in entry:
                fields.add("displayName")
            elif host == "zcode" and set(entry) & {"displayName", "icon"}:
                fields.update({"displayName", "icon"})
        _object(entry, fields, "record native entry")
        if entry["name"] != identity or host != "dsh" and entry["version"] != version:
            raise DataError("record native identity/version differs")
        if host == "dsh":
            if "icon" in entry:
                io.relative_path(entry["icon"], what="DSH icon path")
            for key in ("title", "description"):
                _object(entry[key], {"en", "zh"}, "DSH localized " + key)
                if any(not isinstance(value, str) or not value.strip() for value in entry[key].values()):
                    raise DataError("DSH locale values must be nonempty text")
            _object(entry["engines"], {"dsh"}, "DSH engines")
            if not isinstance(entry["engines"]["dsh"], str) or not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+(?:-[A-Za-z0-9.-]+)?", entry["engines"]["dsh"]):
                raise DataError("DSH engines must use an exact runtime version")
        elif host == "codex":
            if entry["policy"] != {"installation": "AVAILABLE", "authentication": "ON_INSTALL"} or entry["category"] != "developer-tools":
                raise DataError("invalid Codex native policy/category")
        elif not isinstance(entry["description"], str):
            raise DataError("native description must be text")
        if "displayName" in entry and (not isinstance(entry["displayName"], str) or not entry["displayName"].strip()):
            raise DataError("native displayName must be nonempty text")
        if host == "zcode" and "icon" in entry:
            validate_icon_url(entry["icon"], repository)
    installs = git_installs(record)
    if not isinstance(installs, dict) or set(installs) != set(hosts) & GIT_HOSTS:
        raise DataError("record Git file inventory differs from hosts")
    if record["schema_version"] == 2 and "dsh" in hosts:
        raise DataError("legacy record cannot declare DSH")
    if record["schema_version"] == 2 and "codex" not in hosts and record["codex_revision"] is not None:
        raise DataError("non-Codex record requires null Codex revision")
    for host, install in installs.items():
        _object(install, {"revision", "files"}, "Git installation")
        _revision(install["revision"], "record Git revision", nullable=staged)
        if host == "dsh" and install["revision"] is not None and not re.fullmatch(r"[0-9a-f]{40}", install["revision"]):
            raise DataError("DSH installation requires a full 40-character commit")
        hashes = install["files"]
        if not isinstance(hashes, dict) or not hashes:
            raise DataError("Git file inventory must be nonempty")
        prefix = _git_prefix(host, identity, version)
        for path, digest in hashes.items():
            io.relative_path(path)
            if not path.startswith(prefix):
                raise DataError("record Git file path differs from host/identity/version")
            _hash(digest, "Git file digest")
        if not {prefix + "artifact.json", prefix + ("package.json" if host == "dsh" else "plugin.json")} <= set(hashes):
            raise DataError("Git record must include artifact.json and its native manifest")
    revisions = {item["revision"] for item in installs.values()}
    if len(revisions) > 1:
        raise DataError("Git installations must share one distribution commit D")


def _git_package(record, host, files):
    prefix = _git_prefix(host, record["product_id"], record["version"])
    artifact = io.parse_json(files[prefix + "artifact.json"], what="managed Codex artifact")
    fields = {"schema_version", "product_id", "version", "host", "profiles", "source_revision", "working_tree_dirty", "source_tree_hash", "files", "content_hash"}
    _object(artifact, fields, "managed Codex artifact")
    _schema(artifact["schema_version"], "managed Codex artifact")
    for key, value in (("product_id", record["product_id"]), ("version", record["version"]), ("host", host), ("source_revision", record["source_revision"]), ("source_tree_hash", record["source_tree_hash"]), ("working_tree_dirty", False)):
        if type(artifact[key]) is not type(value) or artifact[key] != value:
            raise DataError(f"managed Codex artifact {key} differs")
    pairs = [[path.removeprefix(prefix), digest] for path, digest in sorted(git_installs(record)[host]["files"].items()) if path != prefix + "artifact.json"]
    if artifact["files"] != pairs or artifact["content_hash"] != io.sha256(io.canonical_json(pairs)) or artifact["content_hash"] != record["hosts"][host]["package_content_hash"]:
        raise DataError("managed Codex artifact inventory/hash differs")
    native = io.parse_json(files[prefix + ("package.json" if host == "dsh" else "plugin.json")], what="managed Codex plugin")
    if native.get("name") != record["product_id"] or native.get("version") != record["version"]:
        raise DataError("managed Git native identity/version differs")
    if host == "dsh":
        entry = record["hosts"][host]["entry"]
        if native.get("engines") != entry["engines"] or "icon" in entry and prefix + entry["icon"] not in files:
            raise DataError("DSH native engines/icon differs from record")


def _codex_package(record, files):
    for host in git_installs(record):
        _git_package(record, host, files)


def _catalog_files(records, pointers, retired=None, *, legacy=False):
    markets = _markets("stable", records, pointers, legacy=legacy)
    index = {"schema_version": 2, "plugins": pointers} if legacy else {"schema_version": 3, "plugins": pointers, "retired": retired or {}}
    raw = io.dump_json(index)
    lock = {"schema_version": 1 if legacy else 2, "files": {name: io.sha256(payload) for name, payload in sorted(markets.items())}}
    if not legacy:
        lock["published_index_sha256"] = io.sha256(raw)
    return dict(markets, **{INDEX_PATH: raw, LOCK_PATH: io.dump_json(lock)})


def bootstrap_files():
    """An empty public market exposes no unverified development or preview plugin."""
    return _catalog_files({}, {})


def retired_identities(files):
    if INDEX_PATH not in files:
        return {}
    snapshot = io.parse_json(files[INDEX_PATH], what=INDEX_PATH)
    return copy.deepcopy(snapshot.get("retired", {}))


def staged_receipts(files):
    return {path: io.parse_json(raw, what=path) for path, raw in files.items() if path.startswith("published/staged/")}


def _receipt(receipt, path, repository, files):
    _object(receipt, RECEIPT_FIELDS, "staged distribution receipt")
    _schema(receipt["schema_version"], "staged receipt")
    record = receipt["record"]
    _record(record, "stable", repository, staged=True)
    if record["schema_version"] != 3 or any(item["revision"] is not None for item in git_installs(record).values()):
        raise DataError("staged receipt must not contain a self-referencing distribution revision")
    if path != _stage_path(record["product_id"], record["version"]):
        raise DataError("staged receipt identity/path differs")
    _revision(receipt["base_commit"], "staged original base")
    _hash(receipt["config_hash"], "staged config hash")
    _hash(receipt["plan_hash"], "staged reviewed plan hash")
    expected = {}
    for host, install in git_installs(record).items():
        for name, digest in install["files"].items():
            if name not in files or io.sha256(files[name]) != digest:
                raise DataError("staged Git file missing or changed: " + name)
            expected[name] = files[name]
        _git_package(record, host, expected)
    if not expected:
        raise DataError("staged receipt requires Git installation files")
    return record, expected


def _existing(files, channel, repository, candidate=None, candidate_files=None):
    if not isinstance(files, dict) or any(not isinstance(raw, bytes) or not in_scope(path) for path, raw in files.items()):
        raise DataError("market_files must contain only managed publication paths")
    if not files:
        return {}, {}, False
    records, expected = {}, {}
    for path, raw in files.items():
        if path.startswith("published/releases/"):
            record = io.parse_json(raw, what=path)
            _record(record, "stable", repository)
            if path != _record_path(record["product_id"], record["version"]):
                raise DataError("record path differs from its identity/version")
            records[path] = record
            expected[path] = io.dump_json(record)
            for host, install in git_installs(record).items():
                for name, digest in install["files"].items():
                    if name not in files or io.sha256(files[name]) != digest:
                        raise DataError("managed Git bytes missing or changed: " + name)
                    expected[name] = files[name]
                _git_package(record, host, files)
    pointers, retired = {}, {}
    if INDEX_PATH in files:
        snapshot = io.parse_json(files[INDEX_PATH], what=INDEX_PATH)
        legacy = isinstance(snapshot, dict) and snapshot.get("schema_version") == 2
        _object(snapshot, {"schema_version", "plugins"} if legacy else {"schema_version", "plugins", "retired"}, "published snapshot")
        _schema(snapshot["schema_version"], "published snapshot", 2 if legacy else 3)
        if not isinstance(snapshot["plugins"], dict):
            raise DataError("published plugin pointers must be an object")
        pointers = snapshot["plugins"]
        retired = snapshot.get("retired", {})
        if not isinstance(retired, dict) or any(not isinstance(value, str) or not ID_PATTERN.fullmatch(value) for pair in retired.items() for value in pair) or set(retired) & set(pointers) or any(target not in pointers for target in retired.values()) or len(set(retired.values())) != len(retired):
            raise DataError("retired identities must target active identities without overlap")
        identities = {record["product_id"] for record in records.values()}
        if set(pointers) != identities - set(retired) or not set(retired) <= identities:
            raise DataError("published pointers differ from active released plugin inventory")
        for identity, pointer in pointers.items():
            if not isinstance(pointer, dict) or not isinstance(pointer.get("version"), str):
                raise DataError("invalid published plugin pointer")
            record = records.get(_record_path(identity, pointer["version"]))
            versions = [item["version"] for item in records.values() if item["product_id"] == identity]
            if record is None or pointer != _snapshot(record, legacy=legacy) or pointer["version"] != max(versions, key=version_key):
                raise DataError("published pointer must equal its latest stable record")
        expected.update(_catalog_files(records, pointers, retired, legacy=legacy))
        # Legacy pointer shape is validated above before in-memory normalization.
        pointers = {identity: _snapshot(records[_record_path(identity, pointer["version"])]) for identity, pointer in pointers.items()}
    elif records:
        raise DataError("public records require a published snapshot")
    pending = {}
    pending_ids = set()
    for path, receipt in staged_receipts(files).items():
        record, install_files = _receipt(receipt, path, repository, files)
        identity = record["product_id"]
        if identity in pending_ids or identity in retired or _record_path(identity, record["version"]) in records:
            raise DataError("conflicting staged receipt or retired identity")
        pending_ids.add(identity)
        if identity in pointers and version_key(record["version"]) <= version_key(pointers[identity]["version"]):
            raise DataError("staged version must advance its current pointer")
        expected.update(install_files)
        expected[path] = io.dump_json(receipt)
        pending.update(install_files)
        if candidate is not None and identity == candidate["product_id"]:
            if record != _candidate_record(candidate) or install_files != candidate_files:
                raise DataError("same-version staged Git bytes differ from verified bundle")
    if files != expected:
        raise DataError("managed publication contains unknown, missing or user-edited files")
    return records, pointers, bool(pending)


def _digest(plan):
    return io.sha256(io.canonical_json({key: value for key, value in plan.items() if key != "plan_hash"}))


def _plan_git_files(plan):
    groups = plan["git_install_files"]
    if not isinstance(groups, dict) or set(groups) != set(git_installs(plan["record"])):
        raise DataError("plan Git installation hosts differ from record")
    files = {}
    for host, encoded in groups.items():
        decoded = _decode(encoded)
        if {name: io.sha256(raw) for name, raw in decoded.items()} != git_installs(plan["record"])[host]["files"]:
            raise DataError("plan Git files differ from record inventory")
        if set(files) & set(decoded):
            raise DataError("plan Git installation paths overlap")
        files.update(decoded)
    _codex_package(plan["record"], files)
    return files


def _replacement_inventory(config, records, catalog=None):
    replacements = config.get("identity_replacements", {})
    identities = {record["product_id"] for record in records.values()}
    if catalog is not None and not set(replacements.values()) <= set(catalog):
        raise DataError("identity replacement target must be registered in current catalog")
    if not set(replacements) <= identities:
        raise DataError("identity replacement source must have a published stable record")


def check_plan(plan, expected_hash=None, expected_commit=None):
    _object(plan, PLAN_FIELDS, "distribution plan")
    _schema(plan["schema_version"], "distribution plan", 3)
    if plan["plan_hash"] != _digest(plan):
        raise DataError("distribution plan hash differs from its actual content")
    if expected_hash is not None and expected_hash != plan["plan_hash"]:
        raise ConflictError("reviewed distribution plan hash is stale")
    if expected_commit is not None and expected_commit != plan["base_commit"]:
        raise ConflictError("reviewed marketplace base commit is stale")
    _revision(plan["base_commit"], "main base commit")
    config = validate_config(plan["config"])
    channel = plan["channel"]
    if channel != "stable" or plan["branch"] != "main" or plan["marketplace_name"] != MARKETPLACE["name"] or plan["config_hash"] != io.sha256(io.canonical_json(config)):
        raise DataError("plan requires trusted main/latest-stable policy")
    repository = _repository(plan["repository"])
    record = plan["record"]
    _record(record, channel, repository, staged=True)
    for key in ("product_id", "version", "source_revision", "release_id"):
        if plan[key] != record[key]:
            raise DataError(f"plan {key} differs from its record")
    if plan["release_tag"] != record["tag"] or plan["status"] not in {"plan_ready", "already_deployed"} or type(plan["bootstrap"]) is not bool:
        raise DataError("plan release tag/status/bootstrap differs")
    existing, installs = _decode(plan["existing_files"]), _plan_git_files(plan)
    records, pointers, _ = _existing(existing, channel, repository, record, installs)
    _replacement_inventory(config, records)
    if record["product_id"] in retired_identities(existing):
        raise DataError("retired plugin identity cannot be published again")
    previous = pointers.get(record["product_id"], {}).get("version")
    if previous is not None and version_key(record["version"]) < version_key(previous):
        raise DataError("channel version downgrade is rejected")
    if plan["previous_version"] != previous or plan["bootstrap"] != (not pointers):
        raise DataError("plan history/bootstrap differs from validated channel")
    retired = retired_identities(existing)
    if any(config.get("identity_replacements", {}).get(old) != new for old, new in retired.items()):
        raise DataError("retirement facts cannot be removed or changed")
    return {"ok": True, "plan_hash": plan["plan_hash"], "base_commit": plan["base_commit"], "status": plan["status"]}


def _source_entry(spec, host):
    entry = copy.deepcopy(marketplace_entry(spec, host))
    if host == "dsh":
        version = entry.pop("versions")[0]
        entry["engines"] = version["engines"]
    else:
        del entry["source"]
    return entry


def _new_plan(config, record, existing, base_commit, status="plan_ready"):
    _, pointers, _ = _existing(existing, "stable", record["repository"])
    plan = {"schema_version": 3, "status": status, "channel": "stable", "branch": "main",
            "marketplace_name": config["marketplace"]["name"], "base_commit": base_commit,
            "repository": record["repository"], "product_id": record["product_id"], "version": record["version"],
            "source_revision": record["source_revision"], "release_id": record["release_id"], "release_tag": record["tag"],
            "bootstrap": not pointers, "previous_version": pointers.get(record["product_id"], {}).get("version"),
            "record": record, "config": copy.deepcopy(config), "config_hash": io.sha256(io.canonical_json(config)),
            "existing_files": _encode(existing), "git_install_files": {}}
    return plan


def plan_distribution(root, spec, bundle, release_info, channel, market_files=None, base_commit="absent", *, control_root=None):
    config = load_config(control_root or root)
    if channel != "stable" or release_kind(spec.version) != "stable":
        raise DataError("preview releases are Release-only and cannot update the default market")
    _revision(base_commit, "main base commit")
    channel_config = {"release_mode": "stable", "prerelease": False}
    repository = _repository(spec.manifest["repository"])
    if any(_repository(item.manifest["repository"]) != repository for item in load_catalog(root)):
        raise DataError("all registered plugins must share this GitHub repository")
    if spec.product_id in retired_identities(market_files or {}):
        _existing(market_files, channel, repository)
        raise DataError("retired plugin identity cannot be published again")
    report = verify_release(root, spec, bundle, mode=channel_config["release_mode"], committed_acceptance=True)
    if not report["ok"]:
        raise DataError("trusted release verification failed: " + "; ".join(report["blockers"]))
    canonical = f"{spec.product_id}/v{spec.version}"
    provenance = metadata.git_provenance(root, spec.product_id, spec.version, canonical)
    bundle_provenance = report["bundle_provenance"]
    if provenance["working_tree_dirty"] or provenance["tag"] != canonical or any(provenance[key] != bundle_provenance[key] for key in ("source_revision", "working_tree_dirty", "tag")):
        raise DataError("distribution requires a clean correctly tagged source matching the bundle")
    source_git.validate_head_inputs(root, spec, metadata.capture_release(spec, committed_acceptance=True), provenance["source_revision"])
    if channel == "stable" and not report["publication_ready"]:
        raise DataError("stable distribution requires technical publication readiness")
    _object(release_info, {"id", "tag_name", "draft", "prerelease", "html_url", "published_at", "assets"}, "public Release info")
    _timestamp(release_info["published_at"])
    if type(release_info["id"]) is not int or release_info["id"] <= 0 or release_info["tag_name"] != canonical or release_info["draft"] is not False or type(release_info["prerelease"]) is not bool or release_info["prerelease"] != channel_config["prerelease"]:
        raise DataError("public Release ID/tag/visibility/channel differs")
    if release_info["html_url"] != f"{repository}/releases/tag/{quote(canonical, safe='')}" or not isinstance(release_info["assets"], list):
        raise DataError("public Release repository URL/assets differ")
    assets = {}
    ids = set()
    for asset in release_info["assets"]:
        _asset(asset, repository, canonical)
        if asset["name"] in assets or asset["id"] in ids:
            raise DataError("duplicate Release asset name/ID")
        assets[asset["name"]] = asset
        ids.add(asset["id"])
    contents = integrity.read_tree(bundle)
    manifest = integrity.record(contents)
    if manifest["schema_version"] not in (2, 3):
        raise DataError("hosted distribution requires release schema 2 or 3 installers")
    record = {"schema_version": 3, "channel": channel, "product_id": spec.product_id, "version": spec.version,
              "repository": repository, "source_revision": provenance["source_revision"], "source_tree_hash": spec.source_tree_hash,
              "tag": canonical, "release_id": release_info["id"], "release_url": release_info["html_url"],
              "mode": channel_config["release_mode"], "readiness": copy.deepcopy(manifest["readiness"]),
              "hosts": {}, "git_installs": {}, "release_published_at": release_info["published_at"]}
    git_files = {}
    for host in spec.hosts:
        from .archives import installer_name, read_installer
        name = installer_name(spec.product_id, spec.version, host)
        asset = assets.get(name)
        installer = contents.get(f"installers/{name}")
        if asset is None or installer is None or asset["sha256"] != io.sha256(installer) or asset["size"] != len(installer):
            raise DataError(f"Release installer bytes/hash/size differ or missing: {host}")
        entry = _source_entry(spec, host)
        record["hosts"][host] = {"asset": copy.deepcopy(asset), "package_content_hash": manifest["readiness"]["package_content_hashes"][host], "entry": entry, "installer_format": "npm-tgz" if host == "dsh" else "zip"}
        if host in GIT_HOSTS:
            prefix = _git_prefix(host, spec.product_id, spec.version)
            git_files[host] = {prefix + path: raw for path, raw in read_installer(installer, spec.product_id, host).items()}
            record["git_installs"][host] = {"revision": None, "files": {path: io.sha256(raw) for path, raw in sorted(git_files[host].items())}}

    existing = {} if market_files is None else dict(market_files)
    flat = {name: raw for group in git_files.values() for name, raw in group.items()}
    records, pointers, _ = _existing(existing, channel, repository, record, flat)
    _replacement_inventory(config, records, {item.product_id for item in load_catalog(control_root or root)})
    previous = pointers.get(spec.product_id, {}).get("version")
    if spec.product_id in retired_identities(existing):
        raise DataError("retired plugin identity cannot be published again")
    if previous is not None and version_key(spec.version) < version_key(previous):
        raise DataError("channel version downgrade is rejected")
    prior = records.get(_record_path(spec.product_id, spec.version))
    status = "plan_ready"
    if prior is not None:
        comparable, candidate = _candidate_record(prior), _candidate_record(record)
        if prior["schema_version"] == 2:
            comparable["git_installs"] = git_installs(comparable)
            comparable.pop("codex_revision")
            comparable.pop("codex_files")
            comparable["schema_version"] = 3
            for host, item in comparable["hosts"].items():
                item["installer_format"] = "zip"
            comparable["release_published_at"] = candidate["release_published_at"]
        if comparable != candidate:
            raise DataError("same-version public record/installer bytes differ")
        if previous == spec.version:
            record = copy.deepcopy(prior)
            status = "already_deployed"
    plan = _new_plan(config, record, existing, base_commit, status)
    plan["git_install_files"] = {host: _encode(group) for host, group in git_files.items()}
    plan["plan_hash"] = _digest(plan)
    check_plan(plan)
    return plan


def stage_files(plan):
    check_plan(plan)
    if plan["status"] == "already_deployed":
        return {}
    existing, installs = _decode(plan["existing_files"]), _plan_git_files(plan)
    if not installs:
        return {}
    receipt_path = _stage_path(plan["product_id"], plan["version"])
    if receipt_path in existing:
        return {}  # _existing verified the complete identical receipt and file closure.
    present = set(installs) & set(existing)
    if present:
        if any(existing.get(name) != raw for name, raw in installs.items()):
            raise DataError("partial or changed staged Git installation")
        return {}
    receipt = {"schema_version": 1, "record": _candidate_record(plan["record"]), "base_commit": plan["base_commit"],
               "config_hash": plan["config_hash"], "plan_hash": plan["plan_hash"]}
    return dict(installs, **{receipt_path: io.dump_json(receipt)})


def finalize_files(plan, distribution_revision=None):
    check_plan(plan)
    record = copy.deepcopy(plan["record"])
    installs = git_installs(record)
    if installs:
        if distribution_revision is None:
            distribution_revision = next(iter(installs.values()))["revision"]
        _revision(distribution_revision, "actual Git installation commit D")
        for install in installs.values():
            if install["revision"] is not None and install["revision"] != distribution_revision:
                raise ConflictError("already deployed Git commit differs")
            install["revision"] = distribution_revision
        if record["schema_version"] == 3:
            record["git_installs"] = installs
        else:
            record["codex_revision"] = distribution_revision
    elif distribution_revision is not None:
        raise DataError("non-Git deployment requires null D")
    files, install_files = _decode(plan["existing_files"]), _plan_git_files(plan)
    if plan["status"] == "already_deployed":
        return files
    records, pointers, _ = _existing(files, plan["channel"], plan["repository"], record, install_files)
    retired = retired_identities(files)
    if record["product_id"] in retired:
        raise DataError("retired plugin identity cannot be published again")
    for old, new in plan["config"].get("identity_replacements", {}).items():
        if new == record["product_id"]:
            if old not in pointers and retired.get(old) != new:
                raise DataError("replacement source is not active")
            pointers.pop(old, None)
            retired[old] = new
    records[_record_path(record["product_id"], record["version"])] = record
    pointers[record["product_id"]] = _snapshot(record)
    files.update(install_files)
    # Only the exact validated receipt for this record can be consumed.
    files.pop(_stage_path(record["product_id"], record["version"]), None)
    files[_record_path(record["product_id"], record["version"])] = io.dump_json(record)
    files.update(_catalog_files(records, pointers, retired))
    _existing(files, plan["channel"], plan["repository"])
    return files
