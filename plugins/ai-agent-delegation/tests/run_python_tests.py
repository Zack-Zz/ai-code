#!/usr/bin/env python3
"""Run only this plugin's consumer tests; empty suites are failures."""
from pathlib import Path
import sys
import unittest

if __name__ == "__main__":
    suite = unittest.defaultTestLoader.discover(str(Path(__file__).parent), pattern="test_*.py")
    if not suite.countTestCases():
        sys.exit("no delegation tests discovered")
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
