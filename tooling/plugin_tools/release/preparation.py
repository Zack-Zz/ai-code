"""Preview bounded local version/notes edits; never publish or invent host evidence."""

import json
import os
from pathlib import Path
import re

from .. import io
from ..io import ConflictError, DataError
from ..markets import _existing, _write_market
from ..registry import load_catalog
from ..versions import release_kind, version_key
from .acceptance import FIELDS, PROOF_PATH, PROOF_LIMIT

DOCUMENT_LIMIT = 1024 * 1024


def _text(raw, what):
    try:
        text = raw.decode("utf-8")
    except UnicodeError as exc:
        raise DataError(f"{what} must be UTF-8 Markdown") from exc
    if not text.strip() or "\x00" in text:
        raise DataError(f"{what} must be nonempty Markdown")
    return text


def _body(raw):
    text = _text(raw, "notes-file").strip() + "\n"
    headings = list(re.finditer(r"^### (English|中文)\s*$", text, re.M))
    if [match[1] for match in headings] != ["English", "中文"] or \
            text[:headings[0].start()].strip() or re.search(r"^#{1,2}(?:\s|$)", text, re.M):
        raise DataError("notes-file requires ### English then ### 中文 with nonempty bodies; omit version headings")
    english = text[headings[0].end():headings[1].start()].strip()
    chinese = text[headings[1].end():].strip()
    if not english or not chinese or not re.search(r"[A-Za-z]", english) or not re.search(r"[\u3400-\u9fff]", chinese):
        raise DataError("notes-file requires nonempty English and Chinese bodies")
    return text


def _notes(history, version, body):
    headings = list(re.finditer(r"^## ([0-9]+\.[0-9]+\.[0-9]+(?:-preview\.[0-9]+)?)(?=\s|$)[^\n]*\n?", history, re.M))
    existing = [match for match in headings if match[1] == version]
    if len(existing) > 1:
        raise ConflictError(f"release notes already contain duplicate {version} sections")
    if existing:
        match = existing[0]
        end = re.search(r"^##(?:\s|$)", history[match.end():], re.M)
        section = history[match.end():match.end() + end.start() if end else len(history)]
        if section.strip() != body.strip():
            raise ConflictError(f"release notes already contain different content for {version}; choose a new version")
        return history
    section = f"## {version}\n\n{body}\n"
    if headings:
        position = headings[0].start()
        return history[:position] + section + history[position:]
    return history + ("\n" if history.endswith("\n") else "\n\n") + section


def _config(spec, captured):
    raw = io.read_file(spec.root, "release.json", limit=DOCUMENT_LIMIT, boundary_root=spec.boundary_root)
    config = io.parse_json(raw, what="release.json")
    if "release.json" in captured and captured["release.json"] != raw:
        raise ConflictError("source input changed during preparation: release.json")
    if not isinstance(config, dict) or set(config) != {"schema_version", "notes", "readmes", "acceptance"} or \
            type(config["schema_version"]) is not int or config["schema_version"] != 1:
        raise DataError("release.json requires schema_version/notes/readmes/acceptance")
    if not isinstance(config["readmes"], dict) or set(config["readmes"]) != {"en", "zh-CN"}:
        raise DataError("release readmes must declare exactly en and zh-CN")
    if not isinstance(config["acceptance"], dict) or set(config["acceptance"]) != set(spec.hosts):
        raise DataError("release acceptance must cover exactly the declared hosts")
    documents = [config["notes"], *config["readmes"].values()]
    for relative in documents:
        io.relative_path(relative, what="release document")
        if not relative.endswith(".md") or relative == PROOF_PATH:
            raise DataError("release documents must use distinct Markdown paths")
        data = io.read_file(spec.root, relative, limit=DOCUMENT_LIMIT, boundary_root=spec.boundary_root)
        _text(data, relative)
        if relative in captured and captured[relative] != data:
            raise ConflictError(f"source input changed during preparation: {relative}")
        captured[relative] = data
    if len(set(documents)) != len(documents):
        raise DataError("release documents must use distinct Markdown paths")
    public = set(captured) | {"release.json", PROOF_PATH}
    for path in config["acceptance"].values():
        if path is not None:
            io.relative_path(path, what="acceptance reference")
            if path in public:
                raise DataError("acceptance reference aliases a public input or generated proof")
            # Inspect path safety, preserving all private bytes even if evidence is stale.
            _existing(spec.boundary_root, spec.catalog_path + "/" + path)
    captured["release.json"] = raw
    return config


