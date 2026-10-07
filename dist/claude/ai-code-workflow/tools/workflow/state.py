"""Task and evidence records under workspace/.ai-workflow/.

Records are an audit index: they describe observed state and referenced user
messages, and never generate authorization. All writes take the task's
exclusive lock, compare the expected revision and replace atomically.
"""

from __future__ import annotations

import copy
import re
import subprocess
from pathlib import Path

from . import io as wio
from .io import ConflictError, DataError, InvalidStateError

TASK_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
RFC3339_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(Z|[+-]\d{2}:\d{2})$")
CASE_ID_RE = re.compile(r"^A(0[1-9]|1[0-9]|2[0-5])$")

CHANGE_TYPES = ("feature", "bugfix", "refactor", "documentation", "configuration")
RISKS = ("normal", "critical")
DEPTHS = ("short", "standard", "architectural")
PHASES = ("planning", "implementing", "verifying", "reviewing", "handoff")
STATUSES = ("awaiting_confirmation", "in_progress", "blocked", "ready_for_user_review")
UNRESOLVED_KINDS = ("confirmed_defect", "risk", "environment", "question")
SEVERITIES = ("critical", "high", "medium", "low")
ACTIONS = ("plan", "implement", "run_tests", "diagnose_write", "commit", "amend",
           "tag", "push", "merge", "create_pr", "install", "publish")
EVIDENCE_KINDS = ("test", "review", "inspection", "host_run")
EVIDENCE_RESULTS = ("pass", "fail", "not_run", "blocked_env", "needs_revalidation", "manual_review")
CAPTURE_ORIGINS = ("tool_output", "native_export", "manual_annotation")
HOSTS = ("zcode", "codex")

_CREATE_KEYS = {"schema_version", "plan", "authorization_refs", "protected_paths"}
_UPDATE_KEYS = {"schema_version", "plan", "progress", "append_authorization_refs", "append_evidence_refs"}
_EVIDENCE_KEYS = {"schema_version", "evidence_id", "kind", "workspace_root", "subject_fingerprints",
                  "execution", "host_context", "capture", "result", "observations",
                  "started_at", "finished_at"}
_EXECUTION_KEYS = {"argv", "cwd", "exit_code", "signal", "start_error"}
_HOST_CONTEXT_KEYS = {"host", "host_version", "model", "case_id", "package_content_hash", "policy_hash"}
_CAPTURE_KEYS = {"origin", "relative_path", "content_sha256"}
_AUTH_REF_KEYS = {"message_ref", "actions", "scope_summary"}
_UNRESOLVED_KEYS = {"kind", "summary", "severity", "completion_blocking", "evidence_ref"}


def tasks_root(workspace: Path) -> Path:
    return Path(workspace) / ".ai-workflow" / "tasks"


def task_dir_for(workspace: Path, task_id: str) -> Path:
    if not isinstance(task_id, str) or not TASK_ID_RE.fullmatch(task_id):
        raise DataError(f"invalid task_id: {task_id!r} (expected ^[a-z0-9][a-z0-9_-]{{0,63}}$)")
    path = tasks_root(workspace) / task_id
    wio.resolve_member(workspace, path.relative_to(workspace).as_posix(),
                       must_exist=False, allow_directory=True)
    return path


def task_file_for(workspace: Path, task_id: str) -> Path:
    return task_dir_for(workspace, task_id) / "task.json"


# ---------------------------------------------------------------- validation


def _require_keys(data, allowed, context, *, exact):
    if not isinstance(data, dict):
        raise DataError(f"{context} must be an object")
    keys = set(data)
    unknown = keys - allowed
    if unknown:
        raise DataError(f"unknown field(s) {sorted(unknown)} in {context}")
    if exact:
        missing = allowed - keys
        if missing:
            raise DataError(f"missing field(s) {sorted(missing)} in {context}")


