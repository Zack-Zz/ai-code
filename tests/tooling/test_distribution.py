"""Distribution verifier rejects corruption and checks multi-plugin payload parity."""

import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
import zipfile

CHECKER = Path(__file__).resolve().parents[2] / ".github/scripts/check_dist.py"


def encoded(data):
    return (json.dumps(data, indent=2, sort_keys=True, ensure_ascii=True) + "\n").encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def archive(path, members):
    with zipfile.ZipFile(path, "w") as zipped:
        for name, data in sorted(members.items()):
            info = zipfile.ZipInfo(name)
            info.external_attr = (stat.S_IFREG | 0o644) << 16
            zipped.writestr(info, data)


def fixture(root, revision="1" * 40, dirty=False):
    """Hand-built two-plugin release: one plugin supports both hosts, one Codex."""
    index = {"schema_version": 2, "plugins": {}, "hosts": {},
             "source_revision": revision, "working_tree_dirty": dirty}
    identities = [("ai-one", "1.0.0", ["zcode", "codex"]),
                  ("ai-two", "3.2.1", ["codex"])]
    for host in ("zcode", "codex"):
        market = {"name": "ai-code-local", "plugins": []}
        for name, version, hosts in identities:
            if host in hosts:
                item = {"name": name, "version": version, "source": f"./{name}"}
                if host == "codex":
                    item.update(source={"source": "local", "path": f"./{name}"},
                        policy={"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                        category="developer-tools")
                market["plugins"].append(item)
        market_relative = ".agents/plugins/marketplace.json" if host == "codex" else "marketplace.json"
        market_path = root / host / market_relative
        market_path.parent.mkdir(parents=True, exist_ok=True)
        market_path.write_bytes(encoded(market))
        index["hosts"][host] = {"marketplace": f"{host}/{market_relative}",
                                "marketplace_sha256": sha(market_path.read_bytes())}
        for name, version, hosts in identities:
            if host not in hosts:
                continue
            package = root / host / name
            package.mkdir()
            readme = f"AI capability {name}\n".encode()
            (package / "README.md").write_bytes(readme)
            files = [["README.md", sha(readme)]]
            content_hash = sha(json.dumps(files, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode())
            source_hash = sha(name.encode())
            artifact = {"schema_version": 1, "product_id": name, "version": version,
                        "host": host, "source_tree_hash": source_hash,
                        "source_revision": revision, "working_tree_dirty": dirty,
                        "files": files, "content_hash": content_hash}
            (package / "artifact.json").write_bytes(encoded(artifact))
            singleton = dict(market, plugins=[entry for entry in market["plugins"] if entry["name"] == name])
            zipped = root / host / f"{name}-{version}.zip"
            archive(zipped, {f"{name}/README.md": readme,
                             f"{name}/artifact.json": encoded(artifact),
                             market_relative: encoded(singleton)})
            plugin = index["plugins"].setdefault(name, {"version": version,
                "source_tree_hash": source_hash, "hosts": {}})
            plugin["hosts"][host] = {"package_dir": f"{host}/{name}",
                "package_content_hash": content_hash, "files_count": len(files),
                "zip": f"{host}/{name}-{version}.zip", "zip_sha256": sha(zipped.read_bytes())}
    (root / "index.json").write_bytes(encoded(index))
    return index


class DistributionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.committed, self.fresh = self.root / "committed", self.root / "fresh"
        self.index = fixture(self.committed)
        fixture(self.fresh, revision="2" * 40, dirty=True)

    def check(self):
        return subprocess.run([sys.executable, str(CHECKER), "--committed", str(self.committed),
                               "--fresh", str(self.fresh)], capture_output=True, text=True)

    def rewrite_index(self):
        (self.committed / "index.json").write_bytes(encoded(self.index))

    def test_multiple_versions_and_host_subsets_match_across_provenance(self):
        result = self.check()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_archive_cannot_include_sibling_plugin_even_with_updated_zip_hash(self):
        entry = self.index["plugins"]["ai-one"]["hosts"]["codex"]
        zipped = self.committed / entry["zip"]
        with zipfile.ZipFile(zipped, "a") as output:
            output.writestr("ai-two/README.md", b"injected")
        entry["zip_sha256"] = sha(zipped.read_bytes())
        self.rewrite_index()
        self.assertNotEqual(self.check().returncode, 0)

    def test_archive_market_must_be_singleton_projection_of_aggregate(self):
        entry = self.index["plugins"]["ai-one"]["hosts"]["codex"]
        zipped = self.committed / entry["zip"]
        with zipfile.ZipFile(zipped) as source:
            members = {name: source.read(name) for name in source.namelist()}
        members[".agents/plugins/marketplace.json"] = (
            self.committed / "codex/.agents/plugins/marketplace.json").read_bytes()
        archive(zipped, members)
        entry["zip_sha256"] = sha(zipped.read_bytes())
        self.rewrite_index()
        self.assertNotEqual(self.check().returncode, 0)

    def test_unregistered_distribution_file_is_rejected(self):
        (self.committed / "codex/unregistered.txt").write_text("extra")
        self.assertNotEqual(self.check().returncode, 0)

    def test_boolean_schema_cannot_compare_equal_to_integer_schema(self):
        entry = self.index["plugins"]["ai-one"]["hosts"]["codex"]
        artifact_path = self.committed / entry["package_dir"] / "artifact.json"
        artifact = json.loads(artifact_path.read_text())
        artifact["schema_version"] = True
        artifact_path.write_bytes(encoded(artifact))
        zipped = self.committed / entry["zip"]
        with zipfile.ZipFile(zipped) as source:
            members = {name: source.read(name) for name in source.namelist()}
        members["ai-one/artifact.json"] = encoded(artifact)
        archive(zipped, members)
        entry["zip_sha256"] = sha(zipped.read_bytes())
        self.rewrite_index()
        result = self.check()
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_consistent_float_index_schema_is_invalid(self):
        for root in (self.committed, self.fresh):
            index = json.loads((root / "index.json").read_text())
            index["schema_version"] = 2.0
            (root / "index.json").write_bytes(encoded(index))
        result = self.check()
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_consistent_boolean_artifact_schema_is_invalid(self):
        for root in (self.committed, self.fresh):
            index = json.loads((root / "index.json").read_text())
            entry = index["plugins"]["ai-one"]["hosts"]["codex"]
            artifact_path = root / entry["package_dir"] / "artifact.json"
            artifact = json.loads(artifact_path.read_text())
            artifact["schema_version"] = True
            artifact_path.write_bytes(encoded(artifact))
            zipped = root / entry["zip"]
            with zipfile.ZipFile(zipped) as source:
                members = {name: source.read(name) for name in source.namelist()}
            members["ai-one/artifact.json"] = encoded(artifact)
            archive(zipped, members)
            entry["zip_sha256"] = sha(zipped.read_bytes())
            (root / "index.json").write_bytes(encoded(index))
        result = self.check()
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "requires POSIX special files")
    def test_special_files_cannot_hide_outside_artifact_inventory(self):
        os.mkfifo(self.committed / "codex/ai-one/unregistered.fifo")
        result = self.check()
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)

    def mutate_market_in_both_builds(self, host, field, value):
        for root in (self.committed, self.fresh):
            index = json.loads((root / "index.json").read_text())
            market_entry = index["hosts"][host]
            market_path = root / market_entry["marketplace"]
            market = json.loads(market_path.read_text())
            next(item for item in market["plugins"] if item["name"] == "ai-one")[field] = value
            market_path.write_bytes(encoded(market))
            market_entry["marketplace_sha256"] = sha(market_path.read_bytes())
            for identity, plugin in index["plugins"].items():
                if host not in plugin["hosts"]:
                    continue
                entry = plugin["hosts"][host]
                zipped = root / entry["zip"]
                with zipfile.ZipFile(zipped) as source:
                    members = {name: source.read(name) for name in source.namelist()}
                relative = Path(market_entry["marketplace"]).relative_to(host).as_posix()
                members[relative] = encoded(dict(market,
                    plugins=[item for item in market["plugins"] if item["name"] == identity]))
                archive(zipped, members)
                entry["zip_sha256"] = sha(zipped.read_bytes())
            (root / "index.json").write_bytes(encoded(index))

    def test_consistently_wrong_market_source_is_rejected(self):
        self.mutate_market_in_both_builds("zcode", "source", "./ai-two")
        result = self.check()
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_consistently_wrong_codex_source_type_is_rejected(self):
        self.mutate_market_in_both_builds("codex", "source", {"source": "remote", "path": "./ai-one"})
        result = self.check()
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_consistently_wrong_codex_native_policy_is_rejected(self):
        self.mutate_market_in_both_builds("codex", "policy", {"installation": "unknown", "authentication": "ON_INSTALL"})
        result = self.check()
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_payload_drift_is_rejected_even_when_local_artifact_is_consistent(self):
        entry = self.index["plugins"]["ai-two"]["hosts"]["codex"]
        package = self.committed / entry["package_dir"]
        (package / "README.md").write_bytes(b"changed\n")
        artifact = json.loads((package / "artifact.json").read_text())
        artifact["files"] = [["README.md", sha(b"changed\n")]]
        artifact["content_hash"] = sha(json.dumps(artifact["files"], sort_keys=True,
            separators=(",", ":"), ensure_ascii=True).encode())
        (package / "artifact.json").write_bytes(encoded(artifact))
        entry["package_content_hash"] = artifact["content_hash"]
        zipped = self.committed / entry["zip"]
        with zipfile.ZipFile(zipped) as source:
            members = {name: source.read(name) for name in source.namelist()}
        members["ai-two/README.md"] = b"changed\n"
        members["ai-two/artifact.json"] = encoded(artifact)
        archive(zipped, members)
        entry["zip_sha256"] = sha(zipped.read_bytes())
        self.rewrite_index()
        self.assertNotEqual(self.check().returncode, 0)
