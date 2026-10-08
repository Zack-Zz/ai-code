#!/usr/bin/env python3
"""Grade real collected material; deterministic scenarios use the bound package CLI.

Agent semantics remain not_run/manual_review until sourced host review exists.
The fault driver below is an eval-only harness, never a production CLI option.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).parent))
from _common import (GRADER_VERSION, REPO_ROOT, RUN_INDEX_KEYS, PREPARED_REF,
                     DataError, InvalidStateError, checked_scenario, exit_with, find_case)
from _common import scenario_snapshot
from workflow import build as wbuild
from workflow import io as wio
from workflow import package_check as wpackage
from workflow import product as wproduct
from workflow.product import HOSTS

DETERMINISTIC = {"A23": "_grade_a23", "A24": "_grade_a24", "A25": "_grade_a25"}


def _validate_index(index):
    if not isinstance(index, dict) or set(index) != RUN_INDEX_KEYS:
        raise DataError("run index has missing or unknown fields")
    if not wio.is_strict_int(index["schema_version"]) or index["schema_version"] != 1:
        raise DataError("run index schema_version must be the integer 1")
    if index["host"] not in HOSTS:
        raise DataError(f"run host must be one of {HOSTS}")
    if index["comparison_mode"] not in ("native", "plugin") or index["capture_origin"] not in ("manual_annotation", "native_export"):
        raise DataError("invalid run comparison mode or capture origin")
    for field in ("package_content_hash", "policy_hash", "fixture_baseline_hash"):
        value = index[field]
        if value is not None and not (isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value)):
            raise DataError(f"run {field} must be SHA256 hex or null")
    for field in ("raw_refs", "artifacts", "events"):
        if not isinstance(index[field], list):
            raise DataError(f"run {field} must be a list")


def _result(check_id, result, reason):
    return {"check_id": check_id, "result": result, "reason": reason}


def _scenario(index: dict, run_dir: Path) -> Path | None:
    root = index.get("workspace_root")
    if not root or not Path(root).is_dir() or not (Path(root) / "prepared.json").exists():
        return None
    root, prepared = checked_scenario(Path(root), index["case_id"])
    refs = [r for r in index["artifacts"] if r["target_path"] == PREPARED_REF]
    if len(refs) != 1:
        raise InvalidStateError("prepared scenario is not bound to collected material")
    captured = wio.resolve_member(run_dir, PREPARED_REF)
    current = wio.resolve_member(root, "prepared.json")
    if wio.sha256_file(current) != refs[0]["content_sha256"] or captured.read_bytes() != current.read_bytes():
        raise InvalidStateError("prepared scenario record changed after collection")
    if wio.sha256_bytes(wio.canonical_json(prepared["baseline"])) != index["fixture_baseline_hash"]:
        raise InvalidStateError("run fixture_baseline_hash differs from its captured scenario")
    distribution = wio.load_json(wio.resolve_member(root, "pkg/index.json"))
    for host, item in distribution["hosts"].items():
        artifact = wio.load_json(wio.resolve_member(root, f"pkg/{host}/ai-code-workflow/artifact.json"))
        for key in ("product_id", "version", "source_revision", "working_tree_dirty", "source_tree_hash"):
            if artifact[key] != distribution[key] or type(artifact[key]) is not type(distribution[key]):
                raise InvalidStateError(f"{host} package metadata differs from distribution: {key}")
        if artifact["content_hash"] != item["package_content_hash"]:
            raise InvalidStateError(f"{host} package hash differs from distribution")
        if host == index["host"] and artifact["content_hash"] != index["package_content_hash"]:
            raise InvalidStateError("run package_content_hash differs from actual captured package")
    if index["host"] not in distribution["hosts"]:
        raise InvalidStateError("run host is not present in the prepared distribution")
    return root


class RunFailure(Exception):
    """A real tool execution did not satisfy the scenario's expected status."""


