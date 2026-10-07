"""Check distribution integrity and payload parity across Git build contexts.

Archives retain their own provenance, so a clean CI checkout need not have
the same archive bytes as a pre-commit build. Each archive must still match
its own index, marketplace and package directory exactly.
"""

import argparse
import hashlib
import json
import re
import stat
import zipfile
from pathlib import Path

MARKETPLACE_PATHS = {"claude": ".claude-plugin/marketplace.json", "codex": ".agents/plugins/marketplace.json",
                     "zcode": "marketplace.json"}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def member(root, relative):
    if not isinstance(relative, str) or Path(relative).is_absolute() or ".." in Path(relative).parts:
        raise ValueError(f"invalid distribution path: {relative}")
    path = root / relative
    if not path.resolve().is_relative_to(root.resolve()):
        raise ValueError(f"distribution path escaped root: {relative}")
    for part in [path, *path.parents]:
        if part == root:
            break
        if part.is_symlink():
            raise ValueError(f"symlink in distribution: {relative}")
        if part.exists() and not (stat.S_ISREG(part.lstat().st_mode) or stat.S_ISDIR(part.lstat().st_mode)):
            raise ValueError(f"special file in distribution: {relative}")
    return path


def verify_workflow(root, index):
    """Verify the workflow plugin's own standalone builder output."""
    payload = {}
    if not isinstance(index["hosts"], dict) or not index["hosts"] or set(index["hosts"]) - set(MARKETPLACE_PATHS):
        raise ValueError("distribution must contain a nonempty supported host set")
    for host, entry in index["hosts"].items():
        package = member(root, entry["package_dir"])
        for path in package.rglob("*"):
            member(root, path.relative_to(root).as_posix())
        artifact = json.loads((package / "artifact.json").read_text())
        if type(artifact.get("schema_version")) is not int or artifact["schema_version"] != 1:
            raise ValueError(f"{host}: unsupported artifact schema")
        for field, expected in (("product_id", index["product_id"]), ("version", index["version"]),
                                ("host", host), ("source_revision", index["source_revision"]),
                                ("working_tree_dirty", index["working_tree_dirty"])):
            if artifact[field] != expected:
                raise ValueError(f"{host}: inconsistent artifact {field}")
        actual = {p.relative_to(package).as_posix(): digest(p)
                  for p in package.rglob("*") if p.is_file() and p.relative_to(package).as_posix() != "artifact.json"}
        if actual != dict(artifact["files"]):
            raise ValueError(f"{host}: package bytes differ from artifact")
        encoded = json.dumps(artifact["files"], sort_keys=True, separators=(",", ":"),
                             ensure_ascii=True).encode()
        if hashlib.sha256(encoded).hexdigest() != entry["package_content_hash"] or \
                artifact["content_hash"] != entry["package_content_hash"]:
            raise ValueError(f"{host}: invalid package content hash")
        if artifact["source_tree_hash"] != index["source_tree_hash"]:
            raise ValueError(f"{host}: inconsistent source identity")
        market = member(root, entry["marketplace"])
        archive = member(root, entry["zip"])
        if digest(market) != entry["marketplace_sha256"] or digest(archive) != entry["zip_sha256"]:
            raise ValueError(f"{host}: distribution checksum mismatch")
        if host == "claude":
            native = json.loads(member(package, ".claude-plugin/plugin.json").read_text())
            owner = json.loads(market.read_text()).get("owner")
            if not isinstance(owner, dict) or not isinstance(owner.get("name"), str) or not owner["name"].strip() or owner != native.get("author"):
                raise ValueError("claude: invalid native marketplace owner/publisher")
        expected = {p.relative_to(root / host).as_posix(): p.read_bytes()
                    for p in package.rglob("*") if p.is_file()}
        expected[market.relative_to(root / host).as_posix()] = market.read_bytes()
        with zipfile.ZipFile(archive) as zipped:
            names = zipped.namelist()
            if len(names) != len(set(names)) or set(names) != set(expected):
                raise ValueError(f"{host}: unexpected archive members")
            for info in zipped.infolist():
                if stat.S_IFMT(info.external_attr >> 16) != stat.S_IFREG or \
                        zipped.read(info.filename) != expected[info.filename]:
                    raise ValueError(f"{host}: archive payload mismatch: {info.filename}")
        stable = {key: value for key, value in artifact.items()
                  if key not in ("source_revision", "working_tree_dirty")}
        stable_bytes = json.dumps(stable, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
        payload[host] = (actual, entry["marketplace_sha256"], stable_bytes)
    return (index["product_id"], index["version"], index["source_tree_hash"], payload)


def verify_collection(root, index):
    plugins, hosts = index["plugins"], index["hosts"]
    if not isinstance(plugins, dict) or not plugins or not isinstance(hosts, dict) or not hosts or \
            set(hosts) - set(MARKETPLACE_PATHS):
        raise ValueError("distribution needs registered plugins and supported hosts")
    expected_host_ids = {host: set() for host in hosts}
    for identity, plugin in plugins.items():
        if not isinstance(identity, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]*", identity) or \
                not isinstance(plugin["hosts"], dict) or not plugin["hosts"] or set(plugin["hosts"]) - set(hosts):
            raise ValueError(f"invalid plugin distribution: {identity}")
        for host in plugin["hosts"]:
            expected_host_ids[host].add(identity)
    markets = {}
    registered_files = {"index.json"}
    for host, entry in hosts.items():
        relative = f"{host}/{MARKETPLACE_PATHS[host]}"
        if entry["marketplace"] != relative or not expected_host_ids[host]:
            raise ValueError(f"{host}: invalid marketplace registration")
        market_path = member(root, relative)
        if digest(market_path) != entry["marketplace_sha256"]:
            raise ValueError(f"{host}: marketplace checksum mismatch")
        market = json.loads(market_path.read_text())
        if host == "claude" and market.get("owner") != {"name": "ai-code"}:
            raise ValueError("claude: invalid native marketplace owner")
        entries = market["plugins"]
        if not isinstance(entries, list) or len(entries) != len(expected_host_ids[host]) or \
                {entry["name"] for entry in entries} != expected_host_ids[host]:
            raise ValueError(f"{host}: marketplace plugin registration differs from index")
        for item in entries:
            if item["version"] != plugins[item["name"]]["version"]:
                raise ValueError(f"{host}: marketplace plugin version differs from index")
            identity = item["name"]
            if host == "codex":
                if item.get("source") != {"source": "local", "path": f"./{identity}"} or \
                        item.get("policy") != {"installation": "AVAILABLE", "authentication": "ON_INSTALL"} or \
                        item.get("category") != "developer-tools":
                    raise ValueError(f"{host}: invalid native marketplace registration: {identity}")
            elif item.get("source") != f"./{identity}":
                raise ValueError(f"{host}: marketplace source differs from package directory: {identity}")
        markets[host] = market
        registered_files.add(relative)
    payload = {}
    for identity, plugin in plugins.items():
        plugin_payload = {}
        for host, entry in plugin["hosts"].items():
            if entry["package_dir"] != f"{host}/{identity}" or \
                    entry["zip"] != f"{host}/{identity}-{plugin['version']}.zip":
                raise ValueError(f"{identity}/{host}: invalid package or archive registration")
            package = member(root, entry["package_dir"])
            paths = [p for p in package.rglob("*") if member(root, p.relative_to(root).as_posix()).is_file()]
            artifact_path = member(root, f"{entry['package_dir']}/artifact.json")
            artifact = json.loads(artifact_path.read_text())
            if type(artifact.get("schema_version")) is not int or artifact["schema_version"] != 1:
                raise ValueError(f"{identity}/{host}: unsupported artifact schema")
            for field, expected in (("product_id", identity), ("version", plugin["version"]),
                    ("host", host), ("source_revision", index["source_revision"]),
                    ("working_tree_dirty", index["working_tree_dirty"]),
                    ("source_tree_hash", plugin["source_tree_hash"])):
                if artifact[field] != expected:
                    raise ValueError(f"{identity}/{host}: inconsistent artifact {field}")
            actual = {p.relative_to(package).as_posix(): digest(p) for p in paths if p != artifact_path}
            if actual != dict(artifact["files"]) or len(artifact["files"]) != len(actual) or \
                    entry["files_count"] != len(actual):
                raise ValueError(f"{identity}/{host}: package bytes differ from artifact")
            encoded = json.dumps(artifact["files"], sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
            if hashlib.sha256(encoded).hexdigest() != entry["package_content_hash"] or \
                    artifact["content_hash"] != entry["package_content_hash"]:
                raise ValueError(f"{identity}/{host}: invalid package content hash")
            archive = member(root, entry["zip"])
            if digest(archive) != entry["zip_sha256"]:
                raise ValueError(f"{identity}/{host}: archive checksum mismatch")
            expected = {p.relative_to(root / host).as_posix(): p.read_bytes() for p in paths}
            market = dict(markets[host], plugins=[item for item in markets[host]["plugins"] if item["name"] == identity])
            market_relative = Path(hosts[host]["marketplace"]).relative_to(host).as_posix()
            expected[market_relative] = (json.dumps(market, indent=2, sort_keys=True, ensure_ascii=True) + "\n").encode()
            with zipfile.ZipFile(archive) as zipped:
                names = zipped.namelist()
                if len(names) != len(set(names)) or set(names) != set(expected):
                    raise ValueError(f"{identity}/{host}: unexpected archive members")
                for info in zipped.infolist():
                    if stat.S_IFMT(info.external_attr >> 16) != stat.S_IFREG or \
                            zipped.read(info.filename) != expected[info.filename]:
                        raise ValueError(f"{identity}/{host}: archive payload mismatch: {info.filename}")
            registered_files.update(p.relative_to(root).as_posix() for p in paths)
            registered_files.add(entry["zip"])
            stable = {key: value for key, value in artifact.items() if key not in ("source_revision", "working_tree_dirty")}
            stable_bytes = json.dumps(stable, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
            plugin_payload[host] = (actual, stable_bytes)
        payload[identity] = (plugin["version"], plugin["source_tree_hash"], plugin_payload)
    actual_files = {p.relative_to(root).as_posix() for p in root.rglob("*")
                    if member(root, p.relative_to(root).as_posix()).is_file()}
    if actual_files != registered_files:
        raise ValueError("distribution contains missing or unregistered files")
    return payload, {host: entry["marketplace_sha256"] for host, entry in hosts.items()}


def verify(root):
    index = json.loads(member(root, "index.json").read_text())
    if type(index.get("schema_version")) is not int:
        raise ValueError("distribution index schema must be an integer")
    if index.get("schema_version") == 1:
        return verify_workflow(root, index)
    if index.get("schema_version") == 2:
        return verify_collection(root, index)
    raise ValueError("unsupported distribution index schema")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--committed", required=True, type=Path)
    parser.add_argument("--fresh", required=True, type=Path)
    args = parser.parse_args()
    try:
        if verify(args.committed) != verify(args.fresh):
            raise ValueError("committed distribution payload is stale")
    except (OSError, ValueError, TypeError, AttributeError, KeyError, zipfile.BadZipFile) as exc:
        print(f"distribution check failed: {exc}")
        return 1
    print("distribution payloads match; registered archives independently verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
