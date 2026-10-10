"""Registry boundaries exercised through the real repository CLI."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tooling"))
from plugin_tools import io
from plugin_tools.registry import load_catalog

TOOL = Path(__file__).resolve().parents[2] / "tooling/plugin_tool.py"


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def add_plugin(root, name="ai-one", version="1.0.0", hosts=None, skills=()):
    path = root / "plugins" / name
    hosts = list(hosts or ("codex", "zcode"))
    manifest = {
        "schema_version": 1, "product_id": name, "display_name": name,
        "version": version, "repository": "https://example.com/ai",
        "license": "MIT", "hosts": hosts,
        "core_skills": list(skills), "resources": [
            {"source": "README.md", "target": "README.md", "include": []}
        ],
    }
    write_json(path / "product.json", manifest)
    (path / "README.md").write_text(f"Plugin {name}\n", encoding="utf-8")
    for host in hosts:
        write_json(path / "adapters" / host / "plugin.json", {
            "name": name, "version": version, "description": f"AI capability {name}",
            "license": "MIT",
        })
    if skills:
        for skill in skills:
            skill_file = path / "skills" / skill / "SKILL.md"
            skill_file.parent.mkdir(parents=True)
            skill_file.write_text(f"---\nname: {skill}\ndescription: Useful AI skill\n---\nUse {skill}.\n")
        if "codex" in hosts:
            write_json(path / "adapters/codex/interfaces.json", {
                "schema_version": 1, "skills": {
                    skill: {"display_name": skill, "short_description": "AI capability",
                            "brand_color": "#2563EB", "default_prompt": "Use this AI skill.",
                            "allow_implicit_invocation": True}
                    for skill in skills
                },
            })
    return path


class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="plugin-registry-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.first = add_plugin(self.root)
        self.second = add_plugin(self.root, "ai-two", "3.2.1", hosts=("codex",))
        write_json(self.root / "catalog.json", {"schema_version": 1, "plugins": [
            {"path": "plugins/ai-one"}, {"path": "plugins/ai-two"},
        ]})

    def run_tool(self, *args):
        return subprocess.run([sys.executable, str(TOOL), *args, "--root", str(self.root)],
                              capture_output=True, text=True, timeout=30)

    def test_list_reads_independent_identity_and_host_support(self):
        result = self.run_tool("list")
        self.assertEqual(result.returncode, 0, result.stderr)
        plugins = json.loads(result.stdout)["plugins"]
        self.assertEqual([(p["product_id"], p["version"], p["hosts"]) for p in plugins],
                         [("ai-one", "1.0.0", ["codex", "zcode"]), ("ai-two", "3.2.1", ["codex"])])

    def test_validate_does_not_require_workflow_resources(self):
        result = self.run_tool("validate", "--all")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)["ok"])

    def test_catalog_accepts_preview_versions(self):
        add_plugin(self.root, version="1.0.4-preview.10")
        self.assertEqual(load_catalog(self.root)[0].version, "1.0.4-preview.10")

    def test_catalog_rejects_version_leading_zeroes(self):
        for version in ("01.0.4", "1.00.4", "1.0.04", "1.0.4-preview.01"):
            with self.subTest(version=version):
                add_plugin(self.root, version=version)
                with self.assertRaisesRegex(io.DataError, "invalid product version"):
                    load_catalog(self.root)

    def test_catalog_rejects_escape_noncanonical_duplicate_and_overlap_paths(self):
        cases = ["../elsewhere", "/elsewhere", "plugins//ai-one", "plugins/./ai-one",
                 "plugins/ai-one/", "plugins\\ai-one", "other/ai-one", "plugins/ai-one/nested"]
        for invalid in cases:
            with self.subTest(path=invalid):
                write_json(self.root / "catalog.json", {"schema_version": 1, "plugins": [{"path": invalid}]})
                result = self.run_tool("validate", "--all")
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn("path", result.stderr)
        for paths in [("plugins/ai-one", "plugins/ai-one"),
                      ("plugins/ai-one", "plugins/ai-one/nested")]:
            write_json(self.root / "catalog.json", {"schema_version": 1, "plugins": [{"path": p} for p in paths]})
            result = self.run_tool("validate", "--all")
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertRegex(result.stderr, "duplicate|overlap|path")

    def test_rechecks_plugin_root_after_catalog_selection_without_following_replaced_symlink(self):
        specs = load_catalog(self.root)
        original = self.first.with_name("original")
        self.first.rename(original)
        self.first.symlink_to(original, target_is_directory=True)
        with self.assertRaisesRegex(io.DataError, "symlink"):
            io.read_file(specs[0].root, "README.md")

    def test_catalog_rejects_existing_plugin_outside_direct_plugins_namespace(self):
        outside = add_plugin(self.root / "other", "ai-three")
        write_json(self.root / "catalog.json", {"schema_version": 1, "plugins": [
            {"path": outside.relative_to(self.root).as_posix()},
        ]})
        result = self.run_tool("validate", "--all")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("path", result.stderr)

    def test_rejects_symlinked_plugin_and_resource(self):
        outside = self.root / "external.txt"
        outside.write_text("outside")
        (self.first / "README.md").unlink()
        (self.first / "README.md").symlink_to(outside)
        result = self.run_tool("validate", "--all")
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("symlink", result.stderr)
        (self.first / "README.md").unlink()
        (self.first / "README.md").write_text("restored")
        linked = self.root / "plugins/linked"
        linked.symlink_to(self.first, target_is_directory=True)
        write_json(self.root / "catalog.json", {"schema_version": 1, "plugins": [{"path": "plugins/linked"}]})
        result = self.run_tool("validate", "--all")
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("symlink", result.stderr)

    def test_rejects_duplicate_identity_and_unknown_selected_plugin(self):
        data = json.loads((self.second / "product.json").read_text())
        data["product_id"] = "ai-one"
        write_json(self.second / "product.json", data)
        result = self.run_tool("list")
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("duplicate", result.stderr)
        data["product_id"] = "ai-two"
        write_json(self.second / "product.json", data)
        result = self.run_tool("validate", "--plugin", "unknown")
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("unknown", result.stderr)

    def test_rejects_missing_resources_cache_registration_and_target_collisions(self):
        base = json.loads((self.first / "product.json").read_text())
        cases = [
            [{"source": "missing", "target": "missing", "include": []}],
            base["resources"] + [{"source": "README.md", "target": "README.md", "include": []}],
            [{"source": "README.md", "target": "__pycache__/readme.pyc", "include": []}],
            [{"source": "README.md", "target": "artifact.json", "include": []}],
            [{"source": "README.md", "target": "README.md/child", "include": []}] + base["resources"],
        ]
        for resources in cases:
            with self.subTest(resources=resources):
                write_json(self.first / "product.json", dict(base, resources=resources))
                result = self.run_tool("validate", "--all")
                self.assertEqual(result.returncode, 2, result.stderr)

    def test_generated_agent_parent_child_targets_fail_validation_before_build(self):
        template = self.first / "adapters/zcode/agents/template.md"
        template.parent.mkdir(parents=True)
        template.write_text("---\nname: helper\ndescription: AI helper\n---\n")
        (self.first / "body.md").write_text("Shared AI helper body.\n")
        data = json.loads((self.first / "product.json").read_text())
        data["generated_agents"] = [
            {"host": "zcode", "template": "adapters/zcode/agents/template.md",
             "body": "body.md", "target": target}
            for target in ("agents/a.md", "agents/a.md/b.md")
        ]
        write_json(self.first / "product.json", data)
        result = self.run_tool("validate", "--all")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("generated target path overlap", result.stderr)


if __name__ == "__main__":
    unittest.main()
