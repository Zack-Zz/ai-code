#!/usr/bin/env python3
"""Encode bounded Bridge CLI operations; no engine execution or task state lives here."""

import argparse
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile

API_VERSION = "agent-bridge/v1"
ENGINES = ("claude-code", "zcode", "codex")
OPERATIONS = {
    "engine.list": ("engine", "list"), "preflight": ("preflight",),
    "task.start": ("task", "start"), "task.get": ("task", "get"),
    "task.list": ("task", "list"), "task.watch": ("task", "watch"),
    "task.continue": ("task", "continue"), "task.cancel": ("task", "cancel"),
    "artifact.list": ("artifact", "list"), "artifact.read": ("artifact", "read"),
}
WRITES = {"task.start", "task.continue", "task.cancel"}


class ClientError(Exception):
    """A structured failure, including uncertain execution after transport errors."""

    def __init__(self, code, message, *, exit_code=2, execution_disposition=None):
        super().__init__(message)
        self.code = code
        self.exit_code = exit_code
        self.execution_disposition = execution_disposition

    def envelope(self, operation, request_id=None):
        error = {"code": self.code, "message": str(self)}
        if self.execution_disposition is not None:
            error["executionDisposition"] = self.execution_disposition
        result = {"apiVersion": API_VERSION, "operation": operation, "error": error}
        if request_id:
            result["requestId"] = request_id
        return result


def _value(value, name):
    if not isinstance(value, str) or not value.strip() or value.startswith("-") or "\x00" in value:
        raise ClientError("INVALID_INPUT", f"{name} must be a nonempty value, not an option")
    return value


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        # argparse failures also preserve the documented JSON/exit-2 interface.
        print(json.dumps(ClientError("INVALID_INPUT", message).envelope("client.parse")))
        raise SystemExit(2)


def _read_json(path):
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        raise ClientError("INVALID_INPUT", "input must be a readable JSON file") from None
    if not isinstance(value, dict):
        raise ClientError("INVALID_INPUT", "input JSON must be an object")
    return value


