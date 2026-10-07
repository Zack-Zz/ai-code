"""Repository commands, kept separate from individual plugin commands."""

import argparse
import json
from pathlib import Path
import sys

from .io import DataError, ToolError
from .registry import HOSTS, load_catalog, select_plugins


def _selection(parser):
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument("--all", action="store_true")
    choice.add_argument("--plugin")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    root_default = Path(__file__).resolve().parents[2]
    parser.add_argument("--root", default=str(root_default))
    commands = parser.add_subparsers(dest="command", required=True)
    listing = commands.add_parser("list")
    validating = commands.add_parser("validate")
    _selection(validating)
    building = commands.add_parser("build")
    _selection(building)
    building.add_argument("--host", choices=(*HOSTS, "all"), default="all")
    building.add_argument("--output", required=True)
    package = commands.add_parser("package")
    package_commands = package.add_subparsers(dest="package_command", required=True)
    checking = package_commands.add_parser("check")
    checking.add_argument("--path", required=True)
    checking.add_argument("--host", choices=HOSTS, required=True)
    checking.add_argument("--plugin")
    markets = commands.add_parser("marketplace")
    market_commands = markets.add_subparsers(dest="market_command", required=True)
    syncing = market_commands.add_parser("sync")
    syncing.add_argument("--check", action="store_true")
    releases = commands.add_parser("release")
    release_commands = releases.add_subparsers(dest="release_command", required=True)
    release_check = release_commands.add_parser("check")
    release_prepare = release_commands.add_parser("prepare")
    release_verify = release_commands.add_parser("verify")
    for command in (release_check, release_prepare, release_verify):
        command.add_argument("--plugin", required=True)
        command.add_argument("--previous")
    release_check.add_argument("--mode", choices=("draft", "stable"), default="draft")
    release_prepare.add_argument("--mode", choices=("draft", "stable"), default="draft")
    release_prepare.add_argument("--output", required=True)
    release_prepare.add_argument("--tag")
    release_verify.add_argument("--path", required=True)
    release_verify.add_argument("--mode", choices=("draft", "stable"))
    for command in (listing, validating, building, checking, syncing,
                    release_check, release_prepare, release_verify):
        command.add_argument("--root", default=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    try:
        if args.command == "marketplace":
            from .markets import sync_markets
            result = sync_markets(args.root, check=args.check)
        else:
            specs = load_catalog(args.root)
        if args.command == "release":
            from .release import check_release, prepare_release, verify_release
            spec = select_plugins(specs, args.plugin)[0]
            if args.release_command == "check":
                result = check_release(args.root, spec, mode=args.mode, previous=args.previous)
            elif args.release_command == "prepare":
                result = prepare_release(args.root, spec, args.output, mode=args.mode,
                                         tag=args.tag, previous=args.previous)
            else:
                result = verify_release(args.root, spec, args.path, mode=args.mode,
                                        previous=args.previous)
        elif args.command == "list":
            result = {"plugins": [{"product_id": spec.product_id, "version": spec.version,
                                  "display_name": spec.manifest["display_name"],
                                  "path": spec.catalog_path, "hosts": spec.hosts}
                                 for spec in specs]}
        elif args.command == "validate":
            selected = select_plugins(specs, args.plugin)
            result = {"ok": True, "plugins": [{"product_id": spec.product_id,
                                               "version": spec.version, "files_count": len(spec.files),
                                               "source_tree_hash": spec.source_tree_hash}
                                              for spec in selected]}
        elif args.command == "build":
            from .build import build_plugins
            selected = select_plugins(specs, args.plugin)
            hosts = HOSTS if args.host == "all" else (args.host,)
            result = build_plugins(args.root, selected, args.output, hosts)
        elif args.command == "package":
            from .package_check import check_package, read_artifact
            identity = args.plugin or read_artifact(Path(args.path).absolute())["product_id"]
            spec = select_plugins(specs, identity)[0]
            result = check_package(args.path, args.host, spec)
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if result.get("ok", True) else 1
    except ToolError as exc:
        print(str(exc), file=sys.stderr)
        return exc.exit_code
    except (OSError, UnicodeError) as exc:
        print(f"cannot process plugin inputs: {exc}", file=sys.stderr)
        return 2
