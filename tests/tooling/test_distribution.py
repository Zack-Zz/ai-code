"""Distribution verifier rejects corruption and checks multi-plugin payload parity."""

import hashlib
import json
import os
from pathlib import Path
import stat
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

from tests.tooling import test_release as release_fixtures
from plugin_tools import distribution, io
from plugin_tools.release import prepare_release
from plugin_tools.registry import load_catalog
from urllib.parse import quote


class HostedConfigTests(unittest.TestCase):
    def test_repository_config_selects_separate_channels_and_native_transports(self):
        config = distribution.load_config(Path(__file__).resolve().parents[2])
        self.assertEqual(config.get("channels", {}).get("preview", {}).get("branch"),
                         "codex/marketplace-preview")
        self.assertEqual(config["channels"]["stable"]["marketplace_name"], "ai-code-stable")
        self.assertEqual(config["transports"], {"claude": "archive", "codex": "git-subdir", "zcode": "url-zip"})


class HostedMarketTests(unittest.TestCase):
    def setUp(self):
        self.case = release_fixtures.ReleaseTests()
        self.case.setUp()
        self.addCleanup(self.case.doCleanups)
        self.root = self.case.root
        product = json.loads((self.case.plugin / "product.json").read_text())
        product["repository"] = "https://github.com/Example/ai-code"
        release_fixtures.write_json(self.case.plugin / "product.json", product)
        self.config = distribution.load_config(Path(__file__).resolve().parents[2])
        (self.root / "distribution.json").write_bytes(io.dump_json(self.config))
        self.git("init", "-q", "-b", "main")
        self.git("add", "-A")
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                 "commit", "--no-verify", "-qm", "test source")
        self.git("tag", "ai-one/v1.0.0")
        report = prepare_release(self.root, self.case.spec(), self.case.output)
        self.assertTrue(report["ok"], report)
        self.release_info = self.info(self.case.spec(), self.case.output)

    def git(self, *args):
        result = subprocess.run(["git", *args], cwd=self.root, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def info(self, spec, bundle):
        repository = spec.manifest["repository"].removesuffix(".git").rstrip("/")
        tag = f"{spec.product_id}/v{spec.version}"
        assets = []
        # Actual prepared installer bytes, never invented host acceptance.
        for number, path in enumerate(sorted((bundle / "installers").glob("*.zip")), 1):
            assets.append({"id": number, "name": path.name, "size": path.stat().st_size,
                "sha256": io.sha256(path.read_bytes()),
                "browser_download_url": f"{repository}/releases/download/{quote(tag, safe='')}/{path.name}"})
        return {"id": 21, "tag_name": tag, "draft": False, "prerelease": True,
                "html_url": f"{repository}/releases/tag/{quote(tag, safe='')}", "assets": assets}

    def plan(self, **options):
        return distribution.plan_distribution(self.root, self.case.spec(), self.case.output,
            self.release_info, "preview", **options)

    def test_preview_plan_uses_source_revision_and_does_not_claim_acceptance(self):
        plan = self.plan()
        self.assertEqual(plan.get("source_revision"), self.git("rev-parse", "HEAD"))
        self.assertEqual(plan["status"], "plan_ready")
        self.assertEqual(plan["record"]["readiness"]["accepted_hosts"], [])
        self.assertTrue(plan["bootstrap"])
        self.assertEqual(json.loads(json.dumps(plan)), plan)

    def test_final_markets_bind_transport_urls_installer_hashes_and_actual_D(self):
        plan = self.plan()
        stage = distribution.stage_files(plan)
        self.assertTrue(stage)
        self.assertTrue(all(path.startswith("plugins/codex/ai-one/1.0.0/") for path in stage))
        final = distribution.finalize_files(plan, "d" * 40)
        claude = json.loads(final[".claude-plugin/marketplace.json"])["plugins"][0]
        zcode = json.loads(final["marketplace.json"])["plugins"][0]
        codex = json.loads(final[".agents/plugins/marketplace.json"])["plugins"][0]
        self.assertEqual(claude["source"]["source"], "archive")
        self.assertIn("ai-one%2Fv1.0.0", claude["source"]["url"])
        self.assertEqual(zcode["source"]["path"], "ai-one")
        self.assertEqual(zcode["source"]["type"], "zip")
        self.assertEqual(codex["source"]["sha"], "d" * 40)
        self.assertEqual(codex["source"]["path"], "./plugins/codex/ai-one/1.0.0")
        self.assertEqual(codex["policy"]["installation"], "AVAILABLE")
        self.assertNotIn("d" * 40, json.dumps(plan))

    def test_plan_hash_and_base_commit_are_review_leases(self):
        plan = self.plan()
        self.assertTrue(distribution.check_plan(plan, plan["plan_hash"], "absent")["ok"])
        with self.assertRaises(io.ConflictError):
            distribution.check_plan(plan, "0" * 64)
        with self.assertRaises(io.ConflictError):
            distribution.check_plan(plan, expected_commit="a" * 40)
        plan["version"] = "9.9.9"
        with self.assertRaises(io.DataError):
            distribution.check_plan(plan)

    def test_public_release_visibility_channel_and_asset_binding_are_required(self):
        for field, value in (("draft", True), ("prerelease", False), ("tag_name", "other/v1.0.0")):
            original = self.release_info[field]
            self.release_info[field] = value
            with self.subTest(field=field), self.assertRaises(io.DataError):
                self.plan()
            self.release_info[field] = original
        self.release_info["assets"] = []
        with self.assertRaises(io.DataError):
            self.plan()

    def test_preview_requires_clean_correctly_tagged_source(self):
        (self.case.plugin / "release/NOTES.md").write_text("changed")
        with self.assertRaises(io.DataError):
            self.plan()

    def test_stable_rejects_unverified_bundle(self):
        self.release_info["prerelease"] = False
        with self.assertRaises(io.DataError):
            distribution.plan_distribution(self.root, self.case.spec(), self.case.output,
                self.release_info, "stable")

    def test_old_stable_record_cannot_claim_ready_with_pending_hosts(self):
        record = self.plan()['record']
        record.update(channel='stable', mode='stable', codex_revision='d' * 40)
        record['readiness']['publication_ready'] = True
        with self.assertRaises(io.DataError):
            distribution._record(record, 'stable', record['repository'])

    def test_identical_deployment_is_readonly_and_user_edits_are_rejected(self):
        final = distribution.finalize_files(self.plan(), "d" * 40)
        plan = self.plan(market_files=final, base_commit="c" * 40)
        self.assertEqual(plan["status"], "already_deployed")
        self.assertEqual(distribution.stage_files(plan), {})
        self.assertEqual(distribution.finalize_files(plan, "d" * 40), final)
        for path in ("README.md", "marketplace.json", "plugins/codex/ai-one/1.0.0/plugin.json"):
            changed = dict(final, **{path: b"user edit"})
            with self.subTest(path=path), self.assertRaises(io.DataError):
                self.plan(market_files=changed, base_commit="c" * 40)
        with self.assertRaises(io.DataError):
            self.plan(market_files=dict(final, unexpected=b"unknown"), base_commit="c" * 40)

    def test_retry_recognizes_only_byte_identical_pending_codex_directory(self):
        initial = self.plan()
        staged = distribution.stage_files(initial)
        retry = self.plan(market_files=staged, base_commit="d" * 40)
        self.assertEqual(distribution.stage_files(retry), {})
        final = distribution.finalize_files(retry, "d" * 40)
        self.assertEqual(json.loads(final["channel.json"])["plugins"]["ai-one"]["codex_revision"], "d" * 40)
        name = next(iter(staged))
        with self.assertRaises(io.DataError):
            self.plan(market_files=dict(staged, **{name: b"different bytes"}), base_commit="d" * 40)
        with self.assertRaises(io.DataError):
            self.plan(market_files=dict(staged, **{"plugins/codex/unknown/1.0.0/plugin.json": b"unknown"}), base_commit="d" * 40)

    def add_second(self, hosts):
        plugin = self.root / "plugins/ai-two"
        shutil.copytree(self.case.plugin, plugin)
        product = json.loads((plugin / "product.json").read_text())
        product.update(product_id="ai-two", version="3.2.1", hosts=hosts)
        release_fixtures.write_json(plugin / "product.json", product)
        release = json.loads((plugin / "release.json").read_text())
        release["acceptance"] = {host: None for host in hosts}
        release_fixtures.write_json(plugin / "release.json", release)
        release_fixtures.write_json(self.root / "catalog.json", {"schema_version": 1, "plugins": [
            {"path": "plugins/ai-one"}, {"path": "plugins/ai-two"}]})
        self.git("add", "-A")
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                 "commit", "--no-verify", "-qm", "independent plugin")
        self.git("tag", "ai-two/v3.2.1")
        spec = next(item for item in load_catalog(self.root) if item.product_id == "ai-two")
        bundle = self.case.base / "second-release"
        result = prepare_release(self.root, spec, bundle)
        self.assertTrue(result["ok"], result)
        info = self.info(spec, bundle)
        info["id"] = 22
        return spec, bundle, info

    def test_independent_version_and_host_subset_preserve_other_plugin_and_old_directory(self):
        first = distribution.finalize_files(self.plan(), "d" * 40)
        spec, bundle, info = self.add_second(["codex"])
        plan = distribution.plan_distribution(self.root, spec, bundle, info, "preview",
            market_files=first, base_commit="c" * 40)
        self.assertIsNone(plan["previous_version"])
        self.assertFalse(plan["bootstrap"])
        final = distribution.finalize_files(plan, "e" * 40)
        for name, data in first.items():
            if name.startswith(("plugins/", "records/")):
                self.assertEqual(final[name], data)
        self.assertEqual(final[".claude-plugin/marketplace.json"], first[".claude-plugin/marketplace.json"])
        self.assertEqual(final["marketplace.json"], first["marketplace.json"])
        codex = json.loads(final[".agents/plugins/marketplace.json"])["plugins"]
        self.assertEqual([(item["name"], item["version"], item["source"]["sha"]) for item in codex],
            [("ai-one", "1.0.0", "d" * 40), ("ai-two", "3.2.1", "e" * 40)])

    def test_plugin_without_codex_skips_D_and_undeployed_catalog_plugins(self):
        spec, bundle, info = self.add_second(["zcode"])
        plan = distribution.plan_distribution(self.root, spec, bundle, info, "preview")
        self.assertEqual(distribution.stage_files(plan), {})
        final = distribution.finalize_files(plan)
        self.assertNotIn(".agents/plugins/marketplace.json", final)
        self.assertNotIn(".claude-plugin/marketplace.json", final)
        market = json.loads(final["marketplace.json"])
        self.assertEqual([item["name"] for item in market["plugins"]], ["ai-two"])
        record = json.loads(final["records/ai-two/3.2.1.json"])
        self.assertIsNone(record["codex_revision"])
        with self.assertRaises(io.DataError):
            distribution.finalize_files(plan, "d" * 40)

    def upgraded_first(self, hosts, version):
        product = json.loads((self.case.plugin / "product.json").read_text())
        product.update(version=version, hosts=hosts)
        release_fixtures.write_json(self.case.plugin / "product.json", product)
        release = json.loads((self.case.plugin / "release.json").read_text())
        release["acceptance"] = {host: None for host in hosts}
        release_fixtures.write_json(self.case.plugin / "release.json", release)
        self.git("add", "-A")
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                 "commit", "--no-verify", "-qm", "host subset upgrade")
        self.git("tag", f"ai-one/v{version}")
        spec = self.case.spec()
        bundle = self.case.base / f"upgrade-{version}"
        report = prepare_release(self.root, spec, bundle)
        self.assertTrue(report["ok"], report)
        info = self.info(spec, bundle)
        info["id"] = 30
        return spec, bundle, info

    def test_host_shrink_removes_only_empty_owned_markets_and_keeps_history(self):
        first = distribution.finalize_files(self.plan(), "d" * 40)
        paths = {"claude": ".claude-plugin/marketplace.json",
                 "codex": ".agents/plugins/marketplace.json", "zcode": "marketplace.json"}
        for number, retained in enumerate(paths, 1):
            with self.subTest(retained=retained):
                spec, bundle, info = self.upgraded_first([retained], f"1.0.{number}")
                plan = distribution.plan_distribution(self.root, spec, bundle, info, "preview",
                    market_files=first, base_commit="c" * 40)
                try:
                    final = distribution.finalize_files(plan, "e" * 40 if retained == "codex" else None)
                except io.DataError as exc:
                    self.fail(f"host shrink must produce a valid final managed tree: {exc}")
                for host, path in paths.items():
                    self.assertEqual(path in final, host == retained)
                lock = json.loads(final["marketplaces.lock.json"])
                self.assertEqual(lock["files"], {paths[retained]: io.sha256(final[paths[retained]])})
                for name, data in first.items():
                    if name.startswith(("records/", "plugins/")):
                        self.assertEqual(final[name], data)
                removed = next(path for host, path in paths.items() if host != retained)
                with self.assertRaises(io.DataError):
                    distribution.plan_distribution(self.root, spec, bundle, info, "preview",
                        market_files=dict(first, **{removed: b"user changed market"}), base_commit="c" * 40)

    def test_host_shrink_keeps_other_plugin_in_shared_market(self):
        first = distribution.finalize_files(self.plan(), "d" * 40)
        other_spec, other_bundle, other_info = self.add_second(["zcode"])
        other_plan = distribution.plan_distribution(self.root, other_spec, other_bundle, other_info,
            "preview", market_files=first, base_commit="c" * 40)
        previous = distribution.finalize_files(other_plan)
        spec, bundle, info = self.upgraded_first(["codex"], "1.0.1")
        plan = distribution.plan_distribution(self.root, spec, bundle, info, "preview",
            market_files=previous, base_commit="b" * 40)
        try:
            final = distribution.finalize_files(plan, "e" * 40)
        except io.DataError as exc:
            self.fail(f"host shrink must preserve the other plugin's market: {exc}")
        self.assertNotIn(".claude-plugin/marketplace.json", final)
        zcode = json.loads(final["marketplace.json"])["plugins"]
        self.assertEqual([item["name"] for item in zcode], ["ai-two"])
        self.assertEqual(zcode[0], json.loads(previous["marketplace.json"])["plugins"][1])
        for name, data in previous.items():
            if name.startswith(("records/", "plugins/")):
                self.assertEqual(final[name], data)

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
