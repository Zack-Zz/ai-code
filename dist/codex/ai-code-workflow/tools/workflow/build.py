"""Reproducible package builds for both hosts.

Deterministic rules: every generated JSON uses fixed key order and encoding;
ZIP entries use a fixed timestamp, permission bits and sort order; build time
lives only in the returned report, never in reproducible content.
"""

from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import tempfile
import zipfile
from pathlib import Path

from . import io as wio
from . import policy as wpolicy
from . import package_check as wpackage
from . import product as wproduct
from .io import DataError

HOSTS = ("zcode", "codex")
ZIP_EPOCH = (1980, 1, 1, 0, 0, 0)


def _dump_json(obj) -> bytes:
    return (json.dumps(obj, indent=2, sort_keys=True, ensure_ascii=True) + "\n").encode("utf-8")


def _git_state(source_root: Path):
    def git(*args):
        try:
            result = subprocess.run(["git", *args], cwd=str(source_root),
                                    capture_output=True, text=True, timeout=10)
        except (OSError, subprocess.TimeoutExpired):
            return None
        return result.stdout.strip() if result.returncode == 0 else None

    head = git("rev-parse", "HEAD")
    status = git("status", "--porcelain=v1", "-uall")
    dirty = bool(status)
    return head, dirty


def _adapter_inputs():
    adapter_files = []
    for host in HOSTS:
        adapter_files.extend([f"adapters/{host}/plugin.json", f"adapters/{host}/marketplace.json"])
    adapter_files.extend(["adapters/codex/interfaces.json", "adapters/zcode/agents/workflow-reviewer.md"])
    return adapter_files


def _source_tree_hash(spec, inputs=None) -> str:
    def digest(relative):
        return (wio.sha256_bytes(inputs[relative]) if inputs is not None else
                wio.sha256_file(wio.resolve_member(spec.root, relative)))

    payload = {
        "product_id": spec.product_id,
        "version": spec.version,
        "core_skills": spec.core_skills,
        "shared_skills": spec.shared_skills,
        "files": {target: digest(source.relative_to(spec.root).as_posix()) for source, target in spec.files},
        "product_json": digest("product.json"),
        "adapters": {rel: digest(rel) for rel in _adapter_inputs()},
    }
    return wio.sha256_bytes(wio.canonical_json(payload))


def _load_input_json(path: Path, root: Path, inputs):
    data, raw = wio.read_json_snapshot(path, root=root)
    relative = path.relative_to(root).as_posix()
    if raw != inputs[relative]:
        raise DataError(f"captured source input changed before use: {relative}")
    return data


def _capture_inputs(spec) -> dict:
    """Retain exactly the registered bytes and adapter inputs for this build."""
    paths = {source.relative_to(spec.root).as_posix() for source, _ in spec.files}
    paths.update(_adapter_inputs())
    paths.add("product.json")
    inputs = {"product.json": spec.manifest_bytes}
    for relative in sorted(paths - {"product.json"}):
        payload = wio.read_owned(spec.root / relative, root=spec.root)
        if payload is None:
            raise DataError(f"source input disappeared while capturing: {relative}")
        inputs[relative] = payload
    return inputs


def _verify_source_capture(root: Path, inputs) -> None:
    for relative, expected in sorted(inputs.items()):
        if wio.read_owned(root / relative, root=root) != expected:
            raise DataError(f"source input changed while capturing snapshot: {relative}")


def _inject_identity(data: dict, spec) -> dict:
    data = dict(data)
    data["name"] = spec.product_id
    data["version"] = spec.version
    return data


def _compose_reviewer_agent(template_path: Path, contract_body: str, template_bytes: bytes) -> bytes:
    text = template_bytes.decode("utf-8")
    lines = text.splitlines()
    if lines[0].strip() != "---":
        raise DataError(f"reviewer template must start with frontmatter: {template_path}")
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if end is None:
        raise DataError(f"unterminated frontmatter in reviewer template: {template_path}")
    frontmatter = "\n".join(lines[: end + 1])
    return (frontmatter + "\n\n" + contract_body.rstrip() + "\n").encode("utf-8")


def _codex_skill_yaml(entry: dict) -> bytes:
    wproduct.validate_interface_entry(entry)
    lines = [
        "interface:",
        *(f"  {key}: {json.dumps(entry[key], ensure_ascii=False)}" for key in
          ("display_name", "short_description", "brand_color", "default_prompt")),
        "policy:",
        f'  allow_implicit_invocation: {"true" if entry["allow_implicit_invocation"] else "false"}',
    ]
    return ("\n".join(lines) + "\n").encode("utf-8")


