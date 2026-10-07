"""product.json loading: identity, components and the exact resource whitelist."""

from __future__ import annotations

import json
import posixpath
import re
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import unquote, urlsplit

from . import io
from .io import DataError

PRODUCT_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,63}$")
VERSION_RE = re.compile(r"^[0-9]+\.[0-9]+\.[0-9]+$")
SKILL_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]*$")
WILDCARD_RE = re.compile(r"[*?\[\]]")
FRONTMATTER_LINE_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_-]*):[ \t]*(\S.*)$")
ALLOWED_META_KEYS = {"name", "description", "origin"}

_PRODUCT_KEYS = {
    "schema_version", "product_id", "display_name", "version", "repository",
    "license", "core_skills", "shared_skills", "resources",
}
_PACKAGING_KEYS = {"hosts", "profiles", "generated_agents"}
_CACHE_PARTS = {"__pycache__"}
_INTERFACE_FIELDS = {"display_name", "short_description", "brand_color", "default_prompt",
                     "allow_implicit_invocation"}


def validate_interface_entry(entry, *, what="skill interface") -> dict:
    """Validate the closed metadata contract, not arbitrary host YAML."""
    if not isinstance(entry, dict) or set(entry) != _INTERFACE_FIELDS:
        raise DataError(f"{what} must have exactly {sorted(_INTERFACE_FIELDS)}")
    for key in _INTERFACE_FIELDS - {"allow_implicit_invocation"}:
        if not isinstance(entry[key], str) or not entry[key].strip():
            raise DataError(f"{what}.{key} must be a non-empty string")
    if not re.fullmatch(r"#[0-9A-Fa-f]{6}", entry["brand_color"]):
        raise DataError(f"{what}.brand_color must be a #RRGGBB color")
    if not isinstance(entry["allow_implicit_invocation"], bool):
        raise DataError(f"{what}.allow_implicit_invocation must be a boolean")
    return entry


def load_interfaces(root: Path, skills) -> dict:
    path = io.resolve_member(root, "adapters/codex/interfaces.json")
    data = io.load_json(path)
    if not isinstance(data, dict) or set(data) != {"schema_version", "skills"}:
        raise DataError("interfaces.json must have exactly schema_version/skills")
    if not io.is_strict_int(data["schema_version"]) or data["schema_version"] != 1:
        raise DataError("interfaces.json schema_version must be the integer 1")
    entries = data["skills"]
    if not isinstance(entries, dict) or set(entries) != set(skills):
        raise DataError("interfaces.json skills must match the product skills")
    for name, entry in entries.items():
        validate_interface_entry(entry, what=f"interfaces.json skills.{name}")
    return data


def parse_skill_interface(path: Path) -> dict:
    """Read the emitted two-section format with JSON-quoted YAML scalars.

    This deliberately accepts the project's fixed generated dialect rather
    than adding a general YAML parser or accepting executable YAML tags.
    """
    sections = {}
    section = None
    try:
        lines = Path(path).read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as exc:
        raise DataError(f"cannot read interface {path}: {exc}") from exc
    for line in lines:
        if not line.strip():
            continue
        if line in ("interface:", "policy:"):
            section = line[:-1]
            if section in sections:
                raise DataError(f"duplicate interface section {section}: {path}")
            sections[section] = {}
            continue
        match = re.fullmatch(r"  ([a-z_]+): (.+)", line)
        if section is None or not match:
            raise DataError(f"invalid generated interface structure: {path}")
        key, value = match.groups()
        if key in sections[section]:
            raise DataError(f"duplicate interface field {key}: {path}")
        try:
            sections[section][key] = json.loads(value)
        except (ValueError, TypeError) as exc:
            raise DataError(f"invalid interface scalar {key}: {path}") from exc
    if set(sections) != {"interface", "policy"} or \
            set(sections["interface"]) != _INTERFACE_FIELDS - {"allow_implicit_invocation"} or \
            set(sections["policy"]) != {"allow_implicit_invocation"}:
        raise DataError(f"interface sections/fields do not match their contract: {path}")
    return validate_interface_entry(dict(sections["interface"], **sections["policy"]), what=str(path))