def _validate_plan(data, *, context="plan"):
    _require_keys(data, {"goal", "scope", "acceptance", "change_type", "risk", "depth", "revision"},
                  context, exact=False)
    for field in ("goal", "scope", "acceptance", "change_type", "risk", "depth"):
        if field not in data:
            raise DataError(f"plan missing required field: {field}")
    if not isinstance(data["goal"], str) or not data["goal"]:
        raise DataError("plan.goal must be a non-empty string")
    scope = data["scope"]
    if not isinstance(scope, list) or not scope:
        raise DataError("plan.scope must be a non-empty array")
    for item in scope:
        wio.check_relative(item, what="plan.scope entry")
        if any(ch in item for ch in ("$", "`", ";", "&&", "|")):
            raise DataError(f"plan.scope entry is a path, not a shell expression: {item!r}")
    acceptance = data["acceptance"]
    if not isinstance(acceptance, list) or not acceptance or \
            not all(isinstance(a, str) and a.strip() for a in acceptance):
        raise DataError("plan.acceptance must be a non-empty array of observable conditions")
    if data["change_type"] not in CHANGE_TYPES:
        raise DataError(f"plan.change_type must be one of {CHANGE_TYPES}")
    if data["risk"] not in RISKS:
        raise DataError(f"plan.risk must be one of {RISKS}")
    if data["depth"] not in DEPTHS:
        raise DataError(f"plan.depth must be one of {DEPTHS}")
    if "revision" in data:
        if not wio.is_strict_int(data["revision"]) or data["revision"] < 1:
            raise DataError("plan.revision must be a positive integer")
    return {k: copy.deepcopy(data[k]) for k in
            ("goal", "scope", "acceptance", "change_type", "risk", "depth")}


def _validate_progress(data, *, context="progress"):
    _require_keys(data, {"phase", "status", "completed_steps", "next_action", "unresolved"},
                  context, exact=True)
    if data["phase"] not in PHASES:
        raise DataError(f"progress.phase must be one of {PHASES}")
    if data["status"] not in STATUSES:
        raise DataError(f"progress.status must be one of {STATUSES}")
    if not isinstance(data["completed_steps"], list) or \
            not all(isinstance(s, str) for s in data["completed_steps"]):
        raise DataError("progress.completed_steps must be a list of strings")
    if not isinstance(data["next_action"], str):
        raise DataError("progress.next_action must be a string")
    if not isinstance(data["unresolved"], list):
        raise DataError("progress.unresolved must be a list")
    blocking = False
    for item in data["unresolved"]:
        _require_keys(item, _UNRESOLVED_KEYS, "progress.unresolved item", exact=True)
        if item["kind"] not in UNRESOLVED_KINDS:
            raise DataError(f"unresolved.kind must be one of {UNRESOLVED_KINDS}")
        if not isinstance(item["summary"], str) or not item["summary"]:
            raise DataError("unresolved.summary must be a non-empty string")
        if item["severity"] is not None and item["severity"] not in SEVERITIES:
            raise DataError(f"unresolved.severity must be one of {SEVERITIES} or null")
        if not isinstance(item["completion_blocking"], bool):
            raise DataError("unresolved.completion_blocking must be a boolean")
        if not (item["evidence_ref"] is None or isinstance(item["evidence_ref"], str)):
            raise DataError("unresolved.evidence_ref must be a string or null")
        if item["kind"] == "confirmed_defect" and item["severity"] in ("critical", "high") \
                and not item["completion_blocking"]:
            raise DataError(
                "confirmed_defect with severity critical/high must set completion_blocking=true")
        if item["completion_blocking"]:
            blocking = True
    if data["status"] == "ready_for_user_review" and blocking:
        raise DataError(
            "progress.status cannot be ready_for_user_review while completion_blocking "
            "items remain unresolved")
    return copy.deepcopy(data)