def _write_zip(zip_path: Path, root: Path) -> None:
    entries: list[tuple[str, Path]] = []
    for path in sorted(root.rglob("*")):
        if path.is_file() and path != zip_path:
            entries.append((path.relative_to(root).as_posix(), path))
    entries.sort(key=lambda pair: pair[0])
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for name, path in entries:
            info = zipfile.ZipInfo(name, date_time=ZIP_EPOCH)
            mode = 0o644
            if path.suffix == ".py" and path.name != "__init__.py" or path.name == "workflow_tool.py":
                mode |= 0o111
            info.external_attr = (stat.S_IFREG | mode) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(info, path.read_bytes())


def _build_host(spec, host: str, staging: Path, adapters_root: Path, interfaces: dict, inputs) -> dict:
    package_dir = staging / "ai-code-workflow"
    package_dir.mkdir(parents=True)
    extra_files: list[tuple[Path, str]] = []

    for source, target in spec.files:
        dest = package_dir / target
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, dest)
        relative = source.relative_to(spec.root).as_posix()
        if wio.sha256_file(dest) != wio.sha256_bytes(inputs[relative]):
            raise DataError(f"copied source content differs from captured snapshot: {relative}")

    adapter = adapters_root / host
    if host == "zcode":
        manifest = _inject_identity(_load_input_json(adapter / "plugin.json", spec.root, inputs), spec)
        target = package_dir / ".zcode-plugin" / "plugin.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(_dump_json(manifest))
        extra_files.append((target, ".zcode-plugin/plugin.json"))

        contract_source = next(source for source, target in spec.files
                               if target == "skills/review/references/reviewer-contract.md")
        contract_body = inputs[contract_source.relative_to(spec.root).as_posix()].decode("utf-8")
        agent = package_dir / "agents" / "workflow-reviewer.md"
        agent.parent.mkdir(parents=True, exist_ok=True)
        agent.write_bytes(_compose_reviewer_agent(adapter / "agents" / "workflow-reviewer.md",
                                                  contract_body,
                                                  inputs["adapters/zcode/agents/workflow-reviewer.md"]))
        extra_files.append((agent, "agents/workflow-reviewer.md"))
    elif host == "codex":
        manifest = _inject_identity(_load_input_json(adapter / "plugin.json", spec.root, inputs), spec)
        target = package_dir / "plugin.json"
        target.write_bytes(_dump_json(manifest))
        extra_files.append((target, "plugin.json"))

        interface_names = set(interfaces["skills"])
        declared = set(spec.all_skills)
        if interface_names != declared:
            raise DataError(
                f"interfaces.json skills {sorted(interface_names)} != product skills {sorted(declared)}")
        for skill, entry in sorted(interfaces["skills"].items()):
            yaml_path = package_dir / "skills" / skill / "agents" / "openai.yaml"
            yaml_path.parent.mkdir(parents=True, exist_ok=True)
            yaml_path.write_bytes(_codex_skill_yaml(entry))
            extra_files.append((yaml_path, f"skills/{skill}/agents/openai.yaml"))
    else:  # pragma: no cover - guarded by caller
        raise DataError(f"unknown host: {host}")

    files = sorted(
        [(rel, wio.sha256_file(package_dir / rel)) for rel in
         {target for _, target in spec.files} | {rel for _, rel in extra_files}]
    )
    content_hash = wio.sha256_bytes(wio.canonical_json(files))
    return {"package_dir": package_dir, "files": files, "content_hash": content_hash}


