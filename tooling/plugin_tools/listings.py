"""Opt-in host presentation, separate from plugin identity and native manifests."""

import re
import subprocess
from pathlib import Path, PurePosixPath
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
        expected_path = f"{spec.catalog_path}/{source}" if spec.catalog_path else source
        try:
            validate_icon_url(listing["icon_url"], spec.manifest["repository"], source_path=expected_path)
        except DataError:
            # A renamed product can retain an immutable historical image URL,
            # but only when its actual Git blob equals the registered image.
            validate_icon_url(listing["icon_url"], spec.manifest["repository"])
            if spec.manifest["schema_version"] != 2 or spec.boundary_root is None:
                raise
            prefix = "https://raw.githubusercontent.com/" + spec.manifest["repository"].removeprefix("https://github.com/").removesuffix(".git").rstrip("/") + "/"
            revision, path = listing["icon_url"][len(prefix):].split("/", 1)
            verified = False
            # Source snapshots used for independent checking do not contain a
            # .git directory. The trusted validator's repository may supply the
            # same content-addressed historical object without changing it.
            for git_root in dict.fromkeys((spec.boundary_root, Path(__file__).resolve().parents[2])):
                try:
                    blob = subprocess.run(["git", "show", f"{revision}:{unquote(path)}"], cwd=git_root,
                                          capture_output=True, timeout=15)
                except (OSError, subprocess.TimeoutExpired):
                    continue
                if blob.returncode == 0 and blob.stdout == spec.inputs[source]:
                    verified = True
                    break
            if not verified:
                raise DataError("historical icon URL does not match the trusted image bytes")