def _validate_auth_refs(data, *, context="authorization_refs"):
    if not isinstance(data, list):
        raise DataError(f"{context} must be a list")
    for item in data:
        _require_keys(item, _AUTH_REF_KEYS, f"{context} item", exact=True)
        if not isinstance(item["message_ref"], str) or not item["message_ref"]:
            raise DataError("authorization_ref.message_ref must be a non-empty string")
        if not isinstance(item["actions"], list) or not item["actions"] or \
                not all(a in ACTIONS for a in item["actions"]):
            raise DataError(f"authorization_ref.actions values must be within {ACTIONS}")
        if not isinstance(item["scope_summary"], str):
            raise DataError("authorization_ref.scope_summary must be a string")
    return copy.deepcopy(data)


def _validate_ref_structure(ref):
    _require_keys(ref, {"relative_path", "content_sha256"}, "evidence ref", exact=True)
    wio.check_relative(ref["relative_path"], what="evidence ref path")
    if not isinstance(ref["content_sha256"], str) or not HEX64_RE.fullmatch(ref["content_sha256"]):
        raise DataError("evidence ref content_sha256 must be a sha256 hex")


def _validate_task_record(record, workspace: Path, task_id: str, *, inspect_refs=True):
    """The persisted structure is shared by update and check, before any CAS."""
    _require_keys(record, {"schema_version", "record_revision", "task_id", "workspace", "baseline",
                           "plan", "progress", "authorization_refs", "evidence_refs",
                           "created_at", "updated_at"}, "task record", exact=True)
    if not wio.is_strict_int(record["schema_version"]) or record["schema_version"] != 1 or \
            not wio.is_strict_int(record["record_revision"]) or record["record_revision"] < 1:
        raise DataError("task schema_version/revision must be positive integers, not booleans")
    _require_keys(record["workspace"], {"root", "repository_root", "git_head"}, "workspace", exact=True)
    for field, value in record["workspace"].items():
        if not (isinstance(value, str) or (field != "root" and value is None)):
            raise DataError(f"workspace.{field} must be a string or nullable repository metadata")
    if record["task_id"] != task_id or record["workspace"]["root"] != str(workspace):
        raise InvalidStateError("task record identity does not match the requested task/workspace")
    _require_keys(record["baseline"], {"dirty_files", "protected_fingerprints"}, "baseline", exact=True)
    dirty = record["baseline"]["dirty_files"]
    if not isinstance(dirty, list) or not all(isinstance(rel, str) for rel in dirty):
        raise DataError("baseline.dirty_files must be a list of strings")
    fingerprints = record["baseline"]["protected_fingerprints"]
    if not isinstance(fingerprints, dict):
        raise DataError("baseline.protected_fingerprints must be an object")
    for rel, sha in fingerprints.items():
        wio.check_relative(rel, what="protected fingerprint path")
        if sha is not None and not (isinstance(sha, str) and HEX64_RE.fullmatch(sha)):
            raise DataError("protected fingerprint must be a sha256 hex or null")
    _validate_plan(record["plan"])
    if "revision" not in record["plan"]:
        raise DataError("task plan must include its revision")
    _validate_progress(record["progress"])
    _validate_auth_refs(record["authorization_refs"])
    if not isinstance(record["evidence_refs"], list):
        raise DataError("task evidence_refs must be a list")
    if inspect_refs:
        for ref in record["evidence_refs"]:
            _validate_ref_structure(ref)
    for field in ("created_at", "updated_at"):
        if not isinstance(record[field], str) or not RFC3339_RE.fullmatch(record[field]):
            raise DataError(f"task {field} must be an RFC3339 timestamp")


