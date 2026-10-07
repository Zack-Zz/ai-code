"""The repository CLI exposes three-host builds and bounded release commands."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from .tooling.test_registry import TOOL, add_plugin, write_json
from .tooling.test_release import release_plugin
from plugin_tools.build import build_plugins
from plugin_tools.registry import load_catalog


class ThreeHostCommandTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.root = self.base / "repo"
        add_plugin(self.root, hosts=("claude",))
        write_json(self.root / "catalog.json", {
            "schema_version": 1, "plugins": [{"path": "plugins/ai-one"}],
        })

    def run_tool(self, *args):
        return subprocess.run([sys.executable, str(TOOL), *map(str, args), "--root", str(self.root)],
                              capture_output=True, text=True, timeout=30)

    def test_claude_build_and_check_are_available_through_cli(self):
        output = self.base / "dist"
        result = self.run_tool("build", "--plugin", "ai-one", "--host", "claude", "--output", output)
        self.assertEqual(result.returncode, 0, result.stderr)
        result = self.run_tool("package", "check", "--path", output / "claude/ai-one", "--host", "claude")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(json.loads(result.stdout)["ok"])

    def test_all_uses_the_declared_claude_host_instead_of_fixed_old_hosts(self):
        output = self.base / "dist"
        result = self.run_tool("build", "--plugin", "ai-one", "--host", "all", "--output", output)
        self.assertEqual(result.returncode, 0, result.stderr)
        index = json.loads((output / "index.json").read_text())
        self.assertEqual(set(index["hosts"]), {"claude"})

    def test_marketplace_sync_command_projects_a_built_native_package(self):
        build_plugins(self.root, load_catalog(self.root), self.root / "dist", hosts=("claude",))
        result = self.run_tool("marketplace", "sync")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        market = json.loads((self.root / ".claude-plugin/marketplace.json").read_text())
        self.assertEqual(market["plugins"][0]["source"], "./dist/claude/ai-one")
        result = self.run_tool("marketplace", "sync", "--check")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)


class ReleaseCommandTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.root = self.base / "repo"
        release_plugin(self.root)

    def run_tool(self, *args):
        return subprocess.run([sys.executable, str(TOOL), *map(str, args), "--root", str(self.root)],
                              capture_output=True, text=True, timeout=30)

    def test_release_check_reports_draft_and_stable_qualification_separately(self):
        draft = self.run_tool("release", "check", "--plugin", "ai-one", "--mode", "draft")
        self.assertEqual(draft.returncode, 0, draft.stdout + draft.stderr)
        self.assertFalse(json.loads(draft.stdout)["publication_ready"])
        stable = self.run_tool("release", "check", "--plugin", "ai-one", "--mode", "stable")
        self.assertEqual(stable.returncode, 1, stable.stdout + stable.stderr)
        self.assertTrue(json.loads(stable.stdout)["blockers"])

    def test_release_prepare_and_verify_commands_do_not_publish_or_mutate_source(self):
        before = {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        bundle = self.base / "bundle"
        built = self.run_tool("release", "prepare", "--plugin", "ai-one", "--output", bundle)
        self.assertEqual(built.returncode, 0, built.stdout + built.stderr)
        verified = self.run_tool("release", "verify", "--plugin", "ai-one", "--path", bundle)
        self.assertEqual(verified.returncode, 0, verified.stdout + verified.stderr)
        self.assertFalse(json.loads(verified.stdout)["publication_ready"])
        after = {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
