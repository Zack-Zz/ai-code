"""The tracked-output gate observes the Git index, not local build leftovers."""

import importlib.util
from pathlib import Path
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / ".github/scripts/check_no_dist.py"
spec = importlib.util.spec_from_file_location("no_dist", SCRIPT)
no_dist = importlib.util.module_from_spec(spec)
spec.loader.exec_module(no_dist)


class NoDistTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="ai-no-dist-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        (self.root / ".gitignore").write_text("dist/\n")
        (self.root / "dist").mkdir()
        (self.root / "dist" / "local output.zip").write_bytes(b"local output")

    def test_ignored_untracked_outputs_are_allowed(self):
        no_dist.check(self.root)

    def test_force_added_dist_files_are_rejected(self):
        subprocess.run(["git", "add", "-f", "dist"], cwd=self.root, check=True)
        with self.assertRaisesRegex(ValueError, "tracked"):
            no_dist.check(self.root)

    def test_no_repository_is_a_failure_instead_of_a_clean_index(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(subprocess.CalledProcessError):
                no_dist.check(directory)