def parse_reviewer_meta(path: Path) -> dict:
    """Validate the native reviewer template's limited frontmatter format."""
    try:
        lines = Path(path).read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as exc:
        raise DataError(f"cannot read reviewer {path}: {exc}") from exc
    if not lines or lines[0].strip() != "---":
        raise DataError(f"reviewer must start with frontmatter: {path}")
    meta = {}
    ended = False
    for line in lines[1:]:
        if line.strip() == "---":
            ended = True
            break
        match = FRONTMATTER_LINE_RE.fullmatch(line)
        if not match or match[1] in meta:
            raise DataError(f"invalid or duplicate reviewer frontmatter: {path}")
        key, value = match.groups()
        value = value.strip()
        if key in ("tools", "maxTurns") or value.startswith('"'):
            try:
                value = json.loads(value)
            except (ValueError, TypeError) as exc:
                raise DataError(f"invalid reviewer field {key}: {path}") from exc
        meta[key] = value
    required = {"name", "description", "model", "tools", "maxTurns"}
    if not ended or set(meta) != required:
        raise DataError(f"reviewer frontmatter fields do not match their contract: {path}")
    if meta["name"] != "workflow-reviewer" or not isinstance(meta["description"], str) or \
            not meta["description"].strip() or meta["model"] != "inherit":
        raise DataError(f"reviewer name/description/model contract is invalid: {path}")
    tools = meta["tools"]
    if not isinstance(tools, list) or len(tools) != 3 or \
            not all(isinstance(tool, str) for tool in tools) or \
            set(tools) != {"Read", "Grep", "Glob"}:
        raise DataError(f"reviewer tools must be only Read/Grep/Glob: {path}")
    if not io.is_strict_int(meta["maxTurns"]) or meta["maxTurns"] != 12:
        raise DataError(f"reviewer maxTurns must be the integer 12: {path}")
    return meta


def validate_adapters(root: Path, skills) -> dict:
    interfaces = load_interfaces(root, skills)
    parse_reviewer_meta(io.resolve_member(root, "adapters/zcode/agents/workflow-reviewer.md"))
    return interfaces


def _markdown_destinations(text: str):
    # Examples inside comments, fences and inline code are not live resource
    # references. Absolute project links and plugin-root placeholders are
    # runtime instructions; only relative Markdown destinations are packaged.
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
    inline = re.findall(r"\[[^\]\n]*\]\((<[^>\n]+>|[^)\s]+)(?:\s+['\"][^\n]*?['\"])?\)", text)
    definitions = re.findall(r"^\s*\[[^\]\n]+\]:\s*(<[^>\n]+>|\S+)", text, flags=re.MULTILINE)
    return inline + definitions


def validate_skill_references(files: dict[str, Path]) -> None:
    """Resolve local skill links against packaged target paths and whitelist."""
    for relative, source in sorted(files.items()):
        if not relative.startswith("skills/") or not relative.endswith(".md"):
            continue
        if relative.endswith("/SKILL.md"):
            meta = parse_skill_meta(source)
            if meta["name"] != relative.split("/")[-2]:
                raise DataError(f"skill frontmatter name does not match packaged path: {relative}")
        try:
            text = source.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as exc:
            raise DataError(f"cannot read resource {relative}: {exc}") from exc
        for destination in _markdown_destinations(text):
            destination = destination.removeprefix("<").removesuffix(">")
            if destination.startswith(("/", "#")) or \
                    re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", destination):
                continue
            try:
                path = unquote(urlsplit(destination).path)
            except ValueError as exc:
                raise DataError(f"invalid resource reference in {relative}: {destination}") from exc
            if not path:
                continue
            target = posixpath.normpath(posixpath.join(posixpath.dirname(relative), path))
            io.check_relative(target, what=f"resource reference in {relative}")
            if target not in files:
                raise DataError(f"missing or unregistered resource referenced by {relative}: {target}")


