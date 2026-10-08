"""Deployment safeguards use real archives and local Git, without GitHub writes."""

import importlib.util
import io as bytes_io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import warnings
import zipfile
from unittest import mock

from plugin_tools import io
from plugin_tools.release.layout import zip_bytes
from plugin_tools.release import prepare_release
from plugin_tools.release.integrity import read_tree
from plugin_tools.registry import load_catalog
from tests.tooling.test_release import release_plugin
from tests.tooling.test_registry import write_json

SCRIPT = Path(__file__).resolve().parents[1] / '.github/scripts/deploy_marketplace.py'


def implementation():
    if not SCRIPT.is_file():
        return None
    spec = importlib.util.spec_from_file_location('marketplace_deploy', SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class DeploymentSafeguards(unittest.TestCase):
    def setUp(self):
        self.module = implementation()

    def require_module(self):
        self.assertIsNotNone(self.module, 'Hosted deployment must validate downloads before writing a market')
        return self.module

    def test_complete_bundle_extracts_exact_files(self):
        module = self.require_module()
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / 'bundle'
            module.extract_bundle(zip_bytes({'release.json': b'{}', 'packages/.agents/plugins/marketplace.json': b'{}'}), root)
            self.assertEqual(io.read_file(root, 'packages/.agents/plugins/marketplace.json'), b'{}')

    def test_bundle_extraction_rejects_duplicate_and_escaping_members(self):
        module = self.require_module()
        for names in (['../outside'], ['same', 'same']):
            with self.subTest(names=names), tempfile.TemporaryDirectory() as temporary:
                output = bytes_io.BytesIO()
                with warnings.catch_warnings():
                    warnings.simplefilter('ignore', UserWarning)
                    with zipfile.ZipFile(output, 'w') as archive:
                        for name in names:
                            archive.writestr(name, b'hostile')
                with self.assertRaises(io.DataError):
                    module.extract_bundle(output.getvalue(), Path(temporary) / 'bundle')
                self.assertFalse((Path(temporary) / 'outside').exists())

    def test_unsafe_asset_url_is_rejected_before_download(self):
        module = self.require_module()
        for url in ('http://github.com/example/repo/a.zip', 'https://example.com/a.zip',
                    'https://github.com/other/repo/releases/download/v1/a.zip',
                    'https://github.com/example/repo/releases/download/v1/a.zip?token=secret'):
            with self.subTest(url=url), self.assertRaises(io.DataError):
                module.asset_url(url, 'example/repo', 'v1', 'a.zip')

    def test_deployment_requires_hash_and_base_before_any_api_call(self):
        module = self.require_module()
        class API:
            def __getattr__(self, name):
                raise AssertionError('No API call is allowed before explicit plan bindings')
        with self.assertRaises(io.DataError):
            module.deploy(Path('.'), 'ai-code-workflow', 'ai-code-workflow/v1.0.1',
                          'preview', API(), action='deploy')

    def test_git_writer_creates_and_fast_forwards_only_the_reviewed_branch(self):
        module = self.require_module()
        with tempfile.TemporaryDirectory() as temporary:
            bare = Path(temporary) / 'remote.git'
            subprocess.run(['git', 'init', '--bare', str(bare)], check=True, capture_output=True)
            writer = module.GitWriter('example/repo', origin=str(bare))
            first = writer.publish('codex/marketplace-preview', 'absent', {'README.md': b'first\n'}, 'stage')
            second = writer.publish('codex/marketplace-preview', first,
                                    {'README.md': b'first\n', 'channel.json': b'{}\n'}, 'catalog')
            actual = subprocess.check_output(['git', '--git-dir', str(bare), 'rev-parse',
                                             'refs/heads/codex/marketplace-preview'], text=True).strip()
            self.assertEqual(actual, second)
            with self.assertRaises(io.ConflictError):
                writer.publish('codex/marketplace-preview', first, {'README.md': b'overwrite'}, 'stale')
            self.assertEqual(subprocess.check_output(['git', '--git-dir', str(bare), 'rev-parse',
                                                      'refs/heads/codex/marketplace-preview'], text=True).strip(), second)

    def test_git_writer_empty_post_push_read_preserves_an_uncertain_revision(self):
        module = self.require_module()
        original = subprocess.run
        with tempfile.TemporaryDirectory() as temporary:
            bare = Path(temporary) / 'remote.git'
            original(['git', 'init', '--bare', str(bare)], check=True, capture_output=True)
            reads = [0]
            def runner(arguments, **options):
                if 'ls-remote' in arguments:
                    reads[0] += 1
                    if reads[0] == 2:
                        return subprocess.CompletedProcess(arguments, 0, '', '')
                return original(arguments, **options)
            with mock.patch.object(module.subprocess, 'run', side_effect=runner):
                with self.assertRaises(Exception) as failure:
                    module.GitWriter('example/repo', origin=str(bare)).publish(
                        'codex/marketplace-preview', 'absent', {'README.md': b'bytes'}, 'stage')
            self.assertIsInstance(failure.exception, io.ConflictError)
            self.assertRegex(getattr(failure.exception, 'attempted_revision', ''), r'^[0-9a-f]{40}$')

    def test_git_writer_removes_only_explicitly_reviewed_empty_market_entries(self):
        module = self.require_module()
        with tempfile.TemporaryDirectory() as temporary:
            bare = Path(temporary) / 'remote.git'
            subprocess.run(['git', 'init', '--bare', str(bare)], check=True, capture_output=True)
            writer = module.GitWriter('example/repo', origin=str(bare))
            base = writer.publish('codex/marketplace-preview', 'absent',
                {'README.md': b'keep', 'marketplace.json': b'{}'}, 'old market')
            with self.assertRaises(io.DataError):
                writer.publish('codex/marketplace-preview', base, {'README.md': b'keep'}, 'unreviewed removal')
            failure = None
            try:
                revision = writer.publish('codex/marketplace-preview', base, {'README.md': b'keep'},
                    'reviewed empty host', removals=['marketplace.json'])
            except Exception as exc:
                failure = exc
            self.assertIsNone(failure, f'Explicit managed market removal must be supported: {failure}')
            self.assertNotEqual(revision, base)
            with self.assertRaises(io.DataError):
                writer.publish('codex/marketplace-preview', revision, {}, 'forbidden removal', removals=['README.md'])


class FullDeploymentTests(unittest.TestCase):
    def setUp(self):
        self.module = implementation()
        self.assertIsNotNone(self.module)
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.base = Path(self.temporary.name)
        self.root = self.base / 'source'
        plugin = release_plugin(self.root)
        product = json.loads((plugin / 'product.json').read_text())
        product['repository'] = 'https://github.com/example/repo'
        write_json(plugin / 'product.json', product)
        source_config = Path(__file__).resolve().parents[1] / 'distribution.json'
        (self.root / 'distribution.json').write_bytes(source_config.read_bytes())
        def git(*arguments):
            return subprocess.check_output(['git', *arguments], cwd=self.root, stderr=subprocess.DEVNULL, text=True).strip()
        git('init', '-b', 'main')
        git('config', 'user.name', 'Fixture')
        git('config', 'user.email', 'fixture@example.invalid')
        git('add', '.')
        git('commit', '-m', 'source')
        self.sha = git('rev-parse', 'HEAD')
        self.git = git
        self.tag = 'ai-one/v1.0.0'
        git('tag', 'ai-one/v1.0.0')
        git('update-ref', 'refs/remotes/origin/main', self.sha)
        bundle = self.base / 'bundle'
        self.bundle = bundle
        result = prepare_release(self.root, load_catalog(self.root)[0], bundle)
        self.assertTrue(result['ok'], result)
        files = read_tree(bundle)
        archive_name = 'ai-one-1.0.0-release-bundle.zip'
        archive = zip_bytes(files)
        self.payloads = {archive_name: archive,
            'ai-one-1.0.0-release-bundle.sha256': f'{io.sha256(archive)}  {archive_name}\n'.encode()}
        self.payloads.update({name: files[name] for name in ('release.json', 'release-notes.md', 'SHA256SUMS')})
        for name, raw in files.items():
            if name.startswith(('installers/', 'downloads/')):
                self.payloads[Path(name).name] = raw
        self.release = {'id': 1, 'tag_name': 'ai-one/v1.0.0', 'draft': False, 'prerelease': True,
            'html_url': 'https://github.com/example/repo/releases/tag/ai-one/v1.0.0', 'assets': []}
        for index, (name, raw) in enumerate(self.payloads.items(), 1):
            self.release['assets'].append({'id': index, 'name': name, 'size': len(raw),
                'browser_download_url': 'https://github.com/example/repo/releases/download/ai-one/v1.0.0/' + name,
                'extra_api_metadata': 'must not become part of the strict plan'})
        self.history = {self.tag: (self.sha, self.release, self.payloads)}
        owner = self
        class FakeGitHub:
            repository = 'example/repo'
            revision = 'absent'
            files = {}
            writes = 0
            revisions = {}
            def tag(self, tag):
                return owner.history[tag][0]
            def release(self, tag):
                return owner.history[tag][1]
            def download(self, asset, tag):
                self.module_url_guard(asset, tag)
                return owner.history[tag][2][asset['name']]
            def module_url_guard(self, asset, tag):
                owner.module.asset_url(asset['browser_download_url'], self.repository, tag, asset['name'])
            def market(self, branch):
                if len(branch) == 40:
                    if branch not in self.revisions:
                        raise io.DataError('pinned commit is unavailable')
                    return branch, dict(self.revisions[branch])
                return self.revision, dict(self.files)
            def publish(self, branch, expected, files, message, removals=()):
                if expected != self.revision:
                    raise io.ConflictError('stale fixture branch')
                self.writes += 1
                self.revision = str(self.writes) * 40
                self.files = dict(files)
                self.revisions[self.revision] = dict(files)
                return self.revision
        self.api = FakeGitHub()

    def call(self, **options):
        return self.module.deploy(self.root, 'ai-one', self.tag, 'preview', self.api,
                                  writer=self.api, **options)

    def test_plan_is_read_only_and_deploy_pins_the_staged_commit(self):
        plan = self.call()
        self.assertEqual(self.api.writes, 0)
        result = self.call(action='deploy', expected_plan_hash=plan['plan_hash'], expected_market_commit='absent')
        self.assertEqual(result['status'], 'marketplace_deployed')
        self.assertEqual(self.api.writes, 2)
        market = json.loads(self.api.files['.agents/plugins/marketplace.json'])
        self.assertEqual(market['plugins'][0]['source']['sha'], '1' * 40)

    def test_missing_asset_or_changed_bytes_never_write(self):
        original = self.payloads['ai-one-1.0.0-codex-plugin.zip']
        self.payloads['ai-one-1.0.0-codex-plugin.zip'] = b'changed'
        with self.assertRaises(io.DataError):
            self.call()
        self.assertEqual(self.api.writes, 0)
        self.payloads['ai-one-1.0.0-codex-plugin.zip'] = original
        self.release['assets'] = self.release['assets'][:-1]
        with self.assertRaises(io.DataError):
            self.call()
        self.assertEqual(self.api.writes, 0)

    def test_stale_reviewed_hash_never_writes(self):
        self.call()
        with self.assertRaises(io.ConflictError):
            self.call(action='deploy', expected_plan_hash='f' * 64, expected_market_commit='absent')
        self.assertEqual(self.api.writes, 0)

    def test_exact_retry_is_read_only(self):
        plan = self.call()
        self.call(action='deploy', expected_plan_hash=plan['plan_hash'], expected_market_commit='absent')
        result = self.call(action='deploy', expected_plan_hash=plan['plan_hash'], expected_market_commit='absent')
        self.assertEqual(result['status'], 'already_deployed')
        self.assertEqual(self.api.writes, 2)

    def test_local_distribution_cli_checks_the_reviewed_plan(self):
        plan = self.call()
        plan_path = self.base / 'plan.json'
        plan_path.write_bytes(io.dump_json(plan))
        tool = Path(__file__).resolve().parents[1] / 'tooling/plugin_tool.py'
        result = subprocess.run([sys.executable, str(tool), 'distribution', 'check',
            '--plan', str(plan_path), '--expected-plan-hash', plan['plan_hash'],
            '--expected-market-commit', 'absent', '--root', str(self.root)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(json.loads(result.stdout)['ok'])

    def test_previous_public_bundle_is_reverified_before_new_plan(self):
        old_plan = self.call()
        self.call(action='deploy', expected_plan_hash=old_plan['plan_hash'], expected_market_commit='absent')
        product_path = self.root / 'plugins/ai-one/product.json'
        product = json.loads(product_path.read_text())
        product['version'] = '1.0.1'
        write_json(product_path, product)
        self.git('add', '.')
        self.git('commit', '-m', 'next version')
        self.sha = self.git('rev-parse', 'HEAD')
        self.tag = 'ai-one/v1.0.1'
        self.git('tag', self.tag)
        self.git('update-ref', 'refs/remotes/origin/main', self.sha)
        bundle = self.base / 'next-bundle'
        self.assertTrue(prepare_release(self.root, load_catalog(self.root)[0], bundle)['ok'])
        files = read_tree(bundle)
        archive_name = 'ai-one-1.0.1-release-bundle.zip'
        raw = zip_bytes(files)
        payloads = {archive_name: raw,
                   'ai-one-1.0.1-release-bundle.sha256': f'{io.sha256(raw)}  {archive_name}\n'.encode()}
        payloads.update({name: files[name] for name in ('release.json', 'release-notes.md', 'SHA256SUMS')})
        payloads.update({Path(name).name: value for name, value in files.items()
                         if name.startswith(('installers/', 'downloads/'))})
        release = {'id': 2, 'tag_name': self.tag, 'draft': False, 'prerelease': True,
            'html_url': 'https://github.com/example/repo/releases/tag/' + self.tag,
            'assets': [{'id': number, 'name': name, 'size': len(value),
                'browser_download_url': 'https://github.com/example/repo/releases/download/' + self.tag + '/' + name}
                for number, (name, value) in enumerate(payloads.items(), 1)]}
        self.history[self.tag] = (self.sha, release, payloads)
        self.history['ai-one/v1.0.0'][2]['ai-one-1.0.0-release-bundle.zip'] = b'old public bundle changed'
        with self.assertRaises(io.DataError):
            self.call()
        self.assertEqual(self.api.writes, 2)

    def test_current_market_cannot_self_rehash_a_missing_pinned_commit(self):
        plan = self.call()
        self.call(action='deploy', expected_plan_hash=plan['plan_hash'], expected_market_commit='absent')
        record_path = 'records/ai-one/1.0.0.json'
        record = json.loads(self.api.files[record_path])
        record['codex_revision'] = 'f' * 40
        self.api.files[record_path] = io.dump_json(record)
        channel = json.loads(self.api.files['channel.json'])
        channel['plugins']['ai-one']['codex_revision'] = 'f' * 40
        self.api.files['channel.json'] = io.dump_json(channel)
        market = json.loads(self.api.files['.agents/plugins/marketplace.json'])
        market['plugins'][0]['source']['sha'] = 'f' * 40
        self.api.files['.agents/plugins/marketplace.json'] = io.dump_json(market)
        receipt = json.loads(self.api.files['marketplaces.lock.json'])
        receipt['files']['.agents/plugins/marketplace.json'] = io.sha256(self.api.files['.agents/plugins/marketplace.json'])
        self.api.files['marketplaces.lock.json'] = io.dump_json(receipt)
        with self.assertRaises(io.DataError):
            self.call()

    def test_cli_plan_check_handles_valid_plans_larger_than_one_megabyte(self):
        plan = self.call()
        plan['record']['readiness']['limitations'].append('Public review text. ' * 70000)
        plan['plan_hash'] = io.sha256(io.canonical_json({key: value for key, value in plan.items() if key != 'plan_hash'}))
        plan_path = self.base / 'large-plan.json'
        plan_path.write_bytes(io.dump_json(plan))
        self.assertGreater(plan_path.stat().st_size, 1024 * 1024)
        tool = Path(__file__).resolve().parents[1] / 'tooling/plugin_tool.py'
        result = subprocess.run([sys.executable, str(tool), 'distribution', 'check', '--plan',
            str(plan_path), '--root', str(self.root)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_catalog_failure_retains_the_successful_staging_commit(self):
        plan = self.call()
        original = self.api.publish
        def fail_catalog(branch, expected, files, message, **options):
            if self.api.writes == 1:
                raise io.ConflictError('catalog push unavailable')
            return original(branch, expected, files, message, **options)
        self.api.publish = fail_catalog
        with self.assertRaises(io.ToolError) as failure:
            self.call(action='deploy', expected_plan_hash=plan['plan_hash'], expected_market_commit='absent')
        result = getattr(failure.exception, 'result', {})
        self.assertEqual(result.get('status'), 'published_pending_marketplace')
        self.assertEqual(result.get('distribution_revision'), '1' * 40)
        self.assertEqual(result.get('phase'), 'publishing_catalog')

    def test_final_read_failure_reports_catalog_commit_without_claiming_acceptance(self):
        plan = self.call()
        original = self.api.market
        def fail_final(branch):
            if self.api.writes == 2 and branch.startswith('codex/'):
                raise io.DataError('read-back unavailable')
            return original(branch)
        self.api.market = fail_final
        with self.assertRaises(io.ToolError) as failure:
            self.call(action='deploy', expected_plan_hash=plan['plan_hash'], expected_market_commit='absent')
        result = getattr(failure.exception, 'result', {})
        self.assertEqual(result.get('market_commit'), '2' * 40)
        self.assertEqual(result.get('phase'), 'verifying_catalog')
        self.assertFalse(result.get('ok', True))

    def test_entrypoint_normalizes_a_supported_git_repository_suffix(self):
        product_path = self.root / 'plugins/ai-one/product.json'
        product = json.loads(product_path.read_text())
        product['repository'] += '.git'
        write_json(product_path, product)
        arguments = [str(SCRIPT), '--root', str(self.root), '--plugin', 'ai-one',
                     '--source-tag', self.tag, '--channel', 'preview']
        with mock.patch.object(self.module.sys, 'argv', arguments), \
                mock.patch.object(self.module, 'GitHub') as api_factory, \
                mock.patch.object(self.module, 'deploy', return_value={'ok': True}), \
                mock.patch.object(self.module, 'print'):
            self.assertEqual(self.module.main(), 0)
        self.assertEqual(api_factory.call_args.args, ('example/repo',))


if __name__ == '__main__':
    unittest.main()
