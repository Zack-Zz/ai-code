"""state module: task records, evidence registration and invalidation."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from workflow import io as wio
from workflow import state as ws
from workflow.io import ConflictError, DataError, InvalidStateError

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOL = REPO_ROOT / "scripts" / "workflow_tool.py"


def valid_create_input(**overrides):
    data = {
        "schema_version": 1,
        "plan": {
            "goal": "Add bulk discount tier",
            "scope": ["calc.py", "test_calc.py"],
            "acceptance": ["bulk tier tests pass"],
            "change_type": "feature",
            "risk": "normal",
            "depth": "short",
        },
        "authorization_refs": [
            {"message_ref": "turn 1", "actions": ["plan", "implement"], "scope_summary": "calc only"},
        ],
        "protected_paths": ["user_notes.txt"],
    }
    data.update(overrides)
    return data


def make_evidence(workspace: Path, *, result="pass", subject="calc.py", subject_sha=None,
                  raw_text="suite ok\n", ev_id="ev-1"):
    ev_dir = workspace / ".ai-workflow" / "tasks" / "demo" / "evidence"
    ev_dir.mkdir(parents=True, exist_ok=True)
    raw = ev_dir / f"{ev_id}.out"
    raw.write_text(raw_text)
    return {
        "schema_version": 1,
        "evidence_id": ev_id,
        "kind": "test",
        "workspace_root": str(workspace),
        "subject_fingerprints": {subject: subject_sha or wio.sha256_file(workspace / subject)},
        "execution": {
            "argv": ["python3", "-m", "unittest"],
            "cwd": str(workspace),
            "exit_code": 0 if result == "pass" else 1,
            "signal": None,
            "start_error": None,
        },
        "host_context": None,
        "capture": {
            "origin": "tool_output",
            "relative_path": f"evidence/{ev_id}.out",
            "content_sha256": wio.sha256_file(raw),
        },
        "result": result,
        "observations": ["baseline green"],
        "started_at": "2026-10-01T00:00:00Z",
        "finished_at": "2026-10-01T00:00:01Z",
    }


def make_host_evidence(workspace: Path, host: str, *, result="pass"):
    evidence = make_evidence(workspace, result=result)
    evidence["kind"] = "host_run"
    evidence["execution"] = None
    evidence["capture"]["origin"] = "manual_annotation"
    evidence["host_context"] = {
        "host": host, "host_version": "test-version", "model": "test-model",
        "case_id": "A03", "package_content_hash": "a" * 64, "policy_hash": "b" * 64,
    }
    return evidence


class TaskCreateTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.ws = Path(self.td.name) / "workspace"
        (self.ws / "sub").mkdir(parents=True)
        (self.ws / "calc.py").write_text("x = 1\n")
        (self.ws / "user_notes.txt").write_text("user content\n")

    def tearDown(self):
        self.td.cleanup()

    def test_preview_does_not_write(self):
        result = ws.create_task(self.ws, "demo", valid_create_input(), apply=False)
        self.assertFalse(result["applied"])
        self.assertFalse(result["changed"] is None)
        self.assertFalse((self.ws / ".ai-workflow" / "tasks" / "demo").exists())
        record = result["proposed_record"]
        self.assertEqual(record["record_revision"], 1)
        self.assertEqual(record["task_id"], "demo")
        self.assertEqual(record["workspace"]["root"], str(self.ws.resolve()))
        self.assertEqual(record["baseline"]["protected_fingerprints"]["user_notes.txt"],
                         wio.sha256_file(self.ws / "user_notes.txt"))
        self.assertIn("created_at", record)

    def test_apply_creates_record_with_lock_released(self):
        result = ws.create_task(self.ws, "demo", valid_create_input(), apply=True)
        self.assertTrue(result["applied"])
        task_file = self.ws / ".ai-workflow" / "tasks" / "demo" / "task.json"
        record = wio.load_json(task_file)
        self.assertEqual(record["record_revision"], 1)
        self.assertFalse((task_file.parent / ".write.lock").exists())

    def test_existing_task_not_overwritten(self):
        ws.create_task(self.ws, "demo", valid_create_input(), apply=True)
        with self.assertRaises(ConflictError):
            ws.create_task(self.ws, "demo", valid_create_input(), apply=True)

    def test_invalid_task_id_rejected(self):
        for bad in ("Demo", "../escape", "a" * 65, "-lead", "with space"):
            with self.subTest(bad=bad):
                with self.assertRaises(DataError):
                    ws.create_task(self.ws, bad, valid_create_input(), apply=False)

    def test_caller_cannot_provide_system_fields(self):
        for field in ("workspace", "baseline", "record_revision", "created_at", "updated_at"):
            with self.subTest(field=field):
                payload = valid_create_input()
                payload[field] = {"injected": True} if isinstance(field, str) else 1
                with self.assertRaises(DataError):
                    ws.create_task(self.ws, "demo", payload, apply=False)

    def test_unknown_input_field_rejected(self):
        payload = valid_create_input(approved=True)
        with self.assertRaises(DataError):
            ws.create_task(self.ws, "demo", payload, apply=False)

    def test_plan_scope_rejects_escape_and_absolute(self):
        for bad in ("../x", "/etc/passwd", "rm -rf /"):
            with self.subTest(bad=bad):
                payload = valid_create_input()
                payload["plan"]["scope"] = [bad]
                with self.assertRaises(DataError):
                    ws.create_task(self.ws, "demo", payload, apply=False)

    def test_plan_enums_and_acceptance(self):
        payload = valid_create_input()
        payload["plan"]["change_type"] = "hotfix"
        with self.assertRaises(DataError):
            ws.create_task(self.ws, "demo", payload, apply=False)
        payload = valid_create_input()
        payload["plan"]["acceptance"] = ["完成任务"]
        payload["plan"]["scope"] = []
        with self.assertRaises(DataError):
            ws.create_task(self.ws, "demo", payload, apply=False)

    def test_authorization_actions_enum(self):
        payload = valid_create_input()
        payload["authorization_refs"][0]["actions"] = ["deploy_production"]
        with self.assertRaises(DataError):
            ws.create_task(self.ws, "demo", payload, apply=False)

    def test_workspace_must_exist(self):
        with self.assertRaises(DataError):
            ws.create_task(Path(self.td.name) / "nope", "demo", valid_create_input(), apply=False)


class TaskUpdateTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.ws = Path(self.td.name) / "workspace"
        self.ws.mkdir(parents=True)
        (self.ws / "calc.py").write_text("x = 1\n")
        ws.create_task(self.ws, "demo", valid_create_input(), apply=True)

    def tearDown(self):
        self.td.cleanup()

    def progress(self, **kw):
        base = {
            "phase": "implementing",
            "status": "in_progress",
            "completed_steps": ["plan-confirmed"],
            "next_action": "write test",
            "unresolved": [],
        }
        base.update(kw)
        return base

    def test_update_bumps_revision_and_writes(self):
        result = ws.update_task(self.ws, "demo", 1, {"schema_version": 1, "progress": self.progress()}, apply=True)
        self.assertTrue(result["applied"])
        self.assertEqual(result["record_revision"], 2)
        record = wio.load_json(self.ws / ".ai-workflow" / "tasks" / "demo" / "task.json")
        self.assertEqual(record["record_revision"], 2)

    def test_expected_revision_mismatch_conflicts(self):
        ws.update_task(self.ws, "demo", 1, {"schema_version": 1, "progress": self.progress()}, apply=True)
        with self.assertRaises(ConflictError):
            ws.update_task(self.ws, "demo", 1, {"schema_version": 1, "progress": self.progress()}, apply=True)

    def test_identical_update_is_noop(self):
        first = ws.update_task(self.ws, "demo", 1, {"schema_version": 1, "progress": self.progress()}, apply=True)
        second = ws.update_task(self.ws, "demo", 2, {"schema_version": 1, "progress": self.progress()}, apply=True)
        self.assertTrue(first["applied"])
        self.assertFalse(second["applied"])
        self.assertFalse(second["changed"])
        record = wio.load_json(self.ws / ".ai-workflow" / "tasks" / "demo" / "task.json")
        self.assertEqual(record["record_revision"], 2)

    def test_substantive_plan_change_bumps_plan_revision(self):
        payload = valid_create_input()
        new_plan = dict(payload["plan"])
        new_plan["goal"] = "Extended goal: bulk tier plus reporting"
        result = ws.update_task(self.ws, "demo", 1, {"schema_version": 1, "plan": new_plan}, apply=True)
        record = result["proposed_record"]
        self.assertEqual(record["plan"]["revision"], 2)

    def test_plan_with_revision_in_input_rejected(self):
        payload = valid_create_input()
        new_plan = dict(payload["plan"])
        new_plan["revision"] = 5
        with self.assertRaises(DataError):
            ws.update_task(self.ws, "demo", 1, {"schema_version": 1, "plan": new_plan}, apply=False)

    def test_update_cannot_touch_system_fields(self):
        payload = {"schema_version": 1, "task_id": "other"}
        with self.assertRaises(DataError):
            ws.update_task(self.ws, "demo", 1, payload, apply=False)

    def test_update_requires_at_least_one_change(self):
        with self.assertRaises(DataError):
            ws.update_task(self.ws, "demo", 1, {"schema_version": 1}, apply=False)

    def test_blocking_unresolved_prevents_ready_for_user_review(self):
        progress = self.progress(
            status="ready_for_user_review",
            unresolved=[{
                "kind": "confirmed_defect", "summary": "tenant check still missing",
                "severity": "critical", "completion_blocking": True, "evidence_ref": None,
            }],
        )
        with self.assertRaises(DataError):
            ws.update_task(self.ws, "demo", 1, {"schema_version": 1, "progress": progress}, apply=True)

    def test_confirmed_critical_defect_must_be_blocking(self):
        progress = self.progress(
            unresolved=[{
                "kind": "confirmed_defect", "summary": "x", "severity": "critical",
                "completion_blocking": False, "evidence_ref": None,
            }],
        )
        with self.assertRaises(DataError):
            ws.update_task(self.ws, "demo", 1, {"schema_version": 1, "progress": progress}, apply=False)

    def test_risk_unverified_stays_question_without_forced_blocking(self):
        progress = self.progress(
            status="ready_for_user_review",
            unresolved=[{
                "kind": "risk", "summary": "cache invalidation under load unverified",
                "severity": "medium", "completion_blocking": False,
                "evidence_ref": None,
            }],
        )
        result = ws.update_task(self.ws, "demo", 1, {"schema_version": 1, "progress": progress}, apply=True)
        self.assertTrue(result["applied"])

    def test_concurrent_same_revision_single_writer_wins(self):
        script = "\n".join([
            "import sys",
            "sys.path.insert(0, %r)" % str(REPO_ROOT / "scripts"),
            "from workflow import state",
            "from workflow.io import ConflictError",
            "payload = {'schema_version': 1, 'progress': %s}" % json.dumps(self.progress()),
            "try:",
            "    state.update_task(%r, 'demo', 1, payload, apply=True)" % str(self.ws),
            "    print('WIN')",
            "except ConflictError:",
            "    print('LOSE')",
        ])
        procs = [subprocess.Popen([sys.executable, "-c", script],
                                  stdout=subprocess.PIPE, text=True) for _ in range(2)]
        outs = [p.communicate()[0].strip() for p in procs]
        self.assertEqual(sorted(outs), ["LOSE", "WIN"])


class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.ws = Path(self.td.name) / "workspace"
        self.ws.mkdir(parents=True)
        (self.ws / "calc.py").write_text("x = 1\n")
        ws.create_task(self.ws, "demo", valid_create_input(protected_paths=[]), apply=True)
        self.evidence_path = self.ws / ".ai-workflow" / "tasks" / "demo" / "evidence" / "ev-1.json"
        self.evidence_path.parent.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        self.td.cleanup()

    def write_evidence(self, evidence):
        self.evidence_path.write_text(json.dumps(evidence, indent=2))
        return {
            "relative_path": "evidence/ev-1.json",
            "content_sha256": wio.sha256_file(self.evidence_path),
        }

    def test_register_valid_evidence(self):
        ref = self.write_evidence(make_evidence(self.ws))
        result = ws.update_task(
            self.ws, "demo", 1,
            {"schema_version": 1, "append_evidence_refs": [ref]}, apply=True)
        self.assertTrue(result["applied"])

    def test_register_and_check_host_run_for_each_declared_host(self):
        hosts = json.loads((REPO_ROOT / "product.json").read_text())["hosts"]
        revision = 1
        for host in hosts:
            with self.subTest(host=host):
                ref = self.write_evidence(make_host_evidence(self.ws, host))
                result = ws.update_task(
                    self.ws, "demo", revision,
                    {"schema_version": 1, "append_evidence_refs": [ref]}, apply=True)
                self.assertTrue(result["applied"])
                revision = result["record_revision"]
                self.assertTrue(ws.check_task(self.ws, "demo")["consistent"])

    def test_evidence_schema_hosts_match_declared_targets(self):
        hosts = json.loads((REPO_ROOT / "product.json").read_text())["hosts"]
        schema = json.loads((REPO_ROOT / "schemas/evidence.schema.json").read_text())
        context = next(item for item in schema["properties"]["host_context"]["oneOf"]
                       if item["type"] == "object")
        self.assertEqual(set(context["properties"]["host"]["enum"]), set(hosts))

    def test_host_run_rejects_unknown_host(self):
        ref = self.write_evidence(make_host_evidence(self.ws, "unsupported"))
        with self.assertRaisesRegex(DataError, "host_context.host must be one of"):
            ws.update_task(self.ws, "demo", 1,
                           {"schema_version": 1, "append_evidence_refs": [ref]}, apply=False)

    def test_claude_host_run_keeps_unverified_results_when_metadata_is_missing(self):
        revision = 1
        for outcome in ("manual_review", "not_run", "blocked_env"):
            with self.subTest(result=outcome):
                evidence = make_host_evidence(self.ws, "claude", result=outcome)
                for field in ("host_version", "model", "package_content_hash", "policy_hash"):
                    evidence["host_context"][field] = None
                evidence["started_at"] = evidence["finished_at"] = None
                ref = self.write_evidence(evidence)
                result = ws.update_task(
                    self.ws, "demo", revision,
                    {"schema_version": 1, "append_evidence_refs": [ref]}, apply=True)
                revision = result["record_revision"]
                self.assertTrue(ws.check_task(self.ws, "demo")["consistent"])
                self.assertEqual(wio.load_json(self.evidence_path)["result"], outcome)

    def test_claude_host_run_pass_rejects_failed_execution(self):
        for field, value in (("exit_code", 1), ("signal", "SIGTERM"),
                             ("start_error", "could not start")):
            with self.subTest(field=field):
                evidence = make_host_evidence(self.ws, "claude")
                evidence["execution"] = make_evidence(self.ws)["execution"]
                evidence["execution"][field] = value
                ref = self.write_evidence(evidence)
                with self.assertRaisesRegex(DataError, "host_run pass contradicts its execution failure"):
                    ws.update_task(self.ws, "demo", 1,
                                   {"schema_version": 1, "append_evidence_refs": [ref]}, apply=False)

    def test_register_rejects_wrong_hash(self):
        self.write_evidence(make_evidence(self.ws))
        bad = {"relative_path": "evidence/ev-1.json", "content_sha256": "0" * 64}
        with self.assertRaises(InvalidStateError):
            ws.update_task(self.ws, "demo", 1,
                           {"schema_version": 1, "append_evidence_refs": [bad]}, apply=False)

    def test_register_rejects_missing_evidence_file(self):
        bad = {"relative_path": "evidence/ghost.json", "content_sha256": "0" * 64}
        with self.assertRaises(InvalidStateError):
            ws.update_task(self.ws, "demo", 1,
                           {"schema_version": 1, "append_evidence_refs": [bad]}, apply=False)

    def test_register_rejects_missing_raw_capture(self):
        evidence = make_evidence(self.ws)
        evidence["capture"]["relative_path"] = "evidence/ghost.out"
        ref = self.write_evidence(evidence)
        with self.assertRaises(InvalidStateError):
            ws.update_task(self.ws, "demo", 1,
                           {"schema_version": 1, "append_evidence_refs": [ref]}, apply=False)

    def test_register_rejects_drifted_raw_capture(self):
        evidence = make_evidence(self.ws)
        evidence["capture"]["content_sha256"] = "f" * 64
        ref = self.write_evidence(evidence)
        with self.assertRaises(InvalidStateError):
            ws.update_task(self.ws, "demo", 1,
                           {"schema_version": 1, "append_evidence_refs": [ref]}, apply=False)

    def test_test_pass_requires_execution_success(self):
        evidence = make_evidence(self.ws, result="pass")
        evidence["execution"]["exit_code"] = 1
        ref = self.write_evidence(evidence)
        with self.assertRaises(DataError):
            ws.update_task(self.ws, "demo", 1,
                           {"schema_version": 1, "append_evidence_refs": [ref]}, apply=False)

    def test_test_pass_requires_finished_at_and_capture(self):
        evidence = make_evidence(self.ws)
        evidence["finished_at"] = None
        ref = self.write_evidence(evidence)
        with self.assertRaises(DataError):
            ws.update_task(self.ws, "demo", 1,
                           {"schema_version": 1, "append_evidence_refs": [ref]}, apply=False)

    def test_host_run_requires_host_context(self):
        evidence = make_evidence(self.ws)
        evidence["kind"] = "host_run"
        ref = self.write_evidence(evidence)
        with self.assertRaises(DataError):
            ws.update_task(self.ws, "demo", 1,
                           {"schema_version": 1, "append_evidence_refs": [ref]}, apply=False)

    def test_host_run_with_unverified_host_info_cannot_pass(self):
        for host in ("claude", "codex", "zcode"):
            with self.subTest(host=host):
                evidence = make_host_evidence(self.ws, host)
                for field in ("host_version", "model", "package_content_hash", "policy_hash"):
                    evidence["host_context"][field] = None
                ref = self.write_evidence(evidence)
                with self.assertRaisesRegex(DataError, "host_run pass requires complete host_context"):
                    ws.update_task(self.ws, "demo", 1,
                                   {"schema_version": 1, "append_evidence_refs": [ref]}, apply=False)

    def test_workspace_root_mismatch_rejected(self):
        evidence = make_evidence(self.ws)  # raw capture lives under our task dir
        evidence["workspace_root"] = "/somewhere/else"
        ref = self.write_evidence(evidence)
        with self.assertRaises(InvalidStateError):
            ws.update_task(self.ws, "demo", 1,
                           {"schema_version": 1, "append_evidence_refs": [ref]}, apply=False)


class CheckTaskTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.ws = Path(self.td.name) / "workspace"
        self.ws.mkdir(parents=True)
        (self.ws / "calc.py").write_text("x = 1\n")
        (self.ws / "user_notes.txt").write_text("user content\n")
        ws.create_task(self.ws, "demo", valid_create_input(), apply=True)
        self.ev_dir = self.ws / ".ai-workflow" / "tasks" / "demo" / "evidence"
        self.ev_dir.mkdir(parents=True, exist_ok=True)
        self.ev_path = self.ev_dir / "ev-1.json"
        self.raw_path = self.ev_dir / "ev-1.out"
        self.raw_path.write_text("suite ok\n")

    def tearDown(self):
        self.td.cleanup()

    def register(self):
        evidence = make_evidence(self.ws)
        self.ev_path.write_text(json.dumps(evidence, indent=2))
        ref = {"relative_path": "evidence/ev-1.json",
               "content_sha256": wio.sha256_file(self.ev_path)}
        ws.update_task(self.ws, "demo", 1,
                       {"schema_version": 1, "append_evidence_refs": [ref]}, apply=True)

    def test_consistent_when_nothing_drifted(self):
        self.register()
        result = ws.check_task(self.ws, "demo")
        self.assertEqual(result["identity_status"], "consistent")
        self.assertEqual(result["invalid_evidence"], [])
        self.assertTrue(result["consistent"])

    def test_edited_evidence_invalid(self):
        self.register()
        record_path = self.ws / ".ai-workflow" / "tasks" / "demo" / "task.json"
        record = wio.load_json(record_path)
        evidence = json.loads(self.ev_path.read_text())
        evidence["observations"] = ["tampered"]
        self.ev_path.write_text(json.dumps(evidence, indent=2))
        result = ws.check_task(self.ws, "demo")
        self.assertFalse(result["consistent"])
        self.assertTrue(any("ev-1" in item["relative_path"] and item["reason"]
                            for item in result["invalid_evidence"]))

    def test_drifted_raw_invalid(self):
        self.register()
        self.raw_path.write_text("tampered output\n")
        result = ws.check_task(self.ws, "demo")
        self.assertFalse(result["consistent"])

    def test_changed_subject_needs_revalidation(self):
        self.register()
        (self.ws / "calc.py").write_text("x = 2\n")
        result = ws.check_task(self.ws, "demo")
        self.assertFalse(result["consistent"])
        self.assertTrue(any(item.get("needs_revalidation") for item in result["invalid_evidence"]))

    def test_missing_raw_invalid(self):
        self.register()
        self.raw_path.unlink()
        result = ws.check_task(self.ws, "demo")
        self.assertFalse(result["consistent"])

    def test_workspace_identity_mismatch_reported(self):
        self.register()
        record_path = self.ws / ".ai-workflow" / "tasks" / "demo" / "task.json"
        record = wio.load_json(record_path)
        record["workspace"]["root"] = "/not/this/workspace"
        record_path.write_text(json.dumps(record, indent=2))
        result = ws.check_task(self.ws, "demo")
        self.assertEqual(result["identity_status"], "workspace_mismatch")
        self.assertFalse(result["consistent"])

    def test_baseline_drift_reported_as_pending(self):
        self.register()
        (self.ws / "user_notes.txt").write_text("user edited meanwhile\n")
        result = ws.check_task(self.ws, "demo")
        self.assertEqual(result["identity_status"], "consistent")
        self.assertTrue(any("user_notes.txt" in item.get("summary", "") or
                            "user_notes.txt" in str(item)
                            for item in result["pending_items"]))

    def test_check_unknown_task_fails(self):
        with self.assertRaises(DataError):
            ws.check_task(self.ws, "ghost")

    def test_malformed_evidence_ref_reported_not_crashed(self):
        ws.create_task(self.ws, "demo2", valid_create_input(protected_paths=[]), apply=True)
        task_file = self.ws / ".ai-workflow" / "tasks" / "demo2" / "task.json"
        record = wio.load_json(task_file)
        record["evidence_refs"] = ["not-a-dict", 42]
        task_file.write_text(json.dumps(record))
        result = ws.check_task(self.ws, "demo2")
        self.assertFalse(result["consistent"])
        self.assertEqual(len(result["invalid_evidence"]), 2)
        self.assertTrue(all("malformed evidence ref" in item["reason"]
                            for item in result["invalid_evidence"]))


class RealFixtureCheckTests(unittest.TestCase):
    """state.check_task against evals/fixtures/state_resume (stale by design)."""

    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.ws = Path(self.td.name) / "ws"
        self.ws.mkdir()
        import shutil
        src = REPO_ROOT / "evals" / "fixtures" / "state_resume"
        shutil.copytree(src, self.ws, dirs_exist_ok=True)
        # Point fixture placeholders at the real temp workspace
        for task_file in (self.ws / ".ai-workflow" / "tasks").glob("*/task.json"):
            record = wio.load_json(task_file)
            record["workspace"]["root"] = str(self.ws.resolve())
            if record.get("evidence_refs"):
                ev_path = (self.ws / ".ai-workflow" / "tasks" / "resume-demo" /
                           "evidence" / "ev-baseline.json")
                evidence = wio.load_json(ev_path)
                evidence["workspace_root"] = str(self.ws.resolve())
                evidence["execution"]["cwd"] = str(self.ws.resolve())
                ev_path.write_text(json.dumps(evidence, indent=2) + "\n")
                record["evidence_refs"][0]["content_sha256"] = wio.sha256_file(ev_path)
            task_file.write_text(json.dumps(record, indent=2) + "\n")

    def tearDown(self):
        self.td.cleanup()

    def test_fixture_resume_demo_reports_stale_evidence(self):
        result = ws.check_task(self.ws, "resume-demo")
        self.assertEqual(result["identity_status"], "consistent")
        self.assertFalse(result["consistent"])
        self.assertTrue(any(item.get("needs_revalidation") for item in result["invalid_evidence"]))

    def test_fixture_other_task_consistent_without_evidence(self):
        result = ws.check_task(self.ws, "other-task")
        self.assertTrue(result["consistent"])
        self.assertEqual(result["invalid_evidence"], [])


if __name__ == "__main__":
    unittest.main()
