"""Shared helpers for the eval tools (internal; not part of the product)."""

from __future__ import annotations

import sys
import stat
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from workflow.io import (  # noqa: E402
    ConflictError,
    DataError,
    HostUnavailableError,
    InvalidStateError,
    ToolError,
)

CASES_PATH = REPO_ROOT / "evals" / "cases.json"
FIXTURES = REPO_ROOT / "evals" / "fixtures"
GRADER_VERSION = "1.1.0"
PREPARED_REF = "scenario/prepared.json"

EVENT_KINDS = ("user_message", "agent_message", "skill_load", "tool_call",
               "tool_result", "subagent_call", "subagent_result")
ACTORS = ("user", "agent", "reviewer", "system")
RUN_INDEX_KEYS = {
    "schema_version", "run_id", "case_id", "host", "host_version", "model",
    "package_content_hash", "policy_hash", "comparison_mode", "workspace_root",
    "fixture_baseline_hash", "capture_origin", "raw_refs", "events",
    "artifacts", "started_at", "finished_at",
}
MANIFEST_KEYS = ((RUN_INDEX_KEYS - {"run_id", "capture_origin", "raw_refs", "artifacts"})
                 | {"raw_files", "artifact_files", "converter_id"})


def exit_with(exc: Exception) -> int:
    code = getattr(exc, "exit_code", 1)
    import json
    print(json.dumps({"error": {"code": code, "reason": str(exc)}}), file=sys.stderr)
    return code


def load_cases() -> dict:
    import json
    data = json.loads(CASES_PATH.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise DataError("cases.json schema_version must be 1")
    return data


def find_case(case_id: str) -> dict:
    for case in load_cases()["cases"]:
        if case["case_id"] == case_id:
            return case
    raise DataError(f"unknown case_id: {case_id!r}")


def scenario_snapshot(root: Path, prefixes: list[str]) -> tuple[dict, list]:
    """Read the entire controlled fixture tree, including empty directories.

    A fixture child is never a trusted selected root: reject links and special
    files before reading anything beneath it or allowing the grader to write.
    """
    from workflow import io as wio
    files, directories = {}, []
    for prefix in prefixes:
        base = wio.resolve_member(root, prefix, allow_directory=True)
        if not base.is_dir():
            raise DataError(f"scenario subroot must be a directory: {base}")
        directories.append(prefix)
        for path in sorted(base.rglob("*")):
            rel = path.relative_to(root).as_posix()
            info = path.lstat()
            if stat.S_ISLNK(info.st_mode):
                raise DataError(f"symlinked scenario path rejected: {path}")
            if stat.S_ISDIR(info.st_mode):
                wio.resolve_member(root, rel, allow_directory=True)
                directories.append(rel)
            elif stat.S_ISREG(info.st_mode):
                files[rel] = wio.sha256_bytes(wio.read_owned(path, root=root))
            else:
                raise DataError(f"non-regular scenario path rejected: {path}")
    return files, sorted(directories)


def checked_scenario(root: Path, case_id: str) -> tuple[Path, dict]:
    """Bind a fresh manager/package fixture to its real prepare-time state."""
    from workflow import io as wio
    root = Path(root).resolve()
    prepared = wio.load_json(wio.resolve_member(root, "prepared.json"))
    case = find_case(case_id)
    if not isinstance(prepared, dict) or prepared.get("case_id") != case_id:
        raise DataError("prepared scenario case does not match collect/grade case")
    if prepared.get("fixture") != case["fixture"] or prepared.get("scenario_root") != str(root):
        raise InvalidStateError("prepared scenario identity changed")
    if prepared.get("cases_sha256") != wio.sha256_file(CASES_PATH):
        raise InvalidStateError("prepared cases source changed; prepare a new scenario")
    actual_files, actual_directories = scenario_snapshot(root, ["pkg", "project"])
    if actual_files != prepared.get("baseline") or actual_directories != prepared.get("baseline_directories"):
        raise InvalidStateError("actual prepared scenario baseline changed; no grading writes were applied")
    return root, prepared
