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
from types import SimpleNamespace
from unittest import mock


def accept_fixture(root, identity):
    spec = next(item for item in load_catalog(root) if item.product_id == identity)
    holder = SimpleNamespace(plugin=root / spec.catalog_path, spec=lambda: spec)
    release_fixtures.ReleaseTests.accept(holder, hosts=spec.hosts)


class HostedConfigTests(unittest.TestCase):
    def test_repository_config_selects_main_latest_stable_and_native_transports(self):
        config = distribution.load_config(Path(__file__).resolve().parents[2])
        self.assertEqual(config.get("source_branch"), "main")
        self.assertEqual(config.get("marketplace"), {"branch": "main", "name": "ai-code",
                                                   "version_policy": "latest-stable"})
        self.assertEqual(config["transports"], {"claude": "archive", "codex": "git-subdir", "zcode": "url-zip", "dsh": "git-subdir"})

    def test_requested_marketplace_name_is_accepted_without_an_alias(self):
        config = json.loads((Path(__file__).resolve().parents[2] / "distribution.json").read_text())
        config["marketplace"]["name"] = "ai-code"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "distribution.json").write_bytes(io.dump_json(config))
            self.assertEqual(distribution.load_config(root)["marketplace"]["name"], "ai-code")

    def test_previous_marketplace_name_is_rejected(self):
        config = json.loads((Path(__file__).resolve().parents[2] / "distribution.json").read_text())
        config["marketplace"]["name"] = "ai-code-preview"
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "distribution.json").write_bytes(io.dump_json(config))
            with self.assertRaises(io.DataError):
                distribution.load_config(root)

    def test_public_market_names_and_ownership_hashes_match(self):
        root = Path(__file__).resolve().parents[2]
        lock = json.loads((root / distribution.LOCK_PATH).read_text())
        for path in lock["files"]:
            with self.subTest(path=path):
                raw = (root / path).read_bytes()
                self.assertEqual(json.loads(raw)["name"], "ai-code")
                self.assertEqual(lock["files"][path], hashlib.sha256(raw).hexdigest())