# Execute the exact captured CLI. After its first replacement, a concurrent
# editor changes the next target; the real apply detects that conflict and
# interrupts the UPDATE, generating its own pending record and recovery basis.
FAULT_DRIVER = '''import json, runpy, sys
from pathlib import Path
sys.dont_write_bytecode = True
entry, plan_file, fault_target = sys.argv[1:4]
sys.path.insert(0, str(Path(entry).parent))
from workflow import io
plan = json.loads(Path(plan_file).read_text())
original_read = io.read_owned
original_write = io.atomic_write
injected = False
def concurrent_edit(path, *, root=None):
    global injected
    if not injected and Path(path) == Path(fault_target):
        before = original_read(path, root=root)
        original_write(path, b"eval fault: concurrent edit during update\\n", expected_before=before, root=root)
        injected = True
    return original_read(path, root=root)
io.read_owned = concurrent_edit
sys.argv = [entry, *sys.argv[4:]]
runpy.run_path(entry, run_name="__main__")
'''


class PackageRun:
    def __init__(self, scenario, index, run_dir):
        self.scenario, self.index, self.run_dir = scenario, index, run_dir
        self.package = wio.resolve_member(scenario, f"pkg/{index['host']}/ai-code-workflow", allow_directory=True)
        self.entry = wio.resolve_member(scenario, f"pkg/{index['host']}/ai-code-workflow/tools/workflow_tool.py")
        self.artifact = wio.load_json(self.package / "artifact.json")
        self.commands, self.observations = [], {}
        wio.ensure_directory(run_dir, "grader/commands")
        wio.ensure_directory(run_dir, "grader/materials")
        wio.ensure_directory(scenario, "grader-plans")

    def capture(self, path, name):
        payload = wio.read_owned(Path(path), root=self.scenario)
        rel = wio.check_relative(f"grader/materials/{name}")
        wio.atomic_write(self.run_dir / rel, payload, expected_before=None, root=self.run_dir)
        return {"relative_path": rel, "content_sha256": wio.sha256_bytes(payload),
                "source_path": str(path)}

    def command(self, args, fault=None, entry=None):
        entry = self.entry if entry is None else entry
        if fault is None:
            return [sys.executable, str(entry), *map(str, args)]
        plan, target = fault
        return [sys.executable, "-c", FAULT_DRIVER, str(entry), str(plan), str(target), *map(str, args)]

    def record(self, command, result, method="bound_package_cli"):
        number = len(self.commands) + 1
        refs = {}
        for name, output in (("stdout", result.stdout), ("stderr", result.stderr)):
            rel = f"grader/commands/{number:03d}.{name}.txt"
            payload = output.encode()
            wio.atomic_write(self.run_dir / rel, payload, expected_before=None, root=self.run_dir)
            refs[name] = {"relative_path": rel, "content_sha256": wio.sha256_bytes(payload)}
        self.commands.append({"command": command, "exit_code": result.returncode,
                              "method": method, **refs})
        return result

    def call(self, args, expected=0, fault=None, entry=None):
        command = self.command(args, fault, entry)
        result = self.record(command, subprocess.run(command, capture_output=True, text=True, timeout=60),
                             "bound_package_cli_with_concurrent_edit_fault" if fault else "bound_package_cli")
        if expected is not None and result.returncode != expected:
            raise RunFailure(f"tool exit {result.returncode}, expected {expected}; see command {len(self.commands)}")
        return result

    def plan(self, package, project, action, name, expected=0):
        path = self.scenario / "grader-plans" / f"{name}.json"
        args = ["files", "plan", "--target", project, "--action", action, "--out", path]
        if package is not None:
            args += ["--package", package]
        result = self.call(args, expected)
        if path.is_file():
            self.observations.setdefault("plan_refs", {})[name] = self.capture(path, name + ".plan.json")
        return path, wio.load_json(path) if path.is_file() else None, result

    def apply(self, path, plan, expected=0, fault=None):
        return self.call(["files", "apply", "--plan", path, "--expected-plan-hash", plan["plan_hash"]],
                         expected, fault)

    def finish(self):
        data = {"method": "deterministic_bound_package_cli", "package": self.artifact,
                "commands": self.commands, "observations": self.observations}
        payload = json.dumps(data, indent=2, sort_keys=True).encode() + b"\n"
        rel = "deterministic-evidence.json"
        wio.atomic_write(self.run_dir / rel, payload, expected_before=None, root=self.run_dir)
        return {"relative_path": rel, "content_sha256": wio.sha256_bytes(payload)}


