"""Source-bound release metadata, listing assets and factual host evidence."""

from dataclasses import dataclass, field
from pathlib import Path
import math
import re
import subprocess
import xml.etree.ElementTree as ET

from .. import io
from ..io import DataError
from ..rendering import file_hashes, manifest_path, package_files
from .images import validate_png

HASH = re.compile(r"[0-9a-f]{64}")
CATEGORIES = {"Developer Tools", "Productivity"}
EVIDENCE_FIELDS = {"schema_version", "status", "host", "version", "source_tree_hash", "package_content_hash",
                   "host_version", "summary", "artifacts"}


@dataclass
class Capture:
    config: dict
    inputs: dict = field(default_factory=dict)
    pending: list = field(default_factory=list)
    accepted: dict = field(default_factory=dict)
    package_hashes: dict = field(default_factory=dict)
    private_hashes: dict = field(default_factory=dict)
    proof_inputs: dict = field(default_factory=dict)

    def input_hashes(self):
        return {**{name: io.sha256(raw) for name, raw in self.inputs.items()}, **self.private_hashes}


def _read(spec, relative, captured, *, limit=32 * 1024 * 1024):
    io.relative_path(relative)
    payload = io.read_file(spec.root, relative, limit=limit, boundary_root=spec.boundary_root)
    if relative in spec.inputs and spec.inputs[relative] != payload:
        raise DataError(f"source input changed before release capture: {relative}")
    if relative in captured and captured[relative] != payload:
        raise DataError(f"release input changed during capture: {relative}")
    captured[relative] = payload
    return payload


def _text(spec, relative, captured):
    payload = _read(spec, relative, captured, limit=1024 * 1024)
    try:
        text = payload.decode("utf-8")
    except UnicodeError as exc:
        raise DataError(f"release document is not UTF-8: {relative}") from exc
    if not relative.endswith(".md") or not text.strip():
        raise DataError(f"release document must be nonempty Markdown: {relative}")


def _icon(relative, payload):
    if len(payload) > 5 * 1024 * 1024:
        raise DataError(f"icon exceeds 5 MiB: {relative}")
    if relative.lower().endswith(".svg"):
        try:
            text = payload.decode("utf-8")
            if "<!DOCTYPE" in text.upper() or "<!ENTITY" in text.upper():
                raise DataError(f"unsafe SVG entity declaration: {relative}")
            root = ET.fromstring(text)
            if root.tag.rsplit("}", 1)[-1] != "svg":
                raise DataError(f"icon must be SVG: {relative}")
            view = [float(value) for value in re.split(r"[\s,]+", root.get("viewBox", "").strip()) if value]
            def dimension(name, fallback):
                return float(root.get(name, str(fallback)).removesuffix("px"))
            if len(view) not in (0, 4):
                raise DataError(f"invalid SVG viewBox: {relative}")
            width = dimension("width", view[2] if view else 0)
            height = dimension("height", view[3] if view else 0)
            if not all(math.isfinite(value) for value in [width, height, *view]) or \
                    width != height or width < 48 or (view and (view[2] != view[3] or view[2] <= 0)):
                raise DataError(f"SVG icon must be square and at least 48 pixels: {relative}")
            for node in root.iter():
                if node.tag.rsplit("}", 1)[-1].lower() in {"script", "foreignobject", "set", "animate", "animatemotion", "animatetransform"}:
                    raise DataError(f"unsafe SVG active content: {relative}")
                for key, value in node.attrib.items():
                    local = key.rsplit("}", 1)[-1].lower()
                    if local.startswith("on") or (local in {"href", "src"} and not value.startswith("#")):
                        raise DataError(f"unsafe SVG external reference: {relative}")
                    if _unsafe_css(value):
                        raise DataError(f"unsafe SVG style reference: {relative}")
                if node.tag.rsplit("}", 1)[-1].lower() == "style" and node.text and \
                        _unsafe_css(node.text):
                    raise DataError(f"unsafe SVG stylesheet: {relative}")
        except (ValueError, ET.ParseError, UnicodeError) as exc:
            raise DataError(f"invalid SVG icon: {relative}: {exc}") from exc
    elif relative.lower().endswith(".png"):
        validate_png(payload, relative)
    else:
        raise DataError(f"release icon must be SVG or PNG: {relative}")


