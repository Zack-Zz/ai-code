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
from tests.tooling.test_distribution import accept_fixture

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

    def test_repository_metadata_uses_the_canonical_rest_endpoint(self):
        module = self.require_module()
        with mock.patch.object(module, 'urlopen', return_value=bytes_io.BytesIO(b'{"visibility":"public"}')) as request:
            self.assertEqual(module.GitHub('example/repo').get(''), {'visibility': 'public'})
        self.assertEqual(request.call_args.args[0].full_url, 'https://api.github.com/repos/example/repo')

    def test_rest_resource_paths_preserve_encoded_tags_and_queries(self):
        module = self.require_module()
        resource = 'releases/tags/ai-one%2Fv1.0.0?per_page=1'
        with mock.patch.object(module, 'urlopen', return_value=bytes_io.BytesIO(b'{}')) as request:
            module.GitHub('example/repo').get(resource)
        self.assertEqual(request.call_args.args[0].full_url,
                         'https://api.github.com/repos/example/repo/' + resource)

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
        accept_fixture(self.root, "ai-one")
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
        result = prepare_release(self.root, load_catalog(self.root)[0], bundle, mode="stable")
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
        self.release = {'id': 1, 'tag_name': 'ai-one/v1.0.0', 'draft': False, 'prerelease': False,
            'html_url': 'https://github.com/example/repo/releases/tag/ai-one/v1.0.0', 'assets': []}
        for index, (name, raw) in enumerate(self.payloads.items(), 1):
            self.release['assets'].append({'id': index, 'name': name, 'size': len(raw),
                'browser_download_url': 'https://github.com/example/repo/releases/download/ai-one/v1.0.0/' + name,
                'extra_api_metadata': 'must not become part of the strict plan'})
        self.history = {self.tag: (self.sha, self.release, self.payloads)}
        owner = self
        class FakeGitHub:
            repository = 'example/repo'
            revision = owner.sha
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
        return self.module.deploy(self.root, 'ai-one', self.tag, 'stable', self.api,
                                  writer=self.api, **options)

    def test_plan_is_read_only_and_deploy_pins_the_staged_commit(self):
        plan = self.call()
        self.assertEqual(self.api.writes, 0)
        result = self.call(action='deploy', expected_plan_hash=plan['plan_hash'], expected_market_commit=self.sha)
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
            self.call(action='deploy', expected_plan_hash='f' * 64, expected_market_commit=self.sha)
        self.assertEqual(self.api.writes, 0)

    def test_exact_retry_is_read_only(self):
        plan = self.call()
        self.call(action='deploy', expected_plan_hash=plan['plan_hash'], expected_market_commit=self.sha)
        result = self.call(action='deploy', expected_plan_hash=plan['plan_hash'], expected_market_commit=self.sha)
        self.assertEqual(result['status'], 'already_deployed')
        self.assertEqual(self.api.writes, 2)

    def test_local_distribution_cli_checks_the_reviewed_plan(self):
        plan = self.call()
        plan_path = self.base / 'plan.json'
        plan_path.write_bytes(io.dump_json(plan))
        tool = Path(__file__).resolve().parents[1] / 'tooling/plugin_tool.py'
        result = subprocess.run([sys.executable, str(tool), 'distribution', 'check',
            '--plan', str(plan_path), '--expected-plan-hash', plan['plan_hash'],
            '--expected-market-commit', self.sha, '--root', str(self.root)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue(json.loads(result.stdout)['ok'])

    def test_previous_public_bundle_is_reverified_before_new_plan(self):
        old_plan = self.call()
        self.call(action='deploy', expected_plan_hash=old_plan['plan_hash'], expected_market_commit=self.sha)
        product_path = self.root / 'plugins/ai-one/product.json'
        product = json.loads(product_path.read_text())
        product['version'] = '1.0.1'
        write_json(product_path, product)
        accept_fixture(self.root, 'ai-one')
        self.git('add', '.')
        self.git('commit', '-m', 'next version')
        self.sha = self.git('rev-parse', 'HEAD')
        self.tag = 'ai-one/v1.0.1'
        self.git('tag', self.tag)
        self.git('update-ref', 'refs/remotes/origin/main', self.sha)
        bundle = self.base / 'next-bundle'
        self.assertTrue(prepare_release(self.root, load_catalog(self.root)[0], bundle, mode="stable")['ok'])
        files = read_tree(bundle)
        archive_name = 'ai-one-1.0.1-release-bundle.zip'
        raw = zip_bytes(files)
        payloads = {archive_name: raw,
                   'ai-one-1.0.1-release-bundle.sha256': f'{io.sha256(raw)}  {archive_name}\n'.encode()}
        payloads.update({name: files[name] for name in ('release.json', 'release-notes.md', 'SHA256SUMS')})
        payloads.update({Path(name).name: value for name, value in files.items()
                         if name.startswith(('installers/', 'downloads/'))})
        release = {'id': 2, 'tag_name': self.tag, 'draft': False, 'prerelease': False,
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
        self.call(action='deploy', expected_plan_hash=plan['plan_hash'], expected_market_commit=self.sha)
        record_path = 'published/releases/ai-one/1.0.0.json'
        record = json.loads(self.api.files[record_path])
        record['codex_revision'] = 'f' * 40
        self.api.files[record_path] = io.dump_json(record)
        channel = json.loads(self.api.files['published/index.json'])
        channel['plugins']['ai-one']['codex_revision'] = 'f' * 40
        self.api.files['published/index.json'] = io.dump_json(channel)
        market = json.loads(self.api.files['.agents/plugins/marketplace.json'])
        market['plugins'][0]['source']['sha'] = 'f' * 40
        self.api.files['.agents/plugins/marketplace.json'] = io.dump_json(market)
        receipt = json.loads(self.api.files['published/marketplaces.lock.json'])
        receipt['files']['.agents/plugins/marketplace.json'] = io.sha256(self.api.files['.agents/plugins/marketplace.json'])
        self.api.files['published/marketplaces.lock.json'] = io.dump_json(receipt)
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
            self.call(action='deploy', expected_plan_hash=plan['plan_hash'], expected_market_commit=self.sha)
        result = getattr(failure.exception, 'result', {})
        self.assertEqual(result.get('status'), 'published_pending_marketplace')
        self.assertEqual(result.get('distribution_revision'), '1' * 40)
        self.assertEqual(result.get('phase'), 'publishing_catalog')

    def test_final_read_failure_reports_catalog_commit_without_claiming_acceptance(self):
        plan = self.call()
        original = self.api.market
        def fail_final(branch):
            if self.api.writes == 2 and branch == 'main':
                raise io.DataError('read-back unavailable')
            return original(branch)
        self.api.market = fail_final
        with self.assertRaises(io.ToolError) as failure:
            self.call(action='deploy', expected_plan_hash=plan['plan_hash'], expected_market_commit=self.sha)
        result = getattr(failure.exception, 'result', {})
        self.assertEqual(result.get('market_commit'), '2' * 40)
        self.assertEqual(result.get('phase'), 'verifying_catalog')
        self.assertFalse(result.get('ok', True))

    def test_preview_release_is_a_read_only_noop_before_market_reads(self):
        self.release['prerelease'] = True
        original = self.api.market
        self.api.market = lambda branch: (_ for _ in ()).throw(AssertionError('preview cannot read or update main market'))
        result = self.call()
        self.assertEqual(result['status'], 'preview_release_only')
        self.assertEqual(self.api.writes, 0)
        self.api.market = original

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


class MainGitWriterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='main-publish-test-')
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.bare = self.base / 'remote.git'
        self.source = self.base / 'source'
        self.source.mkdir()
        self.git('init', '--bare', str(self.bare))
        self.git('init', '-b', 'main', cwd=self.source)
        (self.source / 'README.md').write_bytes(b'Human maintained source README\n')
        (self.source / 'script.sh').write_bytes(b'#!/bin/sh\nexit 0\n')
        (self.source / 'script.sh').chmod(0o755)
        (self.source / 'source-link').symlink_to('README.md')
        self.git('add', '.', cwd=self.source)
        self.git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                 'commit', '-m', 'source', cwd=self.source)
        self.git('push', str(self.bare), 'main', cwd=self.source)
        self.head = self.git('rev-parse', 'HEAD', cwd=self.source)
        self.writer = implementation().GitWriter('example/repo', origin=str(self.bare))

    def git(self, *arguments, cwd=None):
        result = subprocess.run(['git', *arguments], cwd=cwd, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def test_main_patch_preserves_source_bytes_modes_and_links(self):
        before = self.git('--git-dir', str(self.bare), 'ls-tree', self.head)
        revision = self.writer.publish('main', self.head,
            {'published/codex/ai-one/1.0.0/plugin.json': b'{"name":"ai-one"}\n'}, 'stage package')
        after = self.git('--git-dir', str(self.bare), 'ls-tree', revision)
        self.assertEqual([line for line in after.splitlines() if not line.endswith('\tpublished')],
                         before.splitlines())
        self.assertEqual(self.git('--git-dir', str(self.bare), 'show', revision + ':README.md'),
                         'Human maintained source README')
        with self.assertRaises(io.ConflictError):
            self.writer.publish('main', self.head, {'published/index.json': b'{}'}, 'stale')
        self.assertEqual(self.git('--git-dir', str(self.bare), 'rev-parse', 'main'), revision)

    def test_writer_rejects_source_dist_old_branches_and_absent_main(self):
        for files in ({'README.md': b'overwrite'}, {'dist/package.zip': b'bytes'},
                      {'published/../README.md': b'escape'}, {'.git/config': b'bad'}):
            with self.subTest(files=files), self.assertRaises(io.DataError):
                self.writer.publish('main', self.head, files, 'unsafe')
        for branch, expected in (('codex/marketplace-preview', 'absent'), ('main', 'absent')):
            with self.subTest(branch=branch), self.assertRaises(io.DataError):
                self.writer.publish(branch, expected, {'published/index.json': b'{}'}, 'unsafe')

    def test_empty_post_push_read_preserves_uncertain_revision(self):
        module = implementation()
        original = subprocess.run
        reads = [0]
        def runner(arguments, **options):
            if 'ls-remote' in arguments:
                reads[0] += 1
                if reads[0] == 2:
                    return subprocess.CompletedProcess(arguments, 0, '', '')
            return original(arguments, **options)
        with mock.patch.object(module.subprocess, 'run', side_effect=runner):
            with self.assertRaises(io.ConflictError) as failure:
                self.writer.publish('main', self.head, {'published/index.json': b'{}'}, 'stage')
        self.assertRegex(getattr(failure.exception, 'attempted_revision', ''), r'^[0-9a-f]{40}$')

    def test_only_explicit_native_market_removals_are_allowed(self):
        initial = self.writer.publish('main', self.head, {'marketplace.json': b'{}'}, 'native')
        with self.assertRaises(io.DataError):
            self.writer.publish('main', initial, {}, 'source removal', removals=['README.md'])
        removed = self.writer.publish('main', initial, {}, 'reviewed native removal', removals=['marketplace.json'])
        self.assertNotEqual(initial, removed)
        self.assertEqual(self.git('--git-dir', str(self.bare), 'show', removed + ':README.md'),
                         'Human maintained source README')


if __name__ == '__main__':
    unittest.main()
