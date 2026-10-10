"""Real local bundles and a fake GitHub API with HTTP attachment readback."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import threading
import unittest
from urllib.request import urlopen
import zipfile

from plugin_tools import io
from plugin_tools.registry import load_catalog
from plugin_tools.rendering import file_hashes, package_files
from tests.tooling.test_registry import write_json
from tests.tooling.test_release import release_plugin

SCRIPT = Path(__file__).resolve().parents[1] / ".github/scripts/publish_release.py"
module_spec = importlib.util.spec_from_file_location("release_publish", SCRIPT)
publish = importlib.util.module_from_spec(module_spec)
module_spec.loader.exec_module(publish)
prepare = publish.drafts.sys.modules["prepare_release"]


class FakeGitHub:
    def __init__(self, revision):
        self.revision = revision
        self.existing = False
        self.created = False
        self.public = False
        self.assets = {}
        self.names = {}
        self.calls = []
        self.corrupt = False
        self.missing = False
        self.wrong_kind = False
        self.move_tag = False
        self.move_tag_on_download = False
        self.fail_edit = False
        self.fail_after_edit = False
        owner = self
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                raw = owner.assets[int(self.path.lstrip('/'))]
                if owner.corrupt:
                    raw = raw[:-1] + bytes([raw[-1] ^ 1])
                self.send_response(200)
                self.end_headers()
                self.wfile.write(raw)
            def log_message(self, *args):
                pass
        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def run(self, args, **options):
        self.calls.append(args)
        binary = not options.get('text', True)
        def result(payload='', code=0):
            if binary and isinstance(payload, str):
                payload = payload.encode()
            return subprocess.CompletedProcess(args, code, payload, b'' if binary else '')
        if args[1:3] == ['release', 'create']:
            if self.created or self.existing:
                return result(code=1)
            self.created = True
            self.tag = args[3]
            self.preview = '--prerelease' in args
            for identity, arg in enumerate(args[4:args.index('--repo')], 1):
                path = Path(arg)
                self.assets[identity] = path.read_bytes()
                self.names[identity] = path.name
                if path.name.endswith('-release-bundle.zip'):
                    with zipfile.ZipFile(path) as archive:
                        assert 'release.json' in archive.namelist()
                        assert 'packages/codex/ai-one/plugin.json' in archive.namelist()
            if self.move_tag:
                self.revision = 'b' * 40
            return result('https://github.com/example/ai-code/releases/tag/' + self.tag)
        if args[1:3] == ['release', 'edit']:
            if self.fail_edit:
                return result(code=1)
            self.public = True
            return result()
        if '--paginate' in args:
            return result('ai-one/v1.0.4-preview.2\n' if self.existing else '')
        endpoint = args[2]
        if '/git/ref/tags/' in endpoint:
            return result(json.dumps({'object': {'type': 'commit', 'sha': self.revision}}))
        if '/releases/assets/' in endpoint:
            identity = int(endpoint.rsplit('/', 1)[1])
            with urlopen(f'http://127.0.0.1:{self.server.server_port}/{identity}', timeout=5) as response:
                raw = response.read()
            if self.move_tag_on_download:
                self.revision = 'b' * 40
            return result(raw)
        if '/releases/tags/' in endpoint:
            if self.public and self.fail_after_edit:
                return result(code=1)
            assets = [{'id': identity, 'name': self.names[identity], 'size': len(raw), 'state': 'uploaded'}
                      for identity, raw in self.assets.items()]
            if self.missing:
                assets.pop()
            return result(json.dumps({'id': 73, 'tag_name': self.tag, 'draft': not self.public,
                                      'prerelease': self.preview != self.wrong_kind, 'assets': assets}))
        raise AssertionError(args)


class ReleasePublishTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="ai-release-publication-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.root = self.base / 'source'
        self.plugin = release_plugin(self.root)
        product_path = self.plugin / 'product.json'
        product = json.loads(product_path.read_text())
        product['repository'] = 'https://github.com/example/ai-code'
        write_json(product_path, product)
        self.bundle = self.base / 'bundle'

    def git(self, *args):
        return subprocess.check_output(['git', '-c', 'user.name=Fixture', '-c',
            'user.email=fixture@example.com', *args], cwd=self.root, text=True).strip()

    def fixture(self, version='1.0.4-preview.2', accepted=False):
        for path in (self.plugin / 'product.json', *sorted((self.plugin / 'adapters').glob('*/plugin.json'))):
            write_json(path, dict(json.loads(path.read_text()), version=version))
        spec = load_catalog(self.root)[0]
        if accepted:
            config = json.loads((self.plugin / 'release.json').read_text())
            for host in spec.hosts:
                raw = f'release/{host}-raw.txt'
                (self.plugin / raw).write_text(f'fixture host evidence {host}')
                record = {'schema_version': 1, 'status': 'accepted', 'host': host, 'version': spec.version,
                    'source_tree_hash': spec.source_tree_hash,
                    'package_content_hash': io.sha256(io.canonical_json(file_hashes(package_files(spec, host)))),
                    'host_version': 'fixture-1', 'summary': 'Fixture acceptance only.',
                    'artifacts': [{'path': raw, 'sha256': io.sha256((self.plugin / raw).read_bytes())}]}
                evidence = f'release/{host}-accepted.json'
                write_json(self.plugin / evidence, record)
                config['acceptance'][host] = evidence
            write_json(self.plugin / 'release.json', config)
        self.git('init', '-q', '-b', 'main')
        self.git('add', '.')
        self.git('commit', '-q', '-m', 'frozen fixture')
        self.revision = self.git('rev-parse', 'HEAD')
        self.tag = 'ai-one/v' + version
        self.git('tag', self.tag)
        self.git('update-ref', 'refs/remotes/origin/main', self.revision)
        self.github = FakeGitHub(self.revision)
        self.addCleanup(self.github.close)
        return prepare.prepare(self.root, 'ai-one', self.tag, self.bundle)

    def call(self, **options):
        return publish.publish_release(self.root, 'ai-one', self.tag, self.bundle,
                                       'example/ai-code', run=self.github.run, **options)

    def test_supplied_draft_receipt_cannot_publish_to_a_different_repository(self):
        self.fixture()
        receipt = publish.drafts.create_draft(self.root, 'ai-one', self.bundle,
            'example/ai-code', run=self.github.run)
        before = len(self.github.calls)
        with self.assertRaisesRegex(ValueError, 'repository'):
            publish.publish_release(self.root, 'ai-one', self.tag, self.bundle,
                'other/repo', run=self.github.run, draft_result=receipt)
        self.assertEqual(len(self.github.calls), before)

    def test_preview_is_prepared_as_draft_and_published_after_all_http_bytes_match(self):
        prepared = self.fixture()
        self.assertEqual((prepared['kind'], prepared['mode']), ('preview', 'draft'))
        report = self.call()
        self.assertTrue(report['ok'], report)
        self.assertFalse(report['draft'])
        self.assertTrue(report['prerelease'])
        self.assertEqual(report['assets_verified'], 11)
        self.assertEqual(sum(args[1:3] == ['release', 'edit'] for args in self.github.calls), 1)
        self.assertTrue(any('/releases/assets/' in args[2] for args in self.github.calls if args[1] == 'api'))

    def test_stable_requires_actual_byte_bound_fixture_acceptance_and_publishes_without_preview(self):
        prepared = self.fixture('1.0.4', accepted=True)
        self.assertEqual((prepared['kind'], prepared['mode']), ('stable', 'stable'))
        report = self.call()
        self.assertTrue(report['ok'], report)
        self.assertFalse(report['prerelease'])
        edit = next(args for args in self.github.calls if args[1:3] == ['release', 'edit'])
        self.assertIn('--prerelease=false', edit)

    def test_separate_draft_and_publish_steps_reverify_the_receipt_without_recreating_release(self):
        self.fixture()
        receipt = publish.drafts.create_draft(self.root, 'ai-one', self.bundle,
                                             'example/ai-code', run=self.github.run)
        receipt = json.loads(json.dumps(receipt))
        report = self.call(draft_result=receipt)
        self.assertTrue(report['ok'], report)
        self.assertEqual(sum(args[1:3] == ['release', 'create'] for args in self.github.calls), 1)
        self.assertEqual(sum(args[1:3] == ['release', 'edit'] for args in self.github.calls), 1)

    def test_new_numeric_version_without_acceptance_cannot_prepare_or_contact_github(self):
        with self.assertRaisesRegex(ValueError, 'stable'):
            self.fixture('1.0.2')
        self.assertEqual(self.github.calls, [])
        self.assertFalse(self.bundle.exists())

    def test_corrupt_same_length_asset_is_never_published(self):
        self.fixture()
        self.github.corrupt = True
        report = self.call()
        self.assertFalse(report['ok'], report)
        self.assertTrue(report['draft'])
        self.assertIn('bytes differ', report['error'])
        self.assertFalse(self.github.public)

    def test_missing_assets_and_wrong_prerelease_flags_leave_draft_unpublished(self):
        self.fixture()
        self.github.missing = True
        report = self.call()
        self.assertFalse(report['ok'], report)
        self.assertFalse(self.github.public)
        self.github.missing = False
        self.github.wrong_kind = True
        receipt = {'ok': True, 'draft': True, 'tag': self.tag, 'kind': 'preview',
                   'revision': self.revision, 'assets_sha256':
                   {self.github.names[key]: io.sha256(raw) for key, raw in self.github.assets.items()}}
        report = self.call(draft_result=receipt)
        self.assertFalse(report['ok'], report)
        self.assertFalse(self.github.public)

    def test_existing_same_version_is_never_overwritten(self):
        self.fixture()
        self.github.existing = True
        with self.assertRaisesRegex(ValueError, 'already exists'):
            self.call()
        self.assertFalse(self.github.created)

    def test_remote_tag_move_after_draft_upload_prevents_publication(self):
        self.fixture()
        self.github.move_tag = True
        report = self.call()
        self.assertFalse(report['ok'], report)
        self.assertTrue(report['draft'])
        self.assertFalse(self.github.public)

    def test_remote_tag_move_during_asset_readback_prevents_publication(self):
        self.fixture()
        self.github.move_tag_on_download = True
        report = self.call()
        self.assertFalse(report['ok'], report)
        self.assertIn('tag', report['error'])
        self.assertFalse(self.github.public)

    def test_publication_failure_has_uncertain_remote_outcome_and_does_not_retry(self):
        self.fixture()
        self.github.fail_edit = True
        report = self.call()
        self.assertFalse(report['ok'], report)
        self.assertIsNone(report['draft'])
        self.assertIsNone(report['published'])
        self.assertIn('uncertain', report['publication_outcome'])
        self.assertEqual(sum(args[1:3] == ['release', 'edit'] for args in self.github.calls), 1)

    def test_failed_public_readback_does_not_claim_completed_publication(self):
        self.fixture()
        self.github.fail_after_edit = True
        report = self.call()
        self.assertFalse(report['ok'], report)
        self.assertIsNone(report['published'])
        self.assertIn('uncertain', report['publication_outcome'])
        self.assertTrue(self.github.public)

    def test_source_tag_must_match_frozen_checkout_and_be_reachable_from_main(self):
        self.fixture()
        source = load_catalog(self.root)[0]
        with self.assertRaisesRegex(ValueError, 'canonical'):
            prepare.source_binding(self.root, source, 'other/v1.0.4-preview.2')
        self.git('update-ref', '-d', 'refs/remotes/origin/main')
        with self.assertRaisesRegex(ValueError, 'reachable'):
            prepare.source_binding(self.root, source, self.tag)
        unrelated = self.git('commit-tree', self.git('rev-parse', 'HEAD^{tree}'), '-m', 'unrelated main')
        self.git('update-ref', 'refs/remotes/origin/main', unrelated)
        with self.assertRaisesRegex(ValueError, 'reachable'):
            prepare.source_binding(self.root, source, self.tag)