def _build_packages_staged(source_root: Path, hosts, output_root: Path, provenance, inputs) -> dict:
    source_root = Path(source_root)
    output_root = Path(output_root)
    spec = wproduct.load_product(source_root)
    if spec.manifest_bytes != inputs["product.json"]:
        raise DataError("captured product manifest changed before use")
    for mode in wpolicy.MODES:
        wpolicy.load_profile(source_root, mode)
    for name in ("task.json", "evidence.json"):
        wio.load_json(source_root / "templates" / name)

    hosts = list(hosts)
    if not hosts:
        raise DataError("no hosts requested")
    unknown = set(hosts) - set(HOSTS)
    if unknown:
        raise DataError(f"unknown host(s): {sorted(unknown)}")
    if "all" in hosts:
        hosts = list(HOSTS)

    adapters_root = source_root / "adapters"
    interfaces = wproduct.validate_adapters(source_root, spec.all_skills)
    interfaces = _load_input_json(adapters_root / "codex/interfaces.json", source_root, inputs)

    if output_root.exists() and any(output_root.iterdir()):
        raise DataError(f"output root is not empty: {output_root}")
    output_root.mkdir(parents=True, exist_ok=True)

    head, dirty = provenance
    source_tree_hash = _source_tree_hash(spec, inputs)

    index_hosts = {}
    for host in hosts:
        host_out = output_root / host
        host_out.mkdir()
        built = _build_host(spec, host, host_out, adapters_root, interfaces, inputs)

        artifact = {
            "schema_version": 1,
            "product_id": spec.product_id,
            "version": spec.version,
            "host": host,
            "profiles": list(wpolicy.MODES),
            "source_revision": head,
            "working_tree_dirty": dirty,
            "source_tree_hash": source_tree_hash,
            "files": built["files"],
            "content_hash": built["content_hash"],
        }
        (built["package_dir"] / "artifact.json").write_bytes(_dump_json(artifact))

        market_template = _load_input_json(adapters_root / host / "marketplace.json", source_root, inputs)
        market_template["plugins"] = [
            dict(entry, name=spec.product_id, version=spec.version)
            for entry in market_template["plugins"]
        ]
        market_rel = ".agents/plugins/marketplace.json" if host == "codex" else "marketplace.json"
        market_path = host_out / market_rel
        market_path.parent.mkdir(parents=True, exist_ok=True)
        market_path.write_bytes(_dump_json(market_template))

        checked = wpackage.check_package(built["package_dir"], host)
        if not checked["ok"]:
            raise DataError(f"built {host} package failed validation: {checked['problems']}")

        zip_name = f"{spec.product_id}-{spec.version}.zip"
        zip_path = host_out / zip_name
        _write_zip(zip_path, host_out)
        with tempfile.TemporaryDirectory(prefix=f".extract-{host}-", dir=output_root) as extracted:
            with zipfile.ZipFile(zip_path) as archive:
                archive.extractall(extracted)
            checked = wpackage.check_package(Path(extracted) / "ai-code-workflow", host)
            if not checked["ok"]:
                raise DataError(f"extracted {host} package failed validation: {checked['problems']}")

        index_hosts[host] = {
            "package_dir": f"{host}/ai-code-workflow",
            "package_content_hash": built["content_hash"],
            "marketplace": f"{host}/{market_rel}",
            "marketplace_sha256": wio.sha256_file(market_path),
            "zip": f"{host}/{zip_name}",
            "zip_sha256": wio.sha256_file(zip_path),
            "files_count": len(built["files"]),
        }

    index = {
        "schema_version": 1,
        "product_id": spec.product_id,
        "version": spec.version,
        "source_revision": head,
        "working_tree_dirty": dirty,
        "source_tree_hash": source_tree_hash,
        "hosts": index_hosts,
    }
    (output_root / "index.json").write_bytes(_dump_json(index))

    return {
        "output_root": str(output_root),
        "hosts": hosts,
        "built_at": wio.now_rfc3339(),
        "index": str(output_root / "index.json"),
        "content_hashes": {h: index_hosts[h]["package_content_hash"] for h in hosts},
    }


def _check_empty_output(output_root: Path) -> None:
    if output_root.is_symlink():
        raise DataError(f"output root must not be a symlink: {output_root}")
    if output_root.exists() and (not output_root.is_dir() or any(output_root.iterdir())):
        raise DataError(f"output root is not an empty directory: {output_root}")


def build_packages(source_root: Path, hosts, output_root: Path) -> dict:
    """Validate in private staging, then publish one complete distribution.

    The sibling temporary directory is on the output filesystem, so rename
    publishes all hosts together. Failures only clean our private staging;
    pre-existing output directories and late user files are never removed.
    """
    output_root = Path(output_root)
    _check_empty_output(output_root)
    source_root = Path(source_root)
    spec = wproduct.load_product(source_root)
    inputs = _capture_inputs(spec)
    # Observe actual Git context before any private directories can make this
    # checkout dirty. Reject input drift during capture; later source edits do
    # not alter the private bytes that are now this build's inputs.
    provenance = _git_state(source_root)
    _verify_source_capture(source_root, inputs)
    output_root.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".workflow-build-", dir=output_root.parent) as temporary:
        private = Path(temporary)
        captured = private / "source"
        for relative, payload in inputs.items():
            destination = captured / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(payload)
        staging = private / "dist"
        report = _build_packages_staged(captured, hosts, staging, provenance, inputs)
        _check_empty_output(output_root)
        os.rename(staging, output_root)
    report["output_root"] = str(output_root)
    report["index"] = str(output_root / "index.json")
    return report