def _validate_evidence_structure(data, *, context="evidence"):
    _require_keys(data, _EVIDENCE_KEYS, context, exact=True)
    if not wio.is_strict_int(data["schema_version"]) or data["schema_version"] != 1:
        raise DataError(f"{context}: schema_version must be the integer 1")
    if not isinstance(data["evidence_id"], str) or not TASK_ID_RE.fullmatch(data["evidence_id"]):
        raise DataError(f"{context}: invalid evidence_id")
    if data["kind"] not in EVIDENCE_KINDS:
        raise DataError(f"{context}: kind must be one of {EVIDENCE_KINDS}")
    if not isinstance(data["workspace_root"], str) or not data["workspace_root"]:
        raise DataError(f"{context}: workspace_root must be a non-empty string")
    fingerprints = data["subject_fingerprints"]
    if not isinstance(fingerprints, dict):
        raise DataError(f"{context}: subject_fingerprints must be an object")
    for rel, sha in fingerprints.items():
        wio.check_relative(rel, what=f"{context}: subject path")
        if sha is not None and not (isinstance(sha, str) and HEX64_RE.fullmatch(sha)):
            raise DataError(f"{context}: fingerprint for {rel} must be a sha256 hex or null")

    execution = data["execution"]
    if execution is not None:
        _require_keys(execution, _EXECUTION_KEYS, f"{context}.execution", exact=True)
        if not isinstance(execution["argv"], list) or not execution["argv"] or \
                not all(isinstance(a, str) and a for a in execution["argv"]):
            raise DataError(f"{context}.execution.argv must be a non-empty list of strings")
        if not isinstance(execution["cwd"], str) or not execution["cwd"]:
            raise DataError(f"{context}.execution.cwd must be a non-empty string")
        if execution["exit_code"] is not None and not wio.is_strict_int(execution["exit_code"]):
            raise DataError(f"{context}.execution.exit_code must be an integer or null")
        for field in ("signal", "start_error"):
            if execution[field] is not None and not isinstance(execution[field], str):
                raise DataError(f"{context}.execution.{field} must be a string or null")

    host_context = data["host_context"]
    if host_context is not None:
        _require_keys(host_context, _HOST_CONTEXT_KEYS, f"{context}.host_context", exact=True)
        if host_context["host"] not in HOSTS:
            raise DataError(f"{context}.host_context.host must be one of {HOSTS}")
        for field in ("host_version", "model"):
            if host_context[field] is not None and not isinstance(host_context[field], str):
                raise DataError(f"{context}.host_context.{field} must be a string or null")
        if not isinstance(host_context["case_id"], str) or not CASE_ID_RE.fullmatch(host_context["case_id"]):
            raise DataError(f"{context}.host_context.case_id must be A01..A25")
        for field in ("package_content_hash", "policy_hash"):
            if host_context[field] is not None and not (
                    isinstance(host_context[field], str) and HEX64_RE.fullmatch(host_context[field])):
                raise DataError(f"{context}.host_context.{field} must be a sha256 hex or null")

    capture = data["capture"]
    _require_keys(capture, _CAPTURE_KEYS, f"{context}.capture", exact=True)
    if capture["origin"] not in CAPTURE_ORIGINS:
        raise DataError(f"{context}.capture.origin must be one of {CAPTURE_ORIGINS}")
    wio.check_relative(capture["relative_path"], what=f"{context}.capture.relative_path")
    if not isinstance(capture["content_sha256"], str) or not HEX64_RE.fullmatch(capture["content_sha256"]):
        raise DataError(f"{context}.capture.content_sha256 must be a sha256 hex")

    if data["result"] not in EVIDENCE_RESULTS:
        raise DataError(f"{context}: result must be one of {EVIDENCE_RESULTS}")
    if not isinstance(data["observations"], list) or \
            not all(isinstance(o, str) for o in data["observations"]):
        raise DataError(f"{context}: observations must be a list of strings")
    for field in ("started_at", "finished_at"):
        if data[field] is not None and not (isinstance(data[field], str) and RFC3339_RE.fullmatch(data[field])):
            raise DataError(f"{context}: {field} must be an RFC3339 string or null")

    if data["kind"] == "host_run" and host_context is None:
        raise DataError(f"{context}: host_run requires host_context")
    if data["kind"] == "test" and data["result"] == "pass":
        if execution is None or execution["exit_code"] != 0 or \
                execution["signal"] is not None or execution["start_error"] is not None:
            raise DataError(
                f"{context}: test pass requires a completed execution with exit_code=0")
        if data["finished_at"] is None:
            raise DataError(f"{context}: test pass requires a finished_at timestamp")
    if data["kind"] == "host_run" and data["result"] == "pass":
        if execution is not None and (execution["exit_code"] != 0 or
                                     execution["signal"] is not None or execution["start_error"] is not None):
            raise DataError(f"{context}: host_run pass contradicts its execution failure")
        if host_context is None or any(host_context[f] is None for f in _HOST_CONTEXT_KEYS - {"host"}):
            raise DataError(
                f"{context}: host_run pass requires complete host_context "
                "(host_version/model/package_content_hash/policy_hash); keep the result "
                "manual_review/not_run/blocked_env when information is missing")
        if data["finished_at"] is None:
            raise DataError(f"{context}: host_run pass requires a finished_at timestamp")
    return data


