"""Public preview versions remain usable by the standalone workflow tools."""

import json
import re
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from workflow import io
from workflow import owned_files
from workflow import product
from tests.workflow.test_product import make_source_root, write_product

PLUGIN_ROOT = Path(__file__).resolve().parents[2]
REPOSITORY_ROOT = PLUGIN_ROOT.parents[1]
VALID_VERSIONS = ("0.0.0", "1.0.2", "12.30.456", "0.0.0-preview.0",
                  "1.0.3-preview.2", "1.0.3-preview.10")
INVALID_VERSIONS = ("01.0.0", "1.00.0", "1.0.01", "1.0.0-preview.01",
                    "1.0.0-preview", "1.0.0-preview.-1", "1.0.0-beta.1",
                    "v1.0.0", "1.0", "1.0.0+build", "1.0.0-preview.1\n",
                    "1.0.0\n", " 1.0.0", "1.0.0 ")


class VersionContractTests(unittest.TestCase):
    def test_source_accepts_stable_and_preview_versions(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_source_root(Path(td))
            for version in VALID_VERSIONS:
                with self.subTest(version=version):
                    write_product(root, lambda data: data.update(version=version))
                    self.assertEqual(product.load_product(root).version, version)

    def test_source_rejects_noncanonical_versions(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_source_root(Path(td))
            for version in (*INVALID_VERSIONS, None, True, 123):
                with self.subTest(version=version):
                    write_product(root, lambda data: data.update(version=version))
                    with self.assertRaisesRegex(io.DataError, "version"):
                        product.load_product(root)

    def test_schema_accepts_only_canonical_public_versions(self):
        schema = io.load_json(PLUGIN_ROOT / "schemas/product.schema.json")
        pattern = schema["properties"]["version"]["pattern"]
        # JSON Schema pattern uses search semantics, including end anchoring.
        for version in VALID_VERSIONS:
            with self.subTest(version=version):
                self.assertIsNotNone(re.search(pattern, version))
        for version in INVALID_VERSIONS:
            with self.subTest(version=version):
                self.assertIsNone(re.search(pattern, version))

    def test_receipt_reopen_accepts_stable_and_preview_rejects_invalid(self):
        with tempfile.TemporaryDirectory() as td:
            target = Path(td).resolve()
            path = owned_files.receipt_file(target)
            path.parent.mkdir(parents=True)
            receipt = {
                "schema_version": 1, "product_id": "ai-code-workflow",
                "managed_root": str(owned_files.managed_root(target)),
                "artifact_hash": "a" * 64, "files": {},
                "last_operation_id": "previous-op",
            }
            for version in VALID_VERSIONS:
                with self.subTest(version=version):
                    path.write_text(json.dumps(dict(receipt, version=version)))
                    plan = owned_files.plan_operation(None, target, "remove")
                    self.assertEqual(plan["conflicts"], [])
            for version in (*INVALID_VERSIONS, None, True, 123):
                with self.subTest(version=version):
                    path.write_text(json.dumps(dict(receipt, version=version)))
                    with self.assertRaisesRegex(io.DataError, "version"):
                        owned_files.plan_operation(None, target, "remove")


class PreviewStandaloneToolTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.td = tempfile.TemporaryDirectory()
        cls.root = Path(cls.td.name)
        cls.repository = cls.root / "repository"
        cls.source = cls.repository / "plugins/ai-code-workflow"
        shutil.copytree(PLUGIN_ROOT, cls.source,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        manifest = io.load_json(cls.source / "product.json")
        manifest["version"] = "1.0.3-preview.10"
        (cls.source / "product.json").write_text(json.dumps(manifest))
        (cls.repository / "catalog.json").write_text(json.dumps({
            "schema_version": 1, "plugins": [{"path": "plugins/ai-code-workflow"}],
        }))
        cls.output = cls.root / "packages"
        built = subprocess.run([
            sys.executable, str(REPOSITORY_ROOT / "tooling/plugin_tool.py"),
            "build", "--root", str(cls.repository), "--all", "--host", "all",
            "--output", str(cls.output),
        ], cwd=cls.root, capture_output=True, text=True)
        if built.returncode:
            cls.td.cleanup()
            raise AssertionError(f"public preview build failed: {built.stderr}")

    @classmethod
    def tearDownClass(cls):
        cls.td.cleanup()

    def run_tool(self, tool, *args):
        result = subprocess.run([sys.executable, "-I", str(tool), *args],
                                cwd=self.root, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_standalone_preview_source_validate(self):
        result = self.run_tool(self.source / "scripts/workflow_tool.py", "validate",
                               "--root", str(self.source))
        self.assertTrue(result["ok"])
        self.assertEqual(result["version"], "1.0.3-preview.10")

    def test_packaged_preview_check_and_receipt_lifecycle(self):
        for host in ("claude", "codex", "zcode"):
            with self.subTest(host=host):
                package = self.output / host / "ai-code-workflow"
                tool = package / "tools/workflow_tool.py"
                checked = self.run_tool(tool, "package", "check", "--path",
                                        str(package), "--host", host)
                self.assertTrue(checked["ok"])
                self.assertEqual(checked["version"], "1.0.3-preview.10")
                target = self.root / f"target-{host}"
                target.mkdir()
                for action in ("stage", "update", "remove"):
                    plan_path = self.root / f"{host}-{action}.json"
                    arguments = ["files", "plan", "--target", str(target),
                                 "--action", action, "--out", str(plan_path)]
                    if action != "remove":
                        arguments.extend(["--package", str(package)])
                    self.run_tool(tool, *arguments)
                    plan = io.load_json(plan_path)
                    self.assertEqual(plan["conflicts"], [])
                    applied = self.run_tool(tool, "files", "apply", "--plan",
                                            str(plan_path), "--expected-plan-hash",
                                            plan["plan_hash"])
                    if action == "update":
                        self.assertFalse(applied["changed"])
                    if action != "remove":
                        receipt = io.load_json(owned_files.receipt_file(target))
                        self.assertEqual(receipt["version"], "1.0.3-preview.10")
                    else:
                        self.assertFalse(owned_files.receipt_file(target).exists())