class HostedMarketTests(unittest.TestCase):
    def setUp(self):
        self.case = release_fixtures.ReleaseTests()
        self.case.setUp()
        self.addCleanup(self.case.doCleanups)
        self.root = self.case.root
        product = json.loads((self.case.plugin / "product.json").read_text())
        product["repository"] = "https://github.com/Example/ai-code"
        release_fixtures.write_json(self.case.plugin / "product.json", product)
        self.config = dict(distribution.load_config(Path(__file__).resolve().parents[2]), identity_replacements={})
        (self.root / "distribution.json").write_bytes(io.dump_json(self.config))
        accept_fixture(self.root, "ai-one")
        self.git("init", "-q", "-b", "main")
        self.git("add", "-A")
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                 "commit", "--no-verify", "-qm", "test source")
        self.git("tag", "ai-one/v1.0.0")
        report = prepare_release(self.root, self.case.spec(), self.case.output, mode="stable")
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
        for number, path in enumerate(sorted((bundle / "installers").iterdir()), 1):
            assets.append({"id": number, "name": path.name, "size": path.stat().st_size,
                "sha256": io.sha256(path.read_bytes()),
                "browser_download_url": f"{repository}/releases/download/{quote(tag, safe='')}/{path.name}"})
        return {"id": 21, "tag_name": tag, "draft": False, "prerelease": False,
                "html_url": f"{repository}/releases/tag/{quote(tag, safe='')}", "published_at": "2026-10-27T00:00:00Z", "assets": assets}

    def plan(self, **options):
        options.setdefault("base_commit", "b" * 40)
        return distribution.plan_distribution(self.root, self.case.spec(), self.case.output,
            self.release_info, "stable", **options)

    def test_stable_plan_uses_frozen_source_and_fixture_byte_bound_acceptance(self):
        plan = self.plan()
        self.assertEqual(plan.get("source_revision"), self.git("rev-parse", "HEAD"))
        self.assertEqual(plan["status"], "plan_ready")
        self.assertEqual(set(plan["record"]["readiness"]["accepted_hosts"]), {"claude", "codex", "zcode"})
        self.assertEqual(plan["branch"], "main")
        self.assertEqual(plan["marketplace_name"], "ai-code")
        self.assertTrue(plan["bootstrap"])
        self.assertEqual(json.loads(json.dumps(plan)), plan)

    def test_final_markets_bind_transport_urls_installer_hashes_and_actual_D(self):
        plan = self.plan()
        stage = distribution.stage_files(plan)
        self.assertTrue(stage)
        self.assertTrue(all(path.startswith("published/codex/ai-one/1.0.0/") or path == "published/staged/ai-one/1.0.0.json" for path in stage))
        final = distribution.finalize_files(plan, "d" * 40)
        for path in distribution.NATIVE_PATHS:
            with self.subTest(path=path):
                self.assertEqual(json.loads(final[path])["title"]["en"] if path == "published/dsh/index.json" else json.loads(final[path])["name"], "ai-code")
        claude = json.loads(final[".claude-plugin/marketplace.json"])["plugins"][0]
        zcode = json.loads(final["marketplace.json"])["plugins"][0]
        codex = json.loads(final[".agents/plugins/marketplace.json"])["plugins"][0]
        self.assertEqual(claude["source"]["source"], "archive")
        self.assertIn("ai-one%2Fv1.0.0", claude["source"]["url"])
        self.assertEqual(zcode["source"]["path"], "ai-one")
        self.assertEqual(zcode["source"]["type"], "zip")
        self.assertEqual(codex["source"]["sha"], "d" * 40)
        self.assertEqual(codex["source"]["path"], "./published/codex/ai-one/1.0.0")
        self.assertEqual(codex["policy"]["installation"], "AVAILABLE")
        self.assertNotIn("d" * 40, json.dumps(plan))

    def test_plan_hash_and_base_commit_are_review_leases(self):
        plan = self.plan()
        self.assertTrue(distribution.check_plan(plan, plan["plan_hash"], "b" * 40)["ok"])
        with self.assertRaises(io.ConflictError):
            distribution.check_plan(plan, "0" * 64)
        with self.assertRaises(io.ConflictError):
            distribution.check_plan(plan, expected_commit="a" * 40)
        plan["version"] = "9.9.9"
        with self.assertRaises(io.DataError):
            distribution.check_plan(plan)

    def test_plan_rejects_previous_namespace_even_with_recomputed_hash(self):
        plan = self.plan()
        config = json.loads((self.root / "distribution.json").read_text())
        config["marketplace"]["name"] = "ai-code-preview"
        plan["marketplace_name"] = "ai-code-preview"
        plan["config_hash"] = io.sha256(io.canonical_json(config))
        plan["plan_hash"] = distribution._digest(plan)
        with self.assertRaisesRegex(io.DataError, "trusted main/latest-stable"):
            distribution.check_plan(plan)

    def test_public_release_visibility_channel_and_asset_binding_are_required(self):
        for field, value in (("draft", True), ("prerelease", True), ("tag_name", "other/v1.0.0")):
            original = self.release_info[field]
            self.release_info[field] = value
            with self.subTest(field=field), self.assertRaises(io.DataError):
                self.plan()
            self.release_info[field] = original
        self.release_info["assets"] = []
        with self.assertRaises(io.DataError):
            self.plan()

    def test_formal_market_requires_clean_correctly_tagged_source(self):
        (self.case.plugin / "release/NOTES.md").write_text("changed")
        with self.assertRaises(io.DataError):
            self.plan()

    def test_stable_rejects_unverified_bundle(self):
        with mock.patch.object(distribution, "verify_release", return_value={"ok": False,
                "blockers": ["source bytes differ from frozen tagged source"]}):
            with self.assertRaisesRegex(io.DataError, "frozen tagged source"):
                self.plan()

    def test_preview_never_enters_the_default_market(self):
        self.release_info["prerelease"] = True
        with self.assertRaisesRegex(io.DataError, "preview"):
            distribution.plan_distribution(self.root, self.case.spec(), self.case.output,
                self.release_info, "preview", base_commit="b" * 40)

    def test_stable_record_can_be_technically_ready_with_pending_hosts(self):
        record = self.plan()['record']
        record.update(channel='stable', mode='stable')
        record['git_installs']['codex']['revision'] = 'd' * 40
        record['readiness']['publication_ready'] = True
        record['readiness']['pending_acceptance'] = ['codex']
        record['readiness']['accepted_hosts'] = ['claude', 'zcode']
        distribution._record(record, 'stable', record['repository'])
        self.assertEqual(record['readiness']['pending_acceptance'], ['codex'])
        self.assertEqual(record['readiness']['accepted_hosts'], ['claude', 'zcode'])

    def test_all_null_stable_release_can_update_market_with_truthful_pending_hosts(self):
        config = json.loads((self.case.plugin / "release.json").read_text())
        config["acceptance"] = {host: None for host in self.case.spec().hosts}
        release_fixtures.write_json(self.case.plugin / "release.json", config)
        self.git("add", "-A")
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                 "commit", "--no-verify", "-qm", "untested host release fixture")
        self.git("tag", "-f", "ai-one/v1.0.0")
        shutil.rmtree(self.case.output)
        report = prepare_release(self.root, self.case.spec(), self.case.output, mode="stable",
                                 committed_acceptance=True)
        self.assertTrue(report["ok"], report)
        self.release_info = self.info(self.case.spec(), self.case.output)
        plan = self.plan()
        self.assertEqual(plan["status"], "plan_ready")
        self.assertTrue(plan["record"]["readiness"]["publication_ready"])
        self.assertEqual(plan["record"]["readiness"]["accepted_hosts"], [])
        self.assertEqual(plan["record"]["readiness"]["pending_acceptance"], ["claude", "codex", "zcode"])
        final = distribution.finalize_files(plan, "d" * 40)
        record = json.loads(final["published/releases/ai-one/1.0.0.json"])
        self.assertEqual(record["readiness"], plan["record"]["readiness"])
        retry = self.plan(market_files=final, base_commit="c" * 40)
        self.assertEqual(retry["status"], "already_deployed")
        self.assertEqual(distribution.finalize_files(retry, "d" * 40), final)
        # Later real evidence stays truthful, but cannot replace the immutable
        # public record or installers for this already published version.
        self.case.accept(hosts=["claude"])
        self.git("add", "-A")
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                 "commit", "--no-verify", "-qm", "later actual host evidence fixture")
        self.git("tag", "-f", "ai-one/v1.0.0")
        shutil.rmtree(self.case.output)
        report = prepare_release(self.root, self.case.spec(), self.case.output, mode="stable",
                                 committed_acceptance=True)
        self.assertTrue(report["ok"], report)
        self.assertTrue(report["publication_ready"], report)
        self.assertEqual(report["readiness"]["accepted_hosts"], ["claude"])
        self.assertEqual(report["pending_acceptance"], ["codex", "zcode"])
        self.release_info = self.info(self.case.spec(), self.case.output)
        with self.assertRaisesRegex(io.DataError, "same-version public record/installer bytes differ"):
            self.plan(market_files=final, base_commit="c" * 40)

    def test_record_host_inventory_still_partitions_hosts_and_requires_package_hashes(self):
        for field, value in (("accepted_hosts", ["claude", "zcode"]),
                             ("pending_acceptance", ["codex"]),
                             ("package_content_hashes", {}),
                             ("publication_ready", False)):
            record = self.plan()["record"]
            record["readiness"][field] = value
            with self.subTest(field=field), self.assertRaises(io.DataError):
                distribution._record(record, "stable", record["repository"], staged=True)

    def test_identical_deployment_is_readonly_and_user_edits_are_rejected(self):
        final = distribution.finalize_files(self.plan(), "d" * 40)
        plan = self.plan(market_files=final, base_commit="c" * 40)
        self.assertEqual(plan["status"], "already_deployed")
        self.assertEqual(distribution.stage_files(plan), {})
        self.assertEqual(distribution.finalize_files(plan, "d" * 40), final)
        for path in ("README.md", "marketplace.json", "published/codex/ai-one/1.0.0/plugin.json"):
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
        self.assertEqual(json.loads(final["published/index.json"])["plugins"]["ai-one"]["git_revisions"]["codex"], "d" * 40)
        name = next(iter(staged))
        with self.assertRaises(io.DataError):
            self.plan(market_files=dict(staged, **{name: b"different bytes"}), base_commit="d" * 40)
        with self.assertRaises(io.DataError):
            self.plan(market_files=dict(staged, **{"published/codex/unknown/1.0.0/plugin.json": b"unknown"}), base_commit="d" * 40)

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
        accept_fixture(self.root, "ai-two")
        self.git("add", "-A")
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                 "commit", "--no-verify", "-qm", "independent plugin")
        self.git("tag", "ai-two/v3.2.1")
        spec = next(item for item in load_catalog(self.root) if item.product_id == "ai-two")
        bundle = self.case.base / "second-release"
        result = prepare_release(self.root, spec, bundle, mode="stable")
        self.assertTrue(result["ok"], result)
        info = self.info(spec, bundle)
        info["id"] = 22
        return spec, bundle, info

    def test_independent_version_and_host_subset_preserve_other_plugin_and_old_directory(self):
        first = distribution.finalize_files(self.plan(), "d" * 40)
        spec, bundle, info = self.add_second(["codex"])
        plan = distribution.plan_distribution(self.root, spec, bundle, info, "stable",
            market_files=first, base_commit="c" * 40)
        self.assertIsNone(plan["previous_version"])
        self.assertFalse(plan["bootstrap"])
        final = distribution.finalize_files(plan, "e" * 40)
        for name, data in first.items():
            if name.startswith(("plugins/", "published/releases/")):
                self.assertEqual(final[name], data)
        self.assertEqual(final[".claude-plugin/marketplace.json"], first[".claude-plugin/marketplace.json"])
        self.assertEqual(final["marketplace.json"], first["marketplace.json"])
        codex = json.loads(final[".agents/plugins/marketplace.json"])["plugins"]
        self.assertEqual([(item["name"], item["version"], item["source"]["sha"]) for item in codex],
            [("ai-one", "1.0.0", "d" * 40), ("ai-two", "3.2.1", "e" * 40)])

    def test_plugin_without_codex_skips_D_and_undeployed_catalog_plugins(self):
        spec, bundle, info = self.add_second(["zcode"])
        plan = distribution.plan_distribution(self.root, spec, bundle, info, "stable", base_commit="b" * 40)
        self.assertEqual(distribution.stage_files(plan), {})
        final = distribution.finalize_files(plan)
        self.assertEqual(json.loads(final[".agents/plugins/marketplace.json"])["plugins"], [])
        self.assertEqual(json.loads(final[".claude-plugin/marketplace.json"])["plugins"], [])
        market = json.loads(final["marketplace.json"])
        self.assertEqual([item["name"] for item in market["plugins"]], ["ai-two"])
        record = json.loads(final["published/releases/ai-two/3.2.1.json"])
        self.assertEqual(record["git_installs"], {})
        with self.assertRaises(io.DataError):
            distribution.finalize_files(plan, "d" * 40)

    def upgraded_first(self, hosts, version):
        product = json.loads((self.case.plugin / "product.json").read_text())
        product.update(version=version, hosts=hosts)
        release_fixtures.write_json(self.case.plugin / "product.json", product)
        release = json.loads((self.case.plugin / "release.json").read_text())
        release["acceptance"] = {host: None for host in hosts}
        release_fixtures.write_json(self.case.plugin / "release.json", release)
        accept_fixture(self.root, "ai-one")
        self.git("add", "-A")
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                 "commit", "--no-verify", "-qm", "host subset upgrade")
        self.git("tag", f"ai-one/v{version}")
        spec = self.case.spec()
        bundle = self.case.base / f"upgrade-{version}"
        report = prepare_release(self.root, spec, bundle, mode="stable")
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
                plan = distribution.plan_distribution(self.root, spec, bundle, info, "stable",
                    market_files=first, base_commit="c" * 40)
                try:
                    final = distribution.finalize_files(plan, "e" * 40 if retained == "codex" else None)
                except io.DataError as exc:
                    self.fail(f"host shrink must produce a valid final managed tree: {exc}")
                for host, path in paths.items():
                    self.assertEqual(bool(json.loads(final[path])["plugins"]), host == retained)
                lock = json.loads(final["published/marketplaces.lock.json"])
                self.assertEqual(lock["files"], {path: io.sha256(final[path]) for path in distribution.NATIVE_PATHS})
                for name, data in first.items():
                    if name.startswith(("published/releases/", "plugins/")):
                        self.assertEqual(final[name], data)
                removed = next(path for host, path in paths.items() if host != retained)
                with self.assertRaises(io.DataError):
                    distribution.plan_distribution(self.root, spec, bundle, info, "stable",
                        market_files=dict(first, **{removed: b"user changed market"}), base_commit="c" * 40)

    def test_host_shrink_keeps_other_plugin_in_shared_market(self):
        first = distribution.finalize_files(self.plan(), "d" * 40)
        other_spec, other_bundle, other_info = self.add_second(["zcode"])
        other_plan = distribution.plan_distribution(self.root, other_spec, other_bundle, other_info,
            "stable", market_files=first, base_commit="c" * 40)
        previous = distribution.finalize_files(other_plan)
        spec, bundle, info = self.upgraded_first(["codex"], "1.0.1")
        plan = distribution.plan_distribution(self.root, spec, bundle, info, "stable",
            market_files=previous, base_commit="b" * 40)
        try:
            final = distribution.finalize_files(plan, "e" * 40)
        except io.DataError as exc:
            self.fail(f"host shrink must preserve the other plugin's market: {exc}")
        self.assertEqual(json.loads(final[".claude-plugin/marketplace.json"])["plugins"], [])
        zcode = json.loads(final["marketplace.json"])["plugins"]
        self.assertEqual([item["name"] for item in zcode], ["ai-two"])
        self.assertEqual(zcode[0], json.loads(previous["marketplace.json"])["plugins"][1])
        for name, data in previous.items():
            if name.startswith(("published/releases/", "plugins/")):
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

