"""Policy profiles: loading, validation and precedence resolution."""

from __future__ import annotations

import re
from pathlib import Path

from . import io
from .io import DataError

MODES = ("collaborative", "continuous")
REVIEW_LEVELS = ("critical", "all")
POLICY_FIELDS = ("mode", "review_level", "max_parallel_tasks",
                 "response_language", "verification_notes")
LANGUAGE_RE = re.compile(r"^(auto|[A-Za-z]{2,3}(-[A-Za-z0-9]{1,8})*)$")
MAX_NOTES = 16
MAX_NOTE_CHARS = 512

CONTINUOUS_WARNING = (
    "mode=continuous only adjusts plan-confirmation pacing inside a scope the "
    "user already authorized; it never creates authorization and never widens "
    "host limits."
)


def validate_field(field: str, value):
    """Validate one policy field; returns the value or raises DataError."""
    if field == "mode":
        if value not in MODES:
            raise DataError(f"mode must be one of {MODES}, got {value!r}")
        return value
    if field == "review_level":
        if value not in REVIEW_LEVELS:
            raise DataError(f"review_level must be one of {REVIEW_LEVELS}, got {value!r}")
        return value
    if field == "max_parallel_tasks":
        if not io.is_strict_int(value) or not 1 <= value <= 8:
            raise DataError(f"max_parallel_tasks must be an integer in [1, 8], got {value!r}")
        return value
    if field == "response_language":
        if not isinstance(value, str) or not LANGUAGE_RE.match(value):
            raise DataError(
                f"response_language must be 'auto' or a valid language tag, got {value!r}")
        return value
    if field == "verification_notes":
        if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
            raise DataError("verification_notes must be a list of strings")
        if len(value) > MAX_NOTES:
            raise DataError(f"verification_notes allows at most {MAX_NOTES} entries")
        for note in value:
            if len(note) > MAX_NOTE_CHARS:
                raise DataError(
                    f"verification_notes entries are limited to {MAX_NOTE_CHARS} chars")
        return list(value)
    raise DataError(f"unknown policy field: {field!r}")


def load_profile(plugin_root: Path, mode: str) -> dict:
    """Load and validate one complete profile from <plugin>/policies/<mode>.json."""
    if mode not in MODES:
        raise DataError(f"unknown policy mode: {mode!r}")
    path = io.resolve_member(Path(plugin_root), f"policies/{mode}.json")
    data = io.load_json(path)
    if not isinstance(data, dict):
        raise DataError(f"policy profile must be a JSON object: {path}")
    if not io.is_strict_int(data.get("schema_version")) or data["schema_version"] != 1:
        raise DataError(f"policy profile schema_version must be the integer 1: {path}")
    unknown = set(data) - {"schema_version"} - set(POLICY_FIELDS)
    if unknown:
        raise DataError(f"unknown policy field(s) {sorted(unknown)} in {path}")
    missing = set(POLICY_FIELDS) - set(data)
    if missing:
        raise DataError(f"policy profile missing field(s) {sorted(missing)}: {path}")
    if data["mode"] != mode:
        raise DataError(f"policy profile file mode {data['mode']!r} does not match {mode!r}: {path}")
    return {f: validate_field(f, data[f]) for f in POLICY_FIELDS}


def validate_override(data, *, context: str, require_schema_version: bool = True) -> dict:
    """Validate a partial override (project file or explicit user options).

    Project override files must carry schema_version=1; explicit in-call user
    options are validated field-by-field without that envelope.
    """
    if not isinstance(data, dict):
        raise DataError(f"{context} must be a JSON object")
    if require_schema_version:
        if not io.is_strict_int(data.get("schema_version")) or data["schema_version"] != 1:
            raise DataError(f"{context} must carry schema_version = 1")
    unknown = set(data) - ({"schema_version"} if require_schema_version else set()) - set(POLICY_FIELDS)
    if unknown:
        raise DataError(f"unknown field(s) {sorted(unknown)} in {context}")
    return {f: validate_field(f, data[f]) for f in POLICY_FIELDS if f in data}


def resolve_policy(plugin_root: Path, workspace: Path, explicit=None) -> dict:
    """Resolve the effective policy.

    Order: full profile of the explicitly chosen mode (default collaborative)
    -> workspace .ai-workflow/policy.json overrides -> explicit user options
    for this run. Per-field precedence follows the same order, later wins.
    Output: effective_policy, sources, warnings, policy_hash. Read-only; the
    result never constitutes an operation authorization.
    """
    plugin_root = Path(plugin_root)
    workspace = Path(workspace)
    explicit = (
        validate_override(explicit, context="explicit user options",
                          require_schema_version=False)
        if explicit else {}
    )

    base_mode = explicit.get("mode", "collaborative")
    effective = load_profile(plugin_root, base_mode)
    sources = {f: f"plugin:policies/{base_mode}.json" for f in POLICY_FIELDS}

    project_path = workspace / ".ai-workflow" / "policy.json"
    if project_path.exists() or project_path.is_symlink():
        project_path = io.resolve_member(workspace, ".ai-workflow/policy.json")
        overrides = validate_override(
            io.load_json(project_path), context=f"project file {project_path}")
        for field, value in overrides.items():
            effective[field] = value
            sources[field] = "project:.ai-workflow/policy.json"

    for field, value in explicit.items():
        effective[field] = value
        sources[field] = "user:explicit"

    warnings = [CONTINUOUS_WARNING] if effective["mode"] == "continuous" else []
    return {
        "effective_policy": effective,
        "sources": sources,
        "warnings": warnings,
        "policy_hash": io.sha256_bytes(io.canonical_json(effective)),
    }
