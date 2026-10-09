import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "bridge_client.py"
MODULE_SPEC = importlib.util.spec_from_file_location("delegation_bridge_client", SCRIPT)
client = importlib.util.module_from_spec(MODULE_SPEC)
MODULE_SPEC.loader.exec_module(client)


class ClientTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.calls_path = self.root / "calls.jsonl"
        self.bridge = self.root / "agent bridge fixture"
        self.bridge.write_text(f"#!{sys.executable}\n" + '''import json, os, sys
from pathlib import Path
args = sys.argv[1:]
with open(os.environ["BRIDGE_FIXTURE_CALLS"], "a") as stream:
    stream.write(json.dumps(args) + "\\n")
operation = "task.start" if "start" in args else "preflight"
for group in ("task", "engine", "artifact"):
    if group in args:
        operation = group + "." + args[args.index(group)+1]
mode = os.environ.get("BRIDGE_FIXTURE_MODE", "ok")
if mode == "invalid":
    print("not json (secret must not be echoed)")
    sys.exit(0)
if mode == "version":
    print(json.dumps({"apiVersion": "agent-bridge/v2", "operation": operation, "data": {}}))
    sys.exit(0)
if mode == "utf8":
    sys.stdout.buffer.write(b"\\xff")
    sys.exit(0)
engine = args[args.index("--engine")+1] if "--engine" in args else "claude-code"
data = {"taskId": "task-001", "engine": engine, "projectId": "project-1", "sessionId": "session-001", "state": "failed" if mode == "task-failed" else "running", "runs": [], "deliveries": []}
if mode == "queued":
    data.pop("sessionId")
    data["state"] = "queued"
if mode == "swapped-target" and operation == "task.start":
    data["engine"] = "zcode"
payloads = {}
for flag in ("--spec-file", "--message-file"):
    if flag in args:
        path = args[args.index(flag)+1]
        payloads[flag] = sys.stdin.read() if path == "-" else Path(path).read_text()
with open(os.environ["BRIDGE_FIXTURE_CALLS"]+".payloads", "a") as stream:
    stream.write(json.dumps(payloads) + "\\n")
if mode == "source-clean" and list(Path(os.environ["BRIDGE_FIXTURE_SOURCE"]).glob("tmp*.json")):
    rejection = {"apiVersion": "agent-bridge/v1", "operation": operation,
                 "error": {"code": "DIRTY_SOURCE", "message": "control temp file dirtied source", "executionDisposition": "not_started"}}
    if "--request-id" in args:
        rejection["requestId"] = args[args.index("--request-id")+1]
    print(json.dumps(rejection))
    sys.exit(2)
request = args[args.index("--request-id")+1] if "--request-id" in args else None
response = {"apiVersion": "agent-bridge/v1", "operation": operation, "data": data}
if request is not None:
    response["requestId"] = request
if mode == "wrong-request":
    response["requestId"] = "different-id"
if mode in ("refused", "system"):
    response.pop("data")
    response["error"] = {"code": "TARGET_UNAVAILABLE", "message": "selected engine unavailable", "executionDisposition": "not_started"}
print(json.dumps(response))
sys.exit(2 if mode == "refused" else 1 if mode == "system" else 0)
''', encoding="utf-8")
        self.bridge.chmod(0o700)
        self.old_calls = os.environ.get("BRIDGE_FIXTURE_CALLS")
        os.environ["BRIDGE_FIXTURE_CALLS"] = str(self.calls_path)
        self.addCleanup(self.restore_environment)
        self.consumer = client.BridgeClient(str(self.bridge), caller_ref="caller-1")
        self.spec = {"taskSpecVersion": "1", "objective": "Fix the parser", "acceptanceCriteria": ["parser regression passes"],
                     "constraints": ["preserve unrelated edits"], "writeScope": ["src/parser.py"],
                     "contextRefs": [{"path": "src/parser.py"}], "scopeReference": "current user request", "verificationIds": ["unit"]}
        self.intent = {"source": "current-user", "kind": "delegation", "scopeReference": "current user request"}
        self.options = {"target_engine": "claude-code", "caller_engine": "codex", "project": "project-1", "request_id": "request-1"}

    def restore_environment(self):
        os.environ.pop("BRIDGE_FIXTURE_MODE", None)
        os.environ.pop("BRIDGE_FIXTURE_SOURCE", None)
        if self.old_calls is None:
            os.environ.pop("BRIDGE_FIXTURE_CALLS", None)
        else:
            os.environ["BRIDGE_FIXTURE_CALLS"] = self.old_calls

    def calls(self):
        return [json.loads(line) for line in self.calls_path.read_text().splitlines()] if self.calls_path.exists() else []

    def test_ordinary_development_never_invokes_bridge(self):
        result = self.consumer.dispatch(self.spec, **self.options)
        self.assertEqual("skipped", result["disposition"])
        self.assertEqual([], self.calls())

    def test_explicit_target_dispatches_with_stable_request_identity(self):
        result = self.consumer.dispatch(self.spec, self.intent, **self.options)
        self.assertEqual("dispatched", result["disposition"])
        self.assertEqual("task-001", result["response"]["data"]["taskId"])
        calls = self.calls()
        self.assertEqual(2, len(calls))
        self.assertIn("preflight", calls[0])
        self.assertIn("start", calls[1])
        self.assertEqual("claude-code", calls[1][calls[1].index("--engine")+1])
        self.assertEqual("request-1", calls[1][calls[1].index("--request-id")+1])

    def test_reference_or_approved_flag_does_not_dispatch(self):
        for intent in ({"source": "quoted", "kind": "delegation", "scopeReference": "current user request"},
                       {"source": "agent", "kind": "delegation", "scopeReference": "current user request"},
                       {"source": "current-user", "kind": "discussion", "approved": True}, {"approved": True}):
            with self.subTest(intent=intent):
                self.assertEqual("skipped", self.consumer.dispatch(self.spec, intent, **self.options)["disposition"])
        self.assertEqual([], self.calls())

    def test_missing_target_does_not_choose_one(self):
        options = {**self.options, "target_engine": None}
        self.assertEqual("needs-target", self.consumer.dispatch(self.spec, self.intent, **options)["disposition"])
        self.assertEqual([], self.calls())

    def test_same_engine_requires_explicit_independent_intent(self):
        options = {**self.options, "caller_engine": "claude-code"}
        with self.assertRaises(client.ClientError) as raised:
            self.consumer.dispatch(self.spec, self.intent, **options)
        self.assertEqual("SAME_ENGINE_INTENT_REQUIRED", raised.exception.code)
        self.assertEqual([], self.calls())
        result = self.consumer.dispatch(self.spec, self.intent, independent_session=True, **options)
        self.assertEqual("dispatched", result["disposition"])
        self.assertTrue(all("--independent-session" in args for args in self.calls()))

    def test_source_reference_mismatch_rejected_before_any_call(self):
        with self.assertRaises(client.ClientError) as raised:
            self.consumer.dispatch(self.spec, {**self.intent, "scopeReference": "other request"}, **self.options)
        self.assertEqual("INTENT_REFERENCE_MISMATCH", raised.exception.code)
        self.assertEqual([], self.calls())

    def test_bridge_exit_and_structured_refusal_preserved_without_fallback(self):
        os.environ["BRIDGE_FIXTURE_MODE"] = "refused"
        with self.assertRaises(client.ClientError) as raised:
            self.consumer.dispatch(self.spec, self.intent, **self.options)
        self.assertEqual(2, raised.exception.exit_code)
        self.assertEqual("TARGET_UNAVAILABLE", raised.exception.code)
        self.assertEqual("not_started", raised.exception.execution_disposition)
        self.assertEqual(1, len(self.calls()))

    def test_invalid_json_and_version_are_system_errors_without_raw_output(self):
        for mode, code in (("invalid", "INVALID_BRIDGE_RESPONSE"), ("version", "UNSUPPORTED_API_VERSION")):
            os.environ["BRIDGE_FIXTURE_MODE"] = mode
            with self.assertRaises(client.ClientError) as raised:
                self.consumer.invoke("task.get", task_id="task-001")
            self.assertEqual(code, raised.exception.code)
            self.assertNotIn("secret", str(raised.exception))
            self.assertEqual(1, raised.exception.exit_code)

    def test_task_failed_state_is_a_successful_query(self):
        os.environ["BRIDGE_FIXTURE_MODE"] = "task-failed"
        result = self.consumer.invoke("task.get", task_id="task-001")
        self.assertEqual("task.get", result["operation"])
        self.assertEqual("failed", result["data"]["state"])
        self.assertEqual(1, len(self.calls()))

    def test_continue_uses_exact_id_and_message_file_no_last_or_shell(self):
        message = "Fix quote '$HOME'; `touch unexpected`\nonly original scope"
        result = self.consumer.invoke("task.continue", task_id="task exact", message=message, request_id="continue-1")
        self.assertEqual("task.continue", result["operation"])
        self.assertEqual(1, len(self.calls()))
        args = self.calls()[0]
        self.assertIn("task exact", args)
        self.assertNotIn("--last", args)
        self.assertIn("--message-file", args)
        self.assertNotIn(message, args)
        self.assertEqual("continue-1", args[args.index("--request-id") + 1])

    def test_receipt_minimal_identity_and_request_id_reused(self):
        receipt = self.root / "receipt.json"
        for _ in range(2):
            self.consumer.dispatch(self.spec, self.intent, receipt_path=receipt, **self.options)
        self.assertTrue(receipt.exists(), "a successful dispatch must save a receipt")
        data = json.loads(receipt.read_text())
        self.assertEqual("task-001", data["taskId"])
        self.assertEqual("session-001", data["sessionId"])
        self.assertEqual("request-1", data["requestId"])
        self.assertNotIn("objective", data)
        starts = [args for args in self.calls() if "start" in args]
        self.assertEqual(["request-1", "request-1"], [args[args.index("--request-id") + 1] for args in starts])

    def test_queued_receipt_does_not_invent_session_and_refresh_uses_exact_task(self):
        os.environ["BRIDGE_FIXTURE_MODE"] = "queued"
        receipt = self.root / "queued.json"
        result = self.consumer.dispatch(self.spec, self.intent, receipt_path=receipt, **self.options)
        self.assertEqual("queued", result["response"]["data"]["state"])
        self.assertIsNone(json.loads(receipt.read_text())["sessionId"])
        os.environ["BRIDGE_FIXTURE_MODE"] = "ok"
        refreshed = self.consumer.refresh_receipt(receipt)
        self.assertEqual("session-001", refreshed["sessionId"])
        self.assertEqual("task-001", self.calls()[-1][self.calls()[-1].index("get") + 1])

    def test_json_and_message_payload_are_out_of_argv_and_use_stdin(self):
        self.consumer.dispatch(self.spec, self.intent, **self.options)
        self.consumer.invoke("task.continue", task_id="task-001", message="- leading dash\n$HOME `literal`", request_id="next")
        calls = self.calls()
        payloads = [json.loads(line) for line in Path(str(self.calls_path)+".payloads").read_text().splitlines()]
        self.assertEqual(self.spec, json.loads(payloads[1]["--spec-file"]))
        self.assertEqual("- leading dash\n$HOME `literal`", payloads[2]["--message-file"])
        for args in calls:
            for flag in ("--spec-file", "--message-file"):
                if flag in args:
                    self.assertEqual("-", args[args.index(flag)+1])

    def test_spec_stdin_never_dirties_source_when_tempdir_is_repo(self):
        source = self.root / "repo"
        source.mkdir()
        (source / "value.txt").write_text("ZERO\n")
        previous_tempdir = tempfile.tempdir
        tempfile.tempdir = str(source)
        self.addCleanup(setattr, tempfile, "tempdir", previous_tempdir)
        os.environ["BRIDGE_FIXTURE_SOURCE"] = str(source)
        os.environ["BRIDGE_FIXTURE_MODE"] = "source-clean"
        try:
            result = self.consumer.dispatch(self.spec, self.intent, **self.options)
        except client.ClientError as error:
            result = error.envelope("task.start")
        self.assertNotIn("error", result, "control input must not create DIRTY_SOURCE during preflight")
        self.assertEqual("dispatched", result["disposition"])
        self.assertEqual(["value.txt"], sorted(path.name for path in source.iterdir()))
        payloads = [json.loads(line) for line in Path(str(self.calls_path)+".payloads").read_text().splitlines()]
        self.assertEqual([self.spec, self.spec], [json.loads(item["--spec-file"]) for item in payloads])

    def test_continue_stdin_preserves_literal_message_without_source_temp_file(self):
        source = self.root / "repo"
        source.mkdir()
        previous_tempdir = tempfile.tempdir
        tempfile.tempdir = str(source)
        self.addCleanup(setattr, tempfile, "tempdir", previous_tempdir)
        os.environ["BRIDGE_FIXTURE_SOURCE"] = str(source)
        os.environ["BRIDGE_FIXTURE_MODE"] = "source-clean"
        message = "- 精确续接\n$HOME; `literal` $(literal)"
        try:
            result = self.consumer.invoke("task.continue", task_id="task-001", message=message, request_id="follow-up")
        except client.ClientError as error:
            result = error.envelope("task.continue")
        self.assertNotIn("error", result, "continue input must not create a source temp file")
        self.assertEqual([], list(source.iterdir()))
        args = self.calls()[0]
        self.assertEqual("-", args[args.index("--message-file")+1])
        payload = json.loads(Path(str(self.calls_path)+".payloads").read_text())
        self.assertEqual(message, payload["--message-file"])

    def test_two_stdin_payloads_are_rejected_before_bridge(self):
        with self.assertRaises(client.ClientError) as raised:
            self.consumer.invoke("task.start", engine="claude-code", project="project-1", spec=self.spec,
                                 message="unexpected second input", request_id="request-1")
        self.assertEqual("INVALID_INPUT", raised.exception.code)
        self.assertEqual([], self.calls())

    def test_stdin_refusal_exit_is_deterministic_without_retry(self):
        for mode, exit_code in (("refused", 2), ("system", 1)):
            os.environ["BRIDGE_FIXTURE_MODE"] = mode
            with self.assertRaises(client.ClientError) as raised:
                self.consumer.invoke("task.continue", task_id="task-001", message="exact message", request_id="follow-up")
            self.assertEqual(exit_code, raised.exception.exit_code)
            self.assertEqual("not_started", raised.exception.execution_disposition)
        self.assertEqual(2, len(self.calls()))
        self.assertTrue(all(args[args.index("--message-file")+1] == "-" for args in self.calls()))

    def test_all_read_and_cancel_verbs_use_bridge_semantics(self):
        for operation, options in (("engine.list", {}), ("task.list", {}),
                ("task.watch", {"task_id": "task-001", "cursor": "17", "wait_ms": 0}),
                ("artifact.list", {"task_id": "task-001"}),
                ("artifact.read", {"task_id": "task-001", "artifact_id": "result-001", "offset": 2, "limit": 4}),
                ("task.cancel", {"task_id": "task-001", "request_id": "cancel-1"})):
            with self.subTest(operation=operation):
                response = self.consumer.invoke(operation, **options)
                self.assertEqual(operation, response["operation"])
        artifact_args = self.calls()[4]
        self.assertIn("result-001", artifact_args)
        self.assertEqual("task-001", artifact_args[artifact_args.index("--task") + 1])

    def test_cli_parse_errors_are_structured_and_json_can_follow_subcommand(self):
        environment = {**os.environ, "AGENT_BRIDGE_BIN": str(self.bridge)}
        from subprocess import run
        good = run([sys.executable, "-B", str(SCRIPT), "engine", "list", "--json"], env=environment, capture_output=True, text=True)
        self.assertEqual(0, good.returncode, good.stderr)
        self.assertEqual("engine.list", json.loads(good.stdout)["operation"])
        bad = run([sys.executable, "-B", str(SCRIPT), "task", "start"], env=environment, capture_output=True, text=True)
        self.assertEqual(2, bad.returncode)
        self.assertTrue(bad.stdout.startswith("{"), "parser refusals must be machine-readable JSON")
        self.assertEqual("INVALID_INPUT", json.loads(bad.stdout)["error"]["code"])

    def test_swapped_start_target_is_rejected_even_without_receipt(self):
        os.environ["BRIDGE_FIXTURE_MODE"] = "swapped-target"
        with self.assertRaises(client.ClientError) as raised:
            self.consumer.dispatch(self.spec, self.intent, **self.options)
        self.assertEqual("INVALID_TASK_BINDING", raised.exception.code)
        self.assertEqual("unknown", raised.exception.execution_disposition)

    def test_readonly_scope_is_not_expanded_or_permission_invented(self):
        spec = {**self.spec, "writeScope": ["src/parser.py"], "constraints": ["project is read-only; do not modify files"], "verificationIds": []}
        self.consumer.dispatch(spec, self.intent, **self.options)
        payloads = [json.loads(line) for line in Path(str(self.calls_path)+".payloads").read_text().splitlines()]
        self.assertEqual(spec, json.loads(payloads[-1]["--spec-file"]))
        self.assertNotIn("permissionProfile", json.loads(payloads[-1]["--spec-file"]))
        self.assertNotIn("role", json.loads(payloads[-1]["--spec-file"]))

    def test_unknown_operation_never_invokes_an_arbitrary_command(self):
        with self.assertRaises(client.ClientError):
            self.consumer.invoke("run", message="touch arbitrary")
        self.assertEqual([], self.calls())

    def test_cli_get_refreshes_queued_receipt_without_second_get(self):
        os.environ["BRIDGE_FIXTURE_MODE"] = "queued"
        receipt = self.root / "queued.json"
        self.consumer.dispatch(self.spec, self.intent, receipt_path=receipt, **self.options)
        os.environ["BRIDGE_FIXTURE_MODE"] = "ok"
        from subprocess import run
        result = run([sys.executable, "-B", str(SCRIPT), "--caller-ref", "caller-1", "task", "get", "task-001", "--receipt-file", str(receipt)],
                     env={**os.environ, "AGENT_BRIDGE_BIN": str(self.bridge)}, capture_output=True, text=True)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("session-001", json.loads(receipt.read_text())["sessionId"])
        self.assertEqual(3, len(self.calls()))

    def test_workspace_policy_is_outer_cli_only_and_retains_explicit_choice(self):
        self.consumer.dispatch(self.spec, self.intent, workspace_policy="existing", **self.options)
        preflight_args = self.calls()[0]
        self.assertIn("--workspace-policy", preflight_args)
        self.assertEqual("existing", preflight_args[preflight_args.index("--workspace-policy") + 1])
        args = self.calls()[-1]
        self.assertIn("--workspace-policy", args)
        self.assertEqual("existing", args[args.index("--workspace-policy") + 1])
        payloads = [json.loads(line) for line in Path(str(self.calls_path)+".payloads").read_text().splitlines()]
        self.assertNotIn("workspacePolicy", json.loads(payloads[-1]["--spec-file"]))

    def test_system_error_and_missing_binary_keep_exit_one(self):
        os.environ["BRIDGE_FIXTURE_MODE"] = "system"
        with self.assertRaises(client.ClientError) as raised:
            self.consumer.invoke("task.get", task_id="task-001")
        self.assertEqual(1, raised.exception.exit_code)
        consumer = client.BridgeClient(str(self.root / "not installed"))
        with self.assertRaises(client.ClientError) as raised:
            consumer.invoke("task.get", task_id="task-001")
        self.assertEqual(1, raised.exception.exit_code)
        self.assertEqual("BRIDGE_UNAVAILABLE", raised.exception.code)

    def test_conflicting_receipt_preserves_existing_file(self):
        receipt = self.root / "already-owned.json"
        receipt.write_text('{"taskId":"unrelated"}\n')
        with self.assertRaises(client.ClientError) as raised:
            self.consumer.dispatch(self.spec, self.intent, receipt_path=receipt, **self.options)
        self.assertEqual("RECEIPT_WRITE_FAILED", raised.exception.code)
        self.assertEqual('{"taskId":"unrelated"}\n', receipt.read_text())

    def test_target_is_kept_for_each_peer_engine(self):
        for target in client.ENGINES:
            caller = next(engine for engine in client.ENGINES if engine != target)
            response = self.consumer.dispatch(self.spec, self.intent, **{**self.options, "target_engine": target, "caller_engine": caller})
            self.assertEqual(target, response["response"]["data"]["engine"])
            args = self.calls()[-1]
            self.assertEqual(target, args[args.index("--engine") + 1])

    def test_foreign_receipt_is_rejected_before_query(self):
        receipt = self.root / "foreign.json"
        receipt.write_text(json.dumps({"apiVersion": client.API_VERSION, "callerRef": "other-caller", "taskId": "foreign-task"}))
        with self.assertRaises(client.ClientError) as raised:
            self.consumer.refresh_receipt(receipt)
        self.assertEqual("INVALID_TASK_BINDING", raised.exception.code)
        self.assertEqual([], self.calls())

    def test_unusable_write_response_preserves_unknown_execution(self):
        for mode in ("version", "wrong-request", "utf8"):
            os.environ["BRIDGE_FIXTURE_MODE"] = mode
            with self.subTest(mode=mode):
                with self.assertRaises(client.ClientError) as raised:
                    self.consumer.invoke("task.start", engine="claude-code", project="project-1", spec=self.spec, request_id="request-1")
                self.assertEqual("unknown", raised.exception.execution_disposition)
                self.assertEqual(1, raised.exception.exit_code)


if __name__ == "__main__":
    unittest.main()