class BridgeClient:
    def __init__(self, executable=None, config=None, caller_ref=None):
        # This is one executable, not an executable plus caller-supplied shell text.
        self.executable = executable or os.environ.get("AGENT_BRIDGE_BIN", "agent-bridge")
        self.config = config or os.environ.get("AGENT_BRIDGE_CONFIG")
        self.caller_ref = caller_ref or os.environ.get("AGENT_BRIDGE_CALLER_REF")

    def invoke(self, operation, *, engine=None, project=None, spec=None, request_id=None,
               independent_session=False, task_id=None, message=None, cursor=None,
               wait_ms=None, artifact_id=None, offset=None, limit=None, workspace_policy=None):
        """Send exactly one CLI operation. No retry, target substitution or installation."""
        if operation not in OPERATIONS:
            raise ClientError("UNKNOWN_OPERATION", "unsupported Bridge operation")
        if workspace_policy is not None and (operation not in ("task.start", "preflight") or workspace_policy not in ("isolated", "existing")):
            raise ClientError("INVALID_INPUT", "workspace_policy is a preflight/task.start choice: isolated or existing")
        if operation in WRITES:
            _value(request_id, "request_id")
        if operation in ("task.start", "preflight"):
            if engine not in ENGINES:
                raise ClientError("INVALID_ENGINE", "a canonical engine ID is required")
            _value(project, "project")
        if operation == "task.start" and not isinstance(spec, dict):
            raise ClientError("INVALID_INPUT", "task start requires a TaskSpec object")
        if spec is not None and message is not None:
            raise ClientError("INVALID_INPUT", "one Bridge operation accepts only one stdin payload")
        if operation in ("task.get", "task.watch", "task.continue", "task.cancel", "artifact.list", "artifact.read"):
            _value(task_id, "task_id")
        if operation == "artifact.read":
            _value(artifact_id, "artifact_id")
        if operation == "task.continue":
            if not isinstance(message, str) or not message.strip() or "\x00" in message:
                raise ClientError("INVALID_INPUT", "message must be nonempty text")
        for number, name in ((wait_ms, "wait_ms"), (offset, "offset"), (limit, "limit")):
            if number is not None and (type(number) is not int or number < 0):
                raise ClientError("INVALID_INPUT", f"{name} must be a nonnegative integer")
        argv = [self.executable]
        for flag, value in (("--config", self.config), ("--caller-ref", self.caller_ref)):
            if value is not None:
                argv.extend([flag, _value(value, flag)])
        argv.extend(OPERATIONS[operation])
        if task_id is not None:
            argv.extend(["--task", task_id] if operation.startswith("artifact.") else [task_id])
        if artifact_id is not None:
            argv.append(artifact_id)
        for flag, value in (("--engine", engine), ("--project", project), ("--request-id", request_id),
                            ("--cursor", cursor), ("--wait-ms", wait_ms), ("--offset", offset), ("--limit", limit)):
            if value is not None:
                argv.extend([flag, str(value)])
        if workspace_policy is not None:
            argv.extend(["--workspace-policy", workspace_policy])
        if independent_session:
            argv.append("--independent-session")
        stdin = None
        for flag, value in (("--spec-file", spec), ("--message-file", message)):
            if value is not None:
                stdin = json.dumps(value, ensure_ascii=False) if flag == "--spec-file" else value
                argv.extend([flag, "-"])
        argv.append("--json")
        try:
            process = subprocess.run(argv, input=stdin, capture_output=True, text=True, encoding="utf-8", shell=False,
                                     timeout=max(30, (wait_ms or 0) / 1000 + 5))
        except subprocess.TimeoutExpired:
            raise ClientError("BRIDGE_TIMEOUT", "Bridge response timed out; query before retrying with the same request ID",
                              exit_code=1, execution_disposition="unknown" if operation in WRITES else None) from None
        except UnicodeError:
            raise ClientError("INVALID_BRIDGE_RESPONSE", "Bridge stdout must be UTF-8 JSON", exit_code=1,
                              execution_disposition="unknown" if operation in WRITES else None) from None
        except OSError:
            raise ClientError("BRIDGE_UNAVAILABLE", "Bridge executable could not be run; check the controlled executable configuration",
                              exit_code=1, execution_disposition="not_started" if operation in WRITES else None) from None
        return self._response(process, operation, request_id)

    @staticmethod
    def _response(process, operation, request_id):
        try:
            result = json.loads(process.stdout)
        except ValueError:
            raise ClientError("INVALID_BRIDGE_RESPONSE", "Bridge stdout must contain one JSON envelope", exit_code=1,
                              execution_disposition="unknown" if operation in WRITES else None) from None
        if not isinstance(result, dict) or result.get("apiVersion") != API_VERSION:
            raise ClientError("UNSUPPORTED_API_VERSION", "Bridge must implement agent-bridge/v1", exit_code=1,
                              execution_disposition="unknown" if operation in WRITES else None)
        if result.get("operation") != operation or (request_id is not None and result.get("requestId") != request_id):
            raise ClientError("INVALID_BRIDGE_RESPONSE", "Bridge operation/request identity does not match", exit_code=1,
                              execution_disposition="unknown" if operation in WRITES else None)
        if process.returncode == 0 and "data" in result and "error" not in result:
            return result
        error = result.get("error")
        if process.returncode in (1, 2) and "data" not in result and isinstance(error, dict) and \
                isinstance(error.get("code"), str) and isinstance(error.get("message"), str):
            raise ClientError(error["code"], error["message"], exit_code=process.returncode,
                              execution_disposition=error.get("executionDisposition"))
        raise ClientError("INVALID_BRIDGE_RESPONSE", "Bridge exit status and JSON envelope disagree", exit_code=1,
                          execution_disposition="unknown" if operation in WRITES else None)

    def dispatch(self, spec, intent=None, *, target_engine=None, caller_engine=None, project=None,
                 request_id=None, independent_session=False, receipt_path=None, workspace_policy=None):
        """Gate an organized current-user intent. This input is not identity attestation."""
        if not isinstance(intent, dict) or intent.get("source") != "current-user" or intent.get("kind") != "delegation":
            return {"disposition": "skipped", "reason": "no explicit current-user delegation"}
        if target_engine is None:
            return {"disposition": "needs-target", "reason": "choose a target from actual engine capabilities"}
        if target_engine not in ENGINES or caller_engine not in ENGINES:
            raise ClientError("INVALID_ENGINE", "caller and target must use canonical engine IDs")
        if not isinstance(spec, dict) or not intent.get("scopeReference") or intent.get("scopeReference") != spec.get("scopeReference"):
            raise ClientError("INTENT_REFERENCE_MISMATCH", "TaskSpec must reference the same current-user request as intent")
        if caller_engine == target_engine and not independent_session:
            raise ClientError("SAME_ENGINE_INTENT_REQUIRED", "same-engine dispatch requires explicit independent-session intent")
        _value(request_id, "request_id")
        self.invoke("preflight", engine=target_engine, project=project, spec=spec, independent_session=independent_session, workspace_policy=workspace_policy)
        response = self.invoke("task.start", engine=target_engine, project=project, spec=spec,
                               request_id=request_id, independent_session=independent_session, workspace_policy=workspace_policy)
        self._task_binding(response, target_engine, project)
        if receipt_path is not None:
            self._receipt(receipt_path, response, target_engine, project, intent)
        return {"disposition": "dispatched", "response": response}

    def _receipt(self, path, response, engine, project, intent):
        task = self._task_binding(response, engine, project)
        receipt = {"apiVersion": API_VERSION, "requestId": response["requestId"], "callerRef": self.caller_ref,
                   "engine": engine, "projectId": project, "taskId": task["taskId"], "sessionId": task.get("sessionId"),
                   "scopeReference": intent["scopeReference"]}
        self._write_receipt(path, receipt)

    @staticmethod
    def _task_binding(response, engine, project):
        task = response["data"]
        if not isinstance(task, dict) or not task.get("taskId") or task.get("engine") != engine or task.get("projectId") != project:
            raise ClientError("INVALID_TASK_BINDING", "start response lacks the exact task/engine/project binding; query the same request ID",
                              exit_code=1, execution_disposition="unknown")
        return task

    def refresh_receipt(self, path):
        """Fetch the exact saved task; queued tasks may acquire a session ID later."""
        previous = _read_json(path)
        if previous.get("apiVersion") != API_VERSION or previous.get("callerRef") != self.caller_ref:
            raise ClientError("INVALID_TASK_BINDING", "receipt caller/API does not match this client")
        response = self.invoke("task.get", task_id=previous.get("taskId"))
        return self.update_receipt(path, response)

    def update_receipt(self, path, response):
        """Update only a matching receipt from an already obtained exact get response."""
        previous = _read_json(path)
        if previous.get("apiVersion") != API_VERSION or previous.get("callerRef") != self.caller_ref:
            raise ClientError("INVALID_TASK_BINDING", "receipt caller/API does not match this client")
        if response.get("operation") != "task.get":
            raise ClientError("INVALID_TASK_BINDING", "receipt refresh requires a task.get response")
        task = response["data"]
        if not isinstance(task, dict) or any(task.get(key) != previous.get(key) for key in ("taskId", "engine", "projectId")):
            raise ClientError("INVALID_TASK_BINDING", "queried task does not match the saved binding", exit_code=1)
        receipt = {**previous, "sessionId": task.get("sessionId")}
        self._write_receipt(path, receipt)
        return receipt

    @staticmethod
    def _write_receipt(path, receipt):
        destination = Path(path)
        temporary = None
        lock_fd = None
        try:
            # Keep one stable lock inode: removing it would let later writers lock a new inode.
            # The kernel releases this lock after a crash; no PID-based lock recovery is needed.
            import fcntl
            lock_path = destination.with_name(f".{destination.name}.agent-bridge-lock")
            lock_fd = os.open(lock_path, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
            owned = os.fstat(lock_fd)
            if not stat.S_ISREG(owned.st_mode) or owned.st_nlink != 1 or \
                    owned.st_uid != os.getuid() or stat.S_IMODE(owned.st_mode) & 0o077:
                raise OSError("receipt lock must be a private owned regular file")
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            if destination.is_symlink():
                raise OSError("receipt is a symlink")
            if destination.exists():
                previous = _read_json(destination)
                if any(previous.get(key) != receipt.get(key) for key in receipt if key != "sessionId") or \
                        (previous.get("sessionId") is not None and previous.get("sessionId") != receipt.get("sessionId")):
                    raise OSError("receipt already belongs to another dispatch/session")
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=destination.parent, delete=False) as stream:
                temporary = Path(stream.name)
                json.dump(receipt, stream, ensure_ascii=False, indent=2)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            temporary.replace(destination)
        except (OSError, ClientError, ImportError):
            raise ClientError("RECEIPT_WRITE_FAILED", "Task started but receipt could not be saved; recover using the same request ID",
                              exit_code=1, execution_disposition="unknown") from None
        finally:
            try:
                if temporary is not None:
                    temporary.unlink(missing_ok=True)
            finally:
                if lock_fd is not None:
                    os.close(lock_fd)


