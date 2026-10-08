"""Pure local hosted-market planning; never writes Git or network state.

Every plan is review data. Callers must regenerate it from trusted source and
actually downloaded release assets before using its hash as a deployment lease.
"""

import base64
import binascii
import copy
from io import BytesIO
import re
from urllib.parse import quote
import zipfile

from . import io
from .io import ConflictError, DataError
from .registry import HOSTS, ID_PATTERN, VERSION_PATTERN, load_catalog
from .release import verify_release
from .release import integrity, metadata, source_git
from .rendering import marketplace_entry, marketplace_path

HASH = re.compile(r"[0-9a-f]{64}")
REVISION = re.compile(r"[0-9a-f]{40}|[0-9a-f]{64}")
TRANSPORTS = {"claude": "archive", "codex": "git-subdir", "zcode": "url-zip"}
CHANNELS = {
    "stable": {"branch": "codex/marketplace", "marketplace_name": "ai-code-stable", "release_mode": "stable", "prerelease": False},
    "preview": {"branch": "codex/marketplace-preview", "marketplace_name": "ai-code-preview", "release_mode": "draft", "prerelease": True},
}
RECORD_FIELDS = {"schema_version", "channel", "product_id", "version", "repository", "source_revision",
                 "source_tree_hash", "tag", "release_id", "release_url", "mode", "readiness", "hosts",
                 "codex_revision", "codex_files"}
PLAN_FIELDS = {"schema_version", "status", "channel", "branch", "marketplace_name", "base_commit",
               "repository", "product_id", "version", "source_revision", "release_id", "release_tag",
               "bootstrap", "previous_version", "record", "existing_files", "codex_files", "plan_hash"}
HOST_FIELDS = {"asset", "package_content_hash", "entry"}
ASSET_FIELDS = {"id", "name", "size", "browser_download_url", "sha256"}
READINESS_FIELDS = {"publication_ready", "pending_acceptance", "accepted_hosts", "package_content_hashes", "limitations"}


def _object(value, fields, what):
    if not isinstance(value, dict) or set(value) != fields:
        raise DataError(f"{what} requires exactly {sorted(fields)}")


def _schema(value, what):
    if type(value) is not int or value != 1:
        raise DataError(f"{what} requires schema 1")


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


def load_config(root):
    config, _ = io.read_json(root, "distribution.json")
    _object(config, {"schema_version", "channels", "transports"}, "distribution config")
    _schema(config["schema_version"], "distribution config")
    if config["transports"] != TRANSPORTS:
        raise DataError("unsupported distribution transports")
    if config["channels"] != CHANNELS or any(type(config["channels"][key]["prerelease"]) is not bool for key in CHANNELS):
        raise DataError("distribution channels require fixed stable/preview contracts")
    return config


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


def _readme(channel):
    return (f"# {CHANNELS[channel]['marketplace_name']}\n\n"
            "Managed plugin distribution. Installation and host behavior require separate acceptance.\n"
            f"Channel: {channel}.\n").encode()


def _record_path(identity, version):
    return f"records/{identity}/{version}.json"


def _snapshot(record):
    return {"version": record["version"], "release_id": record["release_id"],
            "source_revision": record["source_revision"], "source_tree_hash": record["source_tree_hash"],
            "installers": {host: item["asset"]["sha256"] for host, item in sorted(record["hosts"].items())},
            "codex_revision": record["codex_revision"]}


def _entry(record, host):
    entry = copy.deepcopy(record["hosts"][host]["entry"])
    asset = record["hosts"][host]["asset"]
    if host == "codex":
        entry["source"] = {"source": "git-subdir", "url": record["repository"] + ".git",
                           "path": f"./plugins/codex/{record['product_id']}/{record['version']}",
                           "sha": record["codex_revision"]}
    else:
        source = {"source": "archive" if host == "claude" else "url",
                  "url": asset["browser_download_url"], "sha256": asset["sha256"]}
        if host == "zcode":
            source.update(type="zip", path=record["product_id"])
        entry["source"] = source
    return entry


