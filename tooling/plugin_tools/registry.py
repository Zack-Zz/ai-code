"""A path-only catalog and each plugin's identity/resource contract."""

from dataclasses import dataclass, field
from pathlib import Path
import re
import stat

from . import io
from .io import DataError
from .references import validate_skill_references

HOSTS = ("codex", "zcode")
ID_PATTERN = re.compile(r"[a-z0-9][a-z0-9-]{0,63}")
VERSION_PATTERN = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+")
INTERFACE_FIELDS = {"display_name", "short_description", "brand_color", "default_prompt",
                    "allow_implicit_invocation"}
REQUIRED_PRODUCT_FIELDS = {"schema_version", "product_id", "display_name", "version",
                           "repository", "license", "hosts", "resources"}
OPTIONAL_PRODUCT_FIELDS = {"core_skills", "shared_skills", "profiles", "generated_agents"}


@dataclass
class PluginSpec:
    root: Path
    catalog_path: str
    manifest: dict
    files: dict = field(default_factory=dict)  # target -> source relative path
    inputs: dict = field(default_factory=dict)  # source relative path -> captured bytes
    adapters: dict = field(default_factory=dict)
    interfaces: dict = field(default_factory=dict)
    boundary_root: Path | None = None

    @property
    def product_id(self):
        return self.manifest["product_id"]

    @property
    def version(self):
        return self.manifest["version"]

    @property
    def hosts(self):
        return self.manifest["hosts"]

    @property
    def all_skills(self):
        return self.manifest.get("core_skills", []) + self.manifest.get("shared_skills", [])

    @property
    def profiles(self):
        return self.manifest.get("profiles", [])

    @property
    def source_tree_hash(self):
        return io.sha256(io.canonical_json({
            "product_id": self.product_id, "version": self.version,
            "files": {target: io.sha256(self.inputs[source]) for target, source in sorted(self.files.items())},
            "inputs": {relative: io.sha256(payload) for relative, payload in sorted(self.inputs.items())},
        }))


def _string_list(value, field_name, *, pattern=None, nonempty=False):
    if (not isinstance(value, list) or not all(isinstance(item, str) and item for item in value) or
            len(set(value)) != len(value) or (nonempty and not value)):
        raise DataError(f"{field_name} must be a {'nonempty ' if nonempty else ''}list of unique strings")
    if pattern and any(not pattern.fullmatch(item) for item in value):
        raise DataError(f"invalid {field_name} entry")
    return value


def validate_interface(entry, *, what):
    if not isinstance(entry, dict) or set(entry) != INTERFACE_FIELDS:
        raise DataError(f"{what} must have exactly {sorted(INTERFACE_FIELDS)}")
    for key in INTERFACE_FIELDS - {"allow_implicit_invocation"}:
        if not isinstance(entry[key], str) or not entry[key].strip():
            raise DataError(f"{what}.{key} must be a nonempty string")
    if not re.fullmatch(r"#[0-9A-Fa-f]{6}", entry["brand_color"]):
        raise DataError(f"{what}.brand_color must be #RRGGBB")
    if not isinstance(entry["allow_implicit_invocation"], bool):
        raise DataError(f"{what}.allow_implicit_invocation must be a boolean")


def _skill_metadata(payload, name):
    try:
        lines = payload.decode("utf-8").splitlines()
    except UnicodeDecodeError as exc:
        raise DataError(f"invalid UTF-8 skill: {name}") from exc
    if not lines or lines[0].strip() != "---":
        raise DataError(f"skill {name} requires frontmatter")
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        raise DataError(f"skill {name} has unterminated frontmatter")
    names = [line.split(":", 1)[1].strip().strip('\"\'')
             for line in lines[1:end] if line.startswith("name:")]
    descriptions = [line.split(":", 1)[1].strip() for line in lines[1:end] if line.startswith("description:")]
    if names != [name] or len(descriptions) != 1 or not descriptions[0]:
        raise DataError(f"skill {name} frontmatter name/description is invalid")


def _load_json_input(spec, relative):
    data, payload = io.read_json(spec.root, relative, boundary_root=spec.boundary_root)
    spec.inputs[relative] = payload
    return data


