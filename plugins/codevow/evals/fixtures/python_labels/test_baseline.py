"""Baseline suite for the python_labels fixture (grader assertions are separate)."""

import unittest

from labels import label


class BaselineTests(unittest.TestCase):
    def test_idle(self):
        self.assertEqual(label(0), "idle")

    def test_running(self):
        self.assertEqual(label(1), "running")

    def test_unknown(self):
        self.assertEqual(label(99), "unknown")


if __name__ == "__main__":
    unittest.main()