def _updated_package(run):
    """Derive a controlled two-file update from captured bytes, not current source.

    This is a private eval payload, with hashes/metadata/ZIP rebuilt for the
    mutated bytes. It is never presented as a published source build.
    """
    root = run.scenario / "update-pkg"
    shutil.copytree(run.scenario / "pkg", root)
    distribution = wio.load_json(root / "index.json")
    subject_hashes = {}
    for host in distribution["hosts"]:
        package = root / host / "ai-code-workflow"
        for rel in ("LICENSE", "NOTICE"):
            path = package / rel
            before = path.read_bytes()
            wio.atomic_write(path, before + b"\nDisposable eval update payload.\n", expected_before=before, root=root)
            subject_hashes[rel] = wio.sha256_file(path)
        artifact = wio.load_json(package / "artifact.json")
        artifact["files"] = [[rel, wio.sha256_file(package / rel)] for rel, _ in artifact["files"]]
        artifact["content_hash"] = wio.sha256_bytes(wio.canonical_json(artifact["files"]))
        artifact["source_tree_hash"] = wio.sha256_bytes(wio.canonical_json({
            "eval_derived_from": run.artifact["source_tree_hash"], "changed_files": subject_hashes}))
        artifact["working_tree_dirty"] = True
        (package / "artifact.json").write_text(json.dumps(artifact, indent=2) + "\n")
        item = distribution["hosts"][host]
        item["package_content_hash"] = artifact["content_hash"]
        zip_path = root / item["zip"]
        with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zipped:
            for path in sorted((root / host).rglob("*")):
                if path.is_file() and path != zip_path:
                    zipped.write(path, path.relative_to(root / host).as_posix())
        item["zip_sha256"] = wio.sha256_file(zip_path)
    distribution["source_tree_hash"] = artifact["source_tree_hash"]
    distribution["working_tree_dirty"] = True
    (root / "index.json").write_text(json.dumps(distribution, indent=2) + "\n")
    run.observations["update_payload"] = {"method": "controlled two-file mutation of captured package",
                                            "derived_from_content_hash": run.artifact["content_hash"],
                                            "changed_files": subject_hashes,
                                            "artifact_ref": run.capture(root / run.index["host"] / "ai-code-workflow/artifact.json", "update-artifact.json")}
    return root / run.index["host"] / "ai-code-workflow"


