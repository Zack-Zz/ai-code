#!/usr/bin/env python3
"""Materialize a one-shot acceptance scenario for one case.

Copies the fixture into a fresh output directory, applies case-specific
scenario mutations, and records the workspace baseline. Never overwrites an
existing output and never touches user business repositories.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path

from _common import FIXTURES, REPO_ROOT, find_case, scenario_snapshot

sys.path.insert(0, str(Path(__file__).parent))
from _common import ConflictError, DataError, exit_with  # noqa: E402

from workflow import io as wio  # noqa: E402
from workflow import build as wbuild  # noqa: E402

SCENARIO_MUTATIONS = {"A04"}
SCENARIO_EXTRAS = {"A10"}


def _copy_file_fixture(fixture: str, workspace: Path) -> None:
    src = FIXTURES / fixture
    workspace.mkdir(parents=True, exist_ok=True)
    for name in ("labels.py", "test_baseline.py", "auth.py", "audit.py",
                 "status.js", "test_baseline.js", "user", "calc.py",
                 "test_calc.py", "user_notes.txt", ".ai-workflow"):
        source = src / name
        if source.is_dir():
            shutil.copytree(source, workspace / name, dirs_exist_ok=True)
        elif source.is_file():
            shutil.copyfile(source, workspace / name)


def _apply_mutation(case_id: str, workspace: Path) -> None:
    mutation = FIXTURES / "python_labels" / "mutations" / "a04_break_labels.py"
    spec = importlib.util.spec_from_file_location("a04_mutation", mutation)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.apply(workspace)


def _repoint_state_resume(workspace: Path) -> None:
    """Point fixture workspace placeholders at this copy and rebind evidence hashes."""
    import hashlib
    ws_abs = str(workspace.resolve())
    placeholder = "/absolute/path/set/by/prepare"
    for task_file in sorted(workspace.glob(".ai-workflow/tasks/*/task.json")):
        text = task_file.read_text(encoding="utf-8")
        if placeholder not in text:
            continue
        record = json.loads(text)
        record["workspace"]["root"] = ws_abs
        evidence_refs = record.get("evidence_refs") or []
        for ref in evidence_refs:
            ev_path = workspace / ".ai-workflow" / "tasks" / record["task_id"] / ref["relative_path"]
            if ev_path.is_file():
                ev_text = ev_path.read_text(encoding="utf-8").replace(placeholder, ws_abs)
                ev_path.write_text(ev_text, encoding="utf-8")
                ref["content_sha256"] = hashlib.sha256(ev_path.read_bytes()).hexdigest()
        task_file.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")


def prepare(case_id: str, output: Path) -> dict:
    case = find_case(case_id)
    fixture = case["fixture"]
    output = Path(output)
    if output.exists():
        raise ConflictError(f"output already exists: {output}")
    output.mkdir(parents=True)

    prefixes = ["workspace"]
    git_baselines = None
    if fixture in ("python_labels", "python_auth", "node_status", "state_resume"):
        workspace = output / "workspace"
        _copy_file_fixture(fixture, workspace)
        if fixture == "state_resume":
            _repoint_state_resume(workspace)
        if case_id in SCENARIO_MUTATIONS:
            _apply_mutation(case_id, workspace)
        if case_id in SCENARIO_EXTRAS:
            shutil.copyfile(FIXTURES / "python_labels" / "extras" / "test_history_failure.py",
                            workspace / "test_history_failure.py")
    elif fixture == "git_permissions":
        setup = FIXTURES / "git_permissions" / "setup.py"
        result = subprocess.run(
            [sys.executable, str(setup), str(output)],
            capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            raise DataError(f"git fixture setup failed: {result.stderr[:400]}")
        git_baselines = json.loads(result.stdout)["subcase_baselines"]
        prefixes = ["repo"]
    elif fixture == "managed_package":
        wbuild.build_packages(REPO_ROOT, ["all"], output / "pkg")
        (output / "project").mkdir()
        prefixes = ["pkg", "project"]
    else:  # pragma: no cover - cases.json constrains fixture names
        raise DataError(f"unknown fixture: {fixture}")

    baseline, baseline_directories = scenario_snapshot(output, prefixes)
    prepared = {
        "schema_version": 1,
        "case_id": case_id,
        "fixture": fixture,
        "policy_mode": case["policy_mode"],
        "critical": case["critical"],
        "turns": case["turns"],
        "baseline": baseline,
        "baseline_directories": baseline_directories,
        "scenario_root": str(output.resolve()),
        "created_at": wio.now_rfc3339(),
        "cases_sha256": wio.sha256_file(Path(__file__).parent / "cases.json"),
        "note": "one-shot scenario copy; baseline hashes recorded at prepare time",
    }
    if git_baselines is not None:
        prepared["git_subcase_baselines"] = git_baselines
    (output / "prepared.json").write_text(json.dumps(prepared, indent=2, sort_keys=True) + "\n")
    return prepared


def main() -> int:
    parser = argparse.ArgumentParser(prog="prepare.py")
    parser.add_argument("--case", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        prepared = prepare(args.case, Path(args.output))
    except Exception as exc:
        return exit_with(exc)
    print(json.dumps({
        "case_id": prepared["case_id"],
        "fixture": prepared["fixture"],
        "output": str(Path(args.output).resolve()),
        "baseline_files": len(prepared["baseline"]),
    }, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
