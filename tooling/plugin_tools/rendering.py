"""Deterministic native metadata generated solely from trusted plugin inputs."""

import copy
import json

from . import io
from .io import DataError


def interface_yaml(entry):
    lines = ["interface:"]
    lines.extend(f"  {key}: {json.dumps(entry[key], ensure_ascii=False)}" for key in
                 ("display_name", "short_description", "brand_color", "default_prompt"))
    lines.extend(["policy:",
                  f"  allow_implicit_invocation: {'true' if entry['allow_implicit_invocation'] else 'false'}"])
    return ("\n".join(lines) + "\n").encode("utf-8")


def agent_bytes(template, body):
    lines = template.decode("utf-8").splitlines()
    end = next((i for i in range(1, len(lines)) if lines[i].strip() == "---"), None)
    if not lines or lines[0].strip() != "---" or end is None:
        raise DataError("generated agent template requires closed frontmatter")
    return ("\n".join(lines[:end + 1]) + "\n\n" + body.decode("utf-8").rstrip() + "\n").encode("utf-8")


def package_files(spec, host):
    """Return the source-derived closure, independent of artifact.json claims."""
    if host not in spec.hosts:
        raise DataError(f"plugin {spec.product_id} does not support host {host}")
    files = {target: spec.inputs[source] for target, source in spec.files.items()}
    manifest = copy.deepcopy(spec.adapters[host])
    manifest.update(name=spec.product_id, version=spec.version)
    if host == "claude":
        manifest["displayName"] = spec.manifest["display_name"]
    if "publisher" in spec.manifest:
        manifest["author"] = copy.deepcopy(spec.manifest["publisher"])
        if host == "codex":
            extension = manifest.get("extensions", {}).get("com.openai", {})
            interface = extension.get("interface", manifest.get("interface"))
            if isinstance(interface, dict):
                interface["developerName"] = spec.manifest["publisher"]["name"]
    relative = manifest_path(host)
    files[relative] = io.dump_json(manifest)
    if host == "codex":
        for name, entry in spec.interfaces.items():
            files[f"skills/{name}/agents/openai.yaml"] = interface_yaml(entry)
    for agent in spec.manifest.get("generated_agents", []):
        if agent["host"] == host:
            files[agent["target"]] = agent_bytes(spec.inputs[agent["template"]], spec.inputs[agent["body"]])
    return dict(sorted(files.items()))


def file_hashes(files):
    return [[relative, io.sha256(payload)] for relative, payload in sorted(files.items())]


def manifest_path(host):
    paths = {"claude": ".claude-plugin/plugin.json", "codex": "plugin.json", "zcode": ".zcode-plugin/plugin.json"}
    if host not in paths:
        raise DataError(f"unknown host: {host}")
    return paths[host]


def marketplace_path(host):
    paths = {"claude": ".claude-plugin/marketplace.json", "codex": ".agents/plugins/marketplace.json", "zcode": "marketplace.json"}
    if host not in paths:
        raise DataError(f"unknown host: {host}")
    return paths[host]


def marketplace_entry(spec, host):
    entry = {"name": spec.product_id, "version": spec.version}
    if host == "codex":
        entry.update(source={"source": "local", "path": f"./{spec.product_id}"},
                     policy={"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
                     category="developer-tools")
    else:
        entry.update(source=f"./{spec.product_id}", description=spec.adapters[host]["description"])
    return entry


def marketplace(specs, host):
    market = {"name": "ai-code-local", "plugins": [marketplace_entry(spec, host)
                                                    for spec in sorted(specs, key=lambda item: item.product_id)]}
    if host == "claude":
        market["owner"] = {"name": "ai-code"}
    return market
