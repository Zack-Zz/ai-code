"""Deterministic native installers; parsing never extracts or executes code."""

import gzip
from io import BytesIO
import stat
import tarfile
import zipfile

from . import io
from .io import DataError

MAX_BYTES = 256 * 1024 * 1024


def installer_name(identity, version, host):
    return f"{identity}-{version}-{host}-plugin.{'tgz' if host == 'dsh' else 'zip'}"


def installer_bytes(files, identity, host):
    if host != "dsh":
        from .release.layout import zip_bytes
        return zip_bytes({f"{identity}/{name}": data for name, data in files.items()})
    output = BytesIO()
    with gzip.GzipFile(filename="", fileobj=output, mode="wb", mtime=0, compresslevel=9) as compressed:
        with tarfile.open(fileobj=compressed, mode="w", format=tarfile.USTAR_FORMAT) as archive:
            for name, data in sorted(files.items()):
                io.relative_path(name, what="installer member")
                member = tarfile.TarInfo(f"package/{name}")
                member.size = len(data)
                member.mode = 0o755 if name.endswith(".py") and not name.endswith("/__init__.py") else 0o644
                member.mtime = member.uid = member.gid = 0
                member.uname = member.gname = ""
                archive.addfile(member, BytesIO(data))
    return output.getvalue()


def read_installer(raw, identity, host):
    if len(raw) > MAX_BYTES:
        raise DataError("installer exceeds size limit")
    result = {}
    total = 0
    prefix = "package/" if host == "dsh" else f"{identity}/"
    def admit(name, size, regular):
        nonlocal total
        io.relative_path(name, what="installer member")
        if not regular or not name.startswith(prefix) or name == prefix:
            raise DataError("installer member type/root differs from native format")
        relative = io.relative_path(name[len(prefix):], what="installer member")
        if relative in result or any(relative.startswith(x + "/") or x.startswith(relative + "/") for x in result):
            raise DataError("installer contains duplicate or overlapping members")
        if "__pycache__" in relative.split("/") or relative.endswith((".pyc", ".pyo")):
            raise DataError("installer contains cache artifacts")
        total += size
        if size < 0 or total > MAX_BYTES:
            raise DataError("installer unpacked size exceeds limit")
        return relative
    try:
        if host == "dsh":
            # tarfile consumes PAX/GNU headers before yielding ordinary members.
            # Bound the entire gzip stream first, including those hidden bytes.
            with gzip.GzipFile(fileobj=BytesIO(raw), mode="rb") as compressed:
                unpacked = compressed.read(MAX_BYTES + 1)
            if len(unpacked) > MAX_BYTES:
                raise DataError("installer total decompressed size exceeds limit")
            with tarfile.open(fileobj=BytesIO(unpacked), mode="r:") as archive:
                for item in archive:
                    regular = item.type in (tarfile.REGTYPE, tarfile.AREGTYPE) and not item.issparse()
                    name = admit(item.name, item.size, regular)
                    stream = archive.extractfile(item)
                    if stream is None:
                        raise DataError("installer member is unreadable")
                    result[name] = stream.read(MAX_BYTES + 1)
                    if len(result[name]) != item.size:
                        raise DataError("installer member size differs")
        else:
            with zipfile.ZipFile(BytesIO(raw)) as archive:
                for item in archive.infolist():
                    name = admit(item.filename, item.file_size, stat.S_ISREG(item.external_attr >> 16))
                    result[name] = archive.read(item)
    except (OSError, EOFError, ValueError, tarfile.TarError, zipfile.BadZipFile, RuntimeError) as exc:
        raise DataError(f"invalid native installer: {exc}") from exc
    if not result:
        raise DataError("installer is empty")
    return result


def verify_installer(raw, expected_files, identity, host):
    if read_installer(raw, identity, host) != expected_files:
        raise DataError("installer contents differ from trusted files")


def download_name(identity, version, host):
    return f"{identity}-{version}.{'tgz' if host == 'dsh' else 'zip'}"


def download_bytes(files, identity, host, market):
    if host == "dsh":
        return installer_bytes(files, identity, host)
    from .release.layout import zip_bytes
    from .rendering import marketplace_path
    return zip_bytes({**{f"{identity}/{name}": data for name, data in files.items()},
                      marketplace_path(host): io.dump_json(market)})


def download_index(relative, raw, host):
    if host == "dsh":
        return {"archive": relative, "archive_sha256": io.sha256(raw), "archive_format": "npm-tgz"}
    return {"zip": relative, "zip_sha256": io.sha256(raw)}
