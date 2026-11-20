"""Antigravity native packages remain usable through the bundled helpers."""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from workflow import build, io, owned_files, package_check, product

PLUGIN = Path(__file__).resolve().parents[2]


class AntigravityTests(unittest.TestCase):
    def test_standalone_build_check_and_detached_package_detection(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "packages"
            build.build_packages(PLUGIN, ["antigravity"], output)
            package = output / "antigravity/codevow"
            manifest = io.load_json(package / "plugin.json")
            self.assertEqual(manifest["$schema"], "https://antigravity.google/schemas/v1/plugin.json")
            self.assertEqual(manifest["displayName"], "CodeVow")
            self.assertEqual(manifest["logo"], "assets/codevow.png")
            self.assertLessEqual(len(manifest["suggestedPrompts"]), 3)
            self.assertFalse((output / "antigravity/marketplace.json").exists())
            for relative in ("cordis.patch.yml", "reviewer-guard.js", "agents/workflow-reviewer.md",
                             "skills/workflow/agents/openai.yaml"):
                self.assertFalse((package / relative).exists(), relative)
            self.assertTrue(package_check.check_package(package, "antigravity")["ok"])
            detached = Path(temporary) / "detached"
            shutil.copytree(package, detached)
            self.assertEqual(owned_files._host_of(detached), "antigravity")
            result = subprocess.run([sys.executable, "-B", str(detached / "tools/workflow_tool.py"),
                                     "package", "check", "--path", str(detached), "--host", "antigravity"],
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertTrue(json.loads(result.stdout)["ok"])

    def test_antigravity_only_source_keeps_shared_source_hash(self):
        with tempfile.TemporaryDirectory() as temporary:
            source = Path(temporary) / "source"
            shutil.copytree(PLUGIN, source)
            manifest = io.load_json(source / "product.json")
            manifest.update(hosts=["antigravity"], host_listings={}, host_resources={},
                            generated_agents=[], generated_resources=[])
            (source / "product.json").write_text(json.dumps(manifest))
            spec = product.load_product(source)
            output = Path(temporary) / "packages"
            build.build_packages(source, ["all"], output)
            index = io.load_json(output / "index.json")
            self.assertEqual(build._source_tree_hash(spec), index["source_tree_hash"])

    def test_package_check_rejects_resealed_non_native_manifest(self):
        with tempfile.TemporaryDirectory() as temporary:
            output = Path(temporary) / "packages"
            build.build_packages(PLUGIN, ["antigravity"], output)
            package = output / "antigravity/codevow"
            manifest_path = package / "plugin.json"
            manifest = io.load_json(manifest_path)
            del manifest["$schema"]
            manifest_path.write_text(json.dumps(manifest))
            artifact_path = package / "artifact.json"
            artifact = io.load_json(artifact_path)
            artifact["files"] = [[relative, io.sha256_file(package / relative)]
                                 for relative, _ in artifact["files"]]
            artifact["content_hash"] = io.sha256_bytes(io.canonical_json(artifact["files"]))
            artifact_path.write_text(json.dumps(artifact))
            report = package_check.check_package(package, "antigravity")
            self.assertFalse(report["ok"])
            self.assertTrue(any("schema" in problem for problem in report["problems"]))
