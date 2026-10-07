"""Argument handling and the controlled command surface."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import io as wio
from . import policy as wpolicy
from . import product as wproduct
from .io import (
    ConflictError,
    DataError,
    HostUnavailableError,
    InvalidStateError,
    ToolError,
)


def _emit(payload: dict) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=True, sort_keys=True))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="workflow_tool.py",
        description="Controlled file, validation and packaging operations for "
                    "ai-code-workflow. Runs no project commands, no Git changes, "
                    "no model calls.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate", help="validate the product source tree")
    validate.add_argument("--root", required=True)

    resolve = sub.add_parser("policy", help="policy operations")
    policy_sub = resolve.add_subparsers(dest="policy_command", required=True)
    pr = policy_sub.add_parser("resolve", help="resolve the effective policy")
    pr.add_argument("--plugin-root", required=True)
    pr.add_argument("--workspace", required=True)
    pr.add_argument("--mode", choices=list(wpolicy.MODES))
    pr.add_argument("--review-level", choices=list(wpolicy.REVIEW_LEVELS))
    pr.add_argument("--max-parallel-tasks", type=int)
    pr.add_argument("--response-language")
    pr.add_argument("--verification-note", action="append", default=None)

    task = sub.add_parser("task", help="task record operations")
    task_sub = task.add_subparsers(dest="task_command", required=True)
    tc = task_sub.add_parser("create", help="create a task record (preview unless --apply)")
    tc.add_argument("--workspace", required=True)
    tc.add_argument("--id", required=True)
    tc.add_argument("--input", required=True)
    tc.add_argument("--apply", action="store_true")
    tu = task_sub.add_parser("update", help="update a task record under CAS")
    tu.add_argument("--workspace", required=True)
    tu.add_argument("--id", required=True)
    tu.add_argument("--expected-revision", type=int, required=True)
    tu.add_argument("--input", required=True)
    tu.add_argument("--apply", action="store_true")
    tk = task_sub.add_parser("check", help="check identity and evidence consistency")
    tk.add_argument("--workspace", required=True)
    tk.add_argument("--id", required=True)

    build_parser = sub.add_parser("build", help="build host packages deterministically")
    build_parser.add_argument("--host", required=True, choices=["zcode", "codex", "all"])
    build_parser.add_argument("--output", required=True)

    pcheck = sub.add_parser("package", help="package operations")
    package_sub = pcheck.add_subparsers(dest="package_command", required=True)
    pc = package_sub.add_parser("check", help="verify a built package")
    pc.add_argument("--path", required=True)
    pc.add_argument("--host", required=True, choices=["zcode", "codex"])

    files_parser = sub.add_parser("files", help="owned-file management")
    files_sub = files_parser.add_subparsers(dest="files_command", required=True)
    fp = files_sub.add_parser("plan", help="plan a stage/update/remove (read-only)")
    fp.add_argument("--package", default=None)
    fp.add_argument("--target", required=True)
    fp.add_argument("--action", required=True, choices=["stage", "update", "remove"])
    fp.add_argument("--out", required=True)
    fa = files_sub.add_parser("apply", help="apply a validated plan")
    fa.add_argument("--plan", required=True)
    fa.add_argument("--expected-plan-hash", required=True)

    return parser


def _collect_explicit(args) -> dict:
    explicit = {}
    if args.mode:
        explicit["mode"] = args.mode
    if args.review_level:
        explicit["review_level"] = args.review_level
    if args.max_parallel_tasks is not None:
        explicit["max_parallel_tasks"] = args.max_parallel_tasks
    if args.response_language:
        explicit["response_language"] = args.response_language
    if args.verification_note:
        explicit["verification_notes"] = list(args.verification_note)
    return explicit


def _cmd_validate(args) -> int:
    root = Path(args.root)
    spec = wproduct.load_product(root)
    wproduct.validate_adapters(root, spec.all_skills)
    profiles = {mode: wpolicy.load_profile(root, mode) for mode in wpolicy.MODES}
    for name in ("task.json", "evidence.json"):
        wio.load_json(root / "templates" / name)
    targets = spec.targets()
    _emit({
        "ok": True,
        "product_id": spec.product_id,
        "version": spec.version,
        "core_skills": spec.core_skills,
        "shared_skills": spec.shared_skills,
        "registered_files": len(targets),
        "profiles": sorted(profiles),
    })
    return 0


def _cmd_policy_resolve(args) -> int:
    result = wpolicy.resolve_policy(
        Path(args.plugin_root), Path(args.workspace), _collect_explicit(args) or None)
    _emit(result)
    return 0


def _cmd_task_create(args) -> int:
    from . import state as wstate
    result = wstate.create_task(
        Path(args.workspace), args.id, wio.load_json(Path(args.input)), apply=args.apply)
    _emit(result)
    return 0


def _cmd_task_update(args) -> int:
    from . import state as wstate
    result = wstate.update_task(
        Path(args.workspace), args.id, args.expected_revision,
        wio.load_json(Path(args.input)), apply=args.apply)
    _emit(result)
    return 0


def _cmd_task_check(args) -> int:
    from . import state as wstate
    result = wstate.check_task(Path(args.workspace), args.id)
    _emit(result)
    return 0 if result["consistent"] else 4


def _cmd_build(args) -> int:
    from . import build as wbuild
    # The source root is the tree containing product.json — derived from the
    # script location (repo: scripts/workflow/cli.py; package: tools/...).
    source_root = Path(__file__).resolve().parents[2]
    hosts = list(wbuild.HOSTS) if args.host == "all" else [args.host]
    report = wbuild.build_packages(source_root, hosts, Path(args.output))
    _emit(report)
    return 0


def _cmd_package_check(args) -> int:
    from . import package_check as wpc
    result = wpc.check_package(Path(args.path), args.host)
    _emit(result)
    return 0 if result["ok"] else 1


def _cmd_files_plan(args) -> int:
    from . import owned_files as wof
    plan = wof.plan_operation(
        Path(args.package) if args.package else None,
        Path(args.target), args.action)
    import json as _json
    payload = _json.dumps(plan, indent=2, sort_keys=True) + "\n"
    out_path = Path(args.out)
    if out_path.parent != Path(""):
        out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(payload, encoding="utf-8")
    blocking = [c for c in plan["conflicts"] if c.get("blocking")]
    print(_json.dumps({
        "written": str(out_path),
        "operation_id": plan["operation_id"],
        "plan_hash": plan["plan_hash"],
        "items": len(plan["items"]),
        "blocking_conflicts": len(blocking),
    }, indent=2))
    return 3 if blocking else 0


def _cmd_files_apply(args) -> int:
    from . import owned_files as wof
    plan = wio.load_json(Path(args.plan))
    result = wof.apply_operation(plan, args.expected_plan_hash)
    _emit(result)
    return 0


_HANDLERS = {
    ("validate",): _cmd_validate,
    ("policy", "resolve"): _cmd_policy_resolve,
    ("task", "create"): _cmd_task_create,
    ("task", "update"): _cmd_task_update,
    ("task", "check"): _cmd_task_check,
    ("build",): _cmd_build,
    ("package", "check"): _cmd_package_check,
    ("files", "plan"): _cmd_files_plan,
    ("files", "apply"): _cmd_files_apply,
}


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = _build_parser()
    args = parser.parse_args(argv)

    command_key = (args.command,)
    for sub_key in ("policy_command", "task_command", "package_command", "files_command"):
        if getattr(args, sub_key, None):
            command_key = command_key + (getattr(args, sub_key),)

    handler = _HANDLERS.get(command_key)
    if handler is None:  # pragma: no cover - argparse rejects unknown commands
        parser.error(f"unknown command: {command_key}")

    try:
        return handler(args)
    except ToolError as exc:
        print(
            json.dumps({"error": {"code": exc.exit_code, "reason": str(exc)}}),
            file=sys.stderr,
        )
        return exc.exit_code
    except Exception as exc:  # noqa: BLE001 - stable surface for the CLI
        print(
            json.dumps({"error": {"code": 1, "reason": f"{type(exc).__name__}: {exc}"}}),
            file=sys.stderr,
        )
        return 1