def _proof(spec, raw):
    proof = io.parse_json(raw, what=PROOF_PATH)
    if not isinstance(proof, dict) or set(proof) != FIELDS or \
            type(proof["schema_version"]) is not int or proof["schema_version"] != 1 or \
            proof["product_id"] != spec.product_id:
        raise ConflictError("refusing to remove an unrecognized or another plugin's acceptance proof")
    if version_key(proof["version"]) > version_key(spec.version):
        raise ConflictError("acceptance proof belongs to a newer version; review it before preparation")
    if not isinstance(proof["source_tree_hash"], str) or not re.fullmatch(r"[0-9a-f]{64}", proof["source_tree_hash"]):
        raise ConflictError("refusing to remove an invalid generated acceptance proof")
    for key in ("package_content_hashes", "public_inputs"):
        values = proof[key]
        if not isinstance(values, dict) or not values or any(not isinstance(value, str) or
                not re.fullmatch(r"[0-9a-f]{64}", value) for value in values.values()):
            raise ConflictError("refusing to remove an invalid generated acceptance proof")
    if set(proof["package_content_hashes"]) != set(spec.hosts) or \
            not isinstance(proof["hosts"], dict) or set(proof["hosts"]) != set(spec.hosts):
        raise ConflictError("refusing to remove a proof with mismatched host declarations")
    for path in proof["public_inputs"]:
        io.relative_path(path, what="acceptance proof public input")
    for binding in proof["hosts"].values():
        if not isinstance(binding, dict) or set(binding) != {"evidence", "artifacts"} or \
                not isinstance(binding["artifacts"], list) or not binding["artifacts"]:
            raise ConflictError("refusing to remove an invalid generated acceptance proof")
        for artifact in [binding["evidence"], *binding["artifacts"]]:
            if not isinstance(artifact, dict) or set(artifact) != {"path", "sha256"} or \
                    not isinstance(artifact["sha256"], str) or not re.fullmatch(r"[0-9a-f]{64}", artifact["sha256"]):
                raise ConflictError("refusing to remove an invalid generated acceptance proof")
            io.relative_path(artifact["path"], what="acceptance proof private input")


def _recheck(root, captured):
    for relative, expected in captured.items():
        if _existing(root, relative) != expected:
            raise ConflictError(f"source input changed during version preparation: {relative}")


def _read_body_file(source):
    return io.read_file(Path(source.anchor), source.relative_to(source.anchor).as_posix(), limit=DOCUMENT_LIMIT)


def _recheck_body(source):
    if source is not None and _read_body_file(source[0]) != source[1]:
        raise ConflictError("notes-file changed during preparation")


def _remove(root, relative, previous):
    with io.parent_handle(root, relative) as (parent, name):
        if _existing(root, relative) != previous:
            raise ConflictError(f"source input changed before removing proof: {relative}")
        os.unlink(name, dir_fd=parent)


def _apply_changes(root, captured, changes, notes_source=None):
    _recheck(root, captured)
    _recheck_body(notes_source)
    completed = []
    try:
        for relative, old, new in changes:
            if new is None:
                _remove(root, relative, old)
            else:
                _write_market(root, relative, new, old)
            completed.append((relative, old, new))
        expected = {**captured, **{relative: new for relative, _, new in changes}}
        _recheck(root, expected)
        _recheck_body(notes_source)
    except (io.ToolError, OSError) as exc:
        retained = []
        for relative, old, new in reversed(completed):
            try:
                if _existing(root, relative) != new:
                    retained.append(relative)
                    continue
                _write_market(root, relative, old, new)
            except (io.ToolError, OSError):
                retained.append(relative)
        if retained:
            raise ConflictError(f"preparation interrupted: {exc}; review remaining changed paths: {sorted(retained)}") from exc
        raise


