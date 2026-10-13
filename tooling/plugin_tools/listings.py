"""Opt-in host presentation, separate from plugin identity and native manifests."""

import re
from pathlib import PurePosixPath
from urllib.parse import quote, unquote

from . import io
from .io import DataError


def validate_icon_url(value, repository, *, source_path=None):
    if not isinstance(value, str) or len(value) > 2048 or any(character.isspace() for character in value):
        raise DataError("host listing icon_url must be an immutable GitHub raw HTTPS URL")
    if not isinstance(repository, str):
        raise DataError("host listing icon_url requires a GitHub repository")
    repository = repository.rstrip("/").removesuffix(".git")
    match = re.fullmatch(r"https://github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)", repository)
    if match is None or any(part in {".", ".."} for part in match[1].split("/")):
        raise DataError("host listing icon_url requires a canonical GitHub repository")
    prefix = f"https://raw.githubusercontent.com/{match[1]}/"
    source = re.fullmatch(re.escape(prefix) + r"[0-9a-fA-F]{40}/(.+)", value)
    if source is None:
        raise DataError("host listing icon_url must pin this repository with a full Git SHA")
    if source_path is not None:
        if source[1] != quote(source_path, safe="/"):
            raise DataError("host listing icon_url differs from its registered resource source")
    else:
        # Public records have no resource map; frozen-source verification
        # binds the exact URL to the declared resource rather than trusting it.
        path = io.relative_path(unquote(source[1]), what="host listing icon_url path")
        if source[1] != quote(path, safe="/"):
            raise DataError("host listing icon_url path must use canonical URL encoding")
    if PurePosixPath(source_path or source[1]).suffix.lower() not in {".png", ".svg"}:
        raise DataError("host listing icon_url must identify a PNG/SVG resource")


def validate_host_listings(spec):
    listings = spec.manifest.get("host_listings", {})
    if not isinstance(listings, dict) or set(listings) - {"claude", "zcode"}:
        raise DataError("host_listings must be an object with only claude/zcode metadata")
    if set(listings) - set(spec.hosts):
        raise DataError("host_listings must only name declared hosts")
    for host, listing in listings.items():
        if host == "claude":
            if not isinstance(listing, dict) or listing:
                raise DataError("host_listings.claude must be an empty object")
            continue
        if not isinstance(listing, dict) or set(listing) != {"icon_path", "icon_url"}:
            raise DataError("host_listings.zcode requires exactly icon_path/icon_url")
        target = io.relative_path(listing["icon_path"], what="host_listings.zcode.icon_path")
        source = spec.files.get(target)
        if source is None or PurePosixPath(target).suffix.lower() not in {".png", ".svg"} or \
                PurePosixPath(source).suffix.lower() not in {".png", ".svg"}:
            raise DataError("host_listings.zcode.icon_path must name a registered PNG/SVG resource")
        validate_icon_url(listing["icon_url"], spec.manifest["repository"],
                          source_path=f"{spec.catalog_path}/{source}" if spec.catalog_path else source)