def _grade_a23(case, index, run):
    project = wio.resolve_member(run.scenario, "project", allow_directory=True)
    path, plan, _ = run.plan(run.package, project, "stage", "stage")
    first = json.loads(run.apply(path, plan).stdout)
    _, _, duplicate = run.plan(run.package, project, "stage", "repeat", expected=3)
    ok_dup = first.get("applied") is True and duplicate.returncode == 3

    update = _updated_package(run)
    path, plan, _ = run.plan(update, project, "update", "update")
    changed = json.loads(run.apply(path, plan).stdout)
    managed = project / ".ai-workflow/staged/ai-code-workflow"
    update_ok = changed.get("applied") is True and all(
        (managed / rel).read_bytes() == (update / rel).read_bytes() for rel in ("LICENSE", "NOTICE"))
    extra = managed / "unowned-extra.txt"
    wio.atomic_write(extra, b"belongs to the project, not the package\n", expected_before=None, root=run.scenario)
    notice = managed / "NOTICE"
    before = wio.read_owned(notice, root=run.scenario)
    user_edit = b"user's own edit\n"
    wio.atomic_write(notice, user_edit, expected_before=before, root=run.scenario)
    path, plan, _ = run.plan(update, project, "update", "blocked-update", expected=3)
    blocking = [c for c in plan["conflicts"] if c.get("blocking")]
    run.apply(path, plan, expected=3)
    protected = (any(c.get("path") == "unowned-extra.txt" for c in blocking)
                 and any(c.get("path") == "NOTICE" for c in blocking)
                 and wio.read_owned(notice, root=run.scenario) == user_edit)
    wio.atomic_write(notice, before, expected_before=user_edit, root=run.scenario)
    extra_before = extra.read_bytes()
    path, plan, _ = run.plan(None, project, "remove", "remove")
    removed = json.loads(run.apply(path, plan).stdout)
    remaining = sorted(p.relative_to(managed).as_posix() for p in managed.rglob("*") if p.is_file())
    remove_ok = (removed.get("applied") is True and remaining == ["unowned-extra.txt"]
                 and extra.read_bytes() == extra_before
                 and not (project / ".ai-workflow/receipts/ai-code-workflow.json").exists())
    run.observations["management"] = {"first_stage_applied": first.get("applied"),
        "repeat_exit": duplicate.returncode, "successful_update": update_ok,
        "user_edit_preserved": protected, "remove_kept_only_unowned": remove_ok}
    return [_result("A23-no-duplicates", "pass" if ok_dup else "fail", "actual stage and repeat CLI statuses retained"),
            _result("A23-protects-unowned-and-edited", "pass" if update_ok and protected and remove_ok else "fail",
                    "successful update, refused conflicting update and byte-checked remove retained")]


