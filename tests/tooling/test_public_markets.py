"""Public markets use frozen formal state, never a developer's dist or version."""

from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from plugin_tools import io, markets
from tests.tooling.test_registry import add_plugin, write_json
from tests.tooling import test_release as release_fixtures
from tests.tooling import test_distribution as hosted_fixtures
from plugin_tools.registry import load_catalog
from plugin_tools.release import prepare_release
from plugin_tools import distribution

ROOT = Path(__file__).resolve().parents[2]
PATHS = {"claude": ".claude-plugin/marketplace.json",
         "codex": ".agents/plugins/marketplace.json", "zcode": "marketplace.json"}


class PublicMarketTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "repo"
        add_plugin(self.root, hosts=("claude", "codex", "zcode"))
        product_path = self.root / "plugins/ai-one/product.json"
        product = json.loads(product_path.read_text())
        product["repository"] = "https://github.com/Example/ai-code"
        write_json(product_path, product)
        write_json(self.root / "catalog.json", {"schema_version": 1,
            "plugins": [{"path": "plugins/ai-one"}]})
        write_json(self.root / "distribution.json", dict(json.loads((ROOT / "distribution.json").read_text()), identity_replacements={}))
        files = {}
        for host, path in PATHS.items():
            market = {"name": "ai-code", "plugins": []}
            if host == "claude":
                market["owner"] = {"name": "ai-code"}
            files[path] = io.dump_json(market)
        files["published/index.json"] = io.dump_json({"schema_version": 2, "plugins": {}})
        files["published/marketplaces.lock.json"] = io.dump_json({"schema_version": 1,
            "files": {path: io.sha256(raw) for path, raw in files.items() if path in PATHS.values()}})
        for path, raw in files.items():
            target = self.root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)

    def snapshot(self):
        return {path.relative_to(self.root).as_posix(): path.read_bytes()
                for path in self.root.rglob("*") if path.is_file()}

    def test_public_check_needs_no_dist_and_excludes_development_candidates(self):
        before = self.snapshot()
        result = markets.sync_markets(self.root, check=True)
        self.assertTrue(result["ok"], result)
        self.assertFalse((self.root / "dist").exists())
        self.assertEqual(self.snapshot(), before)

    def test_default_sync_cannot_replace_public_root_with_development_output(self):
        before = self.snapshot()
        with self.assertRaises(io.ToolError):
            markets.sync_markets(self.root)
        self.assertEqual(self.snapshot(), before)

    def test_cli_migrates_exact_owned_development_snapshot_to_empty_public_market(self):
        from plugin_tools.registry import load_catalog
        for path in ("published/index.json", "published/marketplaces.lock.json"):
            (self.root / path).unlink()
        (self.root / "published").rmdir()
        legacy = {path: io.dump_json(markets._project_market(load_catalog(self.root), host))
                  for host, path in PATHS.items()}
        for path, raw in legacy.items():
            (self.root / path).write_bytes(raw)
        (self.root / "marketplaces.lock.json").write_bytes(io.dump_json({"schema_version": 1,
            "files": {path: io.sha256(raw) for path, raw in legacy.items()}}))
        result = subprocess.run([sys.executable, str(ROOT / "tooling/plugin_tool.py"),
            "marketplace", "initialize", "--migrate", "--root", str(self.root)],
            capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads((self.root / "published/index.json").read_text())["plugins"], {})
        self.assertFalse((self.root / "marketplaces.lock.json").exists())
        for path in PATHS.values():
            self.assertEqual(json.loads((self.root / path).read_text())["plugins"], [])


