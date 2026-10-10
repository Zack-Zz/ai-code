"""Deterministic release payloads independently derived from trusted source snapshots."""

from io import BytesIO
import stat
import zipfile

from .. import io
from ..io import DataError
from ..registry import HOSTS
from ..rendering import file_hashes, marketplace, marketplace_path, package_files


def zip_bytes(files):
    output = BytesIO()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for relative, payload in sorted(files.items()):
            entry = zipfile.ZipInfo(relative, date_time=(1980, 1, 1, 0, 0, 0))
            permissions = 0o755 if relative.endswith(".py") and not relative.endswith("/__init__.py") else 0o644
            entry.external_attr = (stat.S_IFREG | permissions) << 16
            entry.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(entry, payload)
    return output.getvalue()


def package_outputs(spec, provenance):
    files = {}
    index = {"schema_version": 2, "plugins": {}, "hosts": {},
             "source_revision": provenance["source_revision"], "working_tree_dirty": provenance["working_tree_dirty"]}
    plugin = {"version": spec.version, "source_tree_hash": spec.source_tree_hash, "hosts": {}}
    index["plugins"][spec.product_id] = plugin
    for host in HOSTS:
        if host not in spec.hosts:
            continue
        contents = package_files(spec, host)
        pairs = file_hashes(contents)
        content_hash = io.sha256(io.canonical_json(pairs))
        artifact = {"schema_version": 1, "product_id": spec.product_id, "version": spec.version, "host": host,
            "profiles": spec.profiles, "source_revision": provenance["source_revision"],
            "working_tree_dirty": provenance["working_tree_dirty"], "source_tree_hash": spec.source_tree_hash,
            "files": pairs, "content_hash": content_hash}
        contents["artifact.json"] = io.dump_json(artifact)
        market = io.dump_json(marketplace([spec], host))
        market_relative = marketplace_path(host)
        files[f"{host}/{market_relative}"] = market
        files.update({f"{host}/{spec.product_id}/{name}": payload for name, payload in contents.items()})
        download = {f"{spec.product_id}/{name}": payload for name, payload in contents.items()}
        download[market_relative] = market
        zip_relative = f"{host}/{spec.product_id}-{spec.version}.zip"
        zipped = zip_bytes(download)
        files[zip_relative] = zipped
        index["hosts"][host] = {"marketplace": f"{host}/{market_relative}", "marketplace_sha256": io.sha256(market)}
        plugin["hosts"][host] = {"package_dir": f"{host}/{spec.product_id}", "package_content_hash": content_hash,
            "zip": zip_relative, "zip_sha256": io.sha256(zipped), "files_count": len(pairs)}
    files["index.json"] = io.dump_json(index)
    return files


def _schema(schema_version):
    if type(schema_version) is not int or schema_version not in (1, 2):
        raise DataError("release manifest schema must be 1 or 2")


def payload(spec, capture, provenance, report, schema_version=2):
    _schema(schema_version)
    packages = package_outputs(spec, provenance)
    files = {f"packages/{relative}": data for relative, data in packages.items()}
    source_readmes = {"README.md": capture.inputs[capture.config["readmes"]["en"]],
                      "README_CN.md": capture.inputs[capture.config["readmes"]["zh-CN"]]}
    for host in spec.hosts:
        files[f"downloads/{spec.product_id}-{spec.version}-{host}.zip"] = packages[f"{host}/{spec.product_id}-{spec.version}.zip"]
        if schema_version == 2:
            base = f"{host}/{spec.product_id}/"
            installer = {f"{spec.product_id}/{name.removeprefix(base)}": data
                         for name, data in packages.items() if name.startswith(base)}
            files[f"installers/{spec.product_id}-{spec.version}-{host}-plugin.zip"] = zip_bytes(installer)
        channel = "openai" if host == "codex" else host
        source = {**package_files(spec, host), **source_readmes}
        base = f"submissions/{channel}"
        files.update({f"{base}/plugins/{spec.product_id}/{name}": data for name, data in source.items()})
        files[f"{base}/{spec.product_id}-{spec.version}.zip"] = zip_bytes({f"{spec.product_id}/{name}": data for name, data in source.items()})
        market = marketplace([spec], host)
        if host == "codex":
            market["plugins"][0]["source"] = {"source": "local", "path": f"./plugins/{spec.product_id}"}
        else:
            market["plugins"][0]["source"] = f"./plugins/{spec.product_id}"
        files[f"{base}/{marketplace_path(host)}"] = io.dump_json(market)
    inputs = {"schema_version": 1, "product_id": spec.product_id, "version": spec.version,
        "source_tree_hash": spec.source_tree_hash, "product": spec.manifest, "release_config": capture.config,
        "source_files": [[name, io.sha256(data)] for name, data in sorted(spec.inputs.items())],
        "release_files": [[name, digest] for name, digest in sorted(capture.input_hashes().items())],
        "package_content_hashes": capture.package_hashes}
    files["source-inputs.json"] = io.dump_json(inputs)
    notes = [f"# {spec.manifest['display_name']} {spec.version}", "", f"Plugin: {spec.product_id}",
        f"Mode: {report['mode']}", f"Source revision: {provenance['source_revision'] or 'unavailable'}",
        f"Working tree dirty: {str(provenance['working_tree_dirty']).lower()}",
        f"Tag: {provenance['tag'] or 'none'}", f"Source SHA256: {spec.source_tree_hash}",
        f"Publication ready: {str(report['publication_ready']).lower()}", "", "Host acceptance:"]
    notes.extend(f"- {host}: {'accepted evidence bound to these bytes' if host in capture.accepted else 'unverified'}" for host in sorted(spec.hosts))
    notes.extend(["", "Limitations:", *(f"- {item}" for item in report["limitations"]), "",
                  capture.inputs[capture.config["notes"]].decode("utf-8").rstrip(), ""])
    files["release-notes.md"] = "\n".join(notes).encode()
    files["SHA256SUMS"] = "".join(f"{io.sha256(data)}  {name}\n" for name, data in sorted(files.items())).encode()
    return files


def record(spec, provenance, report, files, schema_version=2):
    _schema(schema_version)
    pairs = file_hashes(files)
    return {"schema_version": schema_version, "product_id": spec.product_id, "version": spec.version,
        "display_name": spec.manifest["display_name"], "mode": report["mode"], "tag": provenance["tag"],
        "source_revision": provenance["source_revision"], "working_tree_dirty": provenance["working_tree_dirty"],
        "source_tree_hash": spec.source_tree_hash, "readiness": report["readiness"],
        "files": pairs, "content_hash": io.sha256(io.canonical_json(pairs))}