def _grade_a24(case, index, run):
    project = wio.resolve_member(run.scenario, "project", allow_directory=True)
    path, plan, _ = run.plan(run.package, project, "stage", "stage")
    run.apply(path, plan)
    receipt = project / ".ai-workflow/receipts/ai-code-workflow.json"
    receipt_before = receipt.read_bytes()
    update = _updated_package(run)
    path, plan, _ = run.plan(update, project, "update", "interrupted-update")
    replaces = sorted((i for i in plan["items"] if i["operation"] == "replace"), key=lambda i: i["relative_path"])
    if len(replaces) < 2:
        raise RunFailure("fault scenario requires at least two real replacements")
    managed = project / ".ai-workflow/staged/ai-code-workflow"
    before = {i["relative_path"]: (managed / i["relative_path"]).read_bytes() for i in replaces}
    fault_target = managed / replaces[1]["relative_path"]
    interrupted = run.apply(path, plan, expected=3, fault=(path, fault_target))
    op = project / ".ai-workflow/backups" / plan["operation_id"]
    pending_path = wio.resolve_member(run.scenario, (op / "pending-operation.json").relative_to(run.scenario).as_posix())
    pending_bytes = pending_path.read_bytes()
    pending = wio.load_json(pending_path)
    first_rel = replaces[0]["relative_path"]
    backup = wio.resolve_member(run.scenario, (op / "files" / first_rel).relative_to(run.scenario).as_posix())
    backup_ok = backup.read_bytes() == before[first_rel] and (op / "receipt.json").read_bytes() == receipt_before
    material_refs = {"pending": run.capture(pending_path, "interrupted-pending.json"),
                     "file_backup": run.capture(backup, "interrupted-file-backup.bin"),
                     "receipt_backup": run.capture(op / "receipt.json", "interrupted-receipt-backup.json"),
                     "fault_target": run.capture(fault_target, "interrupted-concurrent-edit.bin")}
    expected_applied = ["replace:" + first_rel]
    expected_recovery = [
        {"relative_path": item["relative_path"], "operation": item["operation"],
         "expected_before_sha256": item["expected_before_sha256"],
         "desired_sha256": item["desired_sha256"]}
        for item in plan["items"] if item["operation"] != "keep"
    ]
    recovery_matches = (pending.get("recovery_basis") == expected_recovery
                        and pending.get("operation_id") == plan["operation_id"]
                        and type(pending.get("total_items")) is int
                        and pending["total_items"] == len(plan["items"]))
    interrupted_ok = (pending["action"] == "update" and pending["applied"] == expected_applied
                      and recovery_matches
                      and receipt.read_bytes() == receipt_before and backup_ok
                      and (managed / first_rel).read_bytes() == (update / first_rel).read_bytes()
                      and fault_target.read_bytes() == b"eval fault: concurrent edit during update\n")
    later_edit = b"user's later edit after interruption\n"
    first_target = managed / first_rel
    wio.atomic_write(first_target, later_edit, expected_before=first_target.read_bytes(), root=run.scenario)
    run.plan(update, project, "update", "pending-refused", expected=3)
    run.apply(path, plan, expected=3)
    preserved = first_target.read_bytes() == later_edit and pending_path.read_bytes() == pending_bytes and backup.read_bytes() == before[first_rel]
    material_refs["later_user_edit"] = run.capture(first_target, "interrupted-later-user-edit.bin")
    run.observations["interrupted_update"] = {"pending": pending,
        "unapplied_items": ["replace:" + i["relative_path"] for i in replaces[1:]],
        "backups_match_before": backup_ok, "later_user_edit_preserved": preserved,
        "recovery_basis_matches_plan": recovery_matches,
        "failure_exit": interrupted.returncode, "fault_target": str(fault_target),
        "receipt_unchanged": receipt.read_bytes() == receipt_before,
        "before_hashes": {rel: wio.sha256_bytes(data) for rel, data in before.items()},
        "material_refs": material_refs}

    wio.ensure_directory(run.scenario, "project2")
    project2 = run.scenario / "project2"
    path2, plan2, _ = run.plan(run.package, project2, "stage", "concurrent")
    args = ["files", "apply", "--plan", path2, "--expected-plan-hash", plan2["plan_hash"]]
    command = run.command(args)
    processes = [subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True) for _ in range(2)]
    results = []
    for process in processes:
        try:
            stdout, stderr = process.communicate(timeout=60)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
        result = subprocess.CompletedProcess(command, process.returncode, stdout, stderr)
        run.record(command, result)
        results.append(result)
    concurrent_ok = sorted(r.returncode for r in results) == [0, 3]
    if concurrent_ok:
        concurrent_ok = json.loads(next(r.stdout for r in results if r.returncode == 0)).get("applied") is True
    state_ok = False
    receipt_ref = None
    state_error = None
    prefix = "project2/.ai-workflow/staged/ai-code-workflow"
    try:
        actual, _ = scenario_snapshot(run.scenario, [prefix])
        actual = {rel.removeprefix(prefix + "/"): sha for rel, sha in actual.items()}
        expected_files = dict(run.artifact["files"])
        receipt2_path = wio.resolve_member(run.scenario, "project2/.ai-workflow/receipts/ai-code-workflow.json")
        receipt2 = wio.load_json(receipt2_path, root=run.scenario)
        expected_receipt = {"schema_version": 1, "product_id": run.artifact["product_id"],
            "version": run.artifact["version"], "managed_root": str(run.scenario / prefix),
            "artifact_hash": run.artifact["content_hash"], "files": expected_files,
            "last_operation_id": plan2["operation_id"]}
        state_ok = actual == expected_files and wio.canonical_json(receipt2) == wio.canonical_json(expected_receipt)
        receipt_ref = run.capture(receipt2_path, "concurrent-receipt.json")
    except DataError as exc:
        state_error = str(exc)
    concurrent_ok = concurrent_ok and state_ok
    run.observations["concurrency"] = {"exit_codes": [r.returncode for r in results],
        "published_files_and_receipt_match_source": state_ok, "receipt_ref": receipt_ref,
        "state_error": state_error}
    return [_result("A24-interrupt-reported", "pass" if interrupted_ok and preserved else "fail",
                    "real UPDATE conflict, pending items, byte backups and later edit preservation checked"),
            _result("A24-concurrent-conflict", "pass" if concurrent_ok else "fail",
                    f"bound package CLI concurrent exits {[r.returncode for r in results]}")]