def _markets(channel, records, pointers):
    result = {}
    for host in HOSTS:
        entries = []
        for identity, pointer in sorted(pointers.items()):
            record = records[_record_path(identity, pointer["version"])]
            if host in record["hosts"]:
                entries.append(_entry(record, host))
        if entries:
            market = {"name": CHANNELS[channel]["marketplace_name"], "plugins": entries}
            if host == "claude":
                market["owner"] = {"name": "ai-code"}
            result[marketplace_path(host)] = io.dump_json(market)
    return result


def _record(record, channel, repository, *, staged=False):
    _object(record, RECORD_FIELDS, "distribution record")
    _schema(record["schema_version"], "distribution record")
    identity, version = record["product_id"], record["version"]
    if not isinstance(identity, str) or not ID_PATTERN.fullmatch(identity) or not isinstance(version, str) or not VERSION_PATTERN.fullmatch(version):
        raise DataError("record identity/version is invalid")
    tag = f"{identity}/v{version}"
    if record["channel"] != channel or record["repository"] != repository or record["tag"] != tag or record["mode"] != CHANNELS[channel]["release_mode"]:
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
    if channel == "stable" and (readiness["pending_acceptance"] or set(readiness["accepted_hosts"]) != set(hosts)):
        raise DataError("stable record requires accepted evidence for every declared host")
    if not isinstance(readiness["limitations"], list) or not all(isinstance(item, str) for item in readiness["limitations"]):
        raise DataError("invalid readiness limitations")
    if not isinstance(readiness["package_content_hashes"], dict) or set(readiness["package_content_hashes"]) != set(hosts):
        raise DataError("readiness package inventory differs from hosts")
    for host, item in hosts.items():
        _object(item, HOST_FIELDS, "record host")
        _asset(item["asset"], repository, tag, f"{identity}-{version}-{host}-plugin.zip")
        _hash(item["package_content_hash"], "package content hash")
        if readiness["package_content_hashes"][host] != item["package_content_hash"]:
            raise DataError("record readiness/package hashes differ")
        entry = item["entry"]
        fields = {"name", "version", "policy", "category"} if host == "codex" else {"name", "version", "description"}
        _object(entry, fields, "record native entry")
        if entry["name"] != identity or entry["version"] != version:
            raise DataError("record native identity/version differs")
        if host == "codex":
            if entry["policy"] != {"installation": "AVAILABLE", "authentication": "ON_INSTALL"} or entry["category"] != "developer-tools":
                raise DataError("invalid Codex native policy/category")
        elif not isinstance(entry["description"], str):
            raise DataError("native description must be text")
    _revision(record["codex_revision"], "record Codex revision", nullable=staged or "codex" not in hosts)
    if "codex" not in hosts and record["codex_revision"] is not None:
        raise DataError("non-Codex record requires null Codex revision")
    hashes = record["codex_files"]
    if not isinstance(hashes, dict) or ("codex" in hosts) != bool(hashes):
        raise DataError("record Codex file inventory differs from hosts")
    prefix = f"plugins/codex/{identity}/{version}/"
    for path, digest in hashes.items():
        io.relative_path(path)
        if not path.startswith(prefix):
            raise DataError("record Codex file path differs from identity/version")
        _hash(digest, "Codex file digest")
    if hashes and prefix + "artifact.json" not in hashes:
        raise DataError("Codex record must include artifact.json")


def _codex_package(record, files):
    if "codex" not in record["hosts"]:
        return
    prefix = f"plugins/codex/{record['product_id']}/{record['version']}/"
    artifact = io.parse_json(files[prefix + "artifact.json"], what="managed Codex artifact")
    fields = {"schema_version", "product_id", "version", "host", "profiles", "source_revision", "working_tree_dirty", "source_tree_hash", "files", "content_hash"}
    _object(artifact, fields, "managed Codex artifact")
    _schema(artifact["schema_version"], "managed Codex artifact")
    for key, value in (("product_id", record["product_id"]), ("version", record["version"]), ("host", "codex"), ("source_revision", record["source_revision"]), ("source_tree_hash", record["source_tree_hash"]), ("working_tree_dirty", False)):
        if type(artifact[key]) is not type(value) or artifact[key] != value:
            raise DataError(f"managed Codex artifact {key} differs")
    pairs = [[path.removeprefix(prefix), digest] for path, digest in sorted(record["codex_files"].items()) if path != prefix + "artifact.json"]
    if artifact["files"] != pairs or artifact["content_hash"] != io.sha256(io.canonical_json(pairs)) or artifact["content_hash"] != record["hosts"]["codex"]["package_content_hash"]:
        raise DataError("managed Codex artifact inventory/hash differs")
    native = io.parse_json(files[prefix + "plugin.json"], what="managed Codex plugin")
    if native.get("name") != record["product_id"] or native.get("version") != record["version"]:
        raise DataError("managed Codex native identity/version differs")


