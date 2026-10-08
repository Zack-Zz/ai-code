"""Remote writes stay behind reviewed deployment inputs and trusted workflow code."""

from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class HostedWorkflowTests(unittest.TestCase):
    def test_marketplace_deploy_is_manual_and_requires_review_bindings(self):
        path = ROOT / '.github/workflows/marketplace.yml'
        self.assertTrue(path.exists(), 'A dedicated read-plan/write-deploy workflow is required')
        text = path.read_text()
        for item in ('workflow_dispatch:', 'default: plan', 'expected_plan_hash:',
                     'expected_market_commit:', 'environment: plugin-marketplace',
                     'cancel-in-progress: false', 'contents: read'):
            self.assertIn(item, text)
        self.assertNotRegex(text, r'(?m)^  (push|release|pull_request_target):')

    def test_external_actions_are_pinned_and_write_job_uses_trusted_code(self):
        path = ROOT / '.github/workflows/marketplace.yml'
        self.assertTrue(path.exists())
        text = path.read_text()
        for action in re.findall(r'uses:\s*(\S+)', text):
            self.assertRegex(action, r'^[^@]+@[0-9a-f]{40}$')
        self.assertIn('trusted/.github/scripts/deploy_marketplace.py', text)
        self.assertIn("github.ref == 'refs/heads/main'", text)

    def test_release_write_job_uses_trusted_manager_and_frozen_source_separately(self):
        text = (ROOT / '.github/workflows/release.yml').read_text()
        self.assertIn('trusted/.github/scripts/create_release_draft.py --root source', text)
        self.assertIn('path: trusted', text)
        self.assertIn('path: source', text)
        self.assertIn("github.ref == 'refs/heads/main'", text)


if __name__ == '__main__':
    unittest.main()