@dataclass
class ProductSpec:
    root: Path
    product_id: str
    display_name: str
    version: str
    repository: str
    license: str
    core_skills: list
    shared_skills: list
    files: list = field(default_factory=list)  # [(source_abs, target_rel)] sorted by target
    manifest_bytes: bytes = field(default=b"", repr=False)

    @property
    def all_skills(self):
        return list(self.core_skills) + list(self.shared_skills)

    def targets(self):
        return [target for _, target in self.files]


def parse_skill_meta(path: Path) -> dict:
    """Parse the first frontmatter block: single-line name/description/origin."""
    try:
        text = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        raise DataError(f"cannot read skill file {path}: {exc}") from exc
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise DataError(f"skill file must start with a frontmatter block: {path}")
    meta = {}
    ended = False
    for line in lines[1:]:
        if line.strip() == "---":
            ended = True
            break
        match = FRONTMATTER_LINE_RE.match(line)
        if not match:
            raise DataError(
                f"skill frontmatter allows only single-line fields (got {line!r}): {path}")
        key, value = match.group(1), match.group(2).strip()
        if key not in ALLOWED_META_KEYS:
            raise DataError(f"unknown skill frontmatter key {key!r}: {path}")
        if key in meta:
            raise DataError(f"duplicate skill frontmatter key {key!r}: {path}")
        meta[key] = value
    if not ended:
        raise DataError(f"unterminated skill frontmatter: {path}")
    for required in ("name", "description"):
        if required not in meta or not meta[required]:
            raise DataError(f"skill frontmatter missing {required!r}: {path}")
    return meta


def _validate_rel(rel, what):
    return io.check_relative(rel, what=what)


def _validate_skill_list(value, field_name):
    if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
        raise DataError(f"{field_name} must be a list of strings")
    for name in value:
        if not SKILL_NAME_RE.match(name):
            raise DataError(f"invalid skill name {name!r} in {field_name}")
    if len(set(value)) != len(value):
        raise DataError(f"{field_name} contains duplicate entries")
    return list(value)


def _validate_resource_entry(entry, index):
    if not isinstance(entry, dict):
        raise DataError(f"resources[{index}] must be an object")
    if set(entry) != {"source", "target", "include"}:
        raise DataError(
            f"resources[{index}] must have exactly source/target/include keys")
    source = _validate_rel(entry["source"], f"resources[{index}].source")
    target = _validate_rel(entry["target"], f"resources[{index}].target")
    include = entry["include"]
    if not isinstance(include, list) or not all(isinstance(v, str) for v in include):
        raise DataError(f"resources[{index}].include must be a list of strings")
    return source, target, include


def _validate_packaging_metadata(data, root: Path) -> None:
    """Keep the catalog's declarative packaging consistent with this workflow.

    These restrictions belong to this plugin only. Other catalog plugins do
    not inherit the workflow profiles or reviewer composition.
    """
    if "hosts" in data:
        hosts = data["hosts"]
        if not isinstance(hosts, list) or len(hosts) != 2 or \
                not all(isinstance(host, str) for host in hosts) or \
                set(hosts) != {"zcode", "codex"}:
            raise DataError("workflow hosts must declare zcode and codex exactly once")
    if "profiles" in data and data["profiles"] != ["collaborative", "continuous"]:
        raise DataError("workflow profiles must be collaborative and continuous")
    if "generated_agents" in data:
        expected = [{
            "host": "zcode",
            "template": "adapters/zcode/agents/workflow-reviewer.md",
            "body": "skills/review/references/reviewer-contract.md",
            "target": "agents/workflow-reviewer.md",
        }]
        if data["generated_agents"] != expected:
            raise DataError("workflow generated_agents must declare the shared reviewer contract")
        for field in ("template", "body"):
            io.resolve_member(root, expected[0][field])