def _existing(files, channel, repository, candidate, candidate_files):
    if not isinstance(files, dict) or any(not isinstance(data, bytes) for data in files.values()):
        raise DataError("market_files must contain the entire path-to-bytes tree")
    for path in files:
        io.relative_path(path)
    if not files:
        return {}, {}, False
    expected = {}
    records = {}
    for path, data in files.items():
        if path.startswith("records/"):
            record = io.parse_json(data, what=path)
            _record(record, channel, repository)
            if path != _record_path(record["product_id"], record["version"]):
                raise DataError("record path differs from its identity/version")
            records[path] = record
            expected[path] = io.dump_json(record)
            for name, digest in record["codex_files"].items():
                if name not in files or io.sha256(files[name]) != digest:
                    raise DataError(f"managed Codex bytes missing or changed: {name}")
                expected[name] = files[name]
            _codex_package(record, files)
    if "channel.json" in files:
        snapshot = io.parse_json(files["channel.json"], what="channel.json")
        _object(snapshot, {"schema_version", "channel", "plugins"}, "channel snapshot")
        _schema(snapshot["schema_version"], "channel snapshot")
        if snapshot["channel"] != channel or not isinstance(snapshot["plugins"], dict) or not snapshot["plugins"]:
            raise DataError("channel snapshot differs or has no published plugins")
        pointers = snapshot["plugins"]
        for identity, pointer in pointers.items():
            if not isinstance(pointer, dict) or not isinstance(pointer.get("version"), str):
                raise DataError("invalid channel plugin pointer")
            record = records.get(_record_path(identity, pointer["version"]))
            if record is None or pointer != _snapshot(record):
                raise DataError("channel pointer differs from its public record")
        expected["channel.json"] = io.dump_json(snapshot)
        markets = _markets(channel, records, pointers)
        expected.update(markets)
        expected["marketplaces.lock.json"] = io.dump_json({"schema_version": 1, "files": {name: io.sha256(data) for name, data in sorted(markets.items())}})
    else:
        if records:
            raise DataError("public records require a channel snapshot")
        pointers = {}
    # A retry may recognize only this candidate's byte-identical staged D tree.
    candidate_prefix = f"plugins/codex/{candidate['product_id']}/{candidate['version']}/"
    pending = {path: data for path, data in files.items() if path.startswith(candidate_prefix) and path not in expected}
    if pending:
        if pending != candidate_files:
            raise DataError("same-version staged Codex bytes differ from verified bundle")
        expected.update(pending)
    # The initial D commit may contain only installation bytes; finalization
    # creates README and the channel snapshot together with the first markets.
    if pointers or "README.md" in files or not pending:
        expected["README.md"] = _readme(channel)
    if files != expected:
        raise DataError("managed market contains unknown, missing or user-edited files")
    return records, pointers, bool(pending)


def _digest(plan):
    return io.sha256(io.canonical_json({key: value for key, value in plan.items() if key != "plan_hash"}))