# ------------------------------------------------------------------ baseline


def _git_info(workspace: Path):
    def git(*args, raw=False):
        try:
            result = subprocess.run(
                ["git", *args], cwd=str(workspace), capture_output=True, timeout=10)
        except (OSError, subprocess.TimeoutExpired):
            return None
        stdout = result.stdout.decode("utf-8", errors="surrogateescape")
        return (stdout if raw else stdout.removesuffix("\n")) if result.returncode == 0 else None

    root = git("rev-parse", "--show-toplevel")
    head = git("rev-parse", "HEAD")
    status = git("status", "--porcelain=v1", "-z", "-uall", raw=True)
    dirty = []
    if status is not None:
        records = iter(status.split("\0"))
        for line in records:
            entry = line[3:]
            if entry:
                dirty.append(entry)
            if "R" in line[:2] or "C" in line[:2]:
                original = next(records, "")
                if original:
                    dirty.append(original)
    return root, head, sorted(set(dirty))


def _fingerprint(workspace: Path, relative: str):
    path = wio.resolve_member(workspace, relative, must_exist=False)
    if not path.exists():
        return None
    raw = wio.read_owned(path, root=workspace)
    return wio.sha256_bytes(raw) if raw is not None else None


def _compute_baseline(workspace: Path, protected_paths):
    repo_root, head, dirty = _git_info(workspace)
    fingerprints = {}
    for rel in protected_paths:
        wio.check_relative(rel, what="protected_paths entry")
        fingerprints[rel] = _fingerprint(workspace, rel)
    return {
        "workspace": {"root": str(workspace), "repository_root": repo_root, "git_head": head},
        "baseline": {"dirty_files": dirty, "protected_fingerprints": fingerprints},
    }


def _record_bytes(record) -> bytes:
    import json
    return (json.dumps(record, indent=2, sort_keys=True, ensure_ascii=True) + "\n").encode("utf-8")


# ------------------------------------------------------------------- create


def create_task(workspace: Path, task_id: str, input_data, *, apply: bool = False) -> dict:
    workspace = Path(workspace).resolve()
    if not workspace.is_dir():
        raise DataError(f"workspace does not exist or is not a directory: {workspace}")
    workspace_abs = str(workspace.resolve())
    task_dir = task_dir_for(workspace, task_id)
    task_file = task_dir / "task.json"

    if not isinstance(input_data, dict):
        raise DataError("task create input must be an object")
    _require_keys(input_data, _CREATE_KEYS, "task create input", exact=True)
    if not wio.is_strict_int(input_data["schema_version"]) or input_data["schema_version"] != 1:
        raise DataError("task create input schema_version must be the integer 1")
    plan = _validate_plan(input_data["plan"])
    plan["revision"] = 1
    auth_refs = _validate_auth_refs(input_data["authorization_refs"])
    protected = input_data["protected_paths"]
    if not isinstance(protected, list) or not all(isinstance(p, str) for p in protected):
        raise DataError("protected_paths must be a list of strings")

    environment = _compute_baseline(workspace.resolve(), protected)
    now = wio.now_rfc3339()
    record = {
        "schema_version": 1,
        "record_revision": 1,
        "task_id": task_id,
        "workspace": environment["workspace"],
        "baseline": environment["baseline"],
        "plan": plan,
        "progress": {
            "phase": "planning",
            "status": "awaiting_confirmation",
            "completed_steps": ["record-created"],
            "next_action": "Confirm the plan with the user; implementation has not started",
            "unresolved": [],
        },
        "authorization_refs": auth_refs,
        "evidence_refs": [],
        "created_at": now,
        "updated_at": now,
    }
    _validate_progress(record["progress"])

    if not apply:
        return {"applied": False, "changed": True, "record_revision": 1,
                "proposed_record": record, "path": str(task_file)}

    if task_file.exists():
        raise ConflictError(f"task already exists: {task_file}")
    wio.ensure_directory(workspace, task_dir.relative_to(workspace).as_posix())
    operation_id = f"create-{now}-{task_id}"
    lock = task_dir / ".write.lock"
    wio.acquire_lock(lock, operation_id, root=workspace)
    try:
        if task_file.exists():
            raise ConflictError(f"task already exists: {task_file}")
        wio.atomic_write(task_file, _record_bytes(record), expected_before=None, root=workspace)
    finally:
        wio.release_lock(lock, operation_id, root=workspace)
    return {"applied": True, "changed": True, "record_revision": 1,
            "proposed_record": record, "path": str(task_file)}