class FrozenPublicSourceTests(unittest.TestCase):
    accepted_hosts = ("claude", "codex", "zcode")
    unverified_hosts = ()

    def setUp(self):
        self.case = release_fixtures.ReleaseTests()
        self.case.setUp()
        self.addCleanup(self.case.doCleanups)
        self.root = self.case.root
        product_path = self.case.plugin / "product.json"
        product = json.loads(product_path.read_text())
        product["repository"] = "https://github.com/Example/ai-code"
        write_json(product_path, product)
        self.configure_source()
        write_json(self.root / "distribution.json", dict(json.loads((ROOT / "distribution.json").read_text()), identity_replacements={}))
        # Actual private fixture evidence is verified once, and never enters Git.
        self.case.accept(hosts=(*self.accepted_hosts, *self.unverified_hosts))
        for host in self.unverified_hosts:
            path = self.case.plugin / f"release/{host}-accepted.json"
            evidence = json.loads(path.read_text())
            evidence.update(status="unverified", host_version=None, artifacts=[])
            write_json(path, evidence)
        (self.root / ".gitignore").write_text("plugins/*/release/*-raw.txt\nplugins/*/release/*-accepted.json\n")
        self.git("init", "-b", "main")
        self.git("config", "user.name", "Fixture")
        self.git("config", "user.email", "fixture@example.invalid")
        self.commit("frozen public source")
        self.source = self.git("rev-parse", "HEAD")
        self.git("tag", "ai-one/v1.0.0")
        spec = load_catalog(self.root)[0]
        report = prepare_release(self.root, spec, self.case.output, mode="stable")
        self.assertTrue(report["ok"], report)
        info = hosted_fixtures.HostedMarketTests().info(spec, self.case.output)
        plan = distribution.plan_distribution(self.root, spec, self.case.output, info,
            "stable", base_commit=self.source)
        self.write(distribution.stage_files(plan))
        self.commit("installable bytes")
        self.installation = self.git("rev-parse", "HEAD")
        self.write(distribution.finalize_files(plan, self.installation))
        self.commit("public market")

    def configure_source(self):
        pass

    def git(self, *arguments):
        result = subprocess.run(["git", *arguments], cwd=self.root, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def commit(self, message):
        self.git("add", ".")
        self.git("commit", "-m", message)

    def write(self, files):
        for staged in self.root.glob("published/staged/*/*.json"):
            if staged.relative_to(self.root).as_posix() not in files:
                staged.unlink()
        for path, raw in files.items():
            target = self.root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)

    def test_public_source_and_pinned_bytes_check_without_private_host_logs(self):
        for path in self.case.plugin.glob("release/*-raw.txt"):
            path.unlink()
        for path in self.case.plugin.glob("release/*-accepted.json"):
            path.unlink()
        before = markets.read_public_files(self.root)
        record = json.loads(before["published/releases/ai-one/1.0.0.json"])
        self.assertEqual(record["readiness"]["accepted_hosts"], sorted(self.accepted_hosts))
        self.assertEqual(record["readiness"]["pending_acceptance"],
                         sorted(set(PATHS) - set(self.accepted_hosts)))
        self.assertTrue(markets.check_public_markets(self.root)["ok"])
        self.assertEqual(markets.read_public_files(self.root), before)

    def test_rehashed_old_installer_digest_cannot_change_the_frozen_source(self):
        record_path = self.root / "published/releases/ai-one/1.0.0.json"
        record = json.loads(record_path.read_text())
        record["hosts"]["claude"]["asset"]["sha256"] = "0" * 64
        record_path.write_bytes(io.dump_json(record))
        index_path = self.root / "published/index.json"
        index = json.loads(index_path.read_text())
        index["plugins"]["ai-one"]["installers"]["claude"] = "0" * 64
        index_path.write_bytes(io.dump_json(index))
        native_path = self.root / PATHS["claude"]
        native = json.loads(native_path.read_text())
        native["plugins"][0]["source"]["sha256"] = "0" * 64
        native_path.write_bytes(io.dump_json(native))
        lock_path = self.root / "published/marketplaces.lock.json"
        lock = json.loads(lock_path.read_text())
        lock["files"][PATHS["claude"]] = io.sha256(native_path.read_bytes())
        lock["published_index_sha256"] = io.sha256(index_path.read_bytes())
        lock_path.write_bytes(io.dump_json(lock))
        with self.assertRaisesRegex(io.DataError, "installer"):
            markets.check_public_markets(self.root)

    def test_frozen_acceptance_rejects_missing_extra_and_invalid_slots(self):
        read_json = io.read_json
        config = json.loads((self.case.plugin / "release.json").read_text())
        slots = config["acceptance"]
        invalid = [None, [], {host: value for host, value in slots.items() if host != "claude"},
                   {**slots, "unknown": None}, {**slots, "claude": True},
                   {**slots, "claude": ""}, {**slots, "claude": "../private.json"},
                   {**slots, "claude": "/private/evidence.json"}]
        for acceptance in invalid:
            with self.subTest(acceptance=acceptance):
                def corrupt_config(root, relative, *, boundary_root=None):
                    if relative == "release.json":
                        return {**config, "acceptance": acceptance}, b""
                    return read_json(root, relative, boundary_root=boundary_root)

                with mock.patch.object(io, "read_json", side_effect=corrupt_config):
                    with self.assertRaises(io.DataError):
                        markets.check_public_markets(self.root)


class PendingFrozenPublicSourceTests(FrozenPublicSourceTests):
    accepted_hosts = ()

    def test_null_slot_cannot_claim_host_acceptance(self):
        path = self.root / "published/releases/ai-one/1.0.0.json"
        record = json.loads(path.read_text())
        record["readiness"]["accepted_hosts"] = ["claude"]
        record["readiness"]["pending_acceptance"] = ["codex", "zcode"]
        write_json(path, record)
        with self.assertRaisesRegex(io.DataError, "accepted host.*evidence"):
            markets.check_public_markets(self.root)


class MixedFrozenPublicSourceTests(FrozenPublicSourceTests):
    accepted_hosts = ("claude",)


class UnverifiedFrozenPublicSourceTests(FrozenPublicSourceTests):
    accepted_hosts = ("claude", "codex")
    unverified_hosts = ("zcode",)

class PendingDistributionSourceTests(unittest.TestCase):
    def test_D_pending_passes_independent_source_check_and_tampered_receipt_fails(self):
        case = FrozenPublicSourceTests()
        case.setUp()
        self.addCleanup(case.doCleanups)
        pending = markets._public_files_at(case.root, case.installation)
        current = markets.read_public_files(case.root)
        for path in set(current) - set(pending):
            (case.root / path).unlink()
        case.write(pending)
        result = markets.check_public_markets(case.root)
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["pending_distributions"], [{"product_id": "ai-one", "version": "1.0.0", "source_revision": case.source, "receipt": "published/staged/ai-one/1.0.0.json"}])
        self.assertEqual(result["remote_release_verification"], "not_performed")
        path = "published/staged/ai-one/1.0.0.json"
        receipt = json.loads(pending[path])
        receipt["plan_hash"] = "f" * 64
        (case.root / path).write_bytes(io.dump_json(receipt))
        with self.assertRaisesRegex(io.DataError, "reviewed original plan"):
            markets.check_public_markets(case.root)
        (case.root / path).unlink()
        with self.assertRaisesRegex(io.DataError, "unknown, missing"):
            markets.check_public_markets(case.root)
