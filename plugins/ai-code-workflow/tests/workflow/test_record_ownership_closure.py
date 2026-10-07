"""Behavior regressions for the overall review's IO/task/ownership findings."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from workflow import build, io, owned_files as files, state
from tests.workflow.test_state import make_evidence

REPO = Path(__file__).resolve().parents[2]


class OwnershipClosure(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.shared = tempfile.TemporaryDirectory()
        cls.dist = Path(cls.shared.name) / "dist"
        build.build_packages(REPO, ["zcode"], cls.dist)

    @classmethod
    def tearDownClass(cls):
        cls.shared.cleanup()

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name).resolve()
        shutil.copytree(self.dist / "zcode", self.base / "source")
        self.package = self.base / "source/ai-code-workflow"
        self.target = self.base / "project"
        self.target.mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def stage(self):
        plan = files.plan_operation(self.package, self.target, "stage")
        files.apply_operation(plan, plan["plan_hash"])

    def test_published_source_bytes_match_their_verified_hash(self):
        plan = files.plan_operation(self.package, self.target, "stage")
        real_hash = io.sha256_file
        changed = False

        def change_after_hash(path):
            nonlocal changed
            result = real_hash(path)
            pending = self.target / ".ai-workflow/backups" / plan["operation_id"] / "pending-operation.json"
            if Path(path) == self.package / "NOTICE" and pending.exists() and not changed:
                changed = True
                Path(path).write_bytes(b"unverified replacement bytes\n")
            return result

        with patch.object(io, "sha256_file", side_effect=change_after_hash):
            result = files.apply_operation(plan, plan["plan_hash"])
        self.assertTrue(result["applied"])
        receipt = io.load_json(files.receipt_file(self.target))
        self.assertEqual(real_hash(files.managed_root(self.target) / "NOTICE"), receipt["files"]["NOTICE"])

    def test_remove_rejects_receipt_copied_from_another_target(self):
        self.stage()
        other = self.base / "other"
        other.mkdir()
        shutil.copytree(self.target / ".ai-workflow", other / ".ai-workflow")
        before = (files.managed_root(other) / "NOTICE").read_bytes()
        with self.assertRaises(io.ConflictError):
            files.plan_operation(None, other, "remove")
        self.assertEqual((files.managed_root(other) / "NOTICE").read_bytes(), before)

    def test_recovery_scan_rejects_linked_operation_directory(self):
        outside = self.base / "outside-backup"
        outside.mkdir()
        (outside / "pending-operation.json").write_text('{"operation_id":"outside-operation"}')
        backups = files.backups_root(self.target)
        backups.mkdir(parents=True)
        (backups / "linked").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(io.DataError):
            files.plan_operation(self.package, self.target, "stage")

    def test_remove_finishes_receipt_lifecycle_when_payload_already_missing(self):
        self.stage()
        shutil.rmtree(files.managed_root(self.target))
        plan = files.plan_operation(None, self.target, "remove")
        result = files.apply_operation(plan, plan["plan_hash"])
        self.assertTrue(result["changed"])
        self.assertFalse(files.receipt_file(self.target).exists())
        files.plan_operation(self.package, self.target, "stage")

    def test_identical_payload_update_repairs_receipt_metadata(self):
        self.stage()
        path = files.receipt_file(self.target)
        receipt = io.load_json(path)
        receipt["version"] = "0.0.0"
        receipt["artifact_hash"] = "0" * 64
        path.write_text(json.dumps(receipt))
        plan = files.plan_operation(self.package, self.target, "update")
        result = files.apply_operation(plan, plan["plan_hash"])
        self.assertTrue(result["changed"])
        actual = io.load_json(path)
        self.assertEqual(actual["version"], "2.0.0")
        self.assertEqual(actual["artifact_hash"], io.load_json(self.package / "artifact.json")["content_hash"])

    def test_deleted_receipt_during_update_is_a_conflict(self):
        self.stage()
        path = files.receipt_file(self.target)
        # A real payload replacement reaches receipt publication in the old
        # implementation too; this regression is independent of no-op repair.
        (self.package / "NOTICE").write_text("updated fixture notice\n")
        artifact = io.load_json(self.package / "artifact.json")
        artifact["files"] = [[rel, io.sha256_file(self.package / rel)] for rel, _ in artifact["files"]]
        artifact["content_hash"] = io.sha256_bytes(io.canonical_json(artifact["files"]))
        (self.package / "artifact.json").write_text(json.dumps(artifact))
        plan = files.plan_operation(self.package, self.target, "update")
        real_pending = files._write_pending

        def delete_receipt(op_root, current_plan, applied):
            real_pending(op_root, current_plan, applied)
            path.unlink(missing_ok=True)

        with patch.object(files, "_write_pending", side_effect=delete_receipt):
            with self.assertRaises(io.ConflictError):
                files.apply_operation(plan, plan["plan_hash"])
        self.assertFalse(path.exists())

    def test_receipt_version_uses_validated_package_snapshot(self):
        plan = files.plan_operation(self.package, self.target, "stage")
        real_pending = files._write_pending

        def mutate_artifact_metadata(op_root, current_plan, applied):
            real_pending(op_root, current_plan, applied)
            artifact = io.load_json(self.package / "artifact.json")
            artifact["version"] = "9.9.9"
            (self.package / "artifact.json").write_text(json.dumps(artifact))

        with patch.object(files, "_write_pending", side_effect=mutate_artifact_metadata):
            files.apply_operation(plan, plan["plan_hash"])
        self.assertEqual(io.load_json(files.receipt_file(self.target))["version"], "2.0.0")

    def test_malformed_receipt_metadata_is_rejected(self):
        self.stage()
        path = files.receipt_file(self.target)
        original = path.read_bytes()
        for field, value in (("schema_version", True), ("version", 3), ("artifact_hash", "x" * 64),
                             ("managed_root", {}), ("last_operation_id", "../op")):
            with self.subTest(field=field):
                receipt = json.loads(original)
                receipt[field] = value
                path.write_text(json.dumps(receipt))
                with self.assertRaises(io.DataError):
                    files.plan_operation(None, self.target, "remove")


class RecordClosure(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name).resolve()
        self.workspace = self.base / "workspace"
        self.workspace.mkdir()
        (self.workspace / "calc.py").write_text("value = 1\n")
        state.create_task(self.workspace, "demo", io.load_json(REPO / "templates/task.json"), apply=True)
        self.task = self.workspace / ".ai-workflow/tasks/demo/task.json"

    def tearDown(self):
        self.temp.cleanup()

    def register(self, evidence):
        path = self.task.parent / "evidence/ev-1.json"
        path.write_text(json.dumps(evidence))
        ref = {"relative_path": "evidence/ev-1.json", "content_sha256": io.sha256_file(path)}
        return state.update_task(self.workspace, "demo", 1,
                                 {"schema_version": 1, "append_evidence_refs": [ref]}, apply=True)

    def test_host_pass_rejects_declared_execution_failure(self):
        original = self.task.read_bytes()
        for field, value in (("exit_code", 1), ("signal", "SIGTERM"), ("start_error", "ENOENT")):
            with self.subTest(field=field):
                self.task.write_bytes(original)
                evidence = make_evidence(self.workspace)
                evidence["kind"] = "host_run"
                evidence["host_context"] = {
                    "host": "codex", "host_version": "0.159.2", "model": "fixture-model",
                    "case_id": "A03", "package_content_hash": "1" * 64, "policy_hash": "2" * 64}
                evidence["execution"][field] = value
                with self.assertRaises(io.DataError):
                    self.register(evidence)

    def test_check_detects_wrong_task_id_and_malformed_revision(self):
        record = io.load_json(self.task)
        record["task_id"] = "other"
        record["record_revision"] = False
        self.task.write_text(json.dumps(record))
        self.assertFalse(state.check_task(self.workspace, "demo")["consistent"])

    def test_check_does_not_follow_task_metadata_link(self):
        outside = self.base / "outside.json"
        self.task.rename(outside)
        self.task.symlink_to(outside)
        result = state.check_task(self.workspace, "demo")
        self.assertFalse(result["consistent"])

    def test_protected_fingerprint_rejects_symlink_to_outside(self):
        outside = self.base / "outside.py"
        outside.write_text("private outside source\n")
        (self.workspace / "linked.py").symlink_to(outside)
        init = io.load_json(REPO / "templates/task.json")
        init["protected_paths"] = ["linked.py"]
        with self.assertRaises(io.DataError):
            state.create_task(self.workspace, "linked", init)

    def test_missing_intermediate_protected_path_is_absence(self):
        init = io.load_json(REPO / "templates/task.json")
        init["protected_paths"] = ["missing/deep/source.py"]
        proposed = state.create_task(self.workspace, "missing", init)
        self.assertIsNone(proposed["proposed_record"]["baseline"]["protected_fingerprints"]["missing/deep/source.py"])

    def test_illegal_subject_is_reported_without_reading_outside(self):
        evidence = make_evidence(self.workspace)
        self.register(evidence)
        outside = self.base / "outside.py"
        (self.workspace / "calc.py").rename(outside)
        (self.workspace / "calc.py").symlink_to(outside)
        result = state.check_task(self.workspace, "demo")
        self.assertFalse(result["consistent"])
        self.assertEqual(len(result["invalid_evidence"]), 1)

    def test_bad_capture_hash_types_are_reported_as_invalid_evidence(self):
        evidence = make_evidence(self.workspace)
        evidence["capture"]["content_sha256"] = 123
        path = self.task.parent / "evidence/ev-1.json"
        path.write_text(json.dumps(evidence))
        record = io.load_json(self.task)
        record["evidence_refs"] = [{"relative_path": "evidence/ev-1.json", "content_sha256": io.sha256_file(path)}]
        self.task.write_text(json.dumps(record))
        try:
            result = state.check_task(self.workspace, "demo")
        except TypeError as exc:
            self.fail(f"malformed hash escaped validator: {exc}")
        self.assertFalse(result["consistent"])
        self.assertEqual(len(result["invalid_evidence"]), 1)

    def test_shared_validator_rejects_malformed_nested_task_records(self):
        original = self.task.read_bytes()
        mutations = [lambda r: r.update(baseline=[]), lambda r: r.update(plan=[]),
                     lambda r: r["plan"].update(revision=True), lambda r: r.update(progress=None),
                     lambda r: r.update(authorization_refs={}), lambda r: r.update(evidence_refs={}),
                     lambda r: r.update(created_at=False)]
        for index, mutate in enumerate(mutations):
            with self.subTest(index=index):
                record = json.loads(original)
                mutate(record)
                self.task.write_text(json.dumps(record))
                self.assertFalse(state.check_task(self.workspace, "demo")["consistent"])
                with self.assertRaises(io.DataError):
                    state.update_task(self.workspace, "demo", 1,
                                      {"schema_version": 1, "append_authorization_refs": []})

    def test_bad_registered_ref_hash_types_raise_data_error(self):
        for value in (123, {}, False, "1" * 64 + "\n"):
            with self.subTest(value=value):
                with self.assertRaises(io.DataError):
                    state.update_task(self.workspace, "demo", 1, {"schema_version": 1,
                        "append_evidence_refs": [{"relative_path": "evidence/ev-1.json", "content_sha256": value}]})

    def test_persisted_protected_path_escape_is_reported_without_reading(self):
        record = io.load_json(self.task)
        record["baseline"]["protected_fingerprints"] = {"../outside": None}
        self.task.write_text(json.dumps(record))
        result = state.check_task(self.workspace, "demo")
        self.assertFalse(result["consistent"])
        self.assertTrue(result["pending_items"][0]["completion_blocking"])


class BoundedJsonClosure(unittest.TestCase):
    def test_duplicate_lock_owner_is_retained_for_manual_recovery(self):
        with tempfile.TemporaryDirectory() as temp:
            lock = Path(temp) / "lock"
            raw = b'{"operation_id":"foreign","operation_id":"op","pid":1,"created_at":"2026-10-03T00:00:00Z"}'
            lock.write_bytes(raw)
            with self.assertRaisesRegex(io.ConflictError, "manually"):
                io.release_lock(lock, "op")
            self.assertEqual(lock.read_bytes(), raw)

    def test_non_object_and_bad_utf8_locks_require_manual_recovery(self):
        with tempfile.TemporaryDirectory() as temp:
            lock = Path(temp) / "lock"
            for payload in (b"[]", b"true", b"123", b"\xff"):
                with self.subTest(payload=payload):
                    lock.write_bytes(payload)
                    with self.assertRaisesRegex(io.ConflictError, "manually"):
                        io.release_lock(lock, "op")
                    self.assertEqual(lock.read_bytes(), payload)

    def test_opened_file_growth_is_still_bounded(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "input.json"
            path.write_text("{}")
            real_stat = os.fstat
            grown = False

            def grow_after_stat(fd):
                nonlocal grown
                info = real_stat(fd)
                if info.st_ino == path.stat().st_ino and not grown:
                    grown = True
                    path.write_text('"' + "x" * (io.MAX_JSON_BYTES + 1) + '"')
                return info

            with patch.object(os, "fstat", side_effect=grow_after_stat):
                with self.assertRaisesRegex(io.DataError, "1 MiB"):
                    io.load_json(path)

    def test_rooted_json_rejects_parent_link(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "outside").mkdir()
            (root / "outside/input.json").write_text("{}")
            (root / "link").symlink_to(root / "outside", target_is_directory=True)
            with self.assertRaises(io.DataError):
                io.load_json(root / "link/input.json", root=root)

    def test_fifo_is_rejected_without_blocking(self):
        with tempfile.TemporaryDirectory() as temp:
            fifo = Path(temp) / "input.json"
            os.mkfifo(fifo)
            script = "\n".join([
                "import sys", f"sys.path.insert(0, {str(REPO / 'scripts')!r})",
                "from workflow.io import load_json, DataError", "try:",
                "    load_json(sys.argv[1])", "except DataError:", "    sys.exit(2)",
            ])
            try:
                result = subprocess.run([sys.executable, "-c", script, str(fifo)],
                                        capture_output=True, timeout=2)
            except subprocess.TimeoutExpired:
                self.fail("FIFO input blocked instead of being rejected")
            self.assertEqual(result.returncode, 2)


if __name__ == "__main__":
    unittest.main()
