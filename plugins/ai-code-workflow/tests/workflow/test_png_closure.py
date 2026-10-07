"""Self-resealed packages cannot drop the shared PNG or enter file staging."""

import json
from pathlib import Path
import shutil
import tempfile
import unittest

from workflow import build, io, owned_files, package_check
from workflow.io import ToolError


PLUGIN = Path(__file__).resolve().parents[2]


class PngClosureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix="workflow-png-closure-")
        cls.base = Path(cls.tmp.name)
        cls.dist = cls.base / "dist"
        build.build_packages(PLUGIN, ["claude", "codex", "zcode"], cls.dist)

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_all_hosts_reject_missing_png_even_when_artifact_is_resealed(self):
        for host in ("claude", "codex", "zcode"):
            with self.subTest(host=host):
                copy_root = self.base / ("copy-" + host)
                shutil.copytree(self.dist / host, copy_root)
                package = copy_root / "ai-code-workflow"
                (package / "assets/codevow.png").unlink()
                artifact_path = package / "artifact.json"
                artifact = json.loads(artifact_path.read_text())
                artifact["files"] = [entry for entry in artifact["files"] if entry[0] != "assets/codevow.png"]
                artifact["content_hash"] = io.sha256_bytes(io.canonical_json(artifact["files"]))
                artifact_path.write_text(json.dumps(artifact))

                report = package_check.check_package(package, host)
                self.assertFalse(report["ok"], f"{host}: a self-resealed omission must not remove required PNG ownership")
                self.assertTrue(any("assets/codevow.png" in problem for problem in report["problems"]), report)
                workspace = self.base / ("project-" + host)
                workspace.mkdir()
                with self.assertRaisesRegex(ToolError, "package check failed"):
                    owned_files.plan_operation(package, workspace, "stage")
                self.assertFalse((workspace / ".ai-workflow").exists())


if __name__ == "__main__":
    unittest.main()
