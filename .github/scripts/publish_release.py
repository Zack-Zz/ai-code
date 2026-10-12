"""Verify every remote asset before publishing or reusing an immutable release."""

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


def _release_id(gh, repository, tag):
    # GitHub's tag endpoint serves published releases only. The authenticated
    # list includes drafts; resolve an unambiguous ID and read that resource.
    listing = gh("api", "--paginate", f"repos/{repository}/releases",
                 "--jq", ".[] | [.id, .tag_name] | @tsv")
    matches = []
    for line in listing.splitlines():
        fields = line.split("\t")
        if len(fields) != 2:
            raise ValueError("invalid release identity listing")
        identity, listed_tag = fields
        if listed_tag == tag:
            if not drafts.re.fullmatch(r"[1-9][0-9]*", identity):
                raise ValueError("invalid matching Release ID")
            matches.append(int(identity))
    if len(matches) > 1:
        raise ValueError("ambiguous releases for the selected version tag")
    return matches[0] if matches else None


def _ensure_remote_tag(gh, repository, tag, revision, before_create=None):
    try:
        reference = json.loads(gh("api", f"repos/{repository}/git/ref/tags/{quote(tag, safe='')}"))["object"]
    except drafts.GitHubCommandError as exc:
        if exc.status != 404:
            raise
        # Only a missing reference authorizes creation; an annotated tag's
        # missing object must not be mistaken for an absent reference.
        # POST is create-only. A concurrent creation fails; never force/update.
        if before_create is not None:
            before_create()
        gh("api", f"repos/{repository}/git/refs", "--method", "POST",
           "-f", f"ref=refs/tags/{tag}", "-f", f"sha={revision}")
        drafts._bind_remote(gh, repository, tag, revision)
        return
    if drafts._resolve_remote_commit(gh, repository, reference) != revision:
        raise ValueError("remote release tag does not match the reviewed source commit")


