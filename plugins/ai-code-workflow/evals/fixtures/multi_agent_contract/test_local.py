"""Independent checks for the producer and consumer."""

import unittest

from consumer import render_event
from producer import make_event


class LocalTests(unittest.TestCase):
    def test_producer(self):
        self.assertEqual(make_event("job-7"), {"job_id": "job-7", "status": "ready"})

    def test_consumer(self):
        self.assertEqual(
            render_event({"job_id": "job-7", "state": "ready"}), "job-7: ready")


if __name__ == "__main__":
    unittest.main()
