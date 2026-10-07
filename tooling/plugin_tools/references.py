"""Resolve active Markdown skill links against the packaged resource whitelist."""

import posixpath
import re
import string
from urllib.parse import unquote, urlsplit

from . import io
from .io import DataError


def _destination(text, start):
    """Read one Markdown destination, respecting balanced/escaped parentheses."""
    start = next((i for i in range(start, len(text)) if not text[i].isspace()), len(text))
    if start == len(text):
        return None
    angle = text[start] == "<"
    index = start + 1 if angle else start
    depth = 0
    while index < len(text):
        char = text[index]
        if char == "\\" and index + 1 < len(text) and text[index + 1] in string.punctuation:
            index += 2
            continue
        if angle:
            if char == ">":
                return text[start:index + 1], index + 1
            if char in "\n<":
                return None
        else:
            if char.isspace():
                break
            if char == "(":
                depth += 1
            elif char == ")":
                if depth == 0:
                    break
                depth -= 1
        index += 1
    if angle or depth:
        return None
    return text[start:index], index


def _destinations(text):
    # Comments and examples describe syntax; they do not require shipped files.
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)
    visible = []
    fence = None
    for line in text.splitlines():
        marker = re.match(r"^\s*(`{3,}|~{3,})", line)
        if marker:
            token = marker[1]
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
            continue
        if fence is None:
            visible.append(line)
    text = re.sub(r"(`+).*?\1", "", "\n".join(visible), flags=re.DOTALL)
    inline = []
    for match in re.finditer(r"\[[^\]\n]*\]\(", text):
        parsed = _destination(text, match.end())
        if parsed is None:
            continue
        destination, end = parsed
        suffix = text[end:]
        if suffix.startswith(")") or re.match(
                r"\s+(?:\"(?:\\.|[^\"\n])*\"|'(?:\\.|[^'\n])*'|\((?:\\.|[^)\n])*\))?\s*\)", suffix):
            inline.append(destination)
    definitions = []
    for match in re.finditer(r"^\s*\[[^\]\n]+\]:\s*", text, flags=re.MULTILINE):
        parsed = _destination(text, match.end())
        if parsed is not None:
            definitions.append(parsed[0])
    return inline + definitions


def validate_skill_references(files):
    """`files` maps packaged target paths to captured bytes, never source paths."""
    for relative, payload in sorted(files.items()):
        if not relative.startswith("skills/") or not relative.endswith(".md"):
            continue
        try:
            text = payload.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise DataError(f"invalid UTF-8 skill resource: {relative}") from exc
        for destination in _destinations(text):
            destination = destination.removeprefix("<").removesuffix(">")
            destination = re.sub(r"\\([" + re.escape(string.punctuation) + r"])", r"\1", destination)
            if destination.startswith(("/", "#")) or re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", destination):
                continue
            try:
                path = unquote(urlsplit(destination).path)
            except ValueError as exc:
                raise DataError(f"invalid resource reference in {relative}: {destination}") from exc
            if not path:
                continue
            target = posixpath.normpath(posixpath.join(posixpath.dirname(relative), path))
            io.relative_path(target, what=f"resource reference in {relative}")
            if target not in files:
                raise DataError(f"missing or unregistered resource referenced by {relative}: {target}")
