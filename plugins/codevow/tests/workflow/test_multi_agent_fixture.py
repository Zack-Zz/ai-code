"""Verify MA4 exposes a real composition defect, without fixing the fixture."""

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


FIXTURE = Path(__file__).resolve().parents[2] / "evals/fixtures/multi_agent_contract"


def run_tests(workspace, *modules):
    return subprocess.run(
        [sys.executable, "-m", "unittest", *modules],
        cwd=workspace, capture_output=True, text=True,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})


class MultiAgentFixtureTests(unittest.TestCase):
    def test_local_green_composition_red_and_contract_fix_green(self):
        original = {p.name: p.read_bytes() for p in FIXTURE.iterdir() if p.is_file()}
        with tempfile.TemporaryDirectory() as td:
            workspace = Path(td) / "fixture"
            shutil.copytree(FIXTURE, workspace)

            local = run_tests(workspace, "test_local")
            self.assertEqual(local.returncode, 0, local.stdout + local.stderr)
            combined = run_tests(workspace, "test_integration")
            self.assertEqual(combined.returncode, 1, combined.stdout + combined.stderr)
            self.assertIn("KeyError: 'state'", combined.stderr)

            consumer = workspace / "consumer.py"
            consumer.write_text(
                consumer.read_text().replace("event['state']", "event['status']"))
            local_test = workspace / "test_local.py"
            local_test.write_text(
                local_test.read_text().replace('"state": "ready"', '"status": "ready"'))
            fixed = run_tests(workspace, "test_local", "test_integration")
            self.assertEqual(fixed.returncode, 0, fixed.stdout + fixed.stderr)

        self.assertEqual(
            {p.name: p.read_bytes() for p in FIXTURE.iterdir() if p.is_file()}, original)


if __name__ == "__main__":
    unittest.main()