def _grade_a25(case, index, run):
    distribution = wio.load_json(run.scenario / "pkg/index.json")
    spec = wproduct.load_product(REPO_ROOT)
    inputs = wbuild._capture_inputs(spec)
    wbuild._verify_source_capture(REPO_ROOT, inputs)
    source_hash = wbuild._source_tree_hash(spec, inputs)
    if source_hash != distribution["source_tree_hash"]:
        raise InvalidStateError("trusted source_tree_hash differs from prepared distribution; prepare a new scenario")
    hosts = spec.hosts
    reports, artifacts = {}, {}
    shared_files = {}
    problems = []
    if set(distribution["hosts"]) != set(hosts):
        problems.append("distribution hosts differ from declared product hosts")
    for host in hosts:
        if host not in distribution["hosts"]:
            problems.append(f"{host}: declared host package missing")
            continue
        package = run.scenario / "pkg" / host / "ai-code-workflow"
        entry = wio.resolve_member(run.scenario, f"pkg/{host}/ai-code-workflow/tools/workflow_tool.py")
        result = run.call(["package", "check", "--path", package, "--host", host],
                          expected=None, entry=entry)
        if result.returncode != 0:
            problems.append(f"{host}: package check exited {result.returncode}")
        try:
            report = json.loads(result.stdout)
        except json.JSONDecodeError:
            report = None
        if not isinstance(report, dict):
            problems.append(f"{host}: package check report is not a JSON object")
            report = {"ok": False, "problems": ["invalid package check report"]}
        reports[host] = report
        artifacts[host] = wio.load_json(package / "artifact.json")
        if report.get("ok") is not True or report.get("content_hash") != distribution["hosts"][host]["package_content_hash"]:
            problems.append(f"{host}: package check or distribution hash mismatch")
        wrapping = {wpackage.MANIFEST_PATHS[host]}
        # The standalone builder emits this reviewer even when a legacy
        # product omits generated_agents. Explicit declarations are validated
        # by load_product; both forms must use the producer's composition.
        if host in ("claude", "zcode"):
            target = "agents/workflow-reviewer.md"
            template = f"adapters/{host}/agents/workflow-reviewer.md"
            wrapping.add(target)
            contract_source = next(source for source, target in spec.files
                                   if target == "skills/review/references/reviewer-contract.md")
            contract = inputs[contract_source.relative_to(spec.root).as_posix()].decode("utf-8")
            expected = wbuild._compose_reviewer_agent(spec.root / template, contract, inputs[template])
            actual = wio.read_owned(wio.resolve_member(package, target), root=package)
            if actual != expected:
                problems.append(f"{host}: generated reviewer differs from bound template and shared contract")
        if host == "codex":
            wrapping.update(f"skills/{name}/agents/openai.yaml"
                            for name in spec.all_skills)
        shared_files[host] = {rel: wio.sha256_file(wio.resolve_member(package, rel))
                              for rel, _ in artifacts[host]["files"] if rel not in wrapping}
    path_sets = [set(files) for files in shared_files.values()]
    if path_sets and any(paths != path_sets[0] for paths in path_sets):
        problems.append("cross-host shared resource path sets differ")
    shared = sorted(set().union(*path_sets))
    for rel in shared:
        if len({files.get(rel) for files in shared_files.values()}) != 1:
            problems.append(f"cross-host shared resource mismatch: {rel}")
    reference = next(iter(artifacts.values()), None)
    for host, artifact in artifacts.items():
        for key in ("product_id", "version", "source_revision", "working_tree_dirty", "source_tree_hash", "profiles"):
            expected = reference[key] if key == "profiles" else distribution[key]
            if artifact[key] != expected or type(artifact[key]) is not type(expected):
                problems.append(f"{host}: {key} mismatch")
    run.observations["traceability"] = {"reports": reports, "metadata_matches": not problems,
                                        "source_tree_hash": source_hash,
                                        "shared_resources_checked": shared, "problems": problems}
    return [_result("A25-traceable-identical-core", "fail" if problems else "pass",
                    f"captured baseline, source metadata, package CLI checks and shared bytes checked; problems={problems}")]