class IdentityDistributionContractTests(unittest.TestCase):
    def test_schema3_bootstrap_binds_four_native_markets_and_index(self):
        files = distribution.bootstrap_files()
        index = json.loads(files[distribution.INDEX_PATH])
        self.assertEqual(index, {"schema_version": 3, "plugins": {}, "retired": {}})
        lock = json.loads(files[distribution.LOCK_PATH])
        self.assertEqual(lock["schema_version"], 2)
        self.assertEqual(set(lock["files"]), {".claude-plugin/marketplace.json", ".agents/plugins/marketplace.json", "marketplace.json", "published/dsh/index.json"})
        self.assertEqual(lock["published_index_sha256"], io.sha256(files[distribution.INDEX_PATH]))
        self.assertEqual(json.loads(files["published/dsh/index.json"])["format"], 1)

    def test_legacy_git_inventory_normalization_does_not_mutate_record(self):
        record = {"codex_revision": "d" * 40, "codex_files": {"published/codex/old/1.0.0/plugin.json": "a" * 64}}
        expected = json.loads(json.dumps(record))
        self.assertEqual(distribution.git_installs(record), {"codex": {"revision": "d" * 40, "files": record["codex_files"]}})
        self.assertEqual(record, expected)

    def test_identity_replacement_rejects_chains_cycles_and_many_to_one(self):
        base = {"schema_version": 3, "source_branch": "main", "marketplace": distribution.MARKETPLACE,
                "transports": {"claude": "archive", "codex": "git-subdir", "zcode": "url-zip", "dsh": "git-subdir"}}
        for replacements in ({"old": "new", "new": "next"}, {"old": "new", "new": "old"}, {"old": "new", "other": "new"}, {"old": "old"}):
            with self.subTest(replacements=replacements), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                (root / "distribution.json").write_bytes(io.dump_json(dict(base, identity_replacements=replacements)))
                with self.assertRaises(io.DataError):
                    distribution.load_config(root)

