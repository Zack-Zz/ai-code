"""The public stable/preview version syntax and its SemVer precedence."""

import re

from .io import DataError

_NUMBER = r"(0|[1-9][0-9]*)"
VERSION_PATTERN = re.compile(rf"{_NUMBER}\.{_NUMBER}\.{_NUMBER}(?:-preview\.{_NUMBER})?")


def version_key(value):
    """Return a numeric ordering key; a stable release follows its previews."""
    match = VERSION_PATTERN.fullmatch(value) if isinstance(value, str) else None
    if match is None:
        raise DataError("invalid public version: expected X.Y.Z or X.Y.Z-preview.N")
    major, minor, patch, preview = match.groups()
    try:
        return (int(major), int(minor), int(patch), int(preview is None),
                int(preview) if preview is not None else 0)
    except ValueError as exc:
        raise DataError("public version numeric component is too large") from exc


def release_kind(value):
    """Classify new releases from their validated public version syntax."""
    return "stable" if version_key(value)[3] else "preview"