# ------------------------------------------------------------------- update


def _verify_evidence_ref(task_root: Path, ref, workspace_abs: str):
    _validate_ref_structure(ref)
    rel = ref["relative_path"]
    try:
        ev_path = wio.resolve_member(task_root, rel, must_exist=True)
    except DataError as exc:
        raise InvalidStateError(f"evidence file missing: {exc}") from exc
    try:
        evidence, raw = wio.read_json_snapshot(ev_path, root=Path(workspace_abs))
    except DataError as exc:
        raise InvalidStateError(f"evidence file unreadable: {exc}") from exc
    actual = wio.sha256_bytes(raw)
    if actual != ref["content_sha256"]:
        raise InvalidStateError(f"evidence content hash mismatch for {rel}")
    try:
        _validate_evidence_structure(evidence, context=f"evidence {rel}")
    except DataError as exc:
        raise DataError(f"{rel}: {exc}") from exc
    if Path(evidence["workspace_root"]).resolve() != Path(workspace_abs).resolve():
        raise InvalidStateError(
            f"{rel}: workspace_root {evidence['workspace_root']} does not match task workspace")
    capture_rel = evidence["capture"]["relative_path"]
    try:
        capture_path = wio.resolve_member(task_root, capture_rel, must_exist=True)
    except DataError as exc:
        raise InvalidStateError(f"{rel}: capture raw file missing: {exc}") from exc
    capture_bytes = wio.read_owned(capture_path, root=Path(workspace_abs))
    if capture_bytes is None or wio.sha256_bytes(capture_bytes) != evidence["capture"]["content_sha256"]:
        raise InvalidStateError(f"{rel}: capture raw content hash mismatch ({capture_rel})")


