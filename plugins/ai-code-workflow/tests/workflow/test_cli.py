"""CLI surface: subprocess behavior and exit-code mapping."""

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOL = REPO_ROOT / "scripts" / "workflow_tool.py"

BASE_PROFILE = {
    "schema_version": 1,
    "mode": "collaborative",
    "review_level": "critical",
    "max_parallel_tasks": 2,
    "response_language": "auto",
    "verification_notes": [],
}


def run_tool(*args):
    return subprocess.run(
        [sys.executable, str(TOOL), *args],
        capture_output=True, text=True, cwd=str(REPO_ROOT))


class PolicyResolveCLITests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        plugin = Path(self.td.name) / "plugin" / "policies"
        plugin.mkdir(parents=True)
        (plugin / "collaborative.json").write_text(json.dumps(BASE_PROFILE))
        (plugin / "continuous.json").write_text(
            json.dumps(dict(BASE_PROFILE, mode="continuous")))
        self.plugin = plugin.parent
        self.ws = Path(self.td.name) / "ws"
        self.ws.mkdir()

    def tearDown(self):
        self.td.cleanup()

    def test_resolve_prints_effective_policy_and_exits_zero(self):
        result = run_tool("policy", "resolve", "--plugin-root", str(self.plugin),
                          "--workspace", str(self.ws))
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["effective_policy"]["mode"], "collaborative")
        self.assertIn("policy_hash", payload)

    def test_resolve_with_explicit_options(self):
        result = run_tool(
            "policy", "resolve", "--plugin-root", str(self.plugin),
            "--workspace", str(self.ws),
            "--mode", "continuous", "--review-level", "all",
            "--max-parallel-tasks", "3", "--response-language", "zh-CN",
            "--verification-note", "run full suite", "--verification-note", "verify logs")
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        policy = payload["effective_policy"]
        self.assertEqual(policy["mode"], "continuous")
        self.assertEqual(policy["review_level"], "all")
        self.assertEqual(policy["max_parallel_tasks"], 3)
        self.assertEqual(policy["response_language"], "zh-CN")
        self.assertEqual(policy["verification_notes"],
                         ["run full suite", "verify logs"])
        self.assertTrue(payload["warnings"])

    def test_invalid_option_value_maps_to_exit_2(self):
        result = run_tool(
            "policy", "resolve", "--plugin-root", str(self.plugin),
            "--workspace", str(self.ws), "--mode", "bogus")
        self.assertEqual(result.returncode, 2)
        self.assertIn("error", result.stderr)

    def test_out_of_range_parallel_maps_to_exit_2(self):
        result = run_tool(
            "policy", "resolve", "--plugin-root", str(self.plugin),
            "--workspace", str(self.ws), "--max-parallel-tasks", "9")
        self.assertEqual(result.returncode, 2)

    def test_missing_project_file_is_normal(self):
        result = run_tool("policy", "resolve", "--plugin-root", str(self.plugin),
                          "--workspace", str(self.ws))
        self.assertEqual(result.returncode, 0)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["warnings"], [])


class ValidateCLITests(unittest.TestCase):
    def test_validate_rejects_missing_root_with_clear_error(self):
        result = run_tool("validate", "--root", "/definitely/not/here")
        self.assertEqual(result.returncode, 2)
        self.assertIn("error", result.stderr)

    def test_no_subcommand_exits_nonzero(self):
        result = run_tool()
        self.assertNotEqual(result.returncode, 0)


