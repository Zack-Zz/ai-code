"""Package verification: closure, identity, versions and marketplace resolution."""

from __future__ import annotations

import os
import stat
import re
from pathlib import Path

from . import io as wio
from . import product as wproduct
from .io import DataError

PRODUCT_ID = "ai-code-workflow"
SKILLS = ("workflow", "tdd", "debugging", "review", "verification", "review-results")
REQUIRED_SHARED = {
    *(f"skills/{name}/SKILL.md" for name in SKILLS),
    "skills/review/references/reviewer-contract.md", "LICENSE", "NOTICE",
    "LICENSES/backend-engineering-lite.txt", "tools/workflow_tool.py",
    *(f"policies/{mode}.json" for mode in ("collaborative", "continuous")),
    *(f"schemas/{name}.schema.json" for name in ("product", "policy", "task", "evidence")),
    *(f"templates/{name}.json" for name in ("task", "evidence")),
    *(f"tools/workflow/{name}.py" for name in
      ("__init__", "product", "policy", "state", "build", "package_check", "owned_files", "cli", "io")),
}


def marketplace_path(package_root: Path, host: str) -> Path:
    root = Path(package_root).parent
    return root / (".agents/plugins/marketplace.json" if host == "codex" else "marketplace.json")


def is_passive_cache(relative: str, registered) -> bool:
    """Only recognize tagged bytecode beside a known source, never arbitrary code.

    Cache classification is not an authenticity guarantee for Python bytecode.
    Source/ZIP builds exclude all caches; installed packages should be trusted.
    """
    path = Path(relative)
    match = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_]*)\.cpython-[0-9]+(?:\.opt-[0-9]+)?\.pyc", path.name)
    if path.parent.name != "__pycache__" or not match:
        return False
    source = path.parent.parent / (match.group(1) + ".py")
    return source.as_posix() in registered