def load_product(root: Path) -> ProductSpec:
    """Load and fully validate product.json; never writes anything."""
    root = Path(root)
    if not root.is_dir():
        raise DataError(f"source root is not a directory: {root}")
    data, manifest_bytes = io.read_json_snapshot(root / "product.json", root=root)
    if not isinstance(data, dict):
        raise DataError("product.json must contain a JSON object")
    unknown = set(data) - (_PRODUCT_KEYS | _PACKAGING_KEYS)
    if unknown:
        raise DataError(f"unknown product field(s): {sorted(unknown)}")
    missing = _PRODUCT_KEYS - set(data)
    if missing:
        raise DataError(f"missing product field(s): {sorted(missing)}")

    if not io.is_strict_int(data["schema_version"]) or data["schema_version"] != 1:
        raise DataError("product schema_version must be the integer 1")
    _validate_packaging_metadata(data, root)
    product_id = data["product_id"]
    if not isinstance(product_id, str) or not PRODUCT_ID_RE.fullmatch(product_id):
        raise DataError(f"invalid product_id: {product_id!r}")
    display_name = data["display_name"]
    if not isinstance(display_name, str) or not display_name:
        raise DataError("display_name must be a non-empty string")
    version = data["version"]
    if not isinstance(version, str) or not VERSION_RE.fullmatch(version):
        raise DataError(f"invalid version (expected X.Y.Z): {version!r}")
    for key in ("repository", "license"):
        if not isinstance(data[key], str) or not data[key]:
            raise DataError(f"{key} must be a non-empty string")

    core = _validate_skill_list(data["core_skills"], "core_skills")
    if not core:
        raise DataError("core_skills must not be empty")
    shared = _validate_skill_list(data["shared_skills"], "shared_skills")
    overlap = set(core) & set(shared)
    if overlap:
        raise DataError(
            f"duplicate skill(s) between core_skills and shared_skills: {sorted(overlap)}")
    if not isinstance(data["resources"], list):
        raise DataError("resources must be a list of resource objects")

    spec = ProductSpec(
        root=root, product_id=product_id, display_name=display_name,
        version=version, repository=data["repository"], license=data["license"],
        core_skills=core, shared_skills=shared,
        manifest_bytes=manifest_bytes,
    )

    resolved = {}  # target_rel -> source_abs

    def register(source_abs: Path, target_rel: str):
        for relative in (source_abs.relative_to(root).as_posix(), target_rel):
            if _CACHE_PARTS.intersection(relative.split("/")) or relative.endswith(".pyc"):
                raise DataError(f"cache artifacts cannot be registered: {relative!r}")
        if target_rel in resolved:
            raise DataError(f"resource mapping conflict on target: {target_rel}")
        resolved[target_rel] = source_abs

    # Skill components: exactly skills/<name>/SKILL.md per declared skill.
    for name in spec.all_skills:
        rel = f"skills/{name}/SKILL.md"
        source = io.resolve_member(root, rel, must_exist=True)
        meta = parse_skill_meta(source)
        if meta["name"] != name:
            raise DataError(
                f"skill frontmatter name {meta['name']!r} does not match directory {name!r}")
        register(source, rel)

    for index, entry in enumerate(data["resources"]):
        source_rel, target_root, include = _validate_resource_entry(entry, index)
        source_abs = io.resolve_member(
            root, source_rel, must_exist=True, allow_directory=True)
        if source_abs.is_file():
            if include:
                raise DataError(
                    f"resources[{index}]: file source requires include == []")
            register(source_abs, io.check_relative(target_root))
        elif source_abs.is_dir():
            if not include:
                raise DataError(
                    f"resources[{index}]: directory source requires an explicit include list")
            for item in include:
                item_rel = io.check_relative(item, what=f"resources[{index}].include entry")
                if WILDCARD_RE.search(item_rel):
                    raise DataError(
                        f"wildcards are not allowed in include lists: {item_rel!r}")
                if any(part in _CACHE_PARTS for part in item_rel.split("/")) or item_rel.endswith(".pyc"):
                    raise DataError(f"cache artifacts cannot be registered: {item_rel!r}")
                member = io.resolve_member(source_abs, item_rel, must_exist=True)
                target = io.check_relative(
                    f"{target_root.rstrip('/')}/{item_rel}" if target_root else item_rel,
                    what=f"resources[{index}] target")
                register(member, target)
        else:
            raise DataError(f"resources[{index}].source is neither file nor directory: {source_abs}")

    spec.files = sorted(
        ((source, target) for target, source in resolved.items()),
        key=lambda pair: pair[1],
    )
    validate_skill_references({target: source for source, target in spec.files})
    return spec