def grade(run_dir: Path) -> dict:
    run_dir = Path(run_dir).resolve()
    index_path = run_dir / "index.json"
    if not index_path.is_file():
        raise DataError(f"not a collected run directory (index.json missing): {run_dir}")
    if (run_dir / "grade.json").is_file():
        raise DataError(
            f"run already graded: {run_dir / 'grade.json'} (deterministic scenarios "
            "mutate their one-shot workspace; grade a fresh run instead)")
    wio.resolve_member(run_dir, "grade.json", must_exist=False)
    index_path = wio.resolve_member(run_dir, "index.json")
    index = wio.load_json(index_path)
    _validate_index(index)
    for ref in index.get("raw_refs", []) + index.get("artifacts", []):
        path = wio.resolve_member(run_dir, ref["target_path"])
        if wio.sha256_file(path) != ref["content_sha256"]:
            raise DataError(f"collected material changed: {ref['target_path']}")
    case = find_case(index["case_id"])

    deterministic_ref = None
    if index["case_id"] in DETERMINISTIC:
        scenario = _scenario(index, run_dir)
        if scenario is None:
            checks = [_result(c["check_id"], "not_run", "run is not bound to a reachable prepared scenario")
                      for c in case["checks"]]
        else:
            execution = PackageRun(scenario, index, run_dir)
            try:
                checks = globals()[DETERMINISTIC[index["case_id"]]](case, index, execution)
            except RunFailure as exc:
                checks = [_result(c["check_id"], "fail", str(exc)) for c in case["checks"]]
            deterministic_ref = execution.finish()
    else:
        has_events = bool(index["events"])
        checks = []
        for check in case["checks"]:
            if check["method"] == "manual_review":
                checks.append(_result(
                    check["check_id"], "manual_review" if has_events else "not_run",
                    "requires a sourced human/model review of the real run material"
                    if has_events else "no real host run material collected yet"))
            else:
                checks.append(_result(
                    check["check_id"], "manual_review" if has_events else "not_run",
                    "event material present but semantic proof needs sourced review; "
                    "this grader never substitutes the implementer's own pass"
                    if has_events else "requires real host session evidence (T07); "
                                       "blocked on this machine (see adapters/*/capabilities.md)"))

    results = [c["result"] for c in checks]
    if "fail" in results:
        overall = "fail"
    elif results and all(r == "pass" for r in results):
        overall = "pass"
    else:
        overall = "manual_review"

    grade_doc = {
        "case_id": index["case_id"],
        "run_id": index["run_id"],
        "checks": checks,
        "overall": overall,
        "grader_version": GRADER_VERSION,
        "source_refs": {
            "index": "index.json",
            "cases_sha256": wio.sha256_file(REPO_ROOT / "evals" / "cases.json"),
            "grader_sha256": wio.sha256_file(Path(__file__)),
        },
    }
    if deterministic_ref is not None:
        grade_doc["source_refs"]["deterministic_evidence"] = deterministic_ref
    wio.atomic_write(run_dir / "grade.json", (json.dumps(grade_doc, indent=2, sort_keys=True) + "\n").encode(),
                     expected_before=None, root=run_dir)
    return grade_doc


def main() -> int:
    parser = argparse.ArgumentParser(prog="grade.py")
    parser.add_argument("--run", required=True)
    args = parser.parse_args()
    try:
        grade_doc = grade(Path(args.run))
    except Exception as exc:
        return exit_with(exc)
    print(json.dumps({"case_id": grade_doc["case_id"], "overall": grade_doc["overall"],
                      "checks": {c["check_id"]: c["result"] for c in grade_doc["checks"]}},
                     indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