def _unsafe_css(value):
    if "@import" in value.lower() or "\\" in value:
        return True
    urls = list(re.finditer(r"url\(\s*(['\"]?)(.*?)\1\s*\)", value, flags=re.I))
    return len(urls) != len(re.findall(r"url\(", value, flags=re.I)) or \
        any(not item[2].strip().startswith("#") for item in urls)


def validate_listing(spec):
    publisher = spec.manifest.get("publisher")
    if not isinstance(publisher, dict) or not publisher.get("name"):
        raise DataError("release requires a declared publisher")
    for host in spec.hosts:
        files = package_files(spec, host)
        manifest = io.parse_json(files[manifest_path(host)], what=f"{host} native manifest")
        if manifest.get("name") != spec.product_id or manifest.get("version") != spec.version or manifest.get("author") != publisher:
            raise DataError(f"{host} native identity/author differs from the release publisher")
        if host != "codex":
            continue
        if any(key in manifest for key in ("hooks", "apps", "mcpServers", "commands", "agents")):
            unsupported = [key for key in ("hooks", "apps", "mcpServers", "commands", "agents") if key in manifest]
            raise DataError(f"OpenAI skills-only submission does not support: {', '.join(unsupported)}")
        if any(name == ".mcp.json" or name == ".app.json" or name.startswith(("hooks/", "apps/")) for name in files):
            raise DataError("OpenAI skills-only submission contains unsupported hooks/apps/MCP resources")
        if not spec.all_skills:
            raise DataError("OpenAI skills-only submission requires at least one skill")
        try:
            interface = manifest["extensions"]["com.openai"]["interface"]
        except (KeyError, TypeError) as exc:
            raise DataError("portable Codex manifest requires OpenAI interface metadata") from exc
        if not isinstance(interface, dict):
            raise DataError("Codex interface metadata must be an object")
        for key, limit in (("displayName", 30), ("shortDescription", 30), ("longDescription", 4000), ("developerName", 80)):
            value = interface.get(key)
            if not isinstance(value, str) or not value.strip() or len(value) > limit:
                raise DataError(f"Codex interface {key} must have 1..{limit} characters")
        if interface["displayName"] != spec.manifest["display_name"] or interface["developerName"] != publisher["name"]:
            raise DataError("Codex listing name/developerName differs from product/publisher")
        if interface.get("category") not in CATEGORIES:
            raise DataError("Codex interface category must be a supported title")
        if "defaultPrompt" in interface:
            prompts = interface["defaultPrompt"]
            if isinstance(prompts, str):
                prompts = [prompts]
            if not isinstance(prompts, list) or len(prompts) > 3 or \
                    not all(isinstance(value, str) and value.strip() and len(value) <= 128 for value in prompts) or \
                    len(set(prompts)) != len(prompts):
                raise DataError("Codex defaultPrompt must be text or up to three unique entries of 1..128 characters")
        for key in ("logo", "composerIcon"):
            relative = interface.get(key)
            if not isinstance(relative, str) or not relative.startswith("./"):
                raise DataError(f"Codex icon {key} must use a canonical ./ path")
            relative = io.relative_path(relative[2:], what="icon path")
            if relative not in files:
                raise DataError(f"Codex icon is outside the declared package closure: {relative}")
            _icon(relative, files[relative])


