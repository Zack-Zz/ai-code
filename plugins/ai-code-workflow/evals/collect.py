#!/usr/bin/env python3
"""Import real-run material into a normalized, hashed run directory.

The input is a fixed-schema manifest pointing at real raw/artifact files plus
(either) normalized manual annotations validated against those raws, (or) a
native export that only a registered converter may translate. Unknown native
formats are rejected as unsupported_format (exit 5), never guessed.
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from _common import (  # noqa: E402
    ACTORS,
    EVENT_KINDS,
    MANIFEST_KEYS,
    RUN_INDEX_KEYS,
    ConflictError,
    DataError,
    HostUnavailableError,
    exit_with,
    find_case,
    checked_scenario,
    PREPARED_REF,
)

from workflow import io as wio  # noqa: E402
from workflow.product import HOSTS  # noqa: E402

CONVERTERS: dict = {}  # converter_id -> callable; none implemented yet
MAX_EVENT_DATA_BYTES = 64 * 1024


def _validate_manifest(data, expected_case: str) -> dict:
    if not isinstance(data, dict):
        raise DataError("collect input must be an object")
    if set(data) != MANIFEST_KEYS:
        missing = MANIFEST_KEYS - set(data)
        extra = set(data) - MANIFEST_KEYS
        raise DataError(
            f"manifest fields mismatch (missing={sorted(missing)}, unknown={sorted(extra)})")
    if not wio.is_strict_int(data["schema_version"]) or data["schema_version"] != 1:
        raise DataError("manifest schema_version must be the integer 1")
    if data["case_id"] != expected_case:
        raise DataError(f"manifest case_id {data['case_id']!r} != --case {expected_case!r}")
    if data["host"] not in HOSTS:
        raise DataError(f"manifest host must be one of {HOSTS}")
    if data["comparison_mode"] not in ("native", "plugin"):
        raise DataError("manifest comparison_mode must be native or plugin")
    for field in ("host_version", "model", "package_content_hash", "policy_hash",
                  "workspace_root", "fixture_baseline_hash", "converter_id",
                  "started_at", "finished_at"):
        if not (data[field] is None or isinstance(data[field], str)):
            raise DataError(f"manifest {field} must be a string or null")
    for field in ("raw_files", "artifact_files", "events"):
        if not isinstance(data[field], list):
            raise DataError(f"manifest {field} must be a list")
    for group in ("raw_files", "artifact_files"):
        for entry in data[group]:
            if not isinstance(entry, dict) or set(entry) != {"source_path", "target_path"}:
                raise DataError(f"{group} entries need exactly source_path/target_path")
    return data


def _validate_events(events, copied: set) -> None:
    previous_seq = 0
    for event in events:
        if not isinstance(event, dict) or set(event) != {
                "seq", "kind", "actor", "correlation_id", "raw_ref", "data"}:
            raise DataError("event envelope has unknown or missing fields")
        if not wio.is_strict_int(event["seq"]) or event["seq"] <= previous_seq:
            raise DataError(f"event seq must strictly increase (got {event['seq']!r})")
        previous_seq = event["seq"]
        if event["kind"] not in EVENT_KINDS:
            raise DataError(f"unknown event kind: {event['kind']!r}")
        if event["actor"] not in ACTORS:
            raise DataError(f"unknown event actor: {event['actor']!r}")
        if not (event["correlation_id"] is None or isinstance(event["correlation_id"], str)):
            raise DataError("event correlation_id must be a string or null")
        if not isinstance(event["raw_ref"], str) or not event["raw_ref"]:
            raise DataError("event raw_ref must be a non-empty string")
        base = event["raw_ref"].split(":")[0]
        if base not in copied:
            raise DataError(
                f"event raw_ref {event['raw_ref']!r} does not reference a copied raw/artifact file")
        if not isinstance(event["data"], dict):
            raise DataError("event data must be an object")
        if len(wio.canonical_json(event["data"])) > MAX_EVENT_DATA_BYTES:
            raise DataError("event data exceeds the 64 KiB bound")


def _import_file(source: Path, target_rel: str, run_root: Path):
    import os
    import stat as stat_module
    try:
        info = os.lstat(source)
    except FileNotFoundError as exc:
        raise DataError(f"source file does not exist: {source}") from exc
    if stat_module.S_ISLNK(info.st_mode) or not stat_module.S_ISREG(info.st_mode):
        raise DataError(f"source must be a regular non-symlink file: {source}")
    rel = wio.check_relative(target_rel, what="target_path")
    dest = run_root / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, dest)
    return {"source_path": str(source), "target_path": rel,
            "content_sha256": wio.sha256_file(dest)}


def collect(case_id: str, input_path: Path, origin: str, output: Path) -> dict:
    case = find_case(case_id)
    if origin not in ("native_export", "manual_annotation"):
        raise DataError("origin must be native_export or manual_annotation")

    input_path = Path(input_path)
    manifest = _validate_manifest(wio.load_json(input_path), case_id)
    scenario_prepared = None
    if case["kind"] in ("manager", "package") and manifest["workspace_root"]:
        scenario, prepared = checked_scenario(Path(manifest["workspace_root"]), case_id)
        scenario_prepared = wio.resolve_member(scenario, "prepared.json")
        actual_baseline = wio.sha256_bytes(wio.canonical_json(prepared["baseline"]))
        if manifest["fixture_baseline_hash"] not in (None, actual_baseline):
            raise DataError("fixture_baseline_hash does not match the prepared scenario")
        manifest["fixture_baseline_hash"] = actual_baseline
        artifact = wio.load_json(scenario / "pkg" / manifest["host"] / "ai-code-workflow/artifact.json")
        if manifest["package_content_hash"] not in (None, artifact["content_hash"]):
            raise DataError("package_content_hash does not match the scenario package")
        manifest["package_content_hash"] = artifact["content_hash"]
        manifest["workspace_root"] = str(scenario)
    output = Path(output)
    if output.exists():
        raise ConflictError(f"output run directory already exists: {output}")

    if origin == "native_export":
        converter_id = manifest["converter_id"]
        if converter_id not in CONVERTERS:
            raise HostUnavailableError(
                f"unsupported_format: no native converter is implemented for "
                f"converter_id={converter_id!r} (implemented: {sorted(CONVERTERS)}); "
                "use manual_annotation with real source material instead of guessing")
        raise HostUnavailableError(  # pragma: no cover - no converters yet
            "unsupported_format: converter framework present but empty")
    if manifest["converter_id"] is not None:
        raise DataError("manual_annotation input must keep converter_id null; "
                        "it cannot claim native auto-capture")

    seen_targets: set = set()
    reserved = {"index.json", "grade.json", "prepared.json", PREPARED_REF,
                "deterministic-evidence.json"}
    for group in ("raw_files", "artifact_files"):
        for entry in manifest[group]:
            if entry["target_path"] in seen_targets:
                raise DataError(
                    f"duplicate target_path in collect input: {entry['target_path']!r}")
            if entry["target_path"] in reserved or entry["target_path"].startswith("grader/") or entry["target_path"] == "grader":
                raise DataError(
                    f"target_path {entry['target_path']!r} is reserved for the run itself")
            seen_targets.add(entry["target_path"])

    run_root = output
    run_root.mkdir(parents=True)
    try:
        raw_refs = [_import_file(
            input_path.parent / entry["source_path"] if not Path(entry["source_path"]).is_absolute()
            else Path(entry["source_path"]),
            entry["target_path"], run_root) for entry in manifest["raw_files"]]
        artifacts = [_import_file(
            input_path.parent / entry["source_path"] if not Path(entry["source_path"]).is_absolute()
            else Path(entry["source_path"]),
            entry["target_path"], run_root) for entry in manifest["artifact_files"]]
        if scenario_prepared is not None:
            artifacts.append(_import_file(scenario_prepared, PREPARED_REF, run_root))
        copied = {ref["target_path"] for ref in raw_refs} | {ref["target_path"] for ref in artifacts}
        _validate_events(manifest["events"], copied)

        index = {
            "schema_version": 1,
            "run_id": f"run-{uuid.uuid4().hex}",
            "case_id": case_id,
            "host": manifest["host"],
            "host_version": manifest["host_version"],
            "model": manifest["model"],
            "package_content_hash": manifest["package_content_hash"],
            "policy_hash": manifest["policy_hash"],
            "comparison_mode": manifest["comparison_mode"],
            "workspace_root": manifest["workspace_root"],
            "fixture_baseline_hash": manifest["fixture_baseline_hash"],
            "capture_origin": origin,
            "raw_refs": raw_refs,
            "events": manifest["events"],
            "artifacts": artifacts,
            "started_at": manifest["started_at"],
            "finished_at": manifest["finished_at"],
        }
        assert set(index) == RUN_INDEX_KEYS
        (run_root / "index.json").write_text(json.dumps(index, indent=2, sort_keys=True) + "\n")
        return index
    except Exception:
        shutil.rmtree(run_root, ignore_errors=True)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(prog="collect.py")
    parser.add_argument("--case", required=True)
    parser.add_argument("--input", required=True)
    parser.add_argument("--origin", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    try:
        index = collect(args.case, Path(args.input), args.origin, Path(args.output))
    except Exception as exc:
        return exit_with(exc)
    print(json.dumps({"run_id": index["run_id"], "output": str(Path(args.output).resolve()),
                      "raw_files": len(index["raw_refs"]),
                      "events": len(index["events"])}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