def check_plan(plan, expected_hash=None, expected_commit=None):
    _object(plan, PLAN_FIELDS, "distribution plan")
    _schema(plan["schema_version"], "distribution plan")
    if plan["plan_hash"] != _digest(plan):
        raise DataError("distribution plan hash differs from its actual content")
    if expected_hash is not None and expected_hash != plan["plan_hash"]:
        raise ConflictError("reviewed distribution plan hash is stale")
    if expected_commit is not None and expected_commit != plan["base_commit"]:
        raise ConflictError("reviewed marketplace base commit is stale")
    if plan["base_commit"] != "absent":
        _revision(plan["base_commit"], "market base commit")
    channel = plan["channel"]
    if not isinstance(channel, str) or channel not in CHANNELS or plan["branch"] != CHANNELS[channel]["branch"] or plan["marketplace_name"] != CHANNELS[channel]["marketplace_name"]:
        raise DataError("plan channel/branch/market name differs")
    repository = _repository(plan["repository"])
    record = plan["record"]
    _record(record, channel, repository, staged=True)
    for key in ("product_id", "version", "source_revision", "release_id"):
        if plan[key] != record[key]:
            raise DataError(f"plan {key} differs from its record")
    if plan["release_tag"] != record["tag"] or plan["status"] not in {"plan_ready", "already_deployed"} or type(plan["bootstrap"]) is not bool:
        raise DataError("plan release tag/status/bootstrap differs")
    existing, codex = _decode(plan["existing_files"]), _decode(plan["codex_files"])
    if {name: io.sha256(data) for name, data in codex.items()} != record["codex_files"]:
        raise DataError("plan Codex files differ from record inventory")
    _codex_package(record, codex)
    _, pointers, _ = _existing(existing, channel, repository, record, codex)
    previous = pointers.get(record["product_id"], {}).get("version")
    if plan["previous_version"] != previous or plan["bootstrap"] != (not pointers):
        raise DataError("plan history/bootstrap differs from validated channel")
    if not existing and plan["base_commit"] != "absent" or existing and plan["base_commit"] == "absent":
        raise DataError("market base commit must describe the complete existing tree")
    return {"ok": True, "plan_hash": plan["plan_hash"], "base_commit": plan["base_commit"], "status": plan["status"]}


def plan_distribution(root, spec, bundle, release_info, channel, market_files=None, base_commit="absent"):
    config = load_config(root)
    if not isinstance(channel, str) or channel not in config["channels"]:
        raise DataError("distribution channel must be preview or stable")
    channel_config = config["channels"][channel]
    repository = _repository(spec.manifest["repository"])
    if any(_repository(item.manifest["repository"]) != repository for item in load_catalog(root)):
        raise DataError("all registered plugins must share this GitHub repository")
    report = verify_release(root, spec, bundle, mode=channel_config["release_mode"])
    if not report["ok"]:
        raise DataError("trusted release verification failed: " + "; ".join(report["blockers"]))
    canonical = f"{spec.product_id}/v{spec.version}"
    provenance = metadata.git_provenance(root, spec.product_id, spec.version, canonical)
    bundle_provenance = report["bundle_provenance"]
    if provenance["working_tree_dirty"] or provenance["tag"] != canonical or any(provenance[key] != bundle_provenance[key] for key in ("source_revision", "working_tree_dirty", "tag")):
        raise DataError("distribution requires a clean correctly tagged source matching the bundle")
    source_git.validate_head_inputs(root, spec, metadata.capture_release(spec), provenance["source_revision"])
    if channel == "stable" and not report["publication_ready"]:
        raise DataError("stable distribution requires every declared host's byte-bound acceptance")
    _object(release_info, {"id", "tag_name", "draft", "prerelease", "html_url", "assets"}, "public Release info")
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
    if manifest["schema_version"] != 2:
        raise DataError("hosted distribution requires release schema 2 installers")
    record = {"schema_version": 1, "channel": channel, "product_id": spec.product_id, "version": spec.version,
              "repository": repository, "source_revision": provenance["source_revision"], "source_tree_hash": spec.source_tree_hash,
              "tag": canonical, "release_id": release_info["id"], "release_url": release_info["html_url"],
              "mode": channel_config["release_mode"], "readiness": copy.deepcopy(manifest["readiness"]),
              "hosts": {}, "codex_revision": None, "codex_files": {}}
    codex_files = {}
    for host in spec.hosts:
        name = f"{spec.product_id}-{spec.version}-{host}-plugin.zip"
        asset = assets.get(name)
        installer = contents.get(f"installers/{name}")
        if asset is None or installer is None or asset["sha256"] != io.sha256(installer) or asset["size"] != len(installer):
            raise DataError(f"Release installer bytes/hash/size differ or missing: {host}")
        entry = marketplace_entry(spec, host)
        del entry["source"]
        record["hosts"][host] = {"asset": copy.deepcopy(asset), "package_content_hash": manifest["readiness"]["package_content_hashes"][host], "entry": entry}
        if host == "codex":
            with zipfile.ZipFile(BytesIO(installer)) as archive:
                codex_files = {f"plugins/codex/{spec.product_id}/{spec.version}/{path.removeprefix(spec.product_id + '/')}": archive.read(path) for path in archive.namelist()}
            record["codex_files"] = {path: io.sha256(data) for path, data in sorted(codex_files.items())}
    existing = {} if market_files is None else dict(market_files)
    records, pointers, _ = _existing(existing, channel, repository, record, codex_files)
    previous = pointers.get(spec.product_id, {}).get("version")
    if previous is not None and tuple(map(int, spec.version.split("."))) < tuple(map(int, previous.split("."))):
        raise DataError("channel version downgrade is rejected")
    prior = records.get(_record_path(spec.product_id, spec.version))
    status = "plan_ready"
    if prior is not None:
        comparable = dict(prior, codex_revision=None)
        if comparable != record:
            raise DataError("same-version public record/installer bytes differ")
        if previous == spec.version:
            record["codex_revision"] = prior["codex_revision"]
            status = "already_deployed"
    plan = {"schema_version": 1, "status": status, "channel": channel,
            "branch": channel_config["branch"], "marketplace_name": channel_config["marketplace_name"],
            "base_commit": base_commit, "repository": repository, "product_id": spec.product_id,
            "version": spec.version, "source_revision": provenance["source_revision"], "release_id": release_info["id"],
            "release_tag": canonical, "bootstrap": not pointers, "previous_version": previous,
            "record": record, "existing_files": _encode(existing), "codex_files": _encode(codex_files)}
    plan["plan_hash"] = _digest(plan)
    check_plan(plan)
    return plan


