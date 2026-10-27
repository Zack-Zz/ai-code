"""Baseline suite for the state_resume fixture."""

import unittest

from calc import discount


class BaselineTests(unittest.TestCase):
    def test_no_discount(self):
        self.assertEqual(discount(100, False), 100.0)

    def test_member_discount(self):
        self.assertEqual(discount(100, True), 90.0)


if __name__ == "__main__":
    unittest.main()
