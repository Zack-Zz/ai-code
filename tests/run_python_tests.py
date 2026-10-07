#!/usr/bin/env python3
"""Run repository tooling tests; plugin Python suites run in separate processes."""

import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tooling"))

if __name__ == "__main__":
    suite = unittest.defaultTestLoader.discover(
        str(REPO / "tests"), top_level_dir=str(REPO), pattern="test_*.py")
    if suite.countTestCases() == 0:
        print(f"Error: no Python tests discovered under {REPO / 'tests'}", file=sys.stderr)
        sys.exit(1)
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
