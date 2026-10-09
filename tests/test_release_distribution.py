"""Committed distribution checks support actual public and workflow three-host builds."""

import json
import hashlib
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
CHECKER = ROOT / ".github/scripts/check_dist.py"


class ReleaseDistributionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="release-dist-test-")
        cls.addClassCleanup(cls.temp.cleanup)
        cls.base = Path(cls.temp.name)
        for name, tool in (("public", ROOT / "tooling/plugin_tool.py"),
                           ("standalone", ROOT / "plugins/ai-code-workflow/scripts/workflow_tool.py")):
            command = [sys.executable, str(tool), "build"]
            if name == "public":
                command.append("--all")
            result = subprocess.run(command + ["--host", "all", "--output", str(cls.base / name)],
                                    capture_output=True, text=True, cwd=ROOT)
            if result.returncode != 0:
                raise AssertionError(f"actual {name} build failed: {result.stdout}{result.stderr}")

    def copied(self, kind):
        temp = tempfile.TemporaryDirectory(prefix="release-dist-copy-")
        self.addCleanup(temp.cleanup)
        base = Path(temp.name)
        committed, fresh = base / "committed", base / "fresh"
        shutil.copytree(self.base / kind, committed)
        shutil.copytree(self.base / kind, fresh)
        return committed, fresh

    def check(self, committed, fresh):
        return subprocess.run([sys.executable, str(CHECKER), "--committed", str(committed),
                               "--fresh", str(fresh)], capture_output=True, text=True)

    def test_public_three_host_distribution_passes_with_claude_native_market(self):
        committed, fresh = self.copied("public")
        index = json.loads((committed / "index.json").read_text())
        self.assertEqual(set(index["hosts"]), {"claude", "codex", "zcode"})
        self.assertTrue((committed / "claude/.claude-plugin/marketplace.json").is_file())
        result = self.check(committed, fresh)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_standalone_three_host_distribution_passes(self):
        committed, fresh = self.copied("standalone")
        index = json.loads((committed / "index.json").read_text())
        self.assertEqual(set(index["hosts"]), {"claude", "codex", "zcode"})
        result = self.check(committed, fresh)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_two_host_declared_distribution_subset_remains_valid(self):
        for kind in ("public", "standalone"):
            with self.subTest(kind=kind):
                committed, fresh = self.copied(kind)
                for root in (committed, fresh):
                    index = json.loads((root / "index.json").read_text())
                    index["hosts"].pop("claude")
                    if kind == "public":
                        for plugin in index["plugins"].values():
                            plugin["hosts"].pop("claude", None)
                    (root / "index.json").write_text(json.dumps(index))
                    shutil.rmtree(root / "claude")
                result = self.check(committed, fresh)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_empty_or_unknown_host_sets_are_rejected(self):
        for kind in ("public", "standalone"):
            for invalid in ({}, {"unknown": {}}):
                with self.subTest(kind=kind, hosts=invalid):
                    committed, fresh = self.copied(kind)
                    for root in (committed, fresh):
                        index = json.loads((root / "index.json").read_text())
                        index["hosts"] = invalid
                        (root / "index.json").write_text(json.dumps(index))
                    self.assertNotEqual(self.check(committed, fresh).returncode, 0)

    def test_claude_market_requires_the_actual_owner_even_when_consistently_rehashed(self):
        for kind in ("public", "standalone"):
            with self.subTest(kind=kind):
                committed, fresh = self.copied(kind)
                for root in (committed, fresh):
                    index = json.loads((root / "index.json").read_text())
                    market_entry = index["hosts"]["claude"]
                    market_path = root / market_entry["marketplace"]
                    market = json.loads(market_path.read_text())
                    market["owner"] = {"name": "foreign-market-owner"}
                    payload = (json.dumps(market, indent=2, sort_keys=True, ensure_ascii=True) + "\n").encode()
                    market_path.write_bytes(payload)
                    market_entry["marketplace_sha256"] = hashlib.sha256(payload).hexdigest()
                    package_entry = market_entry if kind == "standalone" else index["plugins"]["ai-code-workflow"]["hosts"]["claude"]
                    zipped = root / package_entry["zip"]
                    with zipfile.ZipFile(zipped) as source:
                        members = [(item, source.read(item)) for item in source.infolist()]
                    with zipfile.ZipFile(zipped, "w") as destination:
                        for item, data in members:
                            destination.writestr(item, payload if item.filename == ".claude-plugin/marketplace.json" else data)
                    package_entry["zip_sha256"] = hashlib.sha256(zipped.read_bytes()).hexdigest()
                    (root / "index.json").write_text(json.dumps(index))
                result = self.check(committed, fresh)
                self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn("owner", result.stdout + result.stderr)
