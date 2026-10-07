"""Unregistered executable bytecode cannot pass a trusted source package check."""

import importlib.util
import json
import marshal
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

try:
    from .test_registry import TOOL, add_plugin, write_json
except ImportError:
    from test_registry import TOOL, add_plugin, write_json


class BytecodeClosureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="plugin-bytecode-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / "repo"
        self.plugin = add_plugin(self.root)
        (self.plugin / "module.py").write_text('result = "trusted source"\n')
        manifest = json.loads((self.plugin / "product.json").read_text())
        manifest["resources"].append({"source": "module.py", "target": "tools/module.py", "include": []})
        write_json(self.plugin / "product.json", manifest)
        write_json(self.root / "catalog.json", {"schema_version": 1,
                                               "plugins": [{"path": "plugins/ai-one"}]})
        self.output = self.base / "dist"
        result = self.run_tool("build", "--all", "--output", str(self.output))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.package = self.output / "codex/ai-one"

    def run_tool(self, *args):
        return subprocess.run([sys.executable, str(TOOL), *args, "--root", str(self.root)],
                              capture_output=True, text=True, timeout=30)

    def check(self):
        return self.run_tool("package", "check", "--path", str(self.package), "--host", "codex")

    def test_normal_registered_python_source_package_passes(self):
        result = self.check()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(json.loads(result.stdout)["ok"])
        self.assertEqual((self.package / "tools/module.py").read_text(), 'result = "trusted source"\n')

    def test_valid_cpython_cache_that_executes_foreign_code_fails_trusted_check(self):
        source = self.package / "tools/module.py"
        marker = self.base / "foreign-bytecode.marker"
        cache = Path(importlib.util.cache_from_source(str(source)))
        cache.parent.mkdir()
        code = compile(f"from pathlib import Path\nPath({str(marker)!r}).write_text('foreign code executed')\n",
                       str(source), "exec")
        info = source.stat()
        header = importlib.util.MAGIC_NUMBER + struct.pack("<III", 0, int(info.st_mtime), info.st_size)
        cache.write_bytes(header + marshal.dumps(code))

        executed = subprocess.run([sys.executable, "-c",
                                   f"import sys; sys.path.insert(0, {str(source.parent)!r}); import module"],
                                  capture_output=True, text=True, timeout=30)
        self.assertEqual(executed.returncode, 0, executed.stdout + executed.stderr)
        self.assertEqual(marker.read_text(), "foreign code executed")
        self.assertEqual(source.read_text(), 'result = "trusted source"\n')

        result = self.check()
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        report = json.loads(result.stdout)
        self.assertFalse(report["ok"])
        self.assertEqual(report["caches"], [])
        self.assertIn(cache.relative_to(self.package).as_posix(), "\n".join(report["problems"]))


if __name__ == "__main__":
    unittest.main()
