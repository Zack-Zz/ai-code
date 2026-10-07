"""evals tools: prepare / collect / grade."""

import json
import hashlib
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PREPARE = REPO_ROOT / "evals" / "prepare.py"
COLLECT = REPO_ROOT / "evals" / "collect.py"
GRADE = REPO_ROOT / "evals" / "grade.py"


def run_py(script, *args):
    return subprocess.run([sys.executable, str(script), *args],
                          capture_output=True, text=True, cwd=str(REPO_ROOT))


def write_manifest(path: Path, **overrides):
    data = {
        "schema_version": 1,
        "case_id": "A03",
        "host": "zcode",
        "host_version": None,
        "model": None,
        "package_content_hash": None,
        "policy_hash": None,
        "comparison_mode": "plugin",
        "workspace_root": "/tmp/nowhere",
        "fixture_baseline_hash": None,
        "raw_files": [],
        "artifact_files": [],
        "events": [],
        "converter_id": None,
        "started_at": None,
        "finished_at": None,
    }
    data.update(overrides)
    path.write_text(json.dumps(data, indent=2))
    return data


class PrepareTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.td.cleanup()

    def out(self, name):
        return Path(self.td.name) / name

    def test_unknown_case_rejected(self):
        result = run_py(PREPARE, "--case", "A99", "--output", str(self.out("x")))
        self.assertEqual(result.returncode, 2)

    def test_prepare_refuses_existing_output(self):
        out = self.out("exists")
        out.mkdir()
        result = run_py(PREPARE, "--case", "A03", "--output", str(out))
        self.assertEqual(result.returncode, 3)

    def test_prepare_python_labels_baseline(self):
        out = self.out("a03")
        result = run_py(PREPARE, "--case", "A03", "--output", str(out))
        self.assertEqual(result.returncode, 0, result.stderr)
        prepared = json.loads((out / "prepared.json").read_text())
        self.assertEqual(prepared["case_id"], "A03")
        self.assertEqual(prepared["fixture"], "python_labels")
        self.assertIn("workspace/labels.py", prepared["baseline"])
        self.assertTrue((out / "workspace" / "labels.py").is_file())
        for turn in prepared["turns"]:
            self.assertEqual(turn["role"], "user")

    def test_prepare_applies_case_specific_mutations(self):
        out = self.out("a04")
        result = run_py(PREPARE, "--case", "A04", "--output", str(out))
        self.assertEqual(result.returncode, 0, result.stderr)
        text = (out / "workspace" / "labels.py").read_text()
        self.assertIn("regression at line 3", text)

        out10 = self.out("a10")
        result = run_py(PREPARE, "--case", "A10", "--output", str(out10))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((out10 / "workspace" / "test_history_failure.py").is_file())

    def test_prepare_git_permissions_creates_isolated_repo(self):
        out = self.out("a18")
        result = run_py(PREPARE, "--case", "A18", "--output", str(out))
        self.assertEqual(result.returncode, 0, result.stderr)
        repo = out / "repo"
        remote = out / "remote.git"
        self.assertTrue(repo.is_dir() and remote.is_dir())
        self.assertTrue((repo / "APPROVED.txt").is_file())
        self.assertTrue((repo / ".ai-workflow" / "tasks" / "demo" / "task.json").is_file())

    def test_git_permission_fixture_has_a_real_staged_fix_and_separate_baselines(self):
        out = self.out("a18-staged")
        result = run_py(PREPARE, "--case", "A18", "--output", str(out))
        self.assertEqual(result.returncode, 0, result.stderr)
        staged = subprocess.run(["git", "diff", "--cached", "--name-only"],
                                cwd=out / "repo", capture_output=True, text=True)
        self.assertEqual(staged.stdout.splitlines(), ["fix.py"])
        record = json.loads((out / "prepared.json").read_text())
        self.assertEqual(set(record.get("git_subcase_baselines", {})),
                         {"review_only", "commit_only"})

    def test_a19_user_turn_does_not_itself_authorize_push(self):
        out = self.out("a19-input")
        result = run_py(PREPARE, "--case", "A19", "--output", str(out))
        self.assertEqual(result.returncode, 0, result.stderr)
        record = json.loads((out / "prepared.json").read_text())
        request = record["turns"][0]["content"].lower()
        self.assertNotIn("go ahead and push", request)
        self.assertIn("do not", request)

    def test_prepare_managed_package_builds_real_package(self):
        out = self.out("a23")
        result = run_py(PREPARE, "--case", "A23", "--output", str(out))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((out / "pkg" / "zcode" / "ai-code-workflow" / "artifact.json").is_file())
        self.assertTrue((out / "project").is_dir())


class CollectTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.base = Path(self.td.name)
        (self.base / "raw").mkdir()
        (self.base / "raw" / "session.txt").write_text("real session capture\n")

    def tearDown(self):
        self.td.cleanup()

    def collect(self, manifest_path, origin="manual_annotation", out_name="run"):
        return run_py(COLLECT, "--case", "A03", "--input", str(manifest_path),
                      "--origin", origin, "--output", str(self.base / out_name))

    def test_manual_annotation_roundtrip(self):
        manifest = self.base / "manifest.json"
        write_manifest(
            manifest,
            raw_files=[{"source_path": "raw/session.txt", "target_path": "raw/session.txt"}],
            events=[{
                "seq": 1, "kind": "user_message", "actor": "user",
                "correlation_id": "t1", "raw_ref": "raw/session.txt",
                "data": {"text": "Add label(2)->fault"},
            }])
        result = self.collect(manifest)
        self.assertEqual(result.returncode, 0, result.stderr)
        index = json.loads((self.base / "run" / "index.json").read_text())
        self.assertEqual(index["schema_version"], 1)
        self.assertEqual(index["case_id"], "A03")
        self.assertEqual(index["capture_origin"], "manual_annotation")
        self.assertEqual(len(index["events"]), 1)
        raw_entry = index["raw_refs"][0]
        self.assertEqual(raw_entry["target_path"], "raw/session.txt")
        self.assertEqual(raw_entry["content_sha256"],
                         __import__("hashlib").sha256(b"real session capture\n").hexdigest())

    def test_case_mismatch_rejected(self):
        manifest = self.base / "manifest.json"
        write_manifest(manifest, case_id="A05")
        result = self.collect(manifest)
        self.assertEqual(result.returncode, 2)

    def test_duplicate_keys_rejected(self):
        manifest = self.base / "manifest.json"
        manifest.write_text(json.dumps({
            "schema_version": 1, "case_id": "A03", "host": "zcode",
            "host_version": None, "model": None, "package_content_hash": None,
            "policy_hash": None, "comparison_mode": "plugin",
            "workspace_root": "/x", "fixture_baseline_hash": "0" * 64,
            "raw_files": [], "artifact_files": [], "events": [],
            "converter_id": None, "started_at": None, "finished_at": None})[:-1]
            + ', "case_id": "A03"}')
        result = self.collect(manifest)
        self.assertEqual(result.returncode, 2)

    def test_native_export_without_converter_is_unsupported(self):
        manifest = self.base / "manifest.json"
        write_manifest(manifest, converter_id="codex-session-v1", events=[])
        result = self.collect(manifest, origin="native_export")
        self.assertEqual(result.returncode, 5)
        self.assertIn("unsupported_format", result.stderr)

    def test_event_with_dangling_raw_ref_rejected(self):
        manifest = self.base / "manifest.json"
        write_manifest(
            manifest,
            raw_files=[{"source_path": "raw/session.txt", "target_path": "raw/session.txt"}],
            events=[{
                "seq": 1, "kind": "user_message", "actor": "user",
                "correlation_id": "t1", "raw_ref": "raw/ghost.txt",
                "data": {"text": "x"},
            }])
        result = self.collect(manifest)
        self.assertEqual(result.returncode, 2)

    def test_target_escape_rejected(self):
        manifest = self.base / "manifest.json"
        write_manifest(
            manifest,
            raw_files=[{"source_path": "raw/session.txt", "target_path": "../escape.txt"}])
        result = self.collect(manifest)
        self.assertEqual(result.returncode, 2)

    def test_refuses_existing_output(self):
        manifest = self.base / "manifest.json"
        write_manifest(manifest)
        (self.base / "run").mkdir()
        result = self.collect(manifest)
        self.assertEqual(result.returncode, 3)

    def test_collect_reserves_grader_material_namespace(self):
        manifest = self.base / "reserved.json"
        write_manifest(manifest, raw_files=[{
            "source_path": "raw/session.txt", "target_path": "grader/commands/001.stdout.txt"}])
        result = self.collect(manifest)
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertFalse((self.base / "run").exists())