def prepare_version(root, spec, version, notes_file, *, apply=False):
    """Return a complete local plan, optionally applying only its listed byte changes."""
    if type(apply) is not bool:
        raise DataError("apply must be boolean")
    if version_key(version) < version_key(spec.version):
        raise DataError("version preparation cannot lower the current product version")
    root = Path(root).absolute()
    if root.is_symlink():
        raise DataError("symlinked repository root rejected")
    root = root.resolve()
    if spec.boundary_root != root or spec.root != root / spec.catalog_path:
        raise DataError("selected plugin must belong to the repository catalog")
    catalog_raw = io.read_file(root, "catalog.json", limit=DOCUMENT_LIMIT)
    current = next((candidate for candidate in load_catalog(root) if candidate.product_id == spec.product_id), None)
    if current is None or current.catalog_path != spec.catalog_path or current.inputs != spec.inputs:
        raise ConflictError("catalog or source input changed since plugin selection")
    if io.read_file(root, "catalog.json", limit=DOCUMENT_LIMIT) != catalog_raw:
        raise ConflictError("catalog changed during version preparation")
    source = Path(notes_file).absolute()
    # Anchor to the filesystem root to inspect every source component without following links.
    body_raw = _read_body_file(source)
    body = _body(body_raw)
    captured = dict(spec.inputs)
    config = _config(spec, captured)
    history = _text(captured[config["notes"]], config["notes"])
    new_notes = _notes(history, version, body).encode("utf-8")
    if len(new_notes) > DOCUMENT_LIMIT:
        raise DataError("prepared release notes exceed 1 MiB")
    product = captured["product.json"]
    # Preserve all product formatting and unrelated fields.
    old_token = json.dumps(spec.version).encode()
    product_pattern = re.compile(rb'("version"\s*:\s*)' + re.escape(old_token))
    new_product, replacements = product_pattern.subn(lambda match: match[1] + json.dumps(version).encode(), product)
    if replacements != 1 or io.parse_json(new_product, what="prepared product.json") != {**spec.manifest, "version": version}:
        raise DataError("product version must have one unambiguous JSON field")
    prefix = spec.catalog_path + "/"
    captured = {prefix + relative: raw for relative, raw in captured.items()}
    captured["catalog.json"] = catalog_raw
    changes = []
    for relative, old, new in (("product.json", product, new_product),
                               (config["notes"], captured[prefix + config["notes"]], new_notes)):
        if old != new:
            changes.append((prefix + relative, old, new))
    invalidated = bool(changes)
    reset_hosts = sorted(host for host, path in config["acceptance"].items() if path is not None) if invalidated else []
    proof_path = prefix + PROOF_PATH
    proof_raw = _existing(root, proof_path)
    if proof_raw is not None and len(proof_raw) > PROOF_LIMIT:
        raise DataError("acceptance proof exceeds 1 MiB")
    captured[proof_path] = proof_raw
    if invalidated:
        if reset_hosts:
            new_config = {**config, "acceptance": {host: None for host in spec.hosts}}
            changes.append((prefix + "release.json", captured[prefix + "release.json"], io.dump_json(new_config)))
        if proof_raw is not None:
            if PROOF_PATH in spec.inputs:
                raise DataError("generated acceptance proof must not be a registered public resource")
            _proof(spec, proof_raw)
            changes.append((proof_path, proof_raw, None))
    _recheck(root, captured)
    _recheck_body((source, body_raw))
    if source in {root / relative for relative in captured}:
        raise DataError("notes-file must be a separate body file, outside the prepared source inputs")
    if apply and changes:
        _apply_changes(root, captured, changes, (source, body_raw))
    return {"ok": True, "status": "applied" if apply else "preview", "product_id": spec.product_id,
        "old_version": spec.version, "version": version, "release_kind": release_kind(version),
        "notes_format": "### English followed by ### 中文; body only",
        "changes": [{"path": relative, "action": "remove" if new is None else "update",
            "old": old.decode("utf-8"), "new": new.decode("utf-8") if new is not None else None,
            "old_sha256": io.sha256(old), "new_sha256": io.sha256(new) if new is not None else None}
            for relative, old, new in changes],
        "invalidated_acceptance": {"status": "invalidated" if invalidated else "unchanged", "hosts": reset_hosts,
            "removed_proof": proof_path if invalidated and proof_raw is not None else None,
            "private_materials": "preserved", "published_records": "preserved"},
        "verification": {"source_schema": "validated", "paths": "validated", "source_concurrency": "checked",
            "host_acceptance": "unverified", "build": "not_run", "tests": "not_run", "publication": "not_run"}}