class IdentityRetirementTests(unittest.TestCase):
    setUp = HostedMarketTests.setUp
    git = HostedMarketTests.git
    info = HostedMarketTests.info
    plan = HostedMarketTests.plan
    add_second = HostedMarketTests.add_second
    """Migration stays atomic; successful C preserves all frozen history."""
    def test_new_identity_retires_only_its_old_pointer_after_finalize(self):
        first = distribution.finalize_files(self.plan(), "d" * 40)
        self.config["identity_replacements"] = {"ai-one": "ai-two"}
        (self.root / "distribution.json").write_bytes(io.dump_json(self.config))
        spec, bundle, info = self.add_second(["codex"])
        plan = distribution.plan_distribution(self.root, spec, bundle, info, "stable", market_files=first, base_commit="c" * 40)
        self.assertEqual(json.loads(first[distribution.INDEX_PATH])["retired"], {})
        self.assertNotIn(distribution.INDEX_PATH, distribution.stage_files(plan))
        final = distribution.finalize_files(plan, "e" * 40)
        snapshot = json.loads(final[distribution.INDEX_PATH])
        self.assertEqual(set(snapshot["plugins"]), {"ai-two"})
        self.assertEqual(snapshot["retired"], {"ai-one": "ai-two"})
        for path, raw in first.items():
            if path.startswith(("published/releases/", "published/codex/")):
                self.assertEqual(final[path], raw)
        for path in distribution.NATIVE_PATHS:
            self.assertNotIn('"name": "ai-one"', final[path].decode())
        with self.assertRaisesRegex(io.DataError, "retired"):
            self.plan(market_files=final, base_commit="f" * 40)

    def test_legacy_record_snapshot_lock_are_checked_and_never_rewritten_on_retry(self):
        first = distribution.finalize_files(self.plan(), "d" * 40)
        path = "published/releases/ai-one/1.0.0.json"
        record = json.loads(first[path])
        install = record.pop("git_installs")["codex"]
        record.pop("release_published_at")
        record.update(schema_version=2, codex_revision=install["revision"], codex_files=install["files"])
        for item in record["hosts"].values():
            item.pop("installer_format")
        legacy = {name: raw for name, raw in first.items() if name.startswith("published/codex/")}
        legacy[path] = io.dump_json(record)
        legacy.update(distribution._catalog_files({path: record}, {"ai-one": distribution._snapshot(record, legacy=True)}, legacy=True))
        before = dict(legacy)
        retry = self.plan(market_files=legacy, base_commit="c" * 40)
        self.assertEqual(retry["status"], "already_deployed")
        self.assertEqual(distribution.stage_files(retry), {})
        self.assertEqual(distribution.finalize_files(retry, "d" * 40), before)
        self.assertEqual(legacy, before)
        self.assertNotIn("published/dsh/index.json", legacy)
        self.assertEqual(json.loads(legacy[distribution.LOCK_PATH])["schema_version"], 1)

    def test_stage_has_no_D_and_orphan_or_partial_installation_is_rejected(self):
        plan = self.plan()
        staged = distribution.stage_files(plan)
        path = "published/staged/ai-one/1.0.0.json"
        receipt = json.loads(staged[path])
        self.assertEqual(receipt["record"]["git_installs"]["codex"]["revision"], None)
        self.assertEqual(receipt["plan_hash"], plan["plan_hash"])
        self.assertEqual(receipt["base_commit"], plan["base_commit"])
        self.assertEqual(set(receipt), distribution.RECEIPT_FIELDS)
        for mutation in ({name: raw for name, raw in staged.items() if name != path},
                         {name: raw for number, (name, raw) in enumerate(staged.items()) if number != 0}):
            with self.assertRaises(io.DataError):
                self.plan(market_files=mutation, base_commit="d" * 40)
        retry = self.plan(market_files=staged, base_commit="d" * 40)
        final = distribution.finalize_files(retry, "d" * 40)
        self.assertNotIn(path, final)
        self.assertEqual({name: final[name] for name in staged if name != path}, {name: raw for name, raw in staged.items() if name != path})

