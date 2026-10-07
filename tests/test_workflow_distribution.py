"""Public packaging must preserve the real workflow's standalone commands."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins/ai-code-workflow"


class WorkflowDistributionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.dist = self.base / "dist"

    def command(self, tool, *args):
        return subprocess.run([sys.executable, str(tool), *map(str, args)],
                              capture_output=True, text=True, timeout=40)

    def build(self):
        result = self.command(ROOT / "tooling/plugin_tool.py", "build", "--plugin",
                              "ai-code-workflow", "--host", "all", "--output", self.dist)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_public_packages_satisfy_the_workflow_specific_checker(self):
        self.build()
        for host in ("zcode", "codex"):
            with self.subTest(host=host):
                package = self.dist / host / "ai-code-workflow"
                result = self.command(PLUGIN / "scripts/workflow_tool.py", "package", "check",
                                      "--path", package, "--host", host)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertTrue(json.loads(result.stdout)["ok"])

    def test_packaged_tool_resolves_policies_and_creates_workspace_bound_tasks(self):
        self.build()
        package = self.dist / "codex/ai-code-workflow"
        tool = package / "tools/workflow_tool.py"
        workspace = self.base / "project"
        workspace.mkdir()
        result = self.command(tool, "policy", "resolve", "--plugin-root", package,
                              "--workspace", workspace)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        result = self.command(tool, "task", "create", "--workspace", workspace,
                              "--id", "migration-check", "--input",
                              package / "templates/task.json", "--apply")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        record = workspace / ".ai-workflow/tasks/migration-check/task.json"
        self.assertTrue(record.is_file())
        result = self.command(tool, "task", "check", "--workspace", workspace,
                              "--id", "migration-check")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(json.loads(result.stdout)["consistent"])


if __name__ == "__main__":
    unittest.main()