class PythonGateTests(unittest.TestCase):
    def test_python_helper_rejects_empty_discovery(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            (root / "tests").mkdir()
            (root / "scripts").mkdir()
            (root / "tests/__init__.py").write_text("")
            shutil.copyfile(REPO_ROOT / "tests/run_python_tests.py", root / "tests/run_python_tests.py")
            result = run_py(root / "tests/run_python_tests.py")
            self.assertNotEqual(result.returncode, 0, "zero discovered tests cannot satisfy the gate")


class GradeTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.base = Path(self.td.name)

    def tearDown(self):
        self.td.cleanup()

    def prepared(self, case_id):
        out = self.base / f"{case_id}-prep"
        result = run_py(PREPARE, "--case", case_id, "--output", str(out))
        assert result.returncode == 0, result.stderr
        return out

    def collected(self, case_id):
        prep = self.prepared(case_id)
        run_dir = self.base / (case_id + "-run")
        manifest = self.base / (case_id + "-m.json")
        write_manifest(manifest, case_id=case_id, workspace_root=str(prep))
        result = run_py(COLLECT, "--case", case_id, "--input", str(manifest),
                        "--origin", "manual_annotation", "--output", str(run_dir))
        self.assertEqual(result.returncode, 0, result.stderr)
        return prep, run_dir

    def reseal_fixture(self, prep):
        """Keep a deliberately broken runtime fixture internally hash-consistent."""
        distribution = json.loads((prep / "pkg/index.json").read_text())
        for host, item in distribution["hosts"].items():
            pkg = prep / "pkg" / host / "ai-code-workflow"
            artifact = json.loads((pkg / "artifact.json").read_text())
            artifact["files"] = [[rel, hashlib.sha256((pkg / rel).read_bytes()).hexdigest()]
                                 for rel, _ in artifact["files"]]
            canonical = json.dumps(artifact["files"], sort_keys=True, separators=(",", ":"),
                                   ensure_ascii=True).encode()
            artifact["content_hash"] = hashlib.sha256(canonical).hexdigest()
            (pkg / "artifact.json").write_text(json.dumps(artifact))
            item["package_content_hash"] = artifact["content_hash"]
            archive = prep / "pkg" / item["zip"]
            with zipfile.ZipFile(archive, "w") as zipped:
                for path in sorted((prep / "pkg" / host).rglob("*")):
                    if path.is_file() and path != archive:
                        zipped.write(path, path.relative_to(prep / "pkg" / host).as_posix())
            item["zip_sha256"] = hashlib.sha256(archive.read_bytes()).hexdigest()
        (prep / "pkg/index.json").write_text(json.dumps(distribution))
        record = json.loads((prep / "prepared.json").read_text())
        record["baseline"] = {p.relative_to(prep).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                              for prefix in ("pkg", "project")
                              for p in (prep / prefix).rglob("*") if p.is_file()}
        (prep / "prepared.json").write_text(json.dumps(record))

    def test_a24_corrupt_recovery_hashes_from_bound_runtime_do_not_pass(self):
        prep = self.prepared("A24")
        module = prep / "pkg/zcode/ai-code-workflow/tools/workflow/owned_files.py"
        module.write_text(module.read_text() + '''
_eval_original_pending = _write_pending
def _write_pending(op_root, plan, applied):
    _eval_original_pending(op_root, plan, applied)
    path = op_root / "pending-operation.json"
    payload = json.loads(path.read_text())
    for item in payload["recovery_basis"]:
        item["expected_before_sha256"] = "0" * 64
        item["desired_sha256"] = "0" * 64
    path.write_text(json.dumps(payload))
''')
        self.reseal_fixture(prep)
        manifest = self.base / "bad-recovery-manifest.json"
        write_manifest(manifest, case_id="A24", workspace_root=str(prep))
        run_dir = self.base / "bad-recovery-run"
        result = run_py(COLLECT, "--case", "A24", "--input", str(manifest),
                        "--origin", "manual_annotation", "--output", str(run_dir))
        self.assertEqual(result.returncode, 0, result.stderr)
        result = run_py(GRADE, "--run", str(run_dir))
        self.assertEqual(result.returncode, 0, result.stderr)
        grade = json.loads((run_dir / "grade.json").read_text())
        checks = {c["check_id"]: c["result"] for c in grade["checks"]}
        self.assertEqual(checks["A24-interrupt-reported"], "fail")
        self.assertEqual(grade["overall"], "fail")

    def test_a24_concurrent_success_claim_without_published_files_does_not_pass(self):
        prep = self.prepared("A24")
        module = prep / "pkg/zcode/ai-code-workflow/tools/workflow/owned_files.py"
        module.write_text(module.read_text() + '''
_eval_real_apply = apply_operation
def apply_operation(plan, expected_plan_hash):
    if Path(plan["target_root"]).name == "project2":
        import os
        try:
            fd = os.open(Path(plan["target_root"]) / "claimed-winner", os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            os.close(fd)
        except FileExistsError:
            raise ConflictError("second claimant")
        return {"applied": True, "changed": True}
    return _eval_real_apply(plan, expected_plan_hash)
''')
        self.reseal_fixture(prep)
        manifest = self.base / "fake-publication-manifest.json"
        write_manifest(manifest, case_id="A24", workspace_root=str(prep))
        run_dir = self.base / "fake-publication-run"
        result = run_py(COLLECT, "--case", "A24", "--input", str(manifest),
                        "--origin", "manual_annotation", "--output", str(run_dir))
        self.assertEqual(result.returncode, 0, result.stderr)
        result = run_py(GRADE, "--run", str(run_dir))
        self.assertEqual(result.returncode, 0, result.stderr)
        grade = json.loads((run_dir / "grade.json").read_text())
        checks = {c["check_id"]: c["result"] for c in grade["checks"]}
        self.assertEqual(checks["A24-concurrent-conflict"], "fail")
        self.assertEqual(grade["overall"], "fail")

    def test_a25_checks_shared_root_resources_as_well_as_skills(self):
        prep = self.prepared("A25")
        license_file = prep / "pkg/codex/ai-code-workflow/LICENSE"
        license_file.write_bytes(license_file.read_bytes() + b"\nDifferent host license bytes.\n")
        self.reseal_fixture(prep)
        manifest = self.base / "different-license-manifest.json"
        write_manifest(manifest, case_id="A25", workspace_root=str(prep))
        run_dir = self.base / "different-license-run"
        result = run_py(COLLECT, "--case", "A25", "--input", str(manifest),
                        "--origin", "manual_annotation", "--output", str(run_dir))
        self.assertEqual(result.returncode, 0, result.stderr)
        result = run_py(GRADE, "--run", str(run_dir))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads((run_dir / "grade.json").read_text())["overall"], "fail")

    def test_collect_rejects_linked_scenario_subroots_before_import(self):
        for child in ("project", "pkg"):
            with self.subTest(child=child):
                prep = self.base / ("linked-" + child)
                result = run_py(PREPARE, "--case", "A23", "--output", str(prep))
                self.assertEqual(result.returncode, 0, result.stderr)
                external = self.base / ("external-" + child)
                external.mkdir()
                (external / "sentinel").write_text("user content")
                shutil.rmtree(prep / child)
                (prep / child).symlink_to(external, target_is_directory=True)
                manifest = self.base / (child + "-manifest.json")
                write_manifest(manifest, case_id="A23", workspace_root=str(prep))
                output = self.base / (child + "-run")
                result = run_py(COLLECT, "--case", "A23", "--input", str(manifest),
                                "--origin", "manual_annotation", "--output", str(output))
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertEqual(sorted(p.name for p in external.iterdir()), ["sentinel"])
                self.assertFalse(output.exists())

    def test_grade_rejects_project_link_replacement_without_outside_writes(self):
        prep, run_dir = self.collected("A23")
        external = self.base / "user-project"
        external.mkdir()
        (external / "sentinel").write_text("user content")
        (prep / "project").rmdir()
        (prep / "project").symlink_to(external, target_is_directory=True)
        result = run_py(GRADE, "--run", str(run_dir))
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertEqual(sorted(p.name for p in external.iterdir()), ["sentinel"])

    def test_grade_rejects_broken_output_link_before_scenario_writes(self):
        prep, run_dir = self.collected("A23")
        outside = self.base / "outside-grade.json"
        (run_dir / "grade.json").symlink_to(outside)
        result = run_py(GRADE, "--run", str(run_dir))
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertFalse(outside.exists())
        self.assertFalse((prep / "project" / ".ai-workflow").exists())

    def test_grade_rejects_actual_baseline_drift_before_writes(self):
        prep, run_dir = self.collected("A23")
        (prep / "project" / "user-file").write_text("added after capture")
        result = run_py(GRADE, "--run", str(run_dir))
        self.assertEqual(result.returncode, 4, result.stderr)
        self.assertFalse((prep / "project" / ".ai-workflow").exists())

    def test_grade_rejects_package_metadata_drift_in_all_deterministic_cases(self):
        for case_id in ("A23", "A24", "A25"):
            with self.subTest(case=case_id):
                prep, run_dir = self.collected(case_id)
                path = prep / "pkg/zcode/ai-code-workflow/artifact.json"
                artifact = json.loads(path.read_text())
                artifact["source_revision"] = "f" * 40
                artifact["working_tree_dirty"] = not artifact["working_tree_dirty"]
                path.write_text(json.dumps(artifact))
                result = run_py(GRADE, "--run", str(run_dir))
                self.assertEqual(result.returncode, 4, result.stderr)
                self.assertFalse((prep / "project" / ".ai-workflow").exists())

    def test_collected_prepared_record_is_bound_even_if_source_record_is_rewritten(self):
        prep, run_dir = self.collected("A23")
        index = json.loads((run_dir / "index.json").read_text())
        captured = [r for r in index["artifacts"] if r["target_path"] == "scenario/prepared.json"]
        self.assertEqual(len(captured), 1)
        record = json.loads((prep / "prepared.json").read_text())
        record["baseline"] = {}
        (prep / "prepared.json").write_text(json.dumps(record))
        result = run_py(GRADE, "--run", str(run_dir))
        self.assertEqual(result.returncode, 4, result.stderr)

    def test_manager_grade_executes_bound_package_cli_not_repository_tools(self):
        prep = self.prepared("A23")
        pkg = prep / "pkg/zcode/ai-code-workflow"
        (pkg / "tools/workflow_tool.py").write_text("raise SystemExit(1)\n")
        artifact = json.loads((pkg / "artifact.json").read_text())
        artifact["files"] = [[rel, hashlib.sha256((pkg / rel).read_bytes()).hexdigest()]
                             for rel, _ in artifact["files"]]
        canonical = json.dumps(artifact["files"], sort_keys=True, separators=(",", ":"),
                               ensure_ascii=True).encode()
        artifact["content_hash"] = hashlib.sha256(canonical).hexdigest()
        (pkg / "artifact.json").write_text(json.dumps(artifact))
        distribution = json.loads((prep / "pkg/index.json").read_text())
        distribution["hosts"]["zcode"]["package_content_hash"] = artifact["content_hash"]
        archive = prep / "pkg" / distribution["hosts"]["zcode"]["zip"]
        with zipfile.ZipFile(archive, "w") as zipped:
            for path in sorted((prep / "pkg/zcode").rglob("*")):
                if path.is_file() and path != archive:
                    zipped.write(path, path.relative_to(prep / "pkg/zcode").as_posix())
        distribution["hosts"]["zcode"]["zip_sha256"] = hashlib.sha256(archive.read_bytes()).hexdigest()
        (prep / "pkg/index.json").write_text(json.dumps(distribution))
        record = json.loads((prep / "prepared.json").read_text())
        record["baseline"] = {p.relative_to(prep).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                              for p in (prep / "pkg").rglob("*") if p.is_file()}
        (prep / "prepared.json").write_text(json.dumps(record))
        manifest = self.base / "broken-package-manifest.json"
        write_manifest(manifest, case_id="A23", workspace_root=str(prep))
        run_dir = self.base / "broken-package-run"
        collected = run_py(COLLECT, "--case", "A23", "--input", str(manifest),
                           "--origin", "manual_annotation", "--output", str(run_dir))
        self.assertEqual(collected.returncode, 0, collected.stderr)
        graded = run_py(GRADE, "--run", str(run_dir))
        self.assertEqual(graded.returncode, 0, graded.stderr)
        self.assertEqual(json.loads((run_dir / "grade.json").read_text())["overall"], "fail")
        self.assertFalse((prep / "project" / ".ai-workflow").exists())

    def test_agent_case_without_real_run_stays_unverified(self):
        prep = self.prepared("A03")
        run_dir = self.base / "a03-run"
        manifest = self.base / "m.json"
        write_manifest(manifest, raw_files=[], events=[])
        result = run_py(COLLECT, "--case", "A03", "--input", str(manifest),
                        "--origin", "manual_annotation", "--output", str(run_dir))
        self.assertEqual(result.returncode, 0, result.stderr)
        graded = run_py(GRADE, "--run", str(run_dir))
        self.assertEqual(graded.returncode, 0, graded.stderr)
        grade = json.loads((run_dir / "grade.json").read_text())
        self.assertEqual(grade["case_id"], "A03")
        self.assertNotEqual(grade["overall"], "pass",
                            "no real host evidence must not produce pass")
        results = {c["check_id"]: c["result"] for c in grade["checks"]}
        self.assertIn(results["A03-red-first"], {"not_run", "manual_review", "blocked_env"})

    def test_manager_case_runs_deterministic_scenario(self):
        prep = self.prepared("A23")
        run_dir = self.base / "a23-run"
        manifest = self.base / "m.json"
        write_manifest(manifest, case_id="A23", raw_files=[], events=[],
                       workspace_root=str(prep))
        result = run_py(COLLECT, "--case", "A23", "--input", str(manifest),
                        "--origin", "manual_annotation", "--output", str(run_dir))
        self.assertEqual(result.returncode, 0, result.stderr)
        graded = run_py(GRADE, "--run", str(run_dir))
        grade = json.loads((run_dir / "grade.json").read_text())
        results = {c["check_id"]: c["result"] for c in grade["checks"]}
        self.assertEqual(results.get("A23-no-duplicates"), "pass")
        self.assertEqual(results.get("A23-protects-unowned-and-edited"), "pass")
        self.assertEqual(grade["overall"], "pass")

    def test_manager_case_a24_interrupt_and_concurrency(self):
        prep = self.prepared("A24")
        run_dir = self.base / "a24-run"
        manifest = self.base / "m.json"
        write_manifest(manifest, case_id="A24", raw_files=[], events=[],
                       workspace_root=str(prep))
        result = run_py(COLLECT, "--case", "A24", "--input", str(manifest),
                        "--origin", "manual_annotation", "--output", str(run_dir))
        self.assertEqual(result.returncode, 0, result.stderr)
        graded = run_py(GRADE, "--run", str(run_dir))
        grade = json.loads((run_dir / "grade.json").read_text())
        results = {c["check_id"]: c["result"] for c in grade["checks"]}
        self.assertEqual(results.get("A24-interrupt-reported"), "pass")
        self.assertEqual(results.get("A24-concurrent-conflict"), "pass")
        self.assertEqual(grade["overall"], "pass")
        ref = grade["source_refs"].get("deterministic_evidence")
        self.assertIsInstance(ref, dict, "actual command/fault material must be retained")
        evidence_path = run_dir / ref["relative_path"]
        self.assertEqual(hashlib.sha256(evidence_path.read_bytes()).hexdigest(), ref["content_sha256"])
        material = json.loads(evidence_path.read_text())
        interruption = material["observations"]["interrupted_update"]
        self.assertEqual(interruption["pending"]["action"], "update")
        self.assertEqual(len(interruption["pending"]["applied"]), 1)
        self.assertGreaterEqual(len(interruption["pending"]["recovery_basis"]), 2)
        self.assertTrue(interruption["backups_match_before"])
        self.assertTrue(interruption["later_user_edit_preserved"])
        self.assertIsInstance(interruption.get("material_refs"), dict,
                              "pending record and byte backups must be retained as hashed material")
        for ref in interruption["material_refs"].values():
            self.assertEqual(hashlib.sha256((run_dir / ref["relative_path"]).read_bytes()).hexdigest(),
                             ref["content_sha256"])
        self.assertIn(3, [c["exit_code"] for c in material["commands"]])
        self.assertTrue(all(str((prep / "pkg/zcode/ai-code-workflow/tools/workflow_tool.py").resolve())
                            in c["command"] for c in material["commands"]))
        # regrading a consumed run is a clear error, not a crash (L9)
        regraded = run_py(GRADE, "--run", str(run_dir))
        self.assertEqual(regraded.returncode, 2)

    def test_state_resume_fixture_is_repointed_and_checkable(self):
        prep = self.prepared("A20")
        self.assertTrue((prep / "workspace" / ".ai-workflow" / "tasks" / "resume-demo").is_dir())
        sys.path.insert(0, str(REPO_ROOT / "scripts"))
        from workflow import state as wstate
        result = wstate.check_task(prep / "workspace", "resume-demo")
        self.assertEqual(result["identity_status"], "consistent",
                         "prepare must repoint fixture workspace placeholders")
        self.assertFalse(result["consistent"], "stale evidence stays stale by design")
        self.assertEqual(len(result["invalid_evidence"]), 1)
        self.assertIn("changed since the evidence was captured",
                      result["invalid_evidence"][0]["reason"],
                      "must be subject drift, not a rebound-hash mismatch")
        other = wstate.check_task(prep / "workspace", "other-task")
        self.assertTrue(other["consistent"])

    def test_package_case_checks_real_dist(self):
        prep = self.prepared("A25")
        run_dir = self.base / "a25-run"
        manifest = self.base / "m.json"
        write_manifest(manifest, case_id="A25", raw_files=[], events=[],
                       workspace_root=str(prep))
        result = run_py(COLLECT, "--case", "A25", "--input", str(manifest),
                        "--origin", "manual_annotation", "--output", str(run_dir))
        self.assertEqual(result.returncode, 0, result.stderr)
        graded = run_py(GRADE, "--run", str(run_dir))
        grade = json.loads((run_dir / "grade.json").read_text())
        self.assertEqual(grade["overall"], "pass")
        self.assertEqual(grade["checks"][0]["result"], "pass")

    def test_grade_refuses_unknown_run(self):
        result = run_py(GRADE, "--run", str(self.base / "ghost"))
        self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