def update_task(workspace: Path, task_id: str, expected_revision: int, input_data, *, apply: bool = False) -> dict:
    workspace = Path(workspace).resolve()
    if not workspace.is_dir():
        raise DataError(f"workspace does not exist: {workspace}")
    if not wio.is_strict_int(expected_revision) or expected_revision < 1:
        raise DataError("expected_revision must be a positive integer")
    task_dir = task_dir_for(workspace, task_id)
    task_file = task_dir / "task.json"

    if not isinstance(input_data, dict):
        raise DataError("task update input must be an object")
    _require_keys(input_data, _UPDATE_KEYS, "task update input", exact=False)
    if not wio.is_strict_int(input_data.get("schema_version")) or input_data["schema_version"] != 1:
        raise DataError("task update input schema_version must be the integer 1")
    optional = _UPDATE_KEYS - {"schema_version"}
    if not (set(input_data) & optional):
        raise DataError("task update input needs at least one of plan/progress/append_* fields")

    new_plan = None
    if "plan" in input_data:
        raw_plan = input_data["plan"]
        if not isinstance(raw_plan, dict) or "revision" in raw_plan:
            raise DataError(
                "update plan must not carry revision; the tool computes plan.revision")
        new_plan = _validate_plan(raw_plan)
    new_progress = None
    if "progress" in input_data:
        new_progress = _validate_progress(input_data["progress"])
    append_auth = None
    if "append_authorization_refs" in input_data:
        append_auth = _validate_auth_refs(
            input_data["append_authorization_refs"], context="append_authorization_refs")
    append_evidence = None
    if "append_evidence_refs" in input_data:
        append_evidence = input_data["append_evidence_refs"]
        if not isinstance(append_evidence, list):
            raise DataError("append_evidence_refs must be a list")

    if not task_file.is_file():
        raise DataError(f"task does not exist: {task_file}")

    def _validate_current(current):
        _validate_task_record(current, workspace, task_id)

    def _mutate(current):
        updated = copy.deepcopy(current)
        changed = False
        if new_plan is not None:
            current_plan = {k: v for k, v in current["plan"].items() if k != "revision"}
            if new_plan != current_plan:
                updated["plan"] = dict(new_plan)
                updated["plan"]["revision"] = current["plan"].get("revision", 1) + 1
                changed = True
        if new_progress is not None and new_progress != current["progress"]:
            updated["progress"] = new_progress
            changed = True
        if append_auth:
            merged = list(current["authorization_refs"]) + append_auth
            if merged != current["authorization_refs"]:
                updated["authorization_refs"] = merged
                changed = True
        if append_evidence:
            existing = {ref["relative_path"]: ref for ref in current["evidence_refs"]}
            for ref in append_evidence:
                _verify_evidence_ref(task_dir, ref, current["workspace"]["root"])
                existing[ref["relative_path"]] = {
                    "relative_path": ref["relative_path"],
                    "content_sha256": ref["content_sha256"],
                }
            merged_refs = sorted(existing.values(), key=lambda r: r["relative_path"])
            if merged_refs != current["evidence_refs"]:
                updated["evidence_refs"] = merged_refs
                changed = True
        return updated, changed

    if not apply:
        current = wio.load_json(task_file, root=workspace)
        _validate_current(current)
        if current["record_revision"] != expected_revision:
            raise ConflictError(
                f"expected revision {expected_revision} but task is at "
                f"{current['record_revision']}: {task_file}")
        proposed, changed = _mutate(current)
        if changed:
            proposed["record_revision"] = expected_revision + 1
            proposed["updated_at"] = wio.now_rfc3339()
        return {"applied": False, "changed": changed,
                "record_revision": current["record_revision"] if not changed else expected_revision + 1,
                "proposed_record": proposed, "path": str(task_file)}

    operation_id = f"update-{wio.now_rfc3339()}-{task_id}"
    lock = task_dir / ".write.lock"
    wio.acquire_lock(lock, operation_id, root=workspace)
    try:
        current, before_bytes = wio.read_json_snapshot(task_file, root=workspace)
        _validate_current(current)
        if current["record_revision"] != expected_revision:
            raise ConflictError(
                f"expected revision {expected_revision} but task is at "
                f"{current['record_revision']}: {task_file}")
        updated, changed = _mutate(current)
        if not changed:
            return {"applied": False, "changed": False,
                    "record_revision": current["record_revision"],
                    "proposed_record": current, "path": str(task_file)}
        updated["record_revision"] = current["record_revision"] + 1
        updated["updated_at"] = wio.now_rfc3339()
        _validate_progress(updated["progress"])
        wio.atomic_write(task_file, _record_bytes(updated), expected_before=before_bytes, root=workspace)
    finally:
        wio.release_lock(lock, operation_id, root=workspace)
    return {"applied": True, "changed": True, "record_revision": updated["record_revision"],
            "proposed_record": updated, "path": str(task_file)}


# -------------------------------------------------------------------- check


