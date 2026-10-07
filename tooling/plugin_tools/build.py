"""Independent plugin packages and aggregated markets, published as one transaction."""

import os
from pathlib import Path
import stat
import subprocess
import tempfile
import zipfile

from . import io
from .io import ConflictError, DataError
from .package_check import check_package
from .registry import HOSTS
from .rendering import file_hashes, marketplace, marketplace_path, package_files


def _git_state(root):
    def run(*args):
        try:
            result = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, timeout=10)
        except (OSError, subprocess.TimeoutExpired):
            return None
        return result.stdout.strip() if result.returncode == 0 else None
    return run("rev-parse", "HEAD"), bool(run("status", "--porcelain=v1", "-uall"))


def _empty_output(output):
    if output.is_symlink():
        raise DataError(f"output path must not be a symlink: {output}")
    if output.exists() and (not output.is_dir() or any(output.iterdir())):
        raise ConflictError(f"output path is not an empty directory: {output}")


def _verify_inputs(specs):
    for spec in specs:
        for relative, payload in spec.inputs.items():
            if io.read_file(spec.root, relative, boundary_root=spec.boundary_root) != payload:
                raise DataError(f"plugin {spec.product_id} source input changed during build: {relative}")


def _write_bytes(root, files):
    for relative, payload in files.items():
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(payload)


def _zip(path, files):
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for relative, payload in sorted(files.items()):
            info = zipfile.ZipInfo(relative, date_time=(1980, 1, 1, 0, 0, 0))
            permissions = 0o755 if relative.endswith(".py") and not relative.endswith("/__init__.py") else 0o644
            info.external_attr = (stat.S_IFREG | permissions) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, payload)


def _verify_zip(path, spec, host, artifact):
    """Reopen the download and compare every member to trusted package inputs."""
    expected = {f"{spec.product_id}/{relative}": payload
                for relative, payload in package_files(spec, host).items()}
    expected[f"{spec.product_id}/artifact.json"] = io.dump_json(artifact)
    expected[marketplace_path(host)] = io.dump_json(marketplace([spec], host))
    try:
        with zipfile.ZipFile(path) as archive:
            entries = archive.infolist()
            if [entry.filename for entry in entries] != sorted(expected):
                raise DataError("ZIP member closure or ordering differs from trusted plugin")
            for entry in entries:
                payload = expected[entry.filename]
                if not stat.S_ISREG(entry.external_attr >> 16) or entry.file_size != len(payload):
                    raise DataError(f"ZIP member type/size differs from trusted plugin: {entry.filename}")
                if archive.read(entry) != payload:
                    raise DataError(f"ZIP member content differs from trusted plugin: {entry.filename}")
    except (OSError, zipfile.BadZipFile, RuntimeError) as exc:
        raise DataError(f"cannot verify ZIP archive: {exc}") from exc


def build_plugins(root, specs, output, hosts=HOSTS):
    output = Path(output).absolute()
    _empty_output(output)
    # The selected parent may use OS aliases (/tmp, /var) or an explicit
    # directory alias. Enforce containment on its canonical destination.
    output = output.parent.resolve() / output.name
    _empty_output(output)
    if not specs:
        raise DataError("no plugins selected for build")
    if not hosts or set(hosts) - set(HOSTS):
        raise DataError("unsupported build host")
    active = [spec for spec in specs if set(spec.hosts) & set(hosts)]
    if not active:
        raise DataError(f"selected plugins do not support requested hosts: {list(hosts)}")
    for spec in specs:
        if output == spec.root or spec.root in output.parents:
            raise DataError("build output cannot be inside a plugin source directory")
    _verify_inputs(active)
    revision, dirty = _git_state(Path(root))
    output.parent.mkdir(parents=True, exist_ok=True)
    index = {"schema_version": 2, "plugins": {}, "hosts": {},
             "source_revision": revision, "working_tree_dirty": dirty}
    with tempfile.TemporaryDirectory(prefix=".ai-plugin-build-", dir=output.parent) as temporary:
        stage = Path(temporary) / "dist"
        stage.mkdir()
        for host in HOSTS:
            supported = [spec for spec in active if host in hosts and host in spec.hosts]
            if not supported:
                continue
            host_root = stage / host
            market_rel = marketplace_path(host)
            market_bytes = io.dump_json(marketplace(supported, host))
            _write_bytes(host_root, {market_rel: market_bytes})
            index["hosts"][host] = {"marketplace": f"{host}/{market_rel}",
                                     "marketplace_sha256": io.sha256(market_bytes)}
            for spec in supported:
                files = package_files(spec, host)
                pairs = file_hashes(files)
                content_hash = io.sha256(io.canonical_json(pairs))
                artifact = {"schema_version": 1, "product_id": spec.product_id,
                            "version": spec.version, "host": host, "profiles": spec.profiles,
                            "source_revision": revision, "working_tree_dirty": dirty,
                            "source_tree_hash": spec.source_tree_hash, "files": pairs,
                            "content_hash": content_hash}
                files["artifact.json"] = io.dump_json(artifact)
                package_root = host_root / spec.product_id
                _write_bytes(package_root, files)
                checked = check_package(package_root, host, spec)
                if not checked["ok"]:
                    raise DataError(f"built package failed trusted verification: {checked['problems']}")
                zip_name = f"{spec.product_id}-{spec.version}.zip"
                download = {f"{spec.product_id}/{relative}": payload for relative, payload in files.items()}
                download[market_rel] = io.dump_json(marketplace([spec], host))
                _zip(host_root / zip_name, download)
                _verify_zip(host_root / zip_name, spec, host, artifact)
                plugin_index = index["plugins"].setdefault(spec.product_id, {
                    "version": spec.version, "source_tree_hash": spec.source_tree_hash, "hosts": {}})
                plugin_index["hosts"][host] = {"package_dir": f"{host}/{spec.product_id}",
                                               "package_content_hash": content_hash,
                                               "zip": f"{host}/{zip_name}",
                                               "zip_sha256": io.sha256((host_root / zip_name).read_bytes()),
                                               "files_count": len(pairs)}
        (stage / "index.json").write_bytes(io.dump_json(index))
        _verify_inputs(active)
        _empty_output(output)
        os.rename(stage, output)
    return {"ok": True, "output_root": str(output), "index": str(output / "index.json"),
            "plugins": sorted(index["plugins"]), "hosts": sorted(index["hosts"])}
