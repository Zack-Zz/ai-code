"""Read back every uploaded Draft asset before explicitly publishing a release."""

import argparse
import json
from pathlib import Path
import subprocess
import sys
import tempfile
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parent))
import create_release_draft as drafts

LIMIT = 256 * 1024 * 1024


def publish_release(root, plugin_id, source_tag, bundle, repository, run=None, draft_result=None):
    run = subprocess.run if run is None else run
    root = Path(root).resolve()
    specs = drafts.load_catalog(root)
    spec = drafts.select_plugins(specs, plugin_id)[0]
    tag = f"{spec.product_id}/v{spec.version}"
    if source_tag != tag:
        raise ValueError("source tag differs from the selected plugin version")
    if not drafts.re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("GitHub repository must be OWNER/REPO")
    drafts.bind_repository(specs, repository)

    def gh(*args, binary=False):
        result = run(["gh", *args], cwd=root, capture_output=True, text=not binary, timeout=60)
        if result.returncode:
            raise ValueError("GitHub command failed; no retry or overwrite attempted")
        return result.stdout

    with tempfile.TemporaryDirectory(prefix="ai-release-publish-") as temporary:
        private = Path(temporary)
        captured = private / "bundle"
        captured.mkdir()
        for name, payload in drafts.read_tree(bundle).items():
            path = captured / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
        verified = drafts.verify_release(root, spec, captured, committed_acceptance=True)
        drafts._eligible(verified, tag)
        kind = drafts.release_policy(spec, verified)
        drafts._current_source(root, spec, verified, tag)
        expected = {path.name: path.read_bytes() for path in drafts.release_assets(captured, private, spec)}
        result = drafts.create_draft(root, plugin_id, captured, repository, run=run) if draft_result is None else draft_result
        if not result.get("ok"):
            return result
        edited = False
        try:
            if result.get("draft") is not True or result.get("tag") != tag or result.get("kind") != kind or \
                    result.get("revision") != verified["source_revision"] or \
                    result.get("assets_sha256") != {name: drafts.io.sha256(raw) for name, raw in expected.items()}:
                raise ValueError("Draft receipt differs from the independently verified bundle")

            def read_release(public=False):
                release = json.loads(gh("api", f"repos/{repository}/releases/tags/{quote(tag, safe='')}"))
                if type(release.get("id")) is not int or release["id"] <= 0 or release.get("tag_name") != tag or \
                        release.get("draft") is not (not public) or release.get("prerelease") is not (kind == "preview"):
                    raise ValueError("remote Release identity, draft or prerelease state differs from its version")
                assets = release.get("assets")
                if not isinstance(assets, list) or len(assets) != len(expected) or \
                        {item.get("name") for item in assets} != set(expected):
                    raise ValueError("remote release asset inventory differs from the verified bundle")
                ids = set()
                for asset in assets:
                    identity = asset.get("id")
                    raw = expected[asset["name"]]
                    if type(identity) is not int or identity <= 0 or identity in ids or asset.get("state") != "uploaded" or \
                            type(asset.get("size")) is not int or asset["size"] != len(raw) or len(raw) > LIMIT:
                        raise ValueError("invalid remote asset identity, state or size")
                    ids.add(identity)
                    downloaded = gh("api", f"repos/{repository}/releases/assets/{identity}",
                                    "-H", "Accept: application/octet-stream", binary=True)
                    if downloaded != raw:
                        raise ValueError("uploaded release asset bytes differ from the verified bundle: " + asset["name"])
                return release

            before = read_release()
            final = drafts.verify_release(root, spec, captured, committed_acceptance=True)
            drafts._eligible(final, tag)
            drafts.release_policy(spec, final)
            drafts._current_source(root, spec, final, tag)
            drafts._bind_remote(gh, repository, tag, verified["source_revision"])
            current = read_release()
            if current["id"] != before["id"]:
                raise ValueError("Release changed after attachment verification")
            edited = True
            gh("release", "edit", tag, "--repo", repository, "--verify-tag", "--draft=false",
               f"--prerelease={'true' if kind == 'preview' else 'false'}")
            public = read_release(public=True)
            if public["id"] != before["id"]:
                raise ValueError("published Release identity differs from the reviewed Draft")
            drafts._bind_remote(gh, repository, tag, verified["source_revision"])
            return dict(result, ok=True, draft=False, published=True, release_id=public["id"],
                        prerelease=kind == "preview", assets_verified=len(expected))
        except (drafts.io.ToolError, OSError, ValueError, TypeError, KeyError, AttributeError, subprocess.SubprocessError) as exc:
            failure = dict(result, ok=False, error=str(exc), published=False)
            if edited:
                failure["draft"] = None
                failure["published"] = None
                failure["publication_outcome"] = "uncertain; inspect the remote Release before retrying"
            return failure


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--plugin", required=True)
    parser.add_argument("--source-tag", required=True)
    parser.add_argument("--bundle", required=True, type=Path)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--draft-result", type=Path, required=True)
    args = parser.parse_args()
    try:
        receipt = json.loads(args.draft_result.read_text())
        result = publish_release(args.root, args.plugin, args.source_tag, args.bundle,
                                 args.repository, draft_result=receipt)
    except (drafts.io.ToolError, OSError, ValueError, TypeError, KeyError, AttributeError, subprocess.SubprocessError) as exc:
        result = {"ok": False, "error": str(exc)}
    print(json.dumps(result, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
