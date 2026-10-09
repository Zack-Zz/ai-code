"""Static contract and public-tool fixture checks; these do not prove host behavior."""
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

PLUGIN = Path(__file__).resolve().parents[1]
REPO = PLUGIN.parents[1]
sys.path.insert(0, str(REPO / "tooling"))
from plugin_tools.registry import load_product
from plugin_tools.rendering import package_files
from plugin_tools.release.metadata import capture_release, validate_listing


class PluginContractTests(unittest.TestCase):
    def test_task_spec_example_matches_frozen_consumer_fields(self):
        text = (PLUGIN / "skills/agent-delegation/references/handoff-contract.md").read_text()
        examples = re.findall(r"```json\n(.*?)\n```", text, re.S)
        spec = json.loads(examples[0])
        self.assertEqual("1", spec["taskSpecVersion"])
        self.assertEqual({"taskSpecVersion", "objective", "acceptanceCriteria", "constraints", "writeScope", "contextRefs", "scopeReference", "verificationIds"}, set(spec))

    def test_three_host_shared_bytes_and_release_candidate(self):
        spec = load_product(PLUGIN)
        self.assertEqual(["claude", "codex", "zcode"], spec.hosts)
        self.assertEqual(["agent-delegation"], spec.all_skills)
        packages = [package_files(spec, host) for host in spec.hosts]
        for target in ("skills/agent-delegation/SKILL.md", "tools/bridge_client.py"):
            self.assertEqual(1, len({files[target] for files in packages}))
        validate_listing(spec)
        capture = capture_release(spec)
        self.assertEqual({"claude", "codex", "zcode"}, set(capture.pending))
        self.assertEqual({}, capture.accepted)

    def test_implicit_loading_is_narrow_and_not_execution_authority(self):
        entry = json.loads((PLUGIN / "adapters/codex/interfaces.json").read_text())["skills"]["agent-delegation"]
        self.assertTrue(entry["allow_implicit_invocation"])
        text = (PLUGIN / "skills/agent-delegation/SKILL.md").read_text()
        description = text.split("description: ", 1)[1].splitlines()[0]
        for clause in ("current human explicitly", "natural language", "Ordinary development", "native subagents", "quoted"):
            self.assertIn(clause, description)
        for clause in ("approved=true", "--last", "unverified", "scopeReference", "requestId", "原生 MCP", "不强制 review", "取消请求成功不等于进程停止"):
            self.assertIn(clause, text)
        for host in ("claude", "codex", "zcode"):
            adapter = json.loads((PLUGIN / "adapters" / host / "plugin.json").read_text())
            self.assertFalse(set(adapter) & {"mcpServers", "hooks", "apps", "commands", "agents", "version"})

    def test_public_validate_accepts_plugin_in_temporary_catalog(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            shutil.copytree(PLUGIN, root / "plugins/ai-agent-delegation", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            (root / "catalog.json").write_text(json.dumps({"schema_version": 1, "plugins": [{"path": "plugins/ai-agent-delegation"}]}))
            process = subprocess.run([sys.executable, "-B", str(REPO / "tooling/plugin_tool.py"), "--root", str(root), "validate", "--all"], capture_output=True, text=True)
            self.assertEqual(0, process.returncode, process.stdout + process.stderr)


if __name__ == "__main__":
    unittest.main()
