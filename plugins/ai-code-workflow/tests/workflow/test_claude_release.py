"""Claude packages preserve workflow contracts and derive publisher metadata."""

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from workflow import build, package_check, product
from workflow.io import DataError


PLUGIN = Path(__file__).resolve().parents[2]
PUBLISHER = {"name": "Example Publisher", "url": "https://example.com/publisher"}
CLAUDE_AGENT = {
    "host": "claude",
    "template": "adapters/claude/agents/workflow-reviewer.md",
    "body": "skills/review/references/reviewer-contract.md",
    "target": "agents/workflow-reviewer.md",
}
ZCODE_AGENT = dict(CLAUDE_AGENT, host="zcode", template="adapters/zcode/agents/workflow-reviewer.md")


class ClaudeReleaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="workflow-claude-")
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.source = self.base / "source"
        shutil.copytree(PLUGIN, self.source, ignore=shutil.ignore_patterns("__pycache__", "tests"))
        adapter = self.source / "adapters/claude"
        (adapter / "agents").mkdir(parents=True, exist_ok=True)
        (adapter / "plugin.json").write_text(json.dumps({
            "description": "CodeVow workflow", "license": "MIT",
        }))
        (adapter / "marketplace.json").write_text(json.dumps({
            "name": "ai-code-workflow-local",
            "plugins": [{"name": "ai-code-workflow", "source": "./ai-code-workflow"}],
        }))
        self.template = adapter / "agents/workflow-reviewer.md"
        self.template.write_text(
            "---\nname: workflow-reviewer\ndescription: Read-only final review\n"
            "model: inherit\ntools: Read, Grep, Glob\nmaxTurns: 12\n---\n")
        self.manifest = self.source / "product.json"
        self.data = json.loads(self.manifest.read_text())
        self.data.update(hosts=["claude", "codex", "zcode"], publisher=PUBLISHER,
                         generated_agents=[CLAUDE_AGENT, ZCODE_AGENT])
        self.write_manifest()
        self.output = self.base / "dist"

    def write_manifest(self):
        self.manifest.write_text(json.dumps(self.data, indent=2) + "\n")

    def build(self, hosts):
        try:
            return build.build_packages(self.source, hosts, self.output)
        except DataError as exc:
            self.fail(f"valid Claude workflow source must build: {exc}")

    def test_claude_package_has_native_manifest_shared_reviewer_and_marketplace(self):
        self.build(["claude"])
        package = self.output / "claude/ai-code-workflow"
        manifest = json.loads((package / ".claude-plugin/plugin.json").read_text())
        self.assertEqual(manifest["name"], "ai-code-workflow")
        self.assertEqual(manifest["author"], PUBLISHER)
        reviewer = (package / "agents/workflow-reviewer.md").read_text()
        contract = (package / "skills/review/references/reviewer-contract.md").read_text()
        self.assertTrue(reviewer.endswith(contract.rstrip() + "\n"))
        self.assertIn("tools: Read, Grep, Glob\n", reviewer)
        self.assertIn("model: inherit\n", reviewer)
        market = json.loads((self.output / "claude/.claude-plugin/marketplace.json").read_text())
        self.assertEqual(market["owner"], PUBLISHER)
        self.assertEqual(market["plugins"][0]["source"], "./ai-code-workflow")
        self.assertTrue(package_check.check_package(package, "claude")["ok"])

    def test_declared_claude_subset_does_not_require_other_host_adapters(self):
        self.data.update(hosts=["claude"], generated_agents=[CLAUDE_AGENT])
        self.write_manifest()
        shutil.rmtree(self.source / "adapters/codex")
        shutil.rmtree(self.source / "adapters/zcode")
        self.build(["claude"])
        self.assertTrue(package_check.check_package(self.output / "claude/ai-code-workflow", "claude")["ok"])

    def test_all_hosts_derive_author_and_codex_developer_from_publisher(self):
        self.build(["claude", "codex", "zcode"])
        for host, relative in (("claude", ".claude-plugin/plugin.json"),
                               ("codex", "plugin.json"), ("zcode", ".zcode-plugin/plugin.json")):
            manifest = json.loads((self.output / host / "ai-code-workflow" / relative).read_text())
            self.assertEqual(manifest["author"], PUBLISHER, host)
        codex = json.loads((self.output / "codex/ai-code-workflow/plugin.json").read_text())
        self.assertEqual(codex["extensions"]["com.openai"]["interface"]["developerName"], "Example Publisher")

    def test_claude_checker_rejects_write_tools_even_if_artifact_is_resealed(self):
        self.build(["claude"])
        package = self.output / "claude/ai-code-workflow"
        agent = package / "agents/workflow-reviewer.md"
        agent.write_text(agent.read_text().replace("Read, Grep, Glob", "Read, Grep, Write"))
        artifact_path = package / "artifact.json"
        artifact = json.loads(artifact_path.read_text())
        from workflow import io
        artifact["files"] = [[relative, io.sha256_file(package / relative)] for relative, _ in artifact["files"]]
        artifact["content_hash"] = io.sha256_bytes(io.canonical_json(artifact["files"]))
        artifact_path.write_text(json.dumps(artifact))
        result = package_check.check_package(package, "claude")
        self.assertFalse(result["ok"])
        self.assertTrue(any("Read/Grep/Glob" in problem for problem in result["problems"]), result)

    def test_packaged_claude_tool_resolves_policy_without_original_source(self):
        self.build(["claude"])
        package = self.output / "claude/ai-code-workflow"
        shutil.rmtree(self.source)
        workspace = self.base / "project"
        workspace.mkdir()
        result = subprocess.run([sys.executable, str(package / "tools/workflow_tool.py"),
                                 "policy", "resolve", "--plugin-root", str(package),
                                 "--workspace", str(workspace)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(json.loads(result.stdout)["effective_policy"]["mode"], "collaborative")

    def test_invalid_publisher_does_not_pass_source_validation(self):
        self.data["publisher"] = {"name": "", "url": "https://example.com"}
        self.write_manifest()
        with self.assertRaises(DataError):
            product.load_product(self.source)

    def test_release_icon_cannot_disappear_from_a_resealed_claude_package(self):
        self.build(["claude"])
        package = self.output / "claude/ai-code-workflow"
        (package / "assets/codevow.svg").unlink()
        artifact_path = package / "artifact.json"
        artifact = json.loads(artifact_path.read_text())
        artifact["files"] = [entry for entry in artifact["files"] if entry[0] != "assets/codevow.svg"]
        from workflow import io
        artifact["content_hash"] = io.sha256_bytes(io.canonical_json(artifact["files"]))
        artifact_path.write_text(json.dumps(artifact))
        result = package_check.check_package(package, "claude")
        self.assertFalse(result["ok"], "release packages must preserve required branded assets")
        self.assertTrue(any("assets/codevow.svg" in problem for problem in result["problems"]), result)

    def test_publisher_limits_reject_insecure_urls_and_oversized_names(self):
        for publisher in ({"name": "Publisher", "url": "http://example.com"},
                          {"name": "x" * 121}, {"name": "Publisher", "url": "https://example.com:invalid"}):
            with self.subTest(publisher=publisher):
                self.data["publisher"] = publisher
                self.write_manifest()
                with self.assertRaises(DataError):
                    product.load_product(self.source)

    def test_declared_publisher_contact_is_preserved_in_native_author(self):
        self.data["publisher"] = dict(PUBLISHER, email="publisher@example.com")
        self.write_manifest()
        self.build(["claude"])
        manifest = json.loads((self.output / "claude/ai-code-workflow/.claude-plugin/plugin.json").read_text())
        self.assertEqual(manifest["author"]["email"], "publisher@example.com")


if __name__ == "__main__":
    unittest.main()
