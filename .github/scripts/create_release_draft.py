"""Explicitly requested GitHub draft creation; never publishes or creates tags."""

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tooling"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from plugin_tools import io
from plugin_tools.registry import load_catalog, select_plugins
from plugin_tools.release import verify_release
from plugin_tools.release import metadata, source_git
from plugin_tools.release.integrity import read_tree, record
from plugin_tools.release.layout import zip_bytes
from plugin_tools.versions import release_kind
from plugin_tools.distribution import repository_url
from prepare_release import source_binding


def release_policy(spec, report):
    kind = release_kind(spec.version)
    mode = "draft" if kind == "preview" else "stable"
    if report.get("mode") != mode or (kind == "stable" and report.get("publication_ready") is not True):
        raise ValueError(f"new {kind} release requires {mode} verification and stable host acceptance where applicable")
    return kind


def release_assets(captured, private, spec):
    payload = read_tree(captured)
    complete = private / f"{spec.product_id}-{spec.version}-release-bundle.zip"
    complete.write_bytes(zip_bytes(payload))
    checksum = private / f"{complete.stem}.sha256"
    checksum.write_text(f"{io.sha256(complete.read_bytes())}  {complete.name}\n")
    assets = [complete, checksum, captured / "release.json", captured / "release-notes.md", captured / "SHA256SUMS"]
    assets.extend(captured / f"downloads/{spec.product_id}-{spec.version}-{host}.zip" for host in spec.hosts)
    if record(payload)["schema_version"] == 2:
        assets.extend(captured / f"installers/{spec.product_id}-{spec.version}-{host}-plugin.zip" for host in spec.hosts)
    return assets


def _eligible(report, tag):
    if not report["ok"] or report.get("working_tree_dirty") is not False or \
            not re.fullmatch(r"[0-9a-f]{40,64}", report.get("source_revision") or "") or report.get("tag") != tag:
        raise ValueError("GitHub draft requires a verified bundle and clean source at its existing identity/version tag")


def _current_source(root, spec, report, tag):
    source_binding(root, spec, tag)
    current = metadata.git_provenance(root, spec.product_id, spec.version, tag)
    _eligible(dict(current, ok=True), tag)
    if current["source_revision"] != report["source_revision"]:
        raise ValueError("current Git source differs from the release bundle commit")
    capture = metadata.capture_release(spec, committed_acceptance=True)
    source_git.validate_head_inputs(root, spec, capture, current["source_revision"])


def _remote_commit(gh, repository, tag):
    reference = json.loads(gh("api", f"repos/{repository}/git/ref/tags/{quote(tag, safe='')}"))["object"]
    seen = set()
    while reference.get("type") == "tag":
        sha = reference.get("sha", "")
        if not re.fullmatch(r"[0-9a-f]{40,64}", sha) or sha in seen or len(seen) >= 8:
            raise ValueError("invalid or cyclic remote annotated tag")
        seen.add(sha)
        reference = json.loads(gh("api", f"repos/{repository}/git/tags/{sha}"))["object"]
    if reference.get("type") != "commit":
        raise ValueError("remote release tag does not resolve to a commit")
    return reference.get("sha")


def _bind_remote(gh, repository, tag, revision):
    if _remote_commit(gh, repository, tag) != revision:
        raise ValueError("remote release tag does not match the reviewed source commit")


def bind_repository(specs, repository):
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("GitHub repository must be OWNER/REPO")
    expected = f"https://github.com/{repository}".lower()
    if any(repository_url(item.manifest["repository"]).lower() != expected for item in specs):
        raise ValueError("publication repository differs from the registered source repository")


def create_draft(root, plugin_id, bundle, repository, run=None):
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("GitHub repository must be OWNER/REPO")
    root = Path(root).resolve()
    specs = load_catalog(root)
    spec = select_plugins(specs, plugin_id)[0]
    bind_repository(specs, repository)
    tag = f"{spec.product_id}/v{spec.version}"
    run = subprocess.run if run is None else run

    def gh(*arguments):
        result = run(["gh", *arguments], cwd=root, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            raise ValueError("GitHub command failed; no retry or overwrite attempted: " + result.stderr.strip())
        return result.stdout

    # Capture into a private upload tree; verify the captured bytes against source.
    # This also preserves native hidden files independently of Actions' defaults.
    with tempfile.TemporaryDirectory(prefix="ai-release-upload-") as temporary:
        private = Path(temporary)
        captured = private / "bundle"
        captured.mkdir()
        for relative, payload in read_tree(bundle).items():
            path = captured / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
        report = verify_release(root, spec, captured, committed_acceptance=True)
        _eligible(report, tag)
        kind = release_policy(spec, report)
        _current_source(root, spec, report, tag)
        revision = report["source_revision"]
        releases = gh("api", "--paginate", f"repos/{repository}/releases", "--jq", ".[].tag_name")
        if tag in releases.splitlines():
            raise ValueError("a release already exists for this plugin version; refusing overwrite")
        _bind_remote(gh, repository, tag, revision)
        # Remote discovery may take time; recheck captured bytes and source before writing.
        final = verify_release(root, spec, captured, committed_acceptance=True)
        _eligible(final, tag)
        release_policy(spec, final)
        if final["source_revision"] != revision:
            raise ValueError("release source changed before draft creation")
        _current_source(root, spec, final, tag)
        assets = release_assets(captured, private, spec)
        _bind_remote(gh, repository, tag, revision)
        channel_flags = ["--prerelease"] if kind == "preview" else []
        response = gh("release", "create", tag, *(str(path) for path in assets),
            "--repo", repository, "--draft", "--verify-tag", "--target", revision,
            "--title", f"{spec.manifest['display_name']} {spec.version}",
            "--notes-file", str(captured / "release-notes.md"), *channel_flags)
        result = {"ok": True, "draft": True, "tag": tag, "url": response.strip(),
                  "kind": kind, "revision": revision, "assets": [path.name for path in assets],
                  "assets_sha256": {path.name: io.sha256(path.read_bytes()) for path in assets}}
        try:
            _bind_remote(gh, repository, tag, revision)
        except (io.ToolError, OSError, ValueError, TypeError, KeyError, AttributeError, subprocess.TimeoutExpired) as exc:
            return dict(result, ok=False, error="Draft was created but final tag verification failed; manual review is required: " + str(exc))
        return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--plugin", required=True)
    parser.add_argument("--bundle", type=Path, required=True)
    parser.add_argument("--repository", required=True)
    args = parser.parse_args()
    try:
        result = create_draft(args.root, args.plugin, args.bundle, args.repository)
    except (io.ToolError, OSError, ValueError, TypeError, KeyError, AttributeError, subprocess.TimeoutExpired) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