def _generated_targets(spec):
    targets = {"artifact.json"}
    for host in spec.hosts:
        targets.add("plugin.json" if host == "codex" else ".zcode-plugin/plugin.json")
    if "codex" in spec.hosts:
        targets.update(f"skills/{name}/agents/openai.yaml" for name in spec.all_skills)
    targets.update(agent["target"] for agent in spec.manifest.get("generated_agents", []))
    return targets


def load_product(root, *, catalog_path="", boundary_root=None):
    root = Path(root)
    manifest, raw = io.read_json(root, "product.json", boundary_root=boundary_root)
    if not isinstance(manifest, dict):
        raise DataError("product.json must be an object")
    if missing := REQUIRED_PRODUCT_FIELDS - set(manifest):
        raise DataError(f"product.json missing fields: {sorted(missing)}")
    if unknown := set(manifest) - REQUIRED_PRODUCT_FIELDS - OPTIONAL_PRODUCT_FIELDS:
        raise DataError(f"product.json unknown fields: {sorted(unknown)}")
    if type(manifest["schema_version"]) is not int or manifest["schema_version"] != 1:
        raise DataError("product schema_version must be integer 1")
    for key, pattern in (("product_id", ID_PATTERN), ("version", VERSION_PATTERN)):
        if not isinstance(manifest[key], str) or not pattern.fullmatch(manifest[key]):
            raise DataError(f"invalid product {key}")
    for key in ("display_name", "repository", "license"):
        if not isinstance(manifest[key], str) or not manifest[key].strip():
            raise DataError(f"product {key} must be a nonempty string")
    hosts = _string_list(manifest["hosts"], "hosts", nonempty=True)
    if set(hosts) - set(HOSTS):
        raise DataError("hosts contains an unsupported host")
    core = _string_list(manifest.get("core_skills", []), "core_skills", pattern=ID_PATTERN)
    shared = _string_list(manifest.get("shared_skills", []), "shared_skills", pattern=ID_PATTERN)
    if set(core) & set(shared):
        raise DataError("duplicate skill across core_skills/shared_skills")
    _string_list(manifest.get("profiles", []), "profiles", pattern=ID_PATTERN)
    agents = manifest.get("generated_agents", [])
    if not isinstance(agents, list):
        raise DataError("generated_agents must be a list")
    for agent in agents:
        if not isinstance(agent, dict) or set(agent) != {"host", "template", "body", "target"}:
            raise DataError("generated_agents entries require host/template/body/target")
        if agent["host"] != "zcode" or agent["host"] not in hosts:
            raise DataError("generated_agents supports declared zcode host only")
        for key in ("template", "body", "target"):
            io.relative_path(agent[key], what=f"generated_agents.{key}")
        if not agent["target"].startswith("agents/") or not agent["target"].endswith(".md"):
            raise DataError("generated agent target must be agents/*.md")
    spec = PluginSpec(root, catalog_path, manifest, inputs={"product.json": raw}, boundary_root=boundary_root)
    generated = _generated_targets(spec)
    if len(generated) != 1 + len(hosts) + (len(spec.all_skills) if "codex" in hosts else 0) + len(agents):
        raise DataError("generated target collision")
    for target in generated:
        if any(target.startswith(other + "/") for other in generated if other != target):
            raise DataError(f"generated target path overlap: {target}")

    def register(source, target):
        for relative in (source, target):
            io.relative_path(relative, what="resource path")
            if "__pycache__" in relative.split("/") or relative.endswith((".pyc", ".pyo")):
                raise DataError(f"cache artifacts cannot be registered: {relative}")
        if target in spec.files or target in generated:
            raise DataError(f"resource target collision: {target}")
        if any(target.startswith(existing + "/") or existing.startswith(target + "/")
               for existing in (*spec.files, *generated)):
            raise DataError(f"resource target path overlap: {target}")
        payload = io.read_file(root, source, boundary_root=boundary_root)
        if source in spec.inputs and spec.inputs[source] != payload:
            raise DataError(f"source input changed while loading: {source}")
        spec.inputs[source] = payload
        spec.files[target] = source

    for name in spec.all_skills:
        relative = f"skills/{name}/SKILL.md"
        register(relative, relative)
        _skill_metadata(spec.inputs[relative], name)
    resources = manifest["resources"]
    if not isinstance(resources, list):
        raise DataError("resources must be a list")
    for entry in resources:
        if not isinstance(entry, dict) or set(entry) != {"source", "target", "include"}:
            raise DataError("resources entries require source/target/include")
        source = io.relative_path(entry["source"], what="resource source path")
        target = io.relative_path(entry["target"], what="resource target path")
        include = _string_list(entry["include"], "resource include")
        candidate = root / source
        try:
            is_directory = stat.S_ISDIR(candidate.lstat().st_mode)
        except OSError as exc:
            raise DataError(f"resource path missing: {candidate}") from exc
        if is_directory:
            io.member(root, source, directory=True, boundary_root=boundary_root)
            if not include:
                raise DataError("directory resource requires explicit include list")
            for relative in include:
                io.relative_path(relative, what="resource include path")
                if re.search(r"[*?\[\]]", relative):
                    raise DataError("resource include cannot contain wildcards")
                register(f"{source}/{relative}", f"{target}/{relative}")
        else:
            if include:
                raise DataError("file resource requires empty include list")
            register(source, target)
    validate_skill_references({target: spec.inputs[source] for target, source in spec.files.items()})
    for host in hosts:
        adapter = _load_json_input(spec, f"adapters/{host}/plugin.json")
        if (not isinstance(adapter, dict) or not isinstance(adapter.get("description"), str) or
                not adapter["description"].strip()):
            raise DataError(f"{host} plugin adapter requires description")
        spec.adapters[host] = adapter
    if "codex" in hosts and spec.all_skills:
        interfaces = _load_json_input(spec, "adapters/codex/interfaces.json")
        if (not isinstance(interfaces, dict) or set(interfaces) != {"schema_version", "skills"} or
                type(interfaces["schema_version"]) is not int or interfaces["schema_version"] != 1 or
                not isinstance(interfaces["skills"], dict) or set(interfaces["skills"]) != set(spec.all_skills)):
            raise DataError("interfaces.json must declare exactly the product skills")
        for name, entry in interfaces["skills"].items():
            validate_interface(entry, what=f"interface {name}")
        spec.interfaces = interfaces["skills"]
    for agent in agents:
        for relative in (agent["template"], agent["body"]):
            payload = io.read_file(root, relative, boundary_root=boundary_root)
            if relative in spec.inputs and spec.inputs[relative] != payload:
                raise DataError(f"source input changed while loading: {relative}")
            spec.inputs[relative] = payload
        lines = spec.inputs[agent["template"]].decode("utf-8").splitlines()
        if not lines or lines[0].strip() != "---" or not any(line.strip() == "---" for line in lines[1:]):
            raise DataError("generated agent template requires closed frontmatter")
    return spec


