"""Portable digest-only acceptance statements, reviewed and frozen with source tags.

The exporter alone reads private evidence. Consumers authenticate the statement
against clean tagged Git bytes, then recompute all public inputs and package
hashes. This is a maintainer's factual statement, not host-session certification.
"""

import subprocess

from .. import io
from ..io import ConflictError, DataError
from ..rendering import package_files
from . import metadata, source_git

PROOF_PATH = "release/acceptance-proof.json"
PROOF_LIMIT = 1024 * 1024
FIELDS = {"schema_version", "product_id", "version", "source_tree_hash",
          "package_content_hashes", "public_inputs", "hosts"}


def public_inputs(spec, capture):
    return {**spec.inputs, **{name: capture.inputs[name] for name in
        ("release.json", capture.config["notes"], *capture.config["readmes"].values())}}


def export_acceptance(spec, *, replace=False):
    metadata.validate_listing(spec)
    capture = metadata.capture_release(spec)
    if capture.pending:
        raise DataError("acceptance export requires actual byte-bound acceptance for every host")
    hosts = {}
    for host, path in sorted(capture.accepted.items()):
        evidence = io.parse_json(capture.inputs[path], what="private acceptance")
        hosts[host] = {"evidence": {"path": path, "sha256": io.sha256(capture.inputs[path])},
                       "artifacts": evidence["artifacts"]}
    proof = {"schema_version": 1, "product_id": spec.product_id, "version": spec.version,
        "source_tree_hash": spec.source_tree_hash, "package_content_hashes": capture.package_hashes,
        "public_inputs": {name: io.sha256(raw) for name, raw in sorted(public_inputs(spec, capture).items())},
        "hosts": hosts}
    # Validate the same closed contract used by CI before exporting anything.
    _bindings(spec, capture, proof)
    raw = io.dump_json(proof)
    if len(raw) > PROOF_LIMIT:
        raise DataError("acceptance statement exceeds the CI read limit of 1 MiB")
    metadata.recheck_inputs(spec, capture)
    from ..markets import _existing, _write_market
    previous = _existing(spec.root, PROOF_PATH)
    if previous is not None and previous != raw and not replace:
        raise ConflictError("acceptance statement already exists; review it before using --replace")
    if previous != raw:
        _write_market(spec.root, PROOF_PATH, raw, previous)
    metadata.recheck_inputs(spec, capture)
    return {"ok": True, "product_id": spec.product_id, "version": spec.version,
            "path": str(spec.root / PROOF_PATH), "sha256": io.sha256(raw),
            "accepted_hosts": sorted(hosts)}


def _bindings(spec, capture, proof):
    if not isinstance(proof, dict) or set(proof) != FIELDS or \
            type(proof["schema_version"]) is not int or proof["schema_version"] != 1:
        raise DataError("acceptance statement has invalid fields/schema")
    for name, expected in (("product_id", spec.product_id), ("version", spec.version),
                          ("source_tree_hash", spec.source_tree_hash),
                          ("package_content_hashes", capture.package_hashes)):
        if proof[name] != expected:
            raise DataError(f"acceptance statement {name} differs from the frozen source")
    public = public_inputs(spec, capture)
    hashes = {name: io.sha256(raw) for name, raw in public.items()}
    if proof["public_inputs"] != hashes:
        raise DataError("acceptance statement public input bindings differ from the frozen source")
    if not isinstance(proof["hosts"], dict) or set(proof["hosts"]) != set(spec.hosts):
        raise DataError("acceptance statement must cover exactly the declared hosts")
    public_paths = set(public) | {PROOF_PATH}
    public_hashes = set(hashes.values()) | {io.sha256(raw) for host in spec.hosts
                                           for raw in package_files(spec, host).values()}
    bindings = {}
    evidence_paths = set(capture.config["acceptance"].values())
    if None in evidence_paths or len(evidence_paths) != len(spec.hosts):
        raise DataError("acceptance statement requires a distinct configured evidence path for every host")

    def binding(entry):
        if not isinstance(entry, dict) or set(entry) != {"path", "sha256"}:
            raise DataError("acceptance statement evidence requires path/SHA256")
        path = io.relative_path(entry["path"])
        digest = entry["sha256"]
        if path in public_paths or not isinstance(digest, str) or not metadata.HASH.fullmatch(digest):
            raise DataError("acceptance statement contains invalid or public evidence bindings")
        if path in bindings and bindings[path] != digest:
            raise DataError("acceptance statement has conflicting private input bindings")
        bindings[path] = digest
        return path

    for host, entry in proof["hosts"].items():
        if not isinstance(entry, dict) or set(entry) != {"evidence", "artifacts"}:
            raise DataError("acceptance statement host has invalid fields")
        if binding(entry["evidence"]) != capture.config["acceptance"][host]:
            raise DataError("acceptance statement evidence path differs from release config")
        if not isinstance(entry["artifacts"], list) or not entry["artifacts"]:
            raise DataError("acceptance statement requires nonempty raw artifact bindings")
        seen = set()
        for artifact in entry["artifacts"]:
            path = binding(artifact)
            if path in seen or path in evidence_paths or artifact["sha256"] in public_hashes:
                raise DataError("acceptance statement has duplicate or public raw artifacts")
            seen.add(path)
    return bindings


def proof_at_head(spec):
    if spec.boundary_root is None:
        return False
    prefix = spec.root.relative_to(spec.boundary_root).as_posix()
    path = PROOF_PATH if prefix == "." else prefix + "/" + PROOF_PATH
    result = subprocess.run(["git", "ls-tree", "-z", "HEAD", "--", path],
        cwd=spec.boundary_root, capture_output=True, timeout=30)
    if result.returncode:
        raise DataError("cannot determine the frozen acceptance statement from Git HEAD")
    return bool(result.stdout)


def capture_committed(spec, capture):
    if spec.boundary_root is None:
        raise DataError("committed acceptance requires a trusted Git source boundary")
    raw = io.read_file(spec.root, PROOF_PATH, boundary_root=spec.boundary_root, limit=PROOF_LIMIT)
    proof = io.parse_json(raw, what="acceptance statement")
    capture.private_hashes = _bindings(spec, capture, proof)
    capture.proof_inputs = {PROOF_PATH: raw}
    capture.accepted = dict(capture.config["acceptance"])
    provenance = metadata.git_provenance(spec.boundary_root, spec.product_id, spec.version)
    if provenance["source_revision"] is None or provenance["working_tree_dirty"] is not False or \
            provenance["tag"] != f"{spec.product_id}/v{spec.version}":
        raise DataError("committed acceptance requires clean canonical tagged Git source")
    source_git.validate_head_inputs(spec.boundary_root, spec, capture, provenance["source_revision"])
    return capture
