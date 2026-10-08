"""Check, prepare and independently verify local release bundles."""

import os
from pathlib import Path
import tempfile

from .. import io
from ..build import build_plugins
from ..io import DataError, ToolError
from ..git_paths import reject_git_output
from . import integrity, layout, metadata, source_git

LIMITATIONS = ["This is a local release bundle; no installation, upload, marketplace submission or Git change was performed.",
    "Host evidence is a source-bound factual record, not user authorization or marketplace acceptance.",
    "A previous bundle is caller-supplied trusted history with local integrity checks, not proof of a published release.",
    "Raw host-session artifacts remain local; this bundle contains only their bindings and hashes."]


def _report(spec, mode, capture=None, provenance=None, blockers=()):
    blockers = list(blockers)
    pending = sorted(capture.pending if capture is not None else spec.hosts)
    provenance = provenance or {"source_revision": None, "working_tree_dirty": None, "tag": None}
    limitations = list(LIMITATIONS)
    if provenance["source_revision"] is None:
        limitations.append("Git source revision is unavailable; this candidate has no release provenance.")
    if provenance["working_tree_dirty"]:
        limitations.append("The source working tree is dirty; this candidate is not ready for stable publication.")
    if provenance["tag"] is None:
        limitations.append("No identity/version tag currently binds this candidate to HEAD.")
    if pending:
        limitations.append("Real host acceptance is unverified for: " + ", ".join(pending))
    if mode == "stable":
        if provenance["source_revision"] is None:
            blockers.append("stable release requires a Git source revision")
        if provenance["working_tree_dirty"]:
            blockers.append("stable release requires a clean working tree")
        if provenance["tag"] is None:
            blockers.append("stable release requires its identity/version tag at HEAD")
        if pending:
            blockers.append("stable release requires accepted byte-bound evidence for every host")
    ready = not blockers and not pending and provenance["source_revision"] is not None and \
        not provenance["working_tree_dirty"] and provenance["tag"] is not None
    readiness = {"publication_ready": ready, "pending_acceptance": pending,
        "accepted_hosts": sorted(capture.accepted if capture is not None else []),
        "package_content_hashes": capture.package_hashes if capture is not None else {},
        "limitations": limitations}
    return {"ok": not blockers, "publication_ready": ready, "product_id": spec.product_id,
        "version": spec.version, "display_name": spec.manifest["display_name"], "mode": mode,
        "blockers": blockers, "pending_acceptance": pending, "limitations": limitations,
        "readiness": readiness, "source_tree_hash": spec.source_tree_hash, **{key: provenance[key]
            for key in ("source_revision", "working_tree_dirty", "tag")}}


def _context(root, spec, mode, previous=None, tag=None):
    if mode not in {"draft", "stable"}:
        raise DataError("release mode must be draft or stable")
    if spec.boundary_root is not None and Path(root).resolve() != spec.boundary_root:
        raise DataError("release repository differs from the trusted source boundary")
    metadata.validate_listing(spec)
    capture = metadata.capture_release(spec)
    metadata.recheck_inputs(spec, capture)
    integrity.compare_previous(spec, capture, previous)
    provenance = metadata.git_provenance(root, spec.product_id, spec.version, tag)
    if (provenance["source_revision"] is not None and not provenance["working_tree_dirty"] and
            provenance["tag"] is not None and not capture.pending):
        source_git.validate_head_inputs(root, spec, capture, provenance["source_revision"])
    return capture, provenance, _report(spec, mode, capture, provenance)


def _failure(spec, mode, exc):
    return _report(spec, mode or "draft", blockers=[str(exc)])


def check_release(root, spec, mode="draft", previous=None):
    try:
        return _context(root, spec, mode, previous)[2]
    except (ToolError, OSError, UnicodeError, ValueError, TypeError, KeyError, AttributeError) as exc:
        return _failure(spec, mode, exc)


def _output(root, spec, output):
    path = Path(output).absolute()
    reject_git_output(root, path)
    if path.is_symlink():
        raise DataError("release output must not be a symlink")
    path = path.parent.resolve() / path.name
    if path == spec.root or spec.root in path.parents or (Path(root).resolve() / "plugins") in path.parents:
        raise DataError("release output cannot be inside a plugin source directory")
    _empty(path)
    return path


def _empty(path):
    if path.is_symlink() or path.exists() and (not path.is_dir() or any(path.iterdir())):
        raise DataError("release output must be an absent or empty real directory")


def _write_payload(root, files):
    for relative, payload in sorted(files.items()):
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(payload)