def _artifact_checks(package_root: Path):
    artifact = wio.load_json(wio.resolve_member(package_root, "artifact.json"))
    required = {"schema_version", "product_id", "version", "host", "profiles",
                "source_revision", "working_tree_dirty", "source_tree_hash",
                "files", "content_hash"}
    if not isinstance(artifact, dict) or set(artifact) != required:
        raise DataError("artifact.json fields do not match its contract")
    if not wio.is_strict_int(artifact["schema_version"]) or artifact["schema_version"] != 1:
        raise DataError("artifact.json schema_version must be 1")
    for key in ("product_id", "version", "host"):
        if not isinstance(artifact[key], str):
            raise DataError(f"artifact {key} must be a string")
    if not wproduct.PRODUCT_ID_RE.fullmatch(artifact["product_id"]) or \
            not wproduct.VERSION_RE.fullmatch(artifact["version"]) or \
            artifact["host"] not in ("zcode", "codex"):
        raise DataError("artifact product_id/version/host format is invalid")
    if not isinstance(artifact["working_tree_dirty"], bool):
        raise DataError("artifact working_tree_dirty must be a boolean")
    revision = artifact["source_revision"]
    if revision is not None and (not isinstance(revision, str) or
                                 not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", revision)):
        raise DataError("artifact source_revision must be a Git object ID or null")
    for key in ("source_tree_hash", "content_hash"):
        if not isinstance(artifact[key], str) or not re.fullmatch(r"[0-9a-f]{64}", artifact[key]):
            raise DataError(f"artifact {key} must be SHA256 hex")
    if not isinstance(artifact["profiles"], list) or \
            not all(isinstance(profile, str) for profile in artifact["profiles"]):
        raise DataError("artifact profiles must be a list of strings")
    entries = artifact["files"]
    if not isinstance(entries, list):
        raise DataError("artifact files must be a list")
    for entry in entries:
        if not isinstance(entry, list) or len(entry) != 2:
            raise DataError("artifact files entries must be path/hash pairs")
        wio.check_relative(entry[0])
        if not isinstance(entry[1], str) or not re.fullmatch(r"[0-9a-f]{64}", entry[1]):
            raise DataError("artifact file hash must be SHA256 hex")
    return artifact


def _walk_files(root: Path):
    for path in sorted(root.rglob("*")):
        # A FIFO/socket/device can be an active unregistered member too. Use
        # lstat only: never follow a link or open a special entry to classify it.
        if not stat.S_ISDIR(path.lstat().st_mode):
            yield path


def check_package(package_root: Path, host: str) -> dict:
    """Verify a built package. Returns a report; ok=False means problems."""
    package_root = Path(package_root)
    if host not in ("zcode", "codex"):
        raise DataError(f"unknown host: {host!r}")
    if not package_root.is_dir():
        raise DataError(f"package directory does not exist: {package_root}")

    artifact = _artifact_checks(package_root)
    problems: list[str] = []
    caches: list[str] = []
    safe_files: dict[str, Path] = {}

    if artifact["product_id"] != PRODUCT_ID:
        problems.append(f"product_id {artifact['product_id']!r} != {PRODUCT_ID!r}")
    if artifact["host"] != host:
        problems.append(f"artifact host {artifact['host']!r} != requested {host!r}")
    if artifact["profiles"] != ["collaborative", "continuous"]:
        problems.append(f"unexpected profiles: {artifact['profiles']!r}")

    registered = {rel: sha for rel, sha in artifact["files"]}
    if len(registered) != len(artifact["files"]):
        problems.append("duplicate artifact file entries")
    for rel in sorted(REQUIRED_SHARED - set(registered)):
        problems.append(f"required component missing from artifact: {rel}")
    if wio.sha256_bytes(wio.canonical_json(artifact["files"])) != artifact["content_hash"]:
        problems.append("artifact content_hash does not match its file list")
    if sorted(registered) != [rel for rel, _ in artifact["files"]]:
        problems.append("artifact files list is not sorted")

    for rel, sha in artifact["files"]:
        path = package_root / rel
        wio.check_relative(rel, what="artifact file entry")
        try:
            wio.resolve_member(package_root, rel)
            info = os.lstat(path)
        except DataError as exc:
            problems.append(f"invalid registered file {rel}: {exc}")
            continue
        except FileNotFoundError:
            problems.append(f"registered file missing: {rel}")
            continue
        if not stat.S_ISREG(info.st_mode):
            problems.append(f"registered file is not a regular file: {rel}")
            continue
        if wio.sha256_file(path) != sha:
            problems.append(f"content hash mismatch: {rel}")
        safe_files[rel] = path

    try:
        wproduct.validate_skill_references(safe_files)
    except DataError as exc:
        problems.append(str(exc))

    for path in _walk_files(package_root):
        rel = path.relative_to(package_root).as_posix()
        if rel == "artifact.json" or rel in registered:
            continue
        if stat.S_ISREG(path.lstat().st_mode) and is_passive_cache(rel, registered):
            caches.append(rel)
            continue
        problems.append(f"extra active file not registered in artifact: {rel}")

    manifest_rel = ".zcode-plugin/plugin.json" if host == "zcode" else "plugin.json"
    manifest_path = package_root / manifest_rel
    if manifest_rel not in registered or not manifest_path.is_file():
        problems.append(f"host manifest missing or unregistered: {manifest_rel}")
    else:
        manifest = wio.load_json(manifest_path)
        if manifest.get("name") != artifact["product_id"]:
            problems.append(f"{manifest_rel} name {manifest.get('name')!r} != artifact product_id")
        if manifest.get("version") != artifact["version"]:
            problems.append(f"{manifest_rel} version {manifest.get('version')!r} != artifact version")

    if host == "zcode":
        if "agents/workflow-reviewer.md" not in registered:
            problems.append("zcode reviewer agent missing from artifact files")
        elif "agents/workflow-reviewer.md" in safe_files and \
                "skills/review/references/reviewer-contract.md" in safe_files:
            try:
                wproduct.parse_reviewer_meta(safe_files["agents/workflow-reviewer.md"])
            except DataError as exc:
                problems.append(str(exc))
            agent_text = (package_root / "agents" / "workflow-reviewer.md").read_text(encoding="utf-8")
            contract_rel = "skills/review/references/reviewer-contract.md"
            contract = (package_root / contract_rel).read_text(encoding="utf-8")
            if contract.rstrip() not in agent_text:
                problems.append("reviewer agent does not embed the shared reviewer contract")
    else:
        for skill in ("workflow", "tdd", "debugging", "review", "verification", "review-results"):
            rel = f"skills/{skill}/agents/openai.yaml"
            if rel not in registered:
                problems.append(f"codex skill interface metadata missing: {rel}")
            elif rel in safe_files:
                try:
                    wproduct.parse_skill_interface(safe_files[rel])
                except DataError as exc:
                    problems.append(str(exc))

    marketplace = marketplace_path(package_root, host)
    if not marketplace.is_file():
        problems.append(f"marketplace file missing next to package: {marketplace}")
    else:
        wio.resolve_member(package_root.parent, marketplace.relative_to(package_root.parent).as_posix())
        market = wio.load_json(marketplace)
        entries = market.get("plugins") or []
        entry = next((e for e in entries if e.get("name") == artifact["product_id"]), None)
        if entry is None:
            problems.append("marketplace has no entry for this package")
        else:
            if host == "codex":
                policy = entry.get("policy", {})
                if policy.get("installation") not in ("AVAILABLE", "INSTALLED_BY_DEFAULT", "NOT_AVAILABLE"):
                    problems.append("unsupported Codex marketplace installation policy")
                if policy.get("authentication") not in ("ON_INSTALL", "ON_USE"):
                    problems.append("unsupported Codex marketplace authentication policy")
            source = entry.get("source")
            source_path = source.get("path") if isinstance(source, dict) else source
            if not isinstance(source_path, str) or not source_path.startswith("./"):
                problems.append("marketplace source.path must be a ./relative path")
            else:
                resolved = (package_root.parent / source_path).resolve()
                if resolved != package_root.resolve():
                    problems.append(
                        f"marketplace source resolves to {resolved}, expected {package_root}")
            if entry.get("version") != artifact["version"]:
                problems.append(
                    f"marketplace version {entry.get('version')!r} != artifact version")

    return {
        "ok": not problems,
        "product_id": artifact["product_id"],
        "version": artifact["version"],
        "content_hash": artifact["content_hash"],
        "files_checked": len(registered),
        "problems": problems,
        "caches": caches,
    }
