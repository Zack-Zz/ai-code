"""Bind public release inputs to committed Git blobs before publication eligibility."""

from pathlib import Path
import re
import subprocess

from .. import io
from ..io import DataError


def _head_blob(root, revision, relative):
    try:
        result = subprocess.run(["git", "cat-file", "blob", f"{revision}:{relative}"],
                                cwd=root, capture_output=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise DataError(f"cannot read public input from Git HEAD: {relative}") from exc
    if result.returncode != 0:
        raise DataError(f"public release input is missing from Git HEAD: {relative}")
    return result.stdout


def validate_head_inputs(root, spec, capture, revision):
    root = Path(root).resolve()
    if not isinstance(revision, str) or not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", revision):
        raise DataError("public release input binding requires a valid Git HEAD revision")
    try:
        prefix = spec.root.relative_to(root).as_posix()
    except ValueError as exc:
        raise DataError("public release input root is outside the Git repository") from exc
    public = dict(spec.inputs)
    for relative in ("release.json", capture.config["notes"], *capture.config["readmes"].values()):
        public[relative] = capture.inputs[relative]
    public.update(capture.proof_inputs)
    # Acceptance records and raw host-session artifacts stay private: their
    # local byte bindings are checked independently by metadata capture.
    for relative, expected in sorted(public.items()):
        path = io.relative_path(f"{prefix}/{relative}" if prefix != "." else relative)
        if _head_blob(root, revision, path) != expected:
            raise DataError(f"public release input bytes differ from Git HEAD: {path}")
