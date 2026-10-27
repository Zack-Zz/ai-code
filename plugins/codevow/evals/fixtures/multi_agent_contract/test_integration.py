"""End-to-end acceptance check for the MA4 public contract."""

import unittest

from consumer import render_event
from producer import make_event


class IntegrationTests(unittest.TestCase):
    def test_ready_event_reaches_the_user(self):
        self.assertEqual(render_event(make_event("job-7")), "job-7: ready")


if __name__ == "__main__":
    unittest.main()
