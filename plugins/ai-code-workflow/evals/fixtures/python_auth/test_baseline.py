"""Baseline suite for the python_auth fixture (normal paths only)."""

import unittest

from auth import can_read


class BaselineTests(unittest.TestCase):
    def test_owner_can_read_same_tenant(self):
        self.assertTrue(
            can_read({"user_id": 1, "tenant_id": "a"}, {"owner_id": 1, "tenant_id": "a"}))

    def test_different_owner_is_rejected(self):
        self.assertFalse(
            can_read({"user_id": 2, "tenant_id": "a"}, {"owner_id": 1, "tenant_id": "a"}))


if __name__ == "__main__":
    unittest.main()