def check_task(workspace: Path, task_id: str) -> dict:
    workspace = Path(workspace).resolve()
    if not workspace.is_dir():
        raise DataError(f"workspace does not exist: {workspace}")
    task_dir = task_dir_for(workspace, task_id)
    task_file = task_dir / "task.json"
    if not task_file.exists() and not task_file.is_symlink():
        raise DataError(f"task does not exist: {task_file}")
    try:
        record = wio.load_json(task_file, root=workspace)
        _validate_task_record(record, workspace, task_id, inspect_refs=False)
    except (DataError, InvalidStateError) as exc:
        identity = "invalid_record"
        if isinstance(exc, InvalidStateError):
            identity = ("workspace_mismatch" if record["workspace"]["root"] != str(workspace)
                        else "task_mismatch")
        return {"identity_status": identity, "invalid_evidence": [],
                "pending_items": [{"kind": "invalid_record", "summary": str(exc),
                                   "completion_blocking": True}], "consistent": False}

    invalid_evidence = []
    for ref in record["evidence_refs"]:
        rel = ref.get("relative_path", "<missing>") if isinstance(ref, dict) else "<malformed>"
        problems = []
        needs_revalidation = False
        try:
            _validate_ref_structure(ref)
        except DataError as exc:
            invalid_evidence.append({"relative_path": rel, "needs_revalidation": False,
                                     "reason": f"malformed evidence ref: {exc}"})
            continue
        try:
            ev_path = wio.resolve_member(task_dir, rel, must_exist=True)
            evidence, raw = wio.read_json_snapshot(ev_path, root=workspace)
            if wio.sha256_bytes(raw) != ref["content_sha256"]:
                problems.append("evidence JSON hash mismatch (edited since registration)")
            _validate_evidence_structure(evidence, context=f"evidence {rel}")
        except DataError as exc:
            invalid_evidence.append({"relative_path": rel, "needs_revalidation": False,
                                     "reason": f"invalid evidence structure or file: {exc}"})
            continue
        try:
            capture_path = wio.resolve_member(task_dir, evidence["capture"]["relative_path"], must_exist=True)
            capture_bytes = wio.read_owned(capture_path, root=workspace)
            if capture_bytes is None or wio.sha256_bytes(capture_bytes) != evidence["capture"]["content_sha256"]:
                problems.append("capture raw content hash mismatch")
        except DataError as exc:
            problems.append(f"illegal or missing capture path: {exc}")
        if Path(evidence["workspace_root"]).resolve() != workspace:
            problems.append("evidence workspace_root does not match task workspace")
        for subj, recorded in evidence["subject_fingerprints"].items():
            try:
                current_sha = _fingerprint(workspace, subj)
            except DataError as exc:
                needs_revalidation = True
                problems.append(f"illegal subject {subj}: {exc}")
                continue
            if current_sha != recorded:
                needs_revalidation = True
                problems.append(f"subject {subj} changed since the evidence was captured (re-verify and re-register)")
        if problems:
            invalid_evidence.append({"relative_path": rel, "needs_revalidation": needs_revalidation,
                                     "reason": "; ".join(problems)})

    pending_items = []
    unsafe_baseline = False
    for rel, recorded in record["baseline"]["protected_fingerprints"].items():
        try:
            current_sha = _fingerprint(workspace, rel)
        except DataError as exc:
            unsafe_baseline = True
            pending_items.append({"kind": "invalid_record", "summary": f"illegal protected path {rel}: {exc}",
                                  "completion_blocking": True})
            continue
        if current_sha != recorded:
            pending_items.append({"kind": "baseline_drift",
                                  "summary": f"protected path {rel} differs from the baseline fingerprint",
                                  "completion_blocking": False})
    for item in record["progress"]["unresolved"]:
        pending_items.append({"kind": item["kind"], "summary": item["summary"],
                              "completion_blocking": item["completion_blocking"]})
    return {"identity_status": "consistent", "invalid_evidence": invalid_evidence,
            "pending_items": pending_items, "consistent": not invalid_evidence and not unsafe_baseline}