def stage_files(plan):
    check_plan(plan)
    existing, codex = _decode(plan["existing_files"]), _decode(plan["codex_files"])
    return {path: data for path, data in codex.items() if path not in existing}


def finalize_files(plan, codex_revision=None):
    check_plan(plan)
    record = copy.deepcopy(plan["record"])
    if "codex" in record["hosts"]:
        if codex_revision is None:
            codex_revision = record["codex_revision"]
        _revision(codex_revision, "actual Codex installation commit D")
        if record["codex_revision"] is not None and record["codex_revision"] != codex_revision:
            raise ConflictError("already deployed Codex commit differs")
        record["codex_revision"] = codex_revision
    elif codex_revision is not None:
        raise DataError("non-Codex deployment requires null D")
    files = _decode(plan["existing_files"])
    codex = _decode(plan["codex_files"])
    records, pointers, _ = _existing(files, plan["channel"], plan["repository"], record, codex)
    records[_record_path(record["product_id"], record["version"])] = record
    pointers[record["product_id"]] = _snapshot(record)
    files.update(codex)
    files[_record_path(record["product_id"], record["version"])] = io.dump_json(record)
    files["channel.json"] = io.dump_json({"schema_version": 1, "channel": plan["channel"], "plugins": pointers})
    markets = _markets(plan["channel"], records, pointers)
    # _existing authenticated the complete old tree before any update. Only
    # its three owned native entrances may disappear when no current plugin
    # supports that host; all historical records and package bytes stay put.
    for host in HOSTS:
        path = marketplace_path(host)
        if path not in markets:
            files.pop(path, None)
    files.update(markets)
    files["marketplaces.lock.json"] = io.dump_json({"schema_version": 1, "files": {name: io.sha256(data) for name, data in sorted(markets.items())}})
    files["README.md"] = _readme(plan["channel"])
    # Recompute the entire managed tree to catch closure mistakes before delivery.
    _existing(files, plan["channel"], plan["repository"], record, codex)
    return files