def capture_release(spec, *, committed_acceptance=False):
    if type(committed_acceptance) is not bool:
        raise DataError("committed_acceptance must be boolean")
    inputs = {}
    config = io.parse_json(_read(spec, "release.json", inputs, limit=1024 * 1024), what="release.json")
    if not isinstance(config, dict) or set(config) != {"schema_version", "notes", "readmes", "acceptance"} or \
            type(config["schema_version"]) is not int or config["schema_version"] != 1:
        raise DataError("release.json requires schema_version/notes/readmes/acceptance")
    if not isinstance(config["readmes"], dict) or set(config["readmes"]) != {"en", "zh-CN"}:
        raise DataError("release readmes must declare exactly en and zh-CN")
    if not isinstance(config["acceptance"], dict) or set(config["acceptance"]) != set(spec.hosts):
        raise DataError("release acceptance must cover exactly the declared hosts")
    for relative in (config["notes"], *config["readmes"].values()):
        _text(spec, relative, inputs)
    capture = Capture(config, inputs)
    capture.package_hashes = {host: io.sha256(io.canonical_json(file_hashes(package_files(spec, host)))) for host in spec.hosts}
    if committed_acceptance:
        from .acceptance import PROOF_PATH, capture_committed, proof_at_head
        path = spec.root / PROOF_PATH
        if path.exists() or path.is_symlink() or proof_at_head(spec):
            return capture_committed(spec, capture)
    public_hashes = {io.sha256(value) for value in spec.inputs.values()} | \
        {io.sha256(inputs[relative]) for relative in ("release.json", config["notes"], *config["readmes"].values())} | \
        {io.sha256(value) for host in spec.hosts for value in package_files(spec, host).values()}
    for host, relative in sorted(config["acceptance"].items()):
        if relative is None:
            capture.pending.append(host)
            continue
        evidence = io.parse_json(_read(spec, relative, inputs, limit=1024 * 1024), what=f"{host} evidence")
        if not isinstance(evidence, dict) or set(evidence) != EVIDENCE_FIELDS or type(evidence["schema_version"]) is not int or evidence["schema_version"] != 1:
            raise DataError(f"{host} evidence has invalid fields/schema")
        if evidence["status"] not in {"unverified", "accepted"}:
            raise DataError(f"{host} evidence status must be unverified or accepted")
        for key, value in (("host", host), ("version", spec.version), ("source_tree_hash", spec.source_tree_hash),
                           ("package_content_hash", capture.package_hashes[host])):
            if evidence[key] != value:
                raise DataError(f"{host} evidence {key} does not match the current release")
        if evidence["status"] == "unverified":
            if evidence["artifacts"] != [] or evidence["host_version"] is not None:
                raise DataError(f"{host} unverified evidence must not imply host acceptance")
            capture.pending.append(host)
            continue
        if not all(isinstance(evidence[key], str) and evidence[key].strip() for key in ("host_version", "summary")) or \
                not isinstance(evidence["artifacts"], list) or not evidence["artifacts"]:
            raise DataError(f"{host} accepted evidence needs host version, summary and raw artifacts")
        seen = set()
        public_inputs = set(spec.inputs) | {"release.json", config["notes"], *config["readmes"].values()}
        for entry in evidence["artifacts"]:
            if not isinstance(entry, dict) or set(entry) != {"path", "sha256"} or not isinstance(entry["sha256"], str) or not HASH.fullmatch(entry["sha256"]):
                raise DataError(f"{host} evidence artifact requires path/SHA256")
            if entry["path"] in seen:
                raise DataError(f"{host} evidence has duplicate artifacts")
            if entry["path"] in public_inputs:
                raise DataError(f"{host} raw evidence artifact is also a public release input: {entry['path']}")
            seen.add(entry["path"])
            payload = _read(spec, entry["path"], inputs)
            if io.sha256(payload) in public_hashes:
                raise DataError(f"{host} raw evidence artifact aliases public release bytes: {entry['path']}")
            if io.sha256(payload) != entry["sha256"]:
                raise DataError(f"{host} evidence artifact bytes do not match SHA256: {entry['path']}")
        capture.accepted[host] = relative
    return capture


def recheck_inputs(spec, capture):
    for relative, expected in {**spec.inputs, **capture.inputs, **capture.proof_inputs}.items():
        if io.read_file(spec.root, relative, boundary_root=spec.boundary_root) != expected:
            raise DataError(f"source/release input changed before publication: {relative}")


def git_provenance(root, identity, version, tag=None, excluded=None):
    root = Path(root).resolve()
    def git(*arguments):
        try:
            result = subprocess.run(["git", *arguments], cwd=root, capture_output=True, text=True, timeout=10)
        except (OSError, subprocess.TimeoutExpired):
            return None
        return result.stdout.strip() if result.returncode == 0 else None
    revision = git("rev-parse", "HEAD")
    arguments = ["status", "--porcelain=v1", "-uall"]
    if excluded is not None and Path(excluded).is_relative_to(root):
        arguments.extend(["--", ".", f":(exclude,literal){Path(excluded).relative_to(root).as_posix()}"])
    worktree = git(*arguments)
    if revision is not None and worktree is None:
        raise DataError("Git status is unavailable; source cleanliness cannot be determined")
    canonical = f"{identity}/v{version}"
    if tag is not None and tag != canonical:
        raise DataError(f"release tag must be {canonical}")
    tag_commit = git("rev-parse", "--verify", f"refs/tags/{canonical}^{{commit}}")
    if tag is not None and (revision is None or tag_commit != revision):
        raise DataError("supplied release tag does not resolve to the current HEAD")
    return {"source_revision": revision, "working_tree_dirty": bool(worktree),
            "tag": canonical if tag_commit == revision and revision is not None else None,
            "tag_commit": tag_commit}