def publish_release(root, plugin_id, source_tag, bundle, repository, run=None, draft_result=None,
                    ensure_tag=False):
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
        return drafts.github_command(run, root, *args, binary=binary)

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
        if any(len(raw) > LIMIT for raw in expected.values()):
            raise ValueError("release asset exceeds the verified readback size limit")
        expected_title = f"{spec.manifest['display_name']} {spec.version}"
        expected_body = expected["release-notes.md"].decode("utf-8")
        digests = {name: drafts.io.sha256(raw) for name, raw in expected.items()}
        result = {"ok": True, "draft": None, "tag": tag, "kind": kind,
                  "revision": verified["source_revision"], "assets": sorted(expected),
                  "assets_sha256": digests, "reused": False}
        edited = False
        observed_public = False
        try:
            if draft_result is not None:
                if not draft_result.get("ok"):
                    return draft_result
                if draft_result.get("draft") is not True or draft_result.get("tag") != tag or draft_result.get("kind") != kind or \
                        draft_result.get("revision") != verified["source_revision"] or \
                        draft_result.get("assets_sha256") != digests:
                    raise ValueError("Draft receipt differs from the independently verified bundle")
                result.update(draft_result)

            def recheck_source():
                final = drafts.verify_release(root, spec, captured, committed_acceptance=True)
                drafts._eligible(final, tag)
                drafts.release_policy(spec, final)
                if final["source_revision"] != verified["source_revision"]:
                    raise ValueError("release source changed before publication")
                drafts._current_source(root, spec, final, tag)

            def read_release(public=None):
                nonlocal observed_public
                release = json.loads(gh("api", f"repos/{repository}/releases/{release_id}"))
                if type(release.get("id")) is not int or release["id"] != release_id or release.get("tag_name") != tag or \
                        type(release.get("draft")) is not bool:
                    raise ValueError("remote Release identity or draft state differs from its version")
                # These fields establish observed remote state even when the
                # source, page or attachment verification subsequently fails.
                result.update(draft=release["draft"], release_id=release["id"],
                              url=f"https://github.com/{repository}/releases/tag/{quote(tag, safe='')}")
                observed_public = observed_public or not release["draft"]
                if (public is not None and release["draft"] is not (not public)) or \
                        release.get("prerelease") is not (kind == "preview"):
                    raise ValueError("remote Release identity, draft or prerelease state differs from its version")
                if release.get("name") != expected_title or release.get("body") != expected_body:
                    raise ValueError("remote Release title or body differs from the verified bundle")
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

            release_id = _release_id(gh, repository, tag)
            existing = release_id is not None
            if draft_result is not None and not existing:
                raise ValueError("the receipted Draft is missing; refusing recreation")
            if existing:
                # Existing releases are read-only until their entire uploaded
                # closure is authenticated. Incomplete uploads need manual review.
                before = read_release()
                result.update(draft=before["draft"], release_id=before["id"], reused=True,
                              url=f"https://github.com/{repository}/releases/tag/{quote(tag, safe='')}")
                recheck_source()
                if ensure_tag:
                    _ensure_remote_tag(gh, repository, tag, verified["source_revision"], recheck_source)
                else:
                    drafts._bind_remote(gh, repository, tag, verified["source_revision"])
            else:
                recheck_source()
                if ensure_tag:
                    _ensure_remote_tag(gh, repository, tag, verified["source_revision"], recheck_source)
                else:
                    drafts._bind_remote(gh, repository, tag, verified["source_revision"])
                result = drafts.create_draft(root, plugin_id, captured, repository, run=run)
                result["reused"] = False
                if not result.get("ok"):
                    return result
                release_id = _release_id(gh, repository, tag)
                if release_id is None:
                    raise ValueError("created Draft is missing from the authenticated release listing")
                before = read_release(public=False)
            recheck_source()
            drafts._bind_remote(gh, repository, tag, verified["source_revision"])
            current = read_release(public=not before["draft"])
            if current["id"] != before["id"]:
                raise ValueError("Release changed after attachment verification")
            drafts._bind_remote(gh, repository, tag, verified["source_revision"])
            recheck_source()
            if not before["draft"]:
                return dict(result, ok=True, draft=False, published=True, release_id=current["id"],
                            prerelease=kind == "preview", assets_verified=len(expected), reused=True,
                            publication_verified=True)
            edited = True
            gh("release", "edit", tag, "--repo", repository, "--verify-tag", "--draft=false",
               f"--prerelease={'true' if kind == 'preview' else 'false'}")
            public = read_release(public=True)
            if public["id"] != before["id"]:
                raise ValueError("published Release identity differs from the reviewed Draft")
            drafts._bind_remote(gh, repository, tag, verified["source_revision"])
            return dict(result, ok=True, draft=False, published=True, release_id=public["id"],
                        prerelease=kind == "preview", assets_verified=len(expected), publication_verified=True)
        except (drafts.io.ToolError, OSError, ValueError, TypeError, KeyError, AttributeError, subprocess.SubprocessError) as exc:
            failure = dict(result, ok=False, error=str(exc), published=False, publication_verified=False)
            if edited:
                failure["draft"] = None
                failure["published"] = None
                failure["publication_outcome"] = "uncertain; inspect the remote Release before retrying"
            elif observed_public:
                failure.update(draft=False, published=True)
            elif result.get("draft") is not True:
                failure["published"] = None
                failure["publication_outcome"] = "remote Release state is unverified; inspect it before retrying"
            return failure


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--plugin", required=True)
    parser.add_argument("--source-tag", required=True)
    parser.add_argument("--bundle", required=True, type=Path)
    parser.add_argument("--repository", required=True)
    parser.add_argument("--draft-result", type=Path)
    parser.add_argument("--ensure-tag", action="store_true")
    args = parser.parse_args()
    try:
        receipt = json.loads(args.draft_result.read_text()) if args.draft_result is not None else None
        result = publish_release(args.root, args.plugin, args.source_tag, args.bundle,
                                 args.repository, draft_result=receipt, ensure_tag=args.ensure_tag)
    except (drafts.io.ToolError, OSError, ValueError, TypeError, KeyError, AttributeError, subprocess.SubprocessError) as exc:
        result = {"ok": False, "error": str(exc)}
    print(json.dumps(result, indent=2))
    if not result["ok"]:
        # Actions retains stdout as the receipt artifact. Also expose the safe
        # failure receipt in its logs without changing the workflow or exit code.
        print(json.dumps(result, indent=2), file=sys.stderr)
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
