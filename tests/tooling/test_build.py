"""Independent plugins, aggregate markets, isolated downloads and trusted checking."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import zipfile

try:
    from .test_registry import TOOL, add_plugin, write_json
except ImportError:  # unittest discovery may choose tests/tooling as its top-level root.
    from test_registry import TOOL, add_plugin, write_json


def tree_bytes(root):
    return {path.relative_to(root).as_posix(): path.read_bytes()
            for path in root.rglob("*") if path.is_file()}


def rehash_artifact(package):
    """Model an attacker capable of rewriting every self-reported package hash."""
    artifact = json.loads((package / "artifact.json").read_text())
    artifact["files"] = [[path.relative_to(package).as_posix(), hashlib.sha256(path.read_bytes()).hexdigest()]
                         for path in sorted(package.rglob("*"))
                         if path.is_file() and path.name != "artifact.json"]
    raw = json.dumps(artifact["files"], sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()
    artifact["content_hash"] = hashlib.sha256(raw).hexdigest()
    write_json(package / "artifact.json", artifact)


class BuildTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="plugin-build-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "repo"
        self.first = add_plugin(self.root, skills=("ask",))
        self.second = add_plugin(self.root, "ai-two", "3.2.1", hosts=("codex",))
        write_json(self.root / "catalog.json", {"schema_version": 1, "plugins": [
            {"path": "plugins/ai-one"}, {"path": "plugins/ai-two"},
        ]})
        self.output = Path(self.temp.name) / "dist"

    def run_tool(self, *args):
        return subprocess.run([sys.executable, str(TOOL), *args, "--root", str(self.root)],
                              capture_output=True, text=True, timeout=30)

    def build(self, *selection, output=None, host="all"):
        result = self.run_tool("build", *(selection or ("--all",)), "--host", host,
                               "--output", str(output or self.output))
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads((Path(output or self.output) / "index.json").read_text())

    def check(self, package, host="codex", plugin=None):
        args = ["package", "check", "--path", str(package), "--host", host]
        if plugin:
            args += ["--plugin", plugin]
        return self.run_tool(*args)

    def test_aggregate_markets_and_index_use_independent_versions_and_supported_hosts(self):
        index = self.build()
        self.assertEqual(index["schema_version"], 2)
        self.assertEqual(set(index["plugins"]), {"ai-one", "ai-two"})
        self.assertEqual(index["plugins"]["ai-one"]["version"], "1.0.0")
        self.assertEqual(index["plugins"]["ai-two"]["version"], "3.2.1")
        self.assertEqual(set(index["plugins"]["ai-two"]["hosts"]), {"codex"})
        codex = json.loads((self.output / "codex/.agents/plugins/marketplace.json").read_text())
        zcode = json.loads((self.output / "zcode/marketplace.json").read_text())
        self.assertEqual(codex["name"], "ai-code-local")
        self.assertEqual([(e["name"], e["version"], e["source"]["path"]) for e in codex["plugins"]],
                         [("ai-one", "1.0.0", "./ai-one"), ("ai-two", "3.2.1", "./ai-two")])
        self.assertEqual([(e["name"], e["source"]) for e in zcode["plugins"]], [("ai-one", "./ai-one")])
        self.assertFalse((self.output / "zcode/ai-two").exists())
        for name in ("ai-one", "ai-two"):
            result = self.check(self.output / "codex" / name, plugin=name)
            self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
            self.assertTrue(json.loads(result.stdout)["ok"])

    def test_each_zip_contains_only_its_own_plugin_and_single_plugin_market(self):
        self.build()
        for host, name, version in (("codex", "ai-one", "1.0.0"),
                                    ("codex", "ai-two", "3.2.1"), ("zcode", "ai-one", "1.0.0")):
            with self.subTest(host=host, plugin=name):
                archive = self.output / host / f"{name}-{version}.zip"
                market_rel = ".agents/plugins/marketplace.json" if host == "codex" else "marketplace.json"
                with zipfile.ZipFile(archive) as zf:
                    names = zf.namelist()
                    self.assertTrue(all(member.startswith(name + "/") or member == market_rel for member in names))
                    self.assertEqual([e["name"] for e in json.loads(zf.read(market_rel))["plugins"]], [name])
                    extracted = Path(self.temp.name) / f"extract-{host}-{name}"
                    zf.extractall(extracted)
                result = self.check(extracted / name, host=host)
                self.assertEqual(result.returncode, 0, result.stderr + result.stdout)

    def test_selected_build_excludes_sibling_and_reproduces_identical_bytes(self):
        index = self.build("--plugin", "ai-two")
        self.assertEqual(set(index["plugins"]), {"ai-two"})
        self.assertEqual(set(index["hosts"]), {"codex"})
        self.assertFalse((self.output / "codex/ai-one").exists())
        again = Path(self.temp.name) / "again"
        self.build("--plugin", "ai-two", output=again)
        self.assertEqual(tree_bytes(self.output), tree_bytes(again))

    def test_sibling_changes_do_not_change_other_plugin_hashes(self):
        before = self.build()
        (self.second / "README.md").write_text("Changed sibling capability\n")
        data = json.loads((self.second / "product.json").read_text())
        write_json(self.second / "product.json", dict(data, version="4.0.0"))
        after = self.build(output=Path(self.temp.name) / "after")
        for host in ("codex", "zcode"):
            self.assertEqual(before["plugins"]["ai-one"]["hosts"][host]["package_content_hash"],
                             after["plugins"]["ai-one"]["hosts"][host]["package_content_hash"])
        self.assertEqual(before["plugins"]["ai-one"]["source_tree_hash"], after["plugins"]["ai-one"]["source_tree_hash"])
        self.assertNotEqual(before["plugins"]["ai-two"]["source_tree_hash"], after["plugins"]["ai-two"]["source_tree_hash"])

    def test_unsupported_host_and_occupied_or_symlink_output_leave_output_unchanged(self):
        result = self.run_tool("build", "--plugin", "ai-two", "--host", "zcode", "--output", str(self.output))
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertFalse(self.output.exists())
        self.output.mkdir()
        sentinel = self.output / "user.txt"
        sentinel.write_text("preserve user file")
        result = self.run_tool("build", "--all", "--output", str(self.output))
        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertEqual(sentinel.read_text(), "preserve user file")
        linked = Path(self.temp.name) / "linked"
        linked.symlink_to(self.output, target_is_directory=True)
        result = self.run_tool("build", "--all", "--output", str(linked))
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertIn("symlink", result.stderr)

    def test_checker_rejects_omission_and_modification_even_when_self_rehashed(self):
        self.build()
        package = self.output / "codex/ai-two"
        (package / "README.md").unlink()
        rehash_artifact(package)
        result = self.check(package)
        self.assertEqual(result.returncode, 1, result.stderr + result.stdout)
        self.assertIn("README.md", result.stdout)
        (package / "README.md").write_text("malicious rewritten resource")
        rehash_artifact(package)
        result = self.check(package)
        self.assertEqual(result.returncode, 1, result.stderr + result.stdout)
        self.assertIn("trusted", result.stdout)

    def test_checker_rejects_generated_native_manifest_and_interface_tampering(self):
        self.build()
        package = self.output / "codex/ai-one"
        manifest = json.loads((package / "plugin.json").read_text())
        write_json(package / "plugin.json", dict(manifest, description="foreign content"))
        rehash_artifact(package)
        result = self.check(package)
        self.assertEqual(result.returncode, 1, result.stderr + result.stdout)
        self.assertIn("plugin.json", result.stdout)
        interface = package / "skills/ask/agents/openai.yaml"
        interface.write_text(interface.read_text().replace("true", "false"))
        rehash_artifact(package)
        result = self.check(package)
        self.assertEqual(result.returncode, 1, result.stderr + result.stdout)
        self.assertIn("openai.yaml", result.stdout)

    def test_checker_rejects_market_path_rewrite_and_unregistered_active_files(self):
        self.build()
        package = self.output / "codex/ai-two"
        market_path = self.output / "codex/.agents/plugins/marketplace.json"
        market = json.loads(market_path.read_text())
        market["plugins"][1]["source"]["path"] = "./ai-one"
        write_json(market_path, market)
        (package / "run.py").write_text("print('unregistered')")
        result = self.check(package)
        self.assertEqual(result.returncode, 1, result.stderr + result.stdout)
        self.assertIn("marketplace", result.stdout)
        self.assertIn("run.py", result.stdout)

    def test_output_alias_cannot_publish_inside_plugin_source(self):
        alias = Path(self.temp.name) / "source-alias"
        alias.symlink_to(self.first, target_is_directory=True)
        result = self.run_tool("build", "--plugin", "ai-one", "--output", str(alias / "dist"))
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("source directory", result.stderr)
        self.assertFalse((self.first / "dist").exists())

    def test_archive_mutation_is_rejected_before_publication(self):
        from plugin_tools import build, io
        from plugin_tools.registry import load_catalog

        specs = [spec for spec in load_catalog(self.root) if spec.product_id == "ai-one"]
        write_zip = build._zip

        def append_foreign_member(path, files):
            write_zip(path, files)
            with zipfile.ZipFile(path, "a") as archive:
                archive.writestr("ai-two/foreign.txt", "accidental sibling resource")

        with mock.patch.object(build, "_zip", side_effect=append_foreign_member):
            with self.assertRaisesRegex(io.DataError, "ZIP|archive"):
                build.build_plugins(self.root, specs, self.output, hosts=("codex",))
        self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()
