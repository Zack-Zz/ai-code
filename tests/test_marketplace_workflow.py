"""Remote writes stay behind reviewed deployment inputs and trusted workflow code."""

from pathlib import Path
import json
import os
import re
import subprocess
import sys
import tempfile
import textwrap
import unittest

ROOT = Path(__file__).resolve().parents[1]


class HostedWorkflowTests(unittest.TestCase):
    def test_preview_receipt_finishes_plan_summary_without_requiring_a_market_lease(self):
        text = (ROOT / '.github/workflows/marketplace.yml').read_text()
        body = text.split("python3 - <<'PY'\n", 1)[1].split('\n          PY', 1)[0]
        with tempfile.TemporaryDirectory() as temporary:
            base = Path(temporary)
            (base / 'marketplace-plan.json').write_text(json.dumps({
                'status': 'preview_release_only', 'product_id': 'ai-one', 'version': '1.0.1-preview.1'}))
            result = subprocess.run([sys.executable, '-c', textwrap.dedent(body)], capture_output=True,
                text=True, env=dict(os.environ, RUNNER_TEMP=temporary, GITHUB_OUTPUT=str(base / 'outputs'),
                                    GITHUB_STEP_SUMMARY=str(base / 'summary')))
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn('status=preview_release_only', (base / 'outputs').read_text())
            self.assertNotIn('plan_hash=', (base / 'outputs').read_text())

    def test_ci_does_not_require_committed_distributions_or_development_market_sync(self):
        text = (ROOT / '.github/workflows/ci.yml').read_text()
        self.assertNotIn('check_dist.py', text)
        self.assertNotIn('marketplace sync', text)
        self.assertIn('marketplace check --root .', text)
        self.assertIn('check_no_dist.py', text)
        self.assertIn('npm ci', text)

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
            if not action.startswith('./'):
                self.assertRegex(action, r'^[^@]+@[0-9a-f]{40}$')
        self.assertIn('trusted/.github/scripts/deploy_marketplace.py', text)
        self.assertIn("github.ref == 'refs/heads/main'", text)

    def test_release_kind_is_derived_and_stable_success_explicitly_calls_marketplace(self):
        text = (ROOT / '.github/workflows/release.yml').read_text()
        self.assertIn('options: [prepare, publish]', text)
        self.assertNotIn('inputs.mode', text)
        self.assertNotIn('check_dist.py', text)
        self.assertNotIn('marketplace sync', text)
        self.assertIn('trusted/.github/scripts/prepare_release.py --root source', text)
        self.assertIn('trusted/.github/scripts/publish_release.py --root source', text)
        self.assertIn('uses: ./.github/workflows/marketplace.yml', text)
        self.assertIn("needs.prepare.outputs.kind == 'stable'", text)
        caller = text.split('  sync-marketplace:', 1)[1]
        self.assertIn('contents: write', caller)
        prepare = text.split('  prepare:', 1)[1].split('\n  publish:', 1)[0]
        self.assertIn('contents: read', prepare)
        self.assertNotIn('GH_TOKEN:', prepare)
        self.assertLess(prepare.index('--check-source-only'), prepare.index('npm test'))
        for action in re.findall(r'uses:\s*(\S+)', text):
            if not action.startswith('./'):
                self.assertRegex(action, r'^[^@]+@[0-9a-f]{40}$')

    def test_reusable_marketplace_plans_read_only_before_environment_protected_write(self):
        text = (ROOT / '.github/workflows/marketplace.yml').read_text()
        self.assertIn('workflow_call:', text)
        plan, deploy = text.split('  plan:', 1)[1].split('\n  deploy:', 1)
        self.assertIn('contents: read', plan)
        self.assertNotIn('contents: write', plan)
        self.assertIn('contents: write', deploy)
        self.assertIn('needs: plan', deploy)
        self.assertIn('environment: plugin-marketplace', deploy)
        self.assertIn('--control-root trusted', plan)
        self.assertIn('--control-root trusted', deploy)
        self.assertIn('--channel stable', plan)
        self.assertIn('--channel stable', deploy)
        self.assertNotIn('or absent', text)
        self.assertIn('needs.plan.outputs.base_commit', deploy)

    def test_release_write_job_uses_trusted_manager_and_frozen_source_separately(self):
        text = (ROOT / '.github/workflows/release.yml').read_text()
        self.assertIn('trusted/.github/scripts/create_release_draft.py --root source', text)
        self.assertIn('path: trusted', text)
        self.assertIn('path: source', text)
        self.assertIn("github.ref == 'refs/heads/main'", text)


if __name__ == '__main__':
    unittest.main()