class DshHostedMarketTests(unittest.TestCase):
    git = HostedMarketTests.git
    info = HostedMarketTests.info
    plan = HostedMarketTests.plan

    def setUp(self):
        HostedMarketTests.setUp(self)
        product = json.loads((self.case.plugin / "product.json").read_text())
        product.update(schema_version=2, version="1.0.1", hosts=["claude", "codex", "zcode", "dsh"],
            host_resources={"dsh": [{"source": "adapters/dsh/cordis.patch.yml", "target": "cordis.patch.yml", "include": []}]})
        release_fixtures.write_json(self.case.plugin / "product.json", product)
        release_fixtures.write_json(self.case.plugin / "adapters/dsh/package.json", {
            "name": "ai-one", "version": "1.0.1", "description": "Useful AI skills", "type": "module",
            "engines": {"dsh": "0.2.1-rc.3"}, "dsh": {"bundle": {"patch": "./cordis.patch.yml"}}, "icon": "./assets/icon.svg"})
        (self.case.plugin / "adapters/dsh/cordis.patch.yml").write_text("plugins: {}\n")
        config = json.loads((self.case.plugin / "release.json").read_text())
        config["acceptance"] = {host: None for host in product["hosts"]}
        release_fixtures.write_json(self.case.plugin / "release.json", config)
        self.git("add", "-A")
        self.git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid", "commit", "--no-verify", "-qm", "dsh bundle source")
        self.git("tag", "ai-one/v1.0.1")
        self.case.output = self.case.base / "dsh-release"
        result = prepare_release(self.root, self.case.spec(), self.case.output, mode="stable", committed_acceptance=True)
        self.assertTrue(result["ok"], result)
        self.release_info = self.info(self.case.spec(), self.case.output)

    def test_dsh_TGZ_git_closure_and_native_index_bind_one_actual_D(self):
        from plugin_tools.archives import read_installer
        plan = self.plan()
        self.assertEqual(plan["schema_version"], 3)
        self.assertEqual(set(plan["git_install_files"]), {"codex", "dsh"})
        record = plan["record"]
        self.assertTrue(record["hosts"]["dsh"]["asset"]["name"].endswith("-dsh-plugin.tgz"))
        staged = distribution.stage_files(plan)
        receipt_path = "published/staged/ai-one/1.0.1.json"
        self.assertIn(receipt_path, staged)
        self.assertNotIn("published/dsh/index.json", staged)
        raw = (self.case.output / "installers/ai-one-1.0.1-dsh-plugin.tgz").read_bytes()
        package = read_installer(raw, "ai-one", "dsh")
        self.assertEqual({path.removeprefix("published/dsh/ai-one/1.0.1/"): staged[path] for path in record["git_installs"]["dsh"]["files"]}, package)
        retry = self.plan(market_files=staged, base_commit="d" * 40)
        final = distribution.finalize_files(retry, "d" * 40)
        self.assertNotIn(receipt_path, final)
        index = json.loads(final["published/dsh/index.json"])
        self.assertEqual(index["format"], 1)
        entry = index["plugins"][0]
        self.assertEqual(set(entry["title"]), {"en", "zh"})
        self.assertEqual(entry["versions"], [{"version": "1.0.1", "engines": {"dsh": "0.2.1-rc.3"},
            "publishTimestamp": 1793059200, "source": {"type": "git", "url": "https://github.com/Example/ai-code",
            "commit": "d" * 40, "path": "published/dsh/ai-one/1.0.1"}}])
        self.assertEqual(entry["icon"], "https://raw.githubusercontent.com/Example/ai-code/" + "d" * 40 + "/published/dsh/ai-one/1.0.1/assets/icon.svg")
        pointer = json.loads(final[distribution.INDEX_PATH])["plugins"]["ai-one"]
        self.assertEqual(pointer["git_revisions"], {"codex": "d" * 40, "dsh": "d" * 40})
        from plugin_tools import markets
        scratch = self.case.base / "checked-distribution"
        scratch.mkdir()
        shutil.copytree(self.case.output / "packages", scratch / "dist")
        hosts, captured = markets._validate_dist(scratch, [self.case.spec()])
        self.assertEqual(hosts, {"claude", "codex", "zcode", "dsh"})
        self.assertIn("dist/dsh/ai-one-1.0.1.tgz", captured)
        record["git_installs"]["dsh"]["revision"] = "e" * 40
        record["git_installs"]["codex"]["revision"] = "d" * 40
        with self.assertRaisesRegex(io.DataError, "share one"):
            distribution._record(record, "stable", record["repository"])
