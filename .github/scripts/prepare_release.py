"""Prepare frozen tagged source using the calling trusted main tools."""

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tooling"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from plugin_tools import io
from plugin_tools.registry import load_catalog, select_plugins
from plugin_tools.release import check_release, prepare_release, verify_release
from plugin_tools.versions import release_kind
from check_no_dist import check as check_no_dist


def source_binding(root, spec, tag):
    if tag != f"{spec.product_id}/v{spec.version}":
        raise ValueError("source tag must be the selected plugin's canonical ID/vVERSION")
    def git(*args):
        result = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, timeout=30)
        if result.returncode:
            raise ValueError("frozen source tag must exist and be reachable from origin/main")
        return result.stdout.strip()
    revision = git("rev-parse", "--verify", "HEAD^{commit}")
    tagged = git("rev-parse", "--verify", f"refs/tags/{tag}^{{commit}}")
    if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", revision) or tagged != revision:
        raise ValueError("source checkout must match the frozen tag commit")
    git("merge-base", "--is-ancestor", revision, "refs/remotes/origin/main")
    return revision


def inspect_source(root, plugin_id, source_tag):
    root = Path(root).resolve()
    spec = select_plugins(load_catalog(root), plugin_id)[0]
    kind = release_kind(spec.version)
    mode = "draft" if kind == "preview" else "stable"
    revision = source_binding(root, spec, source_tag)
    check_no_dist(root)
    return spec, {"ok": True, "kind": kind, "mode": mode, "revision": revision,
                  "version": spec.version, "tag": source_tag}


def prepare(root, plugin_id, source_tag, output):
    root = Path(root).resolve()
    spec, result = inspect_source(root, plugin_id, source_tag)
    mode, revision = result["mode"], result["revision"]
    report = check_release(root, spec, mode=mode, committed_acceptance=True)
    if not report["ok"]:
        raise ValueError("release check failed: " + "; ".join(report["blockers"]))
    report = prepare_release(root, spec, output, mode=mode, tag=source_tag, committed_acceptance=True)
    if not report["ok"]:
        raise ValueError("release preparation failed: " + "; ".join(report["blockers"]))
    verified = verify_release(root, spec, output, mode=mode, committed_acceptance=True)
    if not verified["ok"] or verified.get("source_revision") != revision:
        raise ValueError("prepared release failed independent verification")
    source_binding(root, spec, source_tag)
    return dict(result, bundle=str(Path(output).resolve()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--plugin", required=True)
    parser.add_argument("--source-tag", required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check-source-only", action="store_true")
    args = parser.parse_args()
    try:
        if args.check_source_only:
            result = inspect_source(args.root, args.plugin, args.source_tag)[1]
        else:
            if args.output is None:
                parser.error("--output is required for preparation")
            result = prepare(args.root, args.plugin, args.source_tag, args.output)
        if os.environ.get("GITHUB_OUTPUT"):
            with open(os.environ["GITHUB_OUTPUT"], "a") as output:
                for key in ("kind", "mode", "revision"):
                    output.write(f"{key}={result[key]}\n")
    except (io.ToolError, OSError, ValueError, subprocess.SubprocessError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