def load_catalog(root):
    root = Path(root).resolve()
    catalog, _ = io.read_json(root, "catalog.json")
    if (not isinstance(catalog, dict) or set(catalog) != {"schema_version", "plugins"} or
            type(catalog["schema_version"]) is not int or catalog["schema_version"] != 1 or
            not isinstance(catalog["plugins"], list) or not catalog["plugins"]):
        raise DataError("catalog.json requires schema_version 1 and nonempty plugins list")
    paths = []
    for entry in catalog["plugins"]:
        if not isinstance(entry, dict) or set(entry) != {"path"}:
            raise DataError("catalog plugin entries must contain path only")
        relative = io.relative_path(entry["path"], what="catalog plugin path")
        if not re.fullmatch(r"plugins/[a-z0-9][a-z0-9-]{0,63}", relative):
            raise DataError(f"catalog plugin path must be plugins/<slug>: {relative}")
        if any(relative == path or relative.startswith(path + "/") or path.startswith(relative + "/") for path in paths):
            raise DataError(f"duplicate or overlapping catalog plugin path: {relative}")
        paths.append(relative)
    specs = []
    identities = set()
    for relative in paths:
        path = io.member(root, relative, directory=True)
        spec = load_product(path, catalog_path=relative, boundary_root=root)
        if spec.product_id in identities:
            raise DataError(f"duplicate product_id: {spec.product_id}")
        identities.add(spec.product_id)
        specs.append(spec)
    return sorted(specs, key=lambda spec: spec.product_id)


def select_plugins(specs, product_id=None):
    if product_id is None:
        return list(specs)
    selected = [spec for spec in specs if spec.product_id == product_id]
    if not selected:
        raise DataError(f"unknown plugin: {product_id}")
    return selected