class TaskCLITests(unittest.TestCase):
    """End-to-end task record flow through the CLI."""

    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.ws = Path(self.td.name) / "workspace"
        self.ws.mkdir()
        (self.ws / "calc.py").write_text("x = 1\n")
        self.input = Path(self.td.name) / "create.json"
        self.input.write_text(json.dumps({
            "schema_version": 1,
            "plan": {"goal": "g", "scope": ["calc.py"], "acceptance": ["a"],
                     "change_type": "feature", "risk": "normal", "depth": "short"},
            "authorization_refs": [{"message_ref": "t1", "actions": ["plan"], "scope_summary": "s"}],
            "protected_paths": [],
        }))

    def tearDown(self):
        self.td.cleanup()

    def test_create_preview_then_apply_then_update_conflict(self):
        preview = run_tool("task", "create", "--workspace", str(self.ws),
                           "--id", "demo", "--input", str(self.input))
        self.assertEqual(preview.returncode, 0)
        self.assertFalse((self.ws / ".ai-workflow").exists())

        applied = run_tool("task", "create", "--workspace", str(self.ws),
                           "--id", "demo", "--input", str(self.input), "--apply")
        self.assertEqual(applied.returncode, 0, applied.stderr)
        self.assertTrue(json.loads(applied.stdout)["applied"])

        duplicate = run_tool("task", "create", "--workspace", str(self.ws),
                             "--id", "demo", "--input", str(self.input), "--apply")
        self.assertEqual(duplicate.returncode, 3)

        update = Path(self.td.name) / "update.json"
        update.write_text(json.dumps({
            "schema_version": 1,
            "progress": {"phase": "implementing", "status": "in_progress",
                         "completed_steps": ["plan-confirmed"], "next_action": "test",
                         "unresolved": []},
        }))
        stale = run_tool("task", "update", "--workspace", str(self.ws), "--id", "demo",
                         "--expected-revision", "5", "--input", str(update), "--apply")
        self.assertEqual(stale.returncode, 3)

        good = run_tool("task", "update", "--workspace", str(self.ws), "--id", "demo",
                        "--expected-revision", "1", "--input", str(update), "--apply")
        self.assertEqual(good.returncode, 0, good.stderr)

        check = run_tool("task", "check", "--workspace", str(self.ws), "--id", "demo")
        self.assertEqual(check.returncode, 0)
        payload = json.loads(check.stdout)
        self.assertTrue(payload["consistent"])

    def test_check_inconsistent_returns_4(self):
        run_tool("task", "create", "--workspace", str(self.ws), "--id", "demo",
                 "--input", str(self.input), "--apply")
        (self.ws / "calc.py").write_text("changed\n")  # no protected paths; use task tamper
        task_file = self.ws / ".ai-workflow" / "tasks" / "demo" / "task.json"
        record = json.loads(task_file.read_text())
        record["workspace"]["root"] = "/elsewhere"
        task_file.write_text(json.dumps(record))
        result = run_tool("task", "check", "--workspace", str(self.ws), "--id", "demo")
        self.assertEqual(result.returncode, 4)

    def test_invalid_input_maps_to_2(self):
        self.input.write_text('{"schema_version": 1}')
        result = run_tool("task", "create", "--workspace", str(self.ws),
                          "--id", "demo", "--input", str(self.input))
        self.assertEqual(result.returncode, 2)

    def test_unknown_task_check_maps_to_2(self):
        result = run_tool("task", "check", "--workspace", str(self.ws), "--id", "ghost")
        self.assertEqual(result.returncode, 2)


class BuildPackageFilesCLITests(unittest.TestCase):
    """build / package check / files plan+apply through the CLI."""

    @classmethod
    def setUpClass(cls):
        import tempfile as _tempfile
        cls.td = _tempfile.TemporaryDirectory()
        cls.dist = Path(cls.td.name) / "dist"
        result = run_tool("build", "--host", "all", "--output", str(cls.dist))
        assert result.returncode == 0, result.stderr

    @classmethod
    def tearDownClass(cls):
        cls.td.cleanup()

    def test_build_then_package_check_both_hosts(self):
        for host in ("zcode", "codex"):
            result = run_tool("package", "check", "--path",
                              str(self.dist / host / "ai-code-workflow"), "--host", host)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            payload = json.loads(result.stdout)
            self.assertTrue(payload["ok"])

    def test_package_check_failure_exits_1(self):
        pkg = self.dist / "zcode" / "ai-code-workflow"
        notice = pkg / "NOTICE"
        original = notice.read_bytes()
        try:
            notice.write_bytes(b"tampered")
            result = run_tool("package", "check", "--path", str(pkg), "--host", "zcode")
            self.assertEqual(result.returncode, 1)
        finally:
            notice.write_bytes(original)

    def test_files_stage_plan_apply_end_to_end(self):
        import tempfile as _tempfile
        with _tempfile.TemporaryDirectory() as td:
            target = Path(td) / "project"
            target.mkdir()
            plan_out = Path(td) / "plan.json"
            plan_result = run_tool(
                "files", "plan", "--package", str(self.dist / "zcode" / "ai-code-workflow"),
                "--target", str(target), "--action", "stage", "--out", str(plan_out))
            self.assertEqual(plan_result.returncode, 0, plan_result.stderr)
            meta = json.loads(plan_result.stdout)
            plan = json.loads(plan_out.read_text())
            self.assertEqual(plan["plan_hash"], meta["plan_hash"])
            self.assertEqual(plan["operation_id"], meta["operation_id"])

            apply_result = run_tool(
                "files", "apply", "--plan", str(plan_out),
                "--expected-plan-hash", meta["plan_hash"])
            self.assertEqual(apply_result.returncode, 0, apply_result.stderr)
            self.assertTrue(json.loads(apply_result.stdout)["applied"])
            self.assertTrue((target / ".ai-workflow" / "receipts" / "ai-code-workflow.json").is_file())


if __name__ == "__main__":
    unittest.main()
