"""Regressions for the v1 delivery review; all writes use temporary workspaces."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import textwrap
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from workflow import build, io, owned_files, package_check, policy, product, state

REPO = Path(__file__).resolve().parents[2]
COLLECTION_REPO = Path(__file__).resolve().parents[4]


class ReviewRegressions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.shared = tempfile.TemporaryDirectory()
        cls.dist = Path(cls.shared.name) / "dist"
        build.build_packages(REPO, ["zcode", "codex"], cls.dist)

    @classmethod
    def tearDownClass(cls):
        cls.shared.cleanup()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name).resolve()
        self.workspace = self.base / "project"
        self.workspace.mkdir()
        self.pkg = self.dist / "zcode" / "ai-code-workflow"

    def tearDown(self):
        self.temp.cleanup()

    def copy_package(self, host="zcode"):
        root = self.base / host
        shutil.copytree(self.dist / host, root)
        return root / "ai-code-workflow"

    def test_stage_rejects_symlinked_management_root_without_external_writes(self):
        outside = self.base / "outside"
        outside.mkdir()
        (self.workspace / ".ai-workflow").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(io.DataError):
            owned_files.plan_operation(self.pkg, self.workspace, "stage")
        self.assertEqual(list(outside.iterdir()), [])

    def test_apply_rechecks_management_root_after_plan(self):
        plan = owned_files.plan_operation(self.pkg, self.workspace, "stage")
        outside = self.base / "outside"
        outside.mkdir()
        (self.workspace / ".ai-workflow").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(io.ToolError):
            owned_files.apply_operation(plan, plan["plan_hash"])
        self.assertEqual(list(outside.iterdir()), [])

    def test_operation_id_cannot_escape_backup_directory(self):
        with self.assertRaises(io.DataError):
            owned_files.plan_operation(self.pkg, self.workspace, "stage",
                                       operation_id="../../../escaped")
        self.assertFalse((self.base / "escaped").exists())

    def test_stage_rejects_symlinked_nested_component(self):
        managed = owned_files.managed_root(self.workspace)
        managed.mkdir(parents=True)
        outside = self.base / "outside"
        outside.mkdir()
        (managed / "skills").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(io.DataError):
            owned_files.plan_operation(self.pkg, self.workspace, "stage")
        self.assertEqual(list(outside.iterdir()), [])

    def test_atomic_write_preserves_edit_during_temporary_file_sync(self):
        target = self.workspace / "note.txt"
        target.write_bytes(b"before")
        real_sync = os.fsync
        changed = False

        def user_edits(fd):
            nonlocal changed
            if not changed:
                changed = True
                target.write_bytes(b"user edit")
            return real_sync(fd)

        with patch.object(io.os, "fsync", side_effect=user_edits):
            with self.assertRaises(io.ConflictError):
                io.atomic_write(target, b"tool edit", expected_before=b"before")
        self.assertEqual(target.read_bytes(), b"user edit")

    def test_atomic_create_never_replaces_a_late_new_file(self):
        target = self.workspace / "note.txt"
        real_sync = os.fsync

        def user_creates(fd):
            if not target.exists():
                target.write_bytes(b"user new file")
            return real_sync(fd)

        with patch.object(io.os, "fsync", side_effect=user_creates):
            with self.assertRaises(io.ConflictError):
                io.atomic_write(target, b"tool new file", expected_before=None)
        self.assertEqual(target.read_bytes(), b"user new file")

    def test_package_rejects_false_aggregate_hash(self):
        pkg = self.copy_package()
        path = pkg / "artifact.json"
        artifact = io.load_json(path)
        artifact["content_hash"] = "0" * 64
        path.write_text(json.dumps(artifact))
        self.assertFalse(package_check.check_package(pkg, "zcode")["ok"])

    def test_package_does_not_hide_active_code_as_cache(self):
        for rel in ("tools/workflow/__pycache__/hidden.py", "tools/json.pyc"):
            with self.subTest(path=rel):
                if (self.base / "zcode").exists():
                    shutil.rmtree(self.base / "zcode")
                pkg = self.copy_package()
                extra = pkg / rel
                extra.parent.mkdir(parents=True, exist_ok=True)
                extra.write_bytes(b"unregistered active code")
                self.assertFalse(package_check.check_package(pkg, "zcode")["ok"])
                shutil.rmtree(pkg.parent)

    def test_package_rejects_symlinked_artifact_metadata(self):
        pkg = self.copy_package()
        path = pkg / "artifact.json"
        external = self.base / "external-artifact.json"
        path.rename(external)
        path.symlink_to(external)
        with self.assertRaises(io.DataError):
            package_check.check_package(pkg, "zcode")

    def test_package_rejects_symlinked_marketplace_metadata(self):
        pkg = self.copy_package()
        path = pkg.parent / "marketplace.json"
        external = self.base / "external-market.json"
        path.rename(external)
        path.symlink_to(external)
        with self.assertRaises(io.DataError):
            package_check.check_package(pkg, "zcode")

    def test_package_rejects_missing_core_even_when_artifact_is_rehashed(self):
        pkg = self.copy_package()
        rel = "skills/workflow/SKILL.md"
        (pkg / rel).unlink()
        path = pkg / "artifact.json"
        artifact = io.load_json(path)
        artifact["files"] = [entry for entry in artifact["files"] if entry[0] != rel]
        artifact["content_hash"] = io.sha256_bytes(io.canonical_json(artifact["files"]))
        path.write_text(json.dumps(artifact))
        self.assertFalse(package_check.check_package(pkg, "zcode")["ok"])

    def test_package_rejects_symlinked_parent_even_with_matching_file_bytes(self):
        pkg = self.copy_package()
        outside = self.base / "external-policies"
        shutil.move(str(pkg / "policies"), outside)
        (pkg / "policies").symlink_to(outside, target_is_directory=True)
        self.assertFalse(package_check.check_package(pkg, "zcode")["ok"])

    def test_codex_marketplace_is_discoverable_at_native_path(self):
        market_path = self.dist / "codex/.agents/plugins/marketplace.json"
        self.assertTrue(market_path.is_file())
        entry = io.load_json(market_path)["plugins"][0]
        self.assertEqual(entry["policy"]["installation"], "AVAILABLE")
        self.assertEqual(entry["policy"]["authentication"], "ON_INSTALL")
        self.assertEqual((self.dist / "codex" / entry["source"]["path"]).resolve(),
                         (self.dist / "codex/ai-code-workflow").resolve())

    def test_task_update_rejects_copied_workspace_record_in_preview_and_apply(self):
        state.create_task(self.workspace, "demo", io.load_json(REPO / "templates/task.json"), apply=True)
        other = self.base / "other"
        other.mkdir()
        shutil.copytree(self.workspace / ".ai-workflow", other / ".ai-workflow")
        file = other / ".ai-workflow/tasks/demo/task.json"
        before = file.read_bytes()
        update = {"schema_version": 1, "progress": {
            "phase": "implementing", "status": "in_progress", "completed_steps": [],
            "next_action": "Continue", "unresolved": []}}
        for apply in (False, True):
            with self.subTest(apply=apply), self.assertRaises(io.InvalidStateError):
                state.update_task(other, "demo", 1, update, apply=apply)
            self.assertEqual(file.read_bytes(), before)

    def test_task_create_rejects_linked_tasks_directory(self):
        outside = self.base / "external-tasks"
        outside.mkdir()
        (self.workspace / ".ai-workflow").mkdir()
        (self.workspace / ".ai-workflow/tasks").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(io.DataError):
            state.create_task(self.workspace, "demo", io.load_json(REPO / "templates/task.json"), apply=True)
        self.assertEqual(list(outside.iterdir()), [])

    def test_task_update_rejects_boolean_record_revision(self):
        state.create_task(self.workspace, "demo", io.load_json(REPO / "templates/task.json"), apply=True)
        file = self.workspace / ".ai-workflow/tasks/demo/task.json"
        record = io.load_json(file)
        record["record_revision"] = True
        file.write_text(json.dumps(record))
        before = file.read_bytes()
        for apply in (False, True):
            with self.subTest(apply=apply), self.assertRaises(io.DataError):
                state.update_task(self.workspace, "demo", 1,
                                  {"schema_version": 1, "append_authorization_refs": []}, apply=apply)
            self.assertEqual(file.read_bytes(), before)

    def test_task_malformed_revision_has_data_error_before_cas(self):
        state.create_task(self.workspace, "demo", io.load_json(REPO / "templates/task.json"), apply=True)
        file = self.workspace / ".ai-workflow/tasks/demo/task.json"
        record = io.load_json(file)
        record["record_revision"] = False
        file.write_text(json.dumps(record))
        try:
            state.update_task(self.workspace, "demo", 1,
                              {"schema_version": 1, "append_authorization_refs": []})
        except io.ToolError as exc:
            self.assertEqual(exc.exit_code, 2)
        else:
            self.fail("invalid persisted revision must be rejected")

    def test_task_baseline_preserves_modified_filename(self):
        subprocess.run(["git", "init", "-q", str(self.workspace)], check=True)
        file = self.workspace / "notes.txt"
        file.write_text("existing user work\n")
        subprocess.run(["git", "add", "-N", "notes.txt"], cwd=self.workspace, check=True)
        result = state.create_task(self.workspace, "demo", io.load_json(REPO / "templates/task.json"))
        self.assertEqual(result["proposed_record"]["baseline"]["dirty_files"], ["notes.txt"])

    def test_task_baseline_preserves_carriage_return_in_filename(self):
        subprocess.run(["git", "init", "-q", str(self.workspace)], check=True)
        name = "carriage\rreturn.txt"
        (self.workspace / name).write_text("existing user work\n")
        result = state.create_task(self.workspace, "demo", io.load_json(REPO / "templates/task.json"))
        self.assertEqual(result["proposed_record"]["baseline"]["dirty_files"], [name])

    def test_adapter_input_changes_source_identity(self):
        src = self.base / "source"
        spec = product.load_product(REPO)
        for file in [REPO / "product.json", *(p for p, _ in spec.files)]:
            dest = src / file.relative_to(REPO)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(file, dest)
        shutil.copytree(REPO / "adapters", src / "adapters")
        build.build_packages(src, ["codex"], self.base / "before")
        manifest_path = src / "adapters/codex/plugin.json"
        manifest = io.load_json(manifest_path)
        manifest["description"] += " changed adapter"
        manifest_path.write_text(json.dumps(manifest))
        build.build_packages(src, ["codex"], self.base / "after")
        before = io.load_json(self.base / "before/index.json")
        after = io.load_json(self.base / "after/index.json")
        self.assertNotEqual(before["source_tree_hash"], after["source_tree_hash"])

    def test_a25_does_not_accept_an_unbound_empty_run(self):
        run = self.base / "run"
        run.mkdir()
        index = {"schema_version": 1, "run_id": "test-a25", "case_id": "A25",
                 "host": "zcode", "host_version": None, "model": None,
                 "package_content_hash": None, "policy_hash": None,
                 "comparison_mode": "plugin", "workspace_root": str(self.base / "ghost"),
                 "fixture_baseline_hash": None, "capture_origin": "manual_annotation",
                 "raw_refs": [], "events": [], "artifacts": [],
                 "started_at": None, "finished_at": None}
        (run / "index.json").write_text(json.dumps(index))
        result = subprocess.run([sys.executable, str(REPO / "evals/grade.py"), "--run", str(run)],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotEqual(io.load_json(run / "grade.json")["overall"], "pass")

    def run_ci_dist_step(self):
        text = (COLLECTION_REPO / ".github/workflows/ci.yml").read_text()
        step = text.split("      - name: Verify committed dist/", 1)[1].split("\n      - name:", 1)[0]
        run = step.split("        run:", 1)[1]
        command = textwrap.dedent(run.split("|", 1)[1]) if run.lstrip().startswith("|") else run.strip()
        helper = COLLECTION_REPO / ".github/scripts/check_dist.py"
        if helper.exists():
            dest = self.workspace / ".github/scripts/check_dist.py"
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(helper, dest)
        return subprocess.run(["/bin/sh", "-c", command], cwd=self.workspace,
                              capture_output=True, text=True)

    def test_ci_allows_identical_payload_across_git_metadata_changes(self):
        for folder, head, dirty in (("dist", "1" * 40, True), ("dist-ci", "2" * 40, False)):
            with patch.object(build, "_git_state", return_value=(head, dirty)):
                build.build_packages(REPO, ["zcode", "codex"], self.workspace / folder)
        result = self.run_ci_dist_step()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_ci_rejects_consistent_boolean_standalone_index_schema(self):
        for folder in ("dist", "dist-ci"):
            root = self.workspace / folder
            build.build_packages(REPO, ["zcode", "codex"], root)
            index = io.load_json(root / "index.json")
            index["schema_version"] = True
            (root / "index.json").write_text(json.dumps(index))
        result = self.run_ci_dist_step()
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_ci_rejects_consistent_boolean_standalone_artifact_schema(self):
        for folder in ("dist", "dist-ci"):
            root = self.workspace / folder
            build.build_packages(REPO, ["zcode", "codex"], root)
            metadata = root / "zcode/ai-code-workflow/artifact.json"
            artifact = io.load_json(metadata)
            artifact["schema_version"] = True
            metadata.write_text(json.dumps(artifact))
            index = io.load_json(root / "index.json")
            zipped = root / index["hosts"]["zcode"]["zip"]
            with zipfile.ZipFile(zipped) as source:
                members = {info.filename: (info, source.read(info)) for info in source.infolist()}
            with zipfile.ZipFile(zipped, "w") as output:
                for name, (info, data) in members.items():
                    output.writestr(info, metadata.read_bytes() if name == "ai-code-workflow/artifact.json" else data)
            index["hosts"]["zcode"]["zip_sha256"] = io.sha256_file(zipped)
            (root / "index.json").write_text(json.dumps(index))
        result = self.run_ci_dist_step()
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_ci_rejects_a_corrupt_archive_even_if_index_hash_is_unchanged(self):
        for folder in ("dist", "dist-ci"):
            build.build_packages(REPO, ["zcode", "codex"], self.workspace / folder)
        (self.workspace / "dist/zcode/ai-code-workflow-2.0.0.zip").write_bytes(b"corrupt zip")
        result = self.run_ci_dist_step()
        self.assertNotEqual(result.returncode, 0)

    def test_policy_directory_does_not_silently_fall_back(self):
        (self.workspace / ".ai-workflow/policy.json").mkdir(parents=True)
        with self.assertRaises(io.DataError):
            policy.resolve_policy(REPO, self.workspace)

    def test_ci_rejects_unregistered_nested_artifact_json(self):
        for folder in ("dist", "dist-ci"):
            build.build_packages(REPO, ["zcode", "codex"], self.workspace / folder)
        root = self.workspace / "dist"
        extra = root / "zcode/ai-code-workflow/skills/workflow/artifact.json"
        extra.write_text('{"injected":"unregistered"}')
        index = io.load_json(root / "index.json")
        archive = root / index["hosts"]["zcode"]["zip"]
        with zipfile.ZipFile(archive, "a") as zipped:
            zipped.write(extra, "ai-code-workflow/skills/workflow/artifact.json")
        index["hosts"]["zcode"]["zip_sha256"] = io.sha256_file(archive)
        (root / "index.json").write_text(json.dumps(index))
        self.assertNotEqual(self.run_ci_dist_step().returncode, 0)

    def test_ci_rejects_corrupt_stable_artifact_metadata(self):
        for folder in ("dist", "dist-ci"):
            build.build_packages(REPO, ["zcode", "codex"], self.workspace / folder)
        root = self.workspace / "dist"
        metadata = root / "zcode/ai-code-workflow/artifact.json"
        artifact = io.load_json(metadata)
        artifact["host"] = "codex"
        metadata.write_text(json.dumps(artifact))
        index = io.load_json(root / "index.json")
        archive = root / index["hosts"]["zcode"]["zip"]
        with zipfile.ZipFile(archive) as zipped:
            members = {info.filename: (info, zipped.read(info)) for info in zipped.infolist()}
        with zipfile.ZipFile(archive, "w") as zipped:
            for name, (info, data) in members.items():
                zipped.writestr(info, metadata.read_bytes() if name == "ai-code-workflow/artifact.json" else data)
        index["hosts"]["zcode"]["zip_sha256"] = io.sha256_file(archive)
        (root / "index.json").write_text(json.dumps(index))
        self.assertNotEqual(self.run_ci_dist_step().returncode, 0)

    def test_a25_invalid_host_cannot_bypass_package_binding(self):
        import importlib.util
        spec = importlib.util.spec_from_file_location("regression_grade", REPO / "evals/grade.py")
        grader = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(grader)
        run = self.base / "run"
        run.mkdir()
        index = {"schema_version": 1, "run_id": "bad-host", "case_id": "A25",
                 "host": "unknown", "host_version": None, "model": None,
                 "package_content_hash": None, "policy_hash": None,
                 "comparison_mode": "plugin", "workspace_root": str(self.base),
                 "fixture_baseline_hash": io.sha256_bytes(io.canonical_json({})),
                 "capture_origin": "manual_annotation", "raw_refs": [], "events": [],
                 "artifacts": [], "started_at": None, "finished_at": None}
        (self.base / "prepared.json").write_text(json.dumps({"case_id": "A25", "baseline": {}}))
        shutil.copytree(self.dist, self.base / "pkg")
        (run / "index.json").write_text(json.dumps(index))
        with self.assertRaises(io.DataError):
            grader.grade(run)

    def test_ci_does_not_equate_boolean_and_integer_metadata(self):
        for folder in ("dist", "dist-ci"):
            build.build_packages(REPO, ["zcode", "codex"], self.workspace / folder)
        root = self.workspace / "dist"
        metadata = root / "zcode/ai-code-workflow/artifact.json"
        artifact = io.load_json(metadata)
        artifact["schema_version"] = True
        metadata.write_text(json.dumps(artifact))
        index = io.load_json(root / "index.json")
        archive = root / index["hosts"]["zcode"]["zip"]
        with zipfile.ZipFile(archive) as zipped:
            members = {info.filename: (info, zipped.read(info)) for info in zipped.infolist()}
        with zipfile.ZipFile(archive, "w") as zipped:
            for name, (info, data) in members.items():
                zipped.writestr(info, metadata.read_bytes() if name == "ai-code-workflow/artifact.json" else data)
        index["hosts"]["zcode"]["zip_sha256"] = io.sha256_file(archive)
        (root / "index.json").write_text(json.dumps(index))
        self.assertNotEqual(self.run_ci_dist_step().returncode, 0)

    def test_ci_rejects_symlinked_package_payload(self):
        for folder in ("dist", "dist-ci"):
            build.build_packages(REPO, ["zcode", "codex"], self.workspace / folder)
        notice = self.workspace / "dist/zcode/ai-code-workflow/NOTICE"
        outside = self.base / "outside-notice"
        notice.rename(outside)
        notice.symlink_to(outside)
        self.assertNotEqual(self.run_ci_dist_step().returncode, 0)

    def test_policy_symlink_is_not_loaded_from_outside_workspace(self):
        outside = self.base / "foreign.json"
        outside.write_text('{"schema_version":1,"mode":"continuous"}')
        (self.workspace / ".ai-workflow").mkdir()
        (self.workspace / ".ai-workflow/policy.json").symlink_to(outside)
        with self.assertRaises(io.DataError):
            policy.resolve_policy(REPO, self.workspace)


if __name__ == "__main__":
    unittest.main()
