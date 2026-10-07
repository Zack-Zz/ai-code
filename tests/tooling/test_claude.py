"""Three-host packages preserve common resources and distinct native metadata."""

import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest
import zipfile

try:
    from .test_registry import add_plugin, write_json
except ImportError:
    from test_registry import add_plugin, write_json

from plugin_tools import io
from plugin_tools.build import build_plugins
from plugin_tools.package_check import check_package
from plugin_tools.registry import load_catalog
from plugin_tools.rendering import package_files


class ClaudePackagingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="claude-packaging-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / "repo"
        self.plugin = add_plugin(self.root, hosts=("claude", "codex", "zcode"), skills=("ask",))
        self.publisher = {"name": "Example Publisher", "url": "https://example.com/publisher", "email": "dev@example.com"}
        self.manifest = json.loads((self.plugin / "product.json").read_text())
        self.manifest["publisher"] = self.publisher
        self.manifest["generated_agents"] = []
        (self.plugin / "agent-body.md").write_text("Review the common evidence.\n")
        self.manifest["resources"].append({"source": "agent-body.md", "target": "shared/agent-body.md", "include": []})
        for host in ("claude", "zcode"):
            template = self.plugin / f"adapters/{host}/agents/reviewer.md"
            template.parent.mkdir(parents=True)
            template.write_text(f"---\nname: reviewer\ndescription: {host} reviewer\nmodel: inherit\n---\nDiscard template body.\n")
            self.manifest["generated_agents"].append({
                "host": host, "template": f"adapters/{host}/agents/reviewer.md",
                "body": "agent-body.md", "target": "agents/reviewer.md",
            })
        self.save_manifest()
        write_json(self.root / "catalog.json", {"schema_version": 1,
                                               "plugins": [{"path": "plugins/ai-one"}]})
        self.output = self.base / "dist"

    def save_manifest(self):
        write_json(self.plugin / "product.json", self.manifest)

    def build(self):
        specs = self.load_valid_catalog()
        build_plugins(self.root, specs, self.output)
        return specs

    def load_valid_catalog(self):
        try:
            return load_catalog(self.root)
        except io.DataError as exc:
            self.fail(f"valid declared plugin should load: {exc}")

    def test_three_native_layouts_keep_common_resource_bytes_and_independent_author(self):
        specs = self.build()
        self.assertEqual(set(json.loads((self.output / "index.json").read_text())["hosts"]), {"claude", "codex", "zcode"})
        paths = {"claude": ".claude-plugin/plugin.json", "codex": "plugin.json", "zcode": ".zcode-plugin/plugin.json"}
        for host, native in paths.items():
            with self.subTest(host=host):
                package = self.output / host / "ai-one"
                manifest = json.loads((package / native).read_text())
                self.assertEqual((manifest["name"], manifest["version"], manifest["author"]),
                                 ("ai-one", "1.0.0", self.publisher))
                for relative in ("README.md", "skills/ask/SKILL.md", "shared/agent-body.md"):
                    self.assertEqual((package / relative).read_bytes(), (self.output / "codex/ai-one" / relative).read_bytes())
                for other in set(paths.values()) - {native}:
                    self.assertFalse((package / other).exists())
                self.assertTrue(check_package(package, host, specs[0])["ok"])
        for host in ("claude", "zcode"):
            agent = self.output / host / "ai-one/agents/reviewer.md"
            self.assertEqual(agent.read_text(), f"---\nname: reviewer\ndescription: {host} reviewer\nmodel: inherit\n---\n\nReview the common evidence.\n")
        self.assertFalse((self.output / "claude/ai-one/skills/ask/agents/openai.yaml").exists())
        self.assertTrue((self.output / "codex/ai-one/skills/ask/agents/openai.yaml").exists())

    def test_claude_market_owner_is_collection_and_archive_is_single_plugin(self):
        specs = self.build()
        relative = ".claude-plugin/marketplace.json"
        market = json.loads((self.output / "claude" / relative).read_text())
        self.assertEqual(market, {"name": "ai-code-local", "owner": {"name": "ai-code"}, "plugins": [
            {"name": "ai-one", "version": "1.0.0", "source": "./ai-one", "description": "AI capability ai-one"}
        ]})
        with zipfile.ZipFile(self.output / "claude/ai-one-1.0.0.zip") as archive:
            self.assertTrue(all(name.startswith("ai-one/") or name == relative for name in archive.namelist()))
            self.assertEqual(json.loads(archive.read(relative)), market)
            extracted = self.base / "extracted"
            archive.extractall(extracted)
        self.assertTrue(check_package(extracted / "ai-one", "claude", specs[0])["ok"])
        market["owner"]["name"] = "Example Publisher"
        write_json(self.output / "claude" / relative, market)
        self.assertFalse(check_package(self.output / "claude/ai-one", "claude", specs[0])["ok"])

    def test_claude_only_skill_plugin_needs_no_codex_interfaces(self):
        self.manifest["hosts"] = ["claude"]
        self.manifest["generated_agents"] = [entry for entry in self.manifest["generated_agents"] if entry["host"] == "claude"]
        self.save_manifest()
        (self.plugin / "adapters/codex/interfaces.json").unlink()
        self.build()
        index = json.loads((self.output / "index.json").read_text())
        self.assertEqual(set(index["hosts"]), {"claude"})
        self.assertEqual(set(index["plugins"]["ai-one"]["hosts"]), {"claude"})

    def test_minimal_claude_host_is_supported_without_publisher_or_agents(self):
        self.manifest["hosts"] = ["claude"]
        self.manifest.pop("publisher")
        self.manifest["generated_agents"] = []
        self.save_manifest()
        self.build()
        self.assertTrue((self.output / "claude/ai-one/.claude-plugin/plugin.json").is_file())

    def test_publisher_injection_does_not_mutate_nested_adapter_or_captured_inputs(self):
        adapter_path = self.plugin / "adapters/claude/plugin.json"
        data = json.loads(adapter_path.read_text())
        data.update(author={"name": "Template Author"}, metadata={"labels": ["example"]})
        write_json(adapter_path, data)
        spec = self.load_valid_catalog()[0]
        before = copy.deepcopy((spec.manifest, spec.adapters, spec.inputs))
        for host in ("claude", "codex", "zcode"):
            rendered = package_files(spec, host)
            native = {"claude": ".claude-plugin/plugin.json", "codex": "plugin.json", "zcode": ".zcode-plugin/plugin.json"}[host]
            self.assertEqual(json.loads(rendered[native])["author"], self.publisher)
        self.assertEqual((spec.manifest, spec.adapters, spec.inputs), before)

    def test_invalid_publisher_fields_fail_source_validation(self):
        invalid = [None, {}, {"name": " "}, {"name": "x" * 121}, {"name": 7},
                   {"name": "Example", "version": "2.0.0"},
                   {"name": "Example", "url": "http://example.com"},
                   {"name": "Example", "url": "https:///missing-host"},
                   {"name": "Example", "url": "https://example.com/" + "x" * 2048},
                   {"name": "Example", "email": "bad-email"},
                   {"name": "Example", "email": "a" * 321 + "@example.com"}]
        for publisher in invalid:
            with self.subTest(publisher=publisher):
                self.manifest["publisher"] = publisher
                self.save_manifest()
                with self.assertRaisesRegex(io.DataError, "publisher"):
                    load_catalog(self.root)

    def test_codex_developer_name_comes_from_publisher_without_mutating_adapter(self):
        adapter_path = self.plugin / "adapters/codex/plugin.json"
        adapter = json.loads(adapter_path.read_text())
        adapter["extensions"] = {"com.openai": {"interface": {
            "displayName": "Example", "developerName": "Stale Template Publisher"}}}
        write_json(adapter_path, adapter)
        for name in ("Example Publisher", "Changed Publisher"):
            with self.subTest(name=name):
                self.manifest["publisher"]["name"] = name
                self.save_manifest()
                spec = self.load_valid_catalog()[0]
                original = copy.deepcopy((spec.manifest, spec.adapters, spec.inputs))
                rendered = json.loads(package_files(spec, "codex")["plugin.json"])
                self.assertEqual(rendered["extensions"]["com.openai"]["interface"]["developerName"], name)
                self.assertEqual(rendered["author"]["name"], name)
                self.assertEqual((spec.manifest, spec.adapters, spec.inputs), original)

    def test_claude_display_name_comes_from_product_without_changing_machine_identity(self):
        self.manifest["display_name"] = "Example AI Assistant"
        self.save_manifest()
        spec = self.load_valid_catalog()[0]
        original = copy.deepcopy(spec.adapters)
        rendered = json.loads(package_files(spec, "claude")[".claude-plugin/plugin.json"])
        self.assertEqual(rendered.get("displayName"), "Example AI Assistant")
        self.assertEqual(rendered["name"], "ai-one")
        self.assertEqual(spec.adapters, original)

    def test_unexpected_native_manifest_cannot_hide_in_claude_package(self):
        spec = self.build()[0]
        package = self.output / "claude/ai-one"
        write_json(package / "plugin.json", {"name": "ai-one", "version": "1.0.0"})
        checked = check_package(package, "claude", spec)
        self.assertFalse(checked["ok"])
        self.assertTrue(any("plugin.json" in problem for problem in checked["problems"]))

    def test_existing_host_subset_is_still_buildable_with_all_default_hosts(self):
        self.manifest["hosts"] = ["codex", "zcode"]
        self.manifest["generated_agents"] = [entry for entry in self.manifest["generated_agents"] if entry["host"] == "zcode"]
        self.manifest.pop("publisher")
        self.save_manifest()
        self.build()
        index = json.loads((self.output / "index.json").read_text())
        self.assertEqual(set(index["hosts"]), {"codex", "zcode"})
        self.assertNotIn("author", json.loads((self.output / "codex/ai-one/plugin.json").read_text()))


if __name__ == "__main__":
    unittest.main()
