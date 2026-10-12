"""Prepare frozen tagged source using the calling trusted main tools."""

import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tooling"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from plugin_tools import io
from plugin_tools.registry import load_catalog, select_plugins
from plugin_tools.release import check_release, prepare_release, verify_release
from plugin_tools.release.source_git import validate_head_inputs
from plugin_tools.versions import release_kind
from check_no_dist import check as check_no_dist


def _git(root, *args):
    result = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, timeout=30)
    if result.returncode:
        raise ValueError("cannot resolve clean source on origin/main: " + " ".join(args))
    return result.stdout.strip()


def _public_capture(spec):
    """Read the public closure without requiring private acceptance artifacts."""
    inputs = {"release.json": io.read_file(spec.root, "release.json", boundary_root=spec.boundary_root)}
    config = io.parse_json(inputs["release.json"], what="release.json")
    if not isinstance(config, dict) or set(config) != {"schema_version", "notes", "readmes", "acceptance"} or \
            config["schema_version"] != 1 or not isinstance(config["readmes"], dict) or \
            set(config["readmes"]) != {"en", "zh-CN"}:
        raise ValueError("invalid public release configuration")
    for relative in (config["notes"], *config["readmes"].values()):
        inputs[relative] = io.read_file(spec.root, relative, boundary_root=spec.boundary_root)
    proof_inputs = {}
    relative = "release/acceptance-proof.json"
    if (spec.root / relative).exists() or (spec.root / relative).is_symlink():
        proof_inputs[relative] = io.read_file(spec.root, relative, boundary_root=spec.boundary_root)
    return SimpleNamespace(config=config, inputs=inputs, proof_inputs=proof_inputs)


def _proof_presence(root, spec, capture, revision):
    proof_path = f"{spec.catalog_path}/release/acceptance-proof.json"
    if bool(_git(root, "ls-tree", revision, "--", proof_path)) != bool(capture.proof_inputs):
        raise ValueError("public proof inputs differ from frozen source; restore the input or prepare a new version")


def freeze_current(root, plugin_id, expected_revision):
    """Freeze a clean CI clone, deriving its tag and reusing an identical version.

    Only local checkout/tag operations happen here. Remote writes belong to the
    environment-protected publisher after the entire bundle has been verified.
    """
    root = Path(root).resolve()
    revision = _git(root, "rev-parse", "--verify", "HEAD^{commit}")
    if not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", expected_revision or "") or revision != expected_revision:
        raise ValueError("source revision differs from the workflow's frozen dispatch revision")
    if _git(root, "status", "--porcelain=v1", "--untracked-files=all"):
        raise ValueError("automatic preparation requires a clean source checkout")
    _git(root, "merge-base", "--is-ancestor", revision, "refs/remotes/origin/main")
    check_no_dist(root)
    spec = select_plugins(load_catalog(root), plugin_id)[0]
    capture = _public_capture(spec)
    _proof_presence(root, spec, capture, revision)
    validate_head_inputs(root, spec, capture, revision)
    tag = f"{spec.product_id}/v{spec.version}"
    exists = subprocess.run(["git", "show-ref", "--verify", "--quiet", f"refs/tags/{tag}"], cwd=root, timeout=30)
    if exists.returncode not in (0, 1):
        raise ValueError("cannot inspect existing version tag")
    if exists.returncode == 0:
        tagged = _git(root, "rev-parse", "--verify", f"refs/tags/{tag}^{{commit}}")
        _git(root, "merge-base", "--is-ancestor", tagged, "refs/remotes/origin/main")
        _proof_presence(root, spec, capture, tagged)
        # A marketplace receipt may advance main after publication. It must not
        # create a second source identity for the same public version.
        try:
            validate_head_inputs(root, spec, capture, tagged)
        except io.ToolError as exc:
            raise ValueError("existing version has different public bytes; prepare a new version") from exc
        if tagged != revision:
            _git(root, "checkout", "--detach", tagged)
    else:
        _git(root, "tag", tag, revision)
    return inspect_source(root, plugin_id, tag)[1]


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
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--source-tag")
    source.add_argument("--from-main", action="store_true", help="freeze an isolated clean CI checkout automatically")
    parser.add_argument("--revision", help="expected workflow dispatch commit (required with --from-main)")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--check-source-only", action="store_true")
    args = parser.parse_args()
    try:
        if args.from_main:
            if not args.revision:
                parser.error("--revision is required with --from-main")
            frozen = freeze_current(args.root, args.plugin, args.revision)
            args.source_tag = frozen["tag"]
        if args.check_source_only:
            result = inspect_source(args.root, args.plugin, args.source_tag)[1]
        else:
            if args.output is None:
                parser.error("--output is required for preparation")
            result = prepare(args.root, args.plugin, args.source_tag, args.output)
        if os.environ.get("GITHUB_OUTPUT"):
            with open(os.environ["GITHUB_OUTPUT"], "a") as output:
                for key in ("kind", "mode", "revision", "tag", "version"):
                    output.write(f"{key}={result[key]}\n")
    except (io.ToolError, OSError, ValueError, subprocess.SubprocessError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
