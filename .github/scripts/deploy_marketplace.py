"""Plan by default; deploy only public, verified releases at an approved market base."""

import argparse
import base64
from io import BytesIO
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile
from urllib.parse import quote, urlsplit
from urllib.request import Request, urlopen, HTTPRedirectHandler, build_opener
from urllib.error import HTTPError
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'tooling'))
from plugin_tools import io
from plugin_tools.registry import load_catalog, select_plugins
from plugin_tools.release import verify_release
from plugin_tools.release.integrity import read_tree
from plugin_tools.release.integrity import historical

SHA = re.compile(r'[0-9a-f]{40}')
REPO = re.compile(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+')
LIMIT = 256 * 1024 * 1024


class DeploymentFailure(io.ToolError):
    def __init__(self, error, result):
        super().__init__(str(error))
        self.result = dict(result, ok=False, error=str(error))
        if getattr(error, 'attempted_revision', None):
            self.result['attempted_revision'] = error.attempted_revision
            self.result['write_outcome'] = 'uncertain; inspect remote before retrying'


def asset_url(url, repository, tag, name):
    expected = f'https://github.com/{repository}/releases/download/{quote(tag, safe="")}/{quote(name, safe="")}'
    # GitHub sometimes leaves slash-bearing tags unescaped in browser_download_url.
    alternate = f'https://github.com/{repository}/releases/download/{quote(tag, safe="/")}/{quote(name, safe="")}'
    if url not in (expected, alternate) or urlsplit(url).query or urlsplit(url).fragment:
        raise io.DataError('release asset URL is not bound to this repository/tag/name')
    return url


class AssetRedirects(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, newurl):
        parsed = urlsplit(newurl)
        if parsed.scheme != 'https' or parsed.hostname not in {
                'github.com', 'release-assets.githubusercontent.com', 'objects.githubusercontent.com'}:
            raise io.DataError('unexpected release asset redirect')
        return super().redirect_request(request, fp, code, msg, headers, newurl)


class GitHub:
    """REST reads and anonymous asset downloads; no API mutation capability."""
    def __init__(self, repository):
        if not REPO.fullmatch(repository):
            raise io.DataError('GitHub repository must be OWNER/REPO')
        self.repository = repository

    def get(self, relative, missing=False):
        headers = {'Accept': 'application/vnd.github+json', 'User-Agent': 'ai-code-marketplace'}
        token = os.environ.get('GH_TOKEN') or os.environ.get('GITHUB_TOKEN')
        if token:
            headers['Authorization'] = 'Bearer ' + token
        request = Request(f'https://api.github.com/repos/{self.repository}/{relative}', headers=headers)
        try:
            with urlopen(request, timeout=30) as response:
                raw = response.read(16 * 1024 * 1024 + 1)
            if len(raw) > 16 * 1024 * 1024:
                raise io.DataError('GitHub response exceeds limit')
            return io.parse_json(raw, what='GitHub response')
        except HTTPError as exc:
            if missing and exc.code == 404:
                return None
            raise io.DataError(f'GitHub read failed: HTTP {exc.code}') from exc

    def tag(self, tag):
        obj = self.get('git/ref/tags/' + quote(tag, safe=''))['object']
        seen = set()
        while obj.get('type') == 'tag':
            value = obj.get('sha', '')
            if not SHA.fullmatch(value) or value in seen or len(seen) >= 8:
                raise io.DataError('invalid annotated source tag')
            seen.add(value)
            obj = self.get('git/tags/' + value)['object']
        if obj.get('type') != 'commit' or not SHA.fullmatch(obj.get('sha', '')):
            raise io.DataError('source tag must resolve to a GitHub commit')
        return obj['sha']

    def release(self, tag):
        if self.get('').get('visibility') != 'public':
            raise io.DataError('anonymous distribution requires a public repository')
        value = self.get('releases/tags/' + quote(tag, safe=''))
        if value.get('draft') is not False or value.get('tag_name') != tag:
            raise io.DataError('market deployment requires the exact public Release')
        return value

    def download(self, asset, tag):
        url = asset_url(asset['browser_download_url'], self.repository, tag, asset['name'])
        size = asset.get('size')
        if type(size) is not int or not 0 <= size <= LIMIT:
            raise io.DataError('invalid release asset size')
        request = Request(url, headers={'User-Agent': 'ai-code-marketplace'})
        with build_opener(AssetRedirects()).open(request, timeout=60) as response:
            raw = response.read(LIMIT + 1)
        if len(raw) != size or len(raw) > LIMIT:
            raise io.DataError('release asset size differs from GitHub metadata')
        return raw

    def market(self, branch):
        if SHA.fullmatch(branch):
            revision = branch
        else:
            reference = self.get('git/ref/heads/' + quote(branch, safe=''), missing=True)
            if reference is None:
                return 'absent', {}
            revision = reference['object']['sha']
        if not SHA.fullmatch(revision):
            raise io.DataError('invalid market revision')
        commit = self.get('git/commits/' + revision)
        tree = self.get('git/trees/' + commit['tree']['sha'] + '?recursive=1')
        if tree.get('truncated') is not False or len(tree.get('tree', [])) > 20000:
            raise io.DataError('market Git tree is incomplete or too large')
        files = {}
        total = 0
        for entry in tree['tree']:
            if entry['type'] == 'tree':
                continue
            name = io.relative_path(entry['path'])
            if entry['type'] != 'blob' or entry['mode'] not in ('100644', '100755') or name in files:
                raise io.DataError('market contains a link, special or duplicate file')
            blob = self.get('git/blobs/' + entry['sha'])
            if blob.get('encoding') != 'base64':
                raise io.DataError('unsupported GitHub blob encoding')
            raw = base64.b64decode(''.join(blob['content'].split()), validate=True)
            total += len(raw)
            if len(raw) != blob['size'] or total > LIMIT:
                raise io.DataError('market blob bytes exceed declared limit')
            files[name] = raw
        return revision, files


def extract_bundle(raw, output):
    output = Path(output)
    if output.exists():
        raise io.DataError('release extraction requires an absent directory')
    try:
        with zipfile.ZipFile(BytesIO(raw)) as archive:
            entries = archive.infolist()
            names = [io.relative_path(entry.filename) for entry in entries]
            if len(names) != len(set(names)) or len(entries) > 20000 or sum(x.file_size for x in entries) > LIMIT:
                raise io.DataError('release archive closure or size is invalid')
            if any(not stat.S_ISREG(x.external_attr >> 16) for x in entries):
                raise io.DataError('release archive contains a link or nonregular file')
            output.mkdir()
            for entry in entries:
                destination = output / entry.filename
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_bytes(archive.read(entry))
    except (zipfile.BadZipFile, RuntimeError, ValueError) as exc:
        raise io.DataError('invalid release archive') from exc


class GitWriter:
    """Write a reviewed full tree using ordinary Git fast-forward pushes."""
    def __init__(self, repository, origin=None):
        if not REPO.fullmatch(repository):
            raise io.DataError('invalid GitHub repository')
        self.repository = repository
        self.origin = origin or f'https://github.com/{repository}.git'

    def publish(self, branch, expected, files, message, removals=()):
        if branch not in ('codex/marketplace', 'codex/marketplace-preview'):
            raise io.DataError('unsupported distribution branch')
        if expected != 'absent' and not SHA.fullmatch(expected):
            raise io.DataError('expected market commit is invalid')
        removable = {'.claude-plugin/marketplace.json', '.agents/plugins/marketplace.json', 'marketplace.json'}
        if not set(removals).issubset(removable) or len(set(removals)) != len(removals) or expected == 'absent' and removals:
            raise io.DataError('only explicitly reviewed managed market entries may be removed')
        env = dict(os.environ, GIT_TERMINAL_PROMPT='0')
        token = env.get('GH_TOKEN') or env.get('GITHUB_TOKEN')
        if token and self.origin.startswith('https://github.com/'):
            encoded = base64.b64encode(('x-access-token:' + token).encode()).decode()
            env.update(GIT_CONFIG_COUNT='1', GIT_CONFIG_KEY_0='http.https://github.com/.extraheader',
                       GIT_CONFIG_VALUE_0='AUTHORIZATION: basic ' + encoded)
        with tempfile.TemporaryDirectory(prefix='ai-market-git-') as temporary:
            work = Path(temporary)
            def git(*args, check=True):
                result = subprocess.run(['git', '-c', 'core.hooksPath=/dev/null',
                    '-c', 'commit.gpgsign=false', *args], cwd=work, env=env,
                    capture_output=True, text=True, timeout=60)
                if check and result.returncode:
                    # Never print stderr which might contain credential-bearing URLs.
                    raise io.ConflictError('Git operation failed; read the remote branch before retrying')
                return result
            git('init', '--quiet')
            current = git('ls-remote', self.origin, 'refs/heads/' + branch).stdout.strip()
            actual = current.split()[0] if current else 'absent'
            if actual != expected:
                raise io.ConflictError('market changed since the approved plan')
            if expected != 'absent':
                git('fetch', '--quiet', '--depth=1', self.origin, 'refs/heads/' + branch)
                if git('rev-parse', 'FETCH_HEAD').stdout.strip() != expected:
                    raise io.ConflictError('market changed during fetch')
                git('checkout', '--quiet', '--detach', expected)
                tracked = set(filter(None, git('ls-files', '-z').stdout.split('\0')))
                if tracked - set(files) != set(removals):
                    raise io.DataError('removed files differ from the reviewed managed market entries')
                if removals:
                    git('rm', '--', *sorted(removals))
            for name, raw in files.items():
                io.relative_path(name)
                if name == '.git' or name.startswith('.git/'):
                    raise io.DataError('distribution cannot write Git internals')
                destination = work / name
                destination.parent.mkdir(parents=True, exist_ok=True)
                if destination.is_symlink():
                    raise io.DataError('distribution destination is a symlink')
                destination.write_bytes(raw)
            git('add', '--all')
            if expected != 'absent' and git('diff', '--cached', '--quiet', check=False).returncode == 0:
                return expected
            git('-c', 'user.name=ai-code-release', '-c',
                'user.email=41898282+github-actions[bot]@users.noreply.github.com',
                'commit', '--quiet', '-m', message)
            revision = git('rev-parse', 'HEAD').stdout.strip()
            # No --force; concurrent commits cannot be replaced by this push.
            try:
                git('push', '--quiet', self.origin, 'HEAD:refs/heads/' + branch)
                observed = git('ls-remote', self.origin, 'refs/heads/' + branch).stdout.strip().split()
                if not observed or observed[0] != revision:
                    raise io.ConflictError('market changed after push; inspect actual remote state')
            except (io.ToolError, OSError, IndexError, subprocess.TimeoutExpired) as exc:
                exc.attempted_revision = revision
                raise
            return revision


def verify_pinned_trees(api, previous):
    cached = {}
    for path, raw in previous.items():
        if not path.startswith('records/'):
            continue
        record = io.parse_json(raw, what=path)
        revision = record['codex_revision']
        if revision is None:
            continue
        if revision not in cached:
            _, cached[revision] = api.market(revision)
        prefix = f"plugins/codex/{record['product_id']}/{record['version']}/"
        actual = {name: value for name, value in cached[revision].items() if name.startswith(prefix)}
        expected = {name: previous[name] for name in record['codex_files']}
        if actual != expected:
            raise io.DataError('previous pinned Codex commit differs from its recorded file closure')


def verify_history(api, spec, bundle, root, previous, directory, channel):
    """Bind the prior recorded version to its actual public bundle and Git content."""
    paths = [name for name in previous if name.startswith(f'records/{spec.product_id}/')]
    if not paths:
        return
    records = [io.parse_json(previous[name], what=name) for name in paths]
    record = max(records, key=lambda item: tuple(map(int, item['version'].split('.'))))
    if record['version'] == spec.version:
        return  # Current bytes were already reverified from the public Release above.
    tag = record['tag']
    release = api.release(tag)
    if release['id'] != record['release_id'] or release['prerelease'] != (channel == 'preview') or api.tag(tag) != record['source_revision']:
        raise io.DataError('previous public Release/tag differs from the recorded version')
    prefix = f"{spec.product_id}-{record['version']}-release-bundle"
    archive_name, checksum_name = prefix + '.zip', prefix + '.sha256'
    assets = {asset['name']: asset for asset in release['assets']}
    if archive_name not in assets or checksum_name not in assets:
        raise io.DataError('previous public Release lacks its complete bundle')
    raw = api.download(assets[archive_name], tag)
    checksum = api.download(assets[checksum_name], tag)
    if checksum != f'{io.sha256(raw)}  {archive_name}\n'.encode():
        raise io.DataError('previous public bundle checksum differs')
    target = directory / 'previous'
    extract_bundle(raw, target)
    manifest, _ = historical(target / 'release.json')
    if manifest['source_revision'] != record['source_revision'] or manifest['source_tree_hash'] != record['source_tree_hash']:
        raise io.DataError('previous bundle provenance differs from public record')
    if manifest['readiness']['package_content_hashes'] != record['readiness']['package_content_hashes']:
        raise io.DataError('previous bundle package hashes differ from public record')
    report = verify_release(root, spec, bundle, previous=target / 'release.json')
    if not report['ok']:
        raise io.DataError('current version failed verified historical comparison')


def deploy(root, plugin_id, source_tag, channel, api, *, action='plan',
           expected_plan_hash=None, expected_market_commit=None, writer=None):
    if action not in ('plan', 'deploy'):
        raise io.DataError('action must be plan or deploy')
    if action == 'deploy' and (not re.fullmatch(r'[0-9a-f]{64}', expected_plan_hash or '') or
            not (expected_market_commit == 'absent' or SHA.fullmatch(expected_market_commit or ''))):
        raise io.DataError('deploy requires reviewed plan hash and market commit')
    from plugin_tools.distribution import load_config, plan_distribution, stage_files, finalize_files, check_plan
    root = Path(root).resolve()
    spec = select_plugins(load_catalog(root), plugin_id)[0]
    if source_tag != f'{spec.product_id}/v{spec.version}':
        raise io.DataError('source tag differs from the selected plugin version')
    config = load_config(root)
    if channel not in config['channels']:
        raise io.DataError('unknown channel')
    source_sha = api.tag(source_tag)
    head = subprocess.run(['git', 'rev-parse', 'HEAD'], cwd=root, capture_output=True, text=True, timeout=10)
    if head.returncode or head.stdout.strip() != source_sha:
        raise io.DataError('trusted source checkout differs from remote source tag')
    ancestry = subprocess.run(['git', 'merge-base', '--is-ancestor', source_sha, 'origin/main'],
                              cwd=root, capture_output=True, timeout=10)
    if ancestry.returncode:
        raise io.DataError('source release must be reachable from trusted origin/main')
    release = api.release(source_tag)
    assets = release.get('assets', [])
    names = [a['name'] for a in assets]
    if len(names) != len(set(names)):
        raise io.DataError('duplicate Release asset names')
    required = [f'{spec.product_id}-{spec.version}-release-bundle.zip',
                f'{spec.product_id}-{spec.version}-release-bundle.sha256',
                'release.json', 'release-notes.md', 'SHA256SUMS']
    required += [f'{spec.product_id}-{spec.version}-{host}-plugin.zip' for host in spec.hosts]
    required += [f'{spec.product_id}-{spec.version}-{host}.zip' for host in spec.hosts]
    if not set(required).issubset(names):
        raise io.DataError('public Release is missing required assets')
    payload = {name: api.download(next(a for a in assets if a['name'] == name), source_tag) for name in required}
    archive = required[0]
    if payload[required[1]] != f'{io.sha256(payload[archive])}  {archive}\n'.encode():
        raise io.DataError('complete bundle checksum differs from downloaded bytes')
    with tempfile.TemporaryDirectory(prefix='ai-market-bundle-') as temporary:
        bundle = Path(temporary) / 'bundle'
        extract_bundle(payload[archive], bundle)
        report = verify_release(root, spec, bundle)
        if not report['ok']:
            raise io.DataError('public Release differs from trusted source: ' + '; '.join(report['blockers']))
        for name in ('release.json', 'release-notes.md', 'SHA256SUMS'):
            if payload[name] != io.read_file(bundle, name):
                raise io.DataError('public standalone asset differs from complete bundle')
        for host in spec.hosts:
            for directory, suffix in (('installers', '-plugin'), ('downloads', '')):
                name = f'{spec.product_id}-{spec.version}-{host}{suffix}.zip'
                if payload[name] != io.read_file(bundle, f'{directory}/{name}', limit=LIMIT):
                    raise io.DataError('public installer/download differs from complete bundle')
        info = {key: release[key] for key in ('id', 'tag_name', 'draft', 'prerelease', 'html_url')}
        canonical_url = f'https://github.com/{api.repository}/releases/tag/{quote(source_tag, safe="")}'
        if info['html_url'] not in (canonical_url, f'https://github.com/{api.repository}/releases/tag/{quote(source_tag, safe="/")}'):
            raise io.DataError('Release page does not belong to the selected source tag')
        info['html_url'] = canonical_url
        info['assets'] = [dict(id=a['id'], name=a['name'], size=a['size'],
            browser_download_url=f'https://github.com/{api.repository}/releases/download/{quote(source_tag, safe="")}/{quote(a["name"], safe="")}',
            sha256=io.sha256(payload[a['name']])) for a in assets if a['name'] in payload]
        branch = config['channels'][channel]['branch']
        base, previous = api.market(branch)
        plan = plan_distribution(root, spec, bundle, info, channel, previous, base)
        verify_pinned_trees(api, previous)
        verify_history(api, spec, bundle, root, previous, Path(temporary), channel)
        if action == 'plan':
            return plan
        if plan['status'] == 'already_deployed':
            check_plan(plan)
            return {'ok': True, 'status': 'already_deployed', 'product_id': spec.product_id,
                'version': spec.version, 'channel': channel, 'branch': branch,
                'source_revision': source_sha, 'distribution_revision': plan['record']['codex_revision'],
                'market_commit': base, 'release_url': info['html_url'], 'plan_hash': plan['plan_hash']}
        check_plan(plan, expected_plan_hash, expected_market_commit)
        writer = writer or GitWriter(api.repository)
        if api.tag(source_tag) != source_sha:
            raise io.ConflictError('source tag moved before deployment')
        staged = stage_files(plan)
        distribution_sha = base if 'codex' in plan['record']['hosts'] and not staged and base != 'absent' else None
        current = base
        progress = {'ok': False, 'status': 'published_pending_marketplace',
            'product_id': spec.product_id, 'version': spec.version, 'channel': channel,
            'branch': branch, 'source_revision': source_sha, 'release_url': info['html_url'],
            'plan_hash': plan['plan_hash'], 'base_commit': base,
            'distribution_revision': distribution_sha, 'market_commit': None, 'phase': 'staging_distribution'}
        try:
            if staged:
                current = writer.publish(branch, base, {**previous, **staged}, f'Stage {spec.product_id} {spec.version}')
                distribution_sha = current
                progress.update(distribution_revision=current, phase='verifying_distribution')
                staged_sha, actual = api.market(branch)
                if staged_sha != current or actual != {**previous, **staged}:
                    raise io.ConflictError('staged distribution differs from intended content')
            final = finalize_files(plan, distribution_sha)
            if api.tag(source_tag) != source_sha:
                raise io.ConflictError('source tag moved before catalog publication')
            progress['phase'] = 'publishing_catalog'
            removed_markets = sorted(set(previous) - set(final))
            catalog_sha = writer.publish(branch, current, final,
                f'Deploy {spec.product_id} {spec.version} to {channel}', removals=removed_markets)
            progress.update(market_commit=catalog_sha, phase='verifying_catalog')
            observed, actual = api.market(branch)
            if observed != catalog_sha or actual != final:
                raise io.ConflictError('final market differs from intended deployment')
        except (io.ToolError, OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired) as exc:
            raise DeploymentFailure(exc, progress) from exc
        return {'ok': True, 'status': 'marketplace_deployed', 'product_id': spec.product_id,
                'version': spec.version, 'channel': channel, 'branch': branch,
                'source_revision': source_sha, 'distribution_revision': distribution_sha,
                'market_commit': catalog_sha, 'release_url': release['html_url'], 'plan_hash': plan['plan_hash']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path.cwd())
    parser.add_argument('--plugin', required=True)
    parser.add_argument('--source-tag', required=True)
    parser.add_argument('--channel', choices=('preview', 'stable'), required=True)
    parser.add_argument('--action', choices=('plan', 'deploy'), default='plan')
    parser.add_argument('--expected-plan-hash')
    parser.add_argument('--expected-market-commit')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        if args.output and (args.output.exists() or args.output.is_symlink() or not args.output.parent.is_dir()):
            raise io.ConflictError('output must be absent in an existing directory')
        spec = select_plugins(load_catalog(args.root), args.plugin)[0]
        from plugin_tools.distribution import repository_url
        repository = urlsplit(repository_url(spec.manifest['repository'])).path.strip('/')
        result = deploy(args.root, args.plugin, args.source_tag, args.channel, GitHub(repository),
            action=args.action, expected_plan_hash=args.expected_plan_hash,
            expected_market_commit=args.expected_market_commit)
        code = 0
    except (io.ToolError, OSError, ValueError, KeyError, TypeError, subprocess.TimeoutExpired) as exc:
        result = getattr(exc, 'result', {'ok': False,
            'status': 'conflict' if isinstance(exc, io.ConflictError) else 'blocked', 'error': str(exc)})
        code = 1
    if args.output and not args.output.exists() and not args.output.is_symlink():
        try:
            with args.output.open('xb') as destination:
                destination.write(io.dump_json(result))
        except OSError:
            result['output_error'] = 'Could not save result; retained complete state in console output'
            code = 1
    # Console summary excludes encoded public file payloads.
    print(json.dumps({k: v for k, v in result.items() if k not in ('existing_files', 'codex_files')},
                     ensure_ascii=False, indent=2))
    return code


if __name__ == '__main__':
    raise SystemExit(main())