def _verify_payload(root, spec, bundle, mode=None, previous=None, context=None):
    actual = integrity.read_tree(bundle)
    manifest = integrity.record(actual)
    mode = manifest["mode"] if mode is None else mode
    if mode != manifest["mode"]:
        raise DataError("requested release mode differs from bundle mode")
    if context is None:
        capture, current, report = _context(root, spec, mode, previous, manifest["tag"] if mode == "stable" else None)
    else:
        capture, current, report = context
    if not report["ok"]:
        return report
    for key, expected in (("product_id", spec.product_id), ("version", spec.version),
                          ("display_name", spec.manifest["display_name"]), ("source_tree_hash", spec.source_tree_hash)):
        if manifest[key] != expected:
            raise DataError(f"release {key} differs from trusted source")
    if mode == "stable" and (manifest["source_revision"] != current["source_revision"] or manifest["working_tree_dirty"]):
        raise DataError("stable release provenance differs from the current tagged source")
    provenance = {key: manifest[key] for key in ("source_revision", "working_tree_dirty", "tag")}
    stored_report = _report(spec, mode, capture, provenance)
    # A clean, tagged publication claim must also describe bytes in its own
    # declared commit, even when the currently inspected checkout is dirty.
    if stored_report["publication_ready"]:
        source_git.validate_head_inputs(root, spec, capture, provenance["source_revision"])
    schema_version = manifest["schema_version"]
    expected = layout.payload(spec, capture, provenance, stored_report, schema_version=schema_version)
    expected["release.json"] = io.dump_json(layout.record(spec, provenance, stored_report, expected,
                                                       schema_version=schema_version))
    if set(actual) != set(expected):
        raise DataError("release closure differs from trusted source-derived payload")
    mismatched = [relative for relative in sorted(expected) if actual[relative] != expected[relative]]
    if mismatched:
        raise DataError("release bytes differ from trusted source-derived payload: " + ", ".join(mismatched[:8]))
    # Authenticate archive contents as well as archive bytes, before any publishing step.
    integrity.historical(Path(bundle) / "release.json")
    metadata.recheck_inputs(spec, capture)
    if context is None:
        current = metadata.git_provenance(root, spec.product_id, spec.version,
                                          manifest["tag"] if mode == "stable" else None)
        report = _report(spec, mode, capture, current)
        if report["publication_ready"]:
            source_git.validate_head_inputs(root, spec, capture, current["source_revision"])
    same_origin = all(current[key] == provenance[key] for key in ("source_revision", "working_tree_dirty", "tag"))
    ready = stored_report["publication_ready"] and report["publication_ready"] and same_origin
    limitations = list(dict.fromkeys(stored_report["limitations"] + report["limitations"]))
    if not same_origin:
        limitations.append("The current Git source differs from the recorded bundle provenance; this bundle is not publication-ready.")
    readiness = dict(stored_report["readiness"], publication_ready=ready, limitations=limitations)
    return dict(stored_report, ok=stored_report["ok"] and report["ok"],
                blockers=list(dict.fromkeys(stored_report["blockers"] + report["blockers"])),
                publication_ready=ready, readiness=readiness, limitations=limitations,
                bundle_provenance=provenance, bundle_readiness=manifest["readiness"],
                current_source={key: report[key] for key in ("source_revision", "working_tree_dirty", "tag", "publication_ready")},
                bundle=str(Path(bundle).absolute()), files_checked=len(actual))


def verify_release(root, spec, bundle, mode=None, previous=None):
    try:
        return _verify_payload(root, spec, bundle, mode, previous)
    except (ToolError, OSError, UnicodeError, ValueError, TypeError, KeyError, AttributeError) as exc:
        return _failure(spec, mode, exc)


def prepare_release(root, spec, output, mode="draft", tag=None, previous=None):
    try:
        output = _output(root, spec, output)
        capture, provenance, report = _context(root, spec, mode, previous, tag)
        if not report["ok"]:
            return report
        # Build outside the checkout so private preparation cannot dirty stable provenance.
        with tempfile.TemporaryDirectory(prefix="ai-release-packages-") as temporary:
            packages = Path(temporary) / "packages"
            build_plugins(root, [spec], packages, hosts=spec.hosts)
            actual_packages = integrity.read_tree(packages)
            if actual_packages != layout.package_outputs(spec, provenance):
                raise DataError("built package payload/provenance differs from the trusted release snapshot")
        files = layout.payload(spec, capture, provenance, report)
        files["release.json"] = io.dump_json(layout.record(spec, provenance, report, files))
        output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=".ai-release-", dir=output.parent) as temporary:
            private = Path(temporary)
            stage = private / "bundle"
            stage.mkdir()
            _write_payload(stage, files)
            verified = _verify_payload(root, spec, stage, mode, previous, (capture, provenance, report))
            if not verified["ok"]:
                return verified
            metadata.recheck_inputs(spec, capture)
            current = metadata.git_provenance(root, spec.product_id, spec.version, tag, excluded=private)
            if current != provenance:
                raise DataError("Git source provenance changed during release preparation")
            _empty(output)
            os.rename(stage, output)
        return dict(report, output_root=str(output), release_manifest=str(output / "release.json"), files_written=len(files))
    except (ToolError, OSError, UnicodeError, ValueError, TypeError, KeyError, AttributeError) as exc:
        return _failure(spec, mode, exc)