def main(argv=None):
    parser = JsonArgumentParser(description=__doc__)
    parser.add_argument("--config")
    parser.add_argument("--caller-ref")
    parser.add_argument("--json", action="store_true", help="JSON is always emitted")
    groups = parser.add_subparsers(dest="group", required=True)
    engines = groups.add_parser("engine").add_subparsers(dest="verb", required=True)
    parsers = [engines.add_parser("list")]
    preflight = groups.add_parser("preflight")
    task = groups.add_parser("task").add_subparsers(dest="verb", required=True)
    start = task.add_parser("start")
    parsers.extend([preflight, start])
    for selected in (preflight, start):
        selected.add_argument("--engine", choices=ENGINES, required=True)
        selected.add_argument("--project", required=True)
        selected.add_argument("--spec-file", required=True)
        selected.add_argument("--independent-session", action="store_true")
        selected.add_argument("--workspace-policy", choices=("isolated", "existing"))
    start.add_argument("--caller-engine", choices=ENGINES, required=True)
    start.add_argument("--intent-file", required=True)
    start.add_argument("--receipt-file")
    start.add_argument("--request-id", required=True)
    for name in ("get", "watch", "continue", "cancel"):
        selected = task.add_parser(name)
        parsers.append(selected)
        selected.add_argument("task_id")
        if name in ("continue", "cancel"):
            selected.add_argument("--request-id", required=True)
        if name == "get":
            selected.add_argument("--receipt-file")
        if name == "continue":
            selected.add_argument("--message-file", required=True)
        if name == "watch":
            selected.add_argument("--cursor")
            selected.add_argument("--wait-ms", type=int)
    parsers.append(task.add_parser("list"))
    artifacts = groups.add_parser("artifact").add_subparsers(dest="verb", required=True)
    for name in ("list", "read"):
        selected = artifacts.add_parser(name)
        parsers.append(selected)
        selected.add_argument("--task", dest="task_id", required=True)
        if name == "read":
            selected.add_argument("artifact_id")
            selected.add_argument("--offset", type=int)
            selected.add_argument("--limit", type=int)
    for selected in parsers:
        selected.add_argument("--json", action="store_true", default=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    operation = "preflight" if args.group == "preflight" else f"{args.group}.{args.verb}"
    values = vars(args)
    consumer = BridgeClient(config=args.config, caller_ref=args.caller_ref)
    try:
        if operation == "task.start":
            result = consumer.dispatch(_read_json(args.spec_file), _read_json(args.intent_file), target_engine=args.engine,
                                       caller_engine=args.caller_engine, project=args.project, request_id=args.request_id,
                                       independent_session=args.independent_session, receipt_path=args.receipt_file,
                                       workspace_policy=args.workspace_policy)
            if result["disposition"] != "dispatched":
                raise ClientError("NO_DELEGATION_INTENT", result["reason"])
            response = result["response"]
        else:
            options = {key: values[key] for key in ("engine", "project", "request_id", "independent_session", "task_id", "cursor", "wait_ms", "artifact_id", "offset", "limit", "workspace_policy") if key in values}
            if "spec_file" in values:
                options["spec"] = _read_json(args.spec_file)
            if "message_file" in values:
                try:
                    options["message"] = Path(args.message_file).read_text(encoding="utf-8")
                except (OSError, UnicodeError):
                    raise ClientError("INVALID_INPUT", "message must be a readable UTF-8 file") from None
            response = consumer.invoke(operation, **options)
            if operation == "task.get" and args.receipt_file:
                consumer.update_receipt(args.receipt_file, response)
        print(json.dumps(response, ensure_ascii=False))
        return 0
    except ClientError as error:
        print(json.dumps(error.envelope(operation, values.get("request_id")), ensure_ascii=False))
        return error.exit_code


if __name__ == "__main__":
    sys.exit(main())
