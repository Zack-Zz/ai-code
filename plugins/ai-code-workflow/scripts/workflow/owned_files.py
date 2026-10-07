"""Owned-file management: explicit plans, receipts, backups and safe apply.

Scope: only target/.ai-workflow/staged/ai-code-workflow is treated as owned.
The tool never takes over un-owned files, never overwrites user edits, and
never manages host caches or global config. Interrupted operations leave a
pending marker that later calls report instead of blindly replaying.
"""

from __future__ import annotations

import json
import re
import uuid
from pathlib import Path

from . import io as wio
from . import package_check as wpc
from .io import ConflictError, DataError, ToolError

PRODUCT_ID = "ai-code-workflow"
ACTIONS = ("stage", "update", "remove")
OP_ID = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")

_PLAN_KEYS = {"schema_version", "operation_id", "action", "source_package",
              "source_artifact_hash", "target_root", "managed_root",
              "receipt_before_hash", "items", "conflicts", "plan_hash"}
_RECEIPT_KEYS = {"schema_version", "product_id", "version", "managed_root",
                 "artifact_hash", "files", "last_operation_id"}


def managed_root(target_root: Path) -> Path:
    return Path(target_root) / ".ai-workflow" / "staged" / PRODUCT_ID


def receipt_file(target_root: Path) -> Path:
    return Path(target_root) / ".ai-workflow" / "receipts" / f"{PRODUCT_ID}.json"


def product_lock(target_root: Path) -> Path:
    return Path(target_root) / ".ai-workflow" / "receipts" / f"{PRODUCT_ID}.lock"


def backups_root(target_root: Path) -> Path:
    return Path(target_root) / ".ai-workflow" / "backups"


def _plan_hash(plan: dict) -> str:
    payload = {k: v for k, v in plan.items() if k != "plan_hash"}
    return wio.sha256_bytes(wio.canonical_json(payload))


def _scan_disk(root: Path) -> dict:
    """Active (non-cache) files under the managed root: rel -> sha256."""
    if not root.is_dir():
        return {}
    result = {}
    sources = {p.relative_to(root).as_posix() for p in root.rglob("*.py") if p.is_file()}
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise DataError(f"symlinked managed component rejected: {path}")
        if not path.is_dir() and not path.is_file():
            raise DataError(f"non-regular managed component rejected: {path}")
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if wpc.is_passive_cache(rel, sources):
            continue
        result[rel] = wio.sha256_file(path)
    return result


def _validate_roots(target: Path) -> None:
    for rel in (".ai-workflow", ".ai-workflow/staged", ".ai-workflow/receipts",
                ".ai-workflow/backups", f".ai-workflow/staged/{PRODUCT_ID}"):
        wio.resolve_member(target, rel, must_exist=False, allow_directory=True)
    for path in (receipt_file(target), product_lock(target)):
        wio.resolve_member(target, path.relative_to(target).as_posix(), must_exist=False)


def _load_receipt(path: Path, *, root=None, with_bytes=False):
    data, raw = wio.read_json_snapshot(path, root=root)
    if not isinstance(data, dict) or set(data) != _RECEIPT_KEYS:
        raise DataError(f"receipt has unexpected fields: {path}")
    if not wio.is_strict_int(data["schema_version"]) or data["schema_version"] != 1 or data["product_id"] != PRODUCT_ID:
        raise DataError(f"receipt identity mismatch: {path}")
    if not isinstance(data["files"], dict):
        raise DataError(f"receipt files must be an object: {path}")
    if not isinstance(data["managed_root"], str) or not Path(data["managed_root"]).is_absolute():
        raise DataError(f"receipt managed_root must be an absolute path: {path}")
    if not isinstance(data["version"], str) or not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", data["version"]):
        raise DataError(f"receipt version must be a version string: {path}")
    if not isinstance(data["artifact_hash"], str) or not re.fullmatch(r"[0-9a-f]{64}", data["artifact_hash"]):
        raise DataError(f"receipt artifact_hash must be a sha256 hex: {path}")
    if not isinstance(data["last_operation_id"], str) or not OP_ID.fullmatch(data["last_operation_id"]):
        raise DataError(f"receipt last_operation_id is invalid: {path}")
    for rel, sha in data["files"].items():
        wio.check_relative(rel, what="receipt file entry")
        if not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{64}", sha):
            raise DataError(f"receipt hash for {rel} must be a sha256 hex: {path}")
    return (data, raw) if with_bytes else data


def _pending_operations(target_root: Path) -> list:
    pending = []
    root = backups_root(target_root)
    if not root.is_dir():
        return pending
    for op_dir in sorted(root.iterdir()):
        wio.resolve_member(target_root, op_dir.relative_to(target_root).as_posix(), allow_directory=True)
        if not op_dir.is_dir():
            continue
        marker = op_dir / "pending-operation.json"
        wio.resolve_member(target_root, marker.relative_to(target_root).as_posix(), must_exist=False)
        if marker.is_file():
            try:
                data = wio.load_json(marker, root=target_root)
            except DataError:
                data = {"operation_id": op_dir.name}
            pending.append({"operation_id": data.get("operation_id", op_dir.name) if isinstance(data, dict) else op_dir.name,
                            "marker": str(marker)})
    return pending


def _require_no_pending(target_root: Path) -> None:
    pending = _pending_operations(target_root)
    if pending:
        raise ConflictError(
            "an interrupted operation is pending (recovery required before new "
            f"operations): {[p['marker'] for p in pending]}. Recovery basis: "
            "replace/delete items have byte backups under the same operation "
            "directory; create items had no prior content and can be deleted "
            "after verifying their hash matches the pending record. Resolve "
            "manually, then remove the pending marker.")


def _checked_package(package_root) -> tuple[Path, dict, dict]:
    if package_root is None:
        raise DataError("this action requires --package")
    package_root = Path(package_root).resolve()
    report = wpc.check_package(package_root, package_root.parent.name
                               if package_root.parent.name in ("zcode", "codex")
                               else _host_of(package_root))
    if not report["ok"]:
        raise ToolError(f"package check failed: {report['problems']}")
    artifact = wio.load_json(package_root / "artifact.json", root=package_root)
    if not isinstance(artifact, dict) or artifact.get("content_hash") != report["content_hash"] or \
            artifact.get("version") != report["version"] or \
            wio.sha256_bytes(wio.canonical_json(artifact.get("files"))) != report["content_hash"]:
        raise ConflictError("source artifact changed during package validation")
    files = dict(artifact["files"])
    return package_root, report, files


def _host_of(package_root: Path) -> str:
    if (package_root / ".zcode-plugin" / "plugin.json").is_file():
        return "zcode"
    if (package_root / "plugin.json").is_file():
        return "codex"
    raise DataError(f"cannot determine host of package: {package_root}")


def plan_operation(package_root, target_root, action: str, operation_id=None) -> dict:
    """Build a plan without touching the target. operation_id is generated once;
    apply re-derives with the same id so valid plans are not invalidated."""
    if action not in ACTIONS:
        raise DataError(f"action must be one of {ACTIONS}, got {action!r}")
    operation_id = f"op-{uuid.uuid4().hex}" if operation_id is None else operation_id
    if not isinstance(operation_id, str) or not OP_ID.fullmatch(operation_id):
        raise DataError("operation_id must be a bounded lowercase name, not a path")
    target_root = Path(target_root)
    if not target_root.is_dir():
        raise DataError(f"target root does not exist: {target_root}")
    target_root = target_root.resolve()  # canonical form: plans and applies must agree
    _validate_roots(target_root)
    target_abs = str(target_root)
    managed = managed_root(target_root)
    receipt_path = receipt_file(target_root)

    _require_no_pending(target_root)

    receipt_before_hash = None
    conflicts: list[dict] = []
    items: list[dict] = []

    if action in ("stage", "update"):
        package_root, report, package_files = _checked_package(package_root)
        source_package = str(Path(package_root).resolve())
        source_artifact_hash = report["content_hash"]
        receipt = None

        if action == "stage":
            if receipt_path.is_file():
                raise ConflictError(
                    f"package already staged (receipt exists); use action update: {receipt_path}")
            disk = _scan_disk(managed)
            for rel in sorted(disk):
                conflicts.append({
                    "path": rel, "blocking": True,
                    "reason": "un-owned file already present in the managed root"})
            for rel in sorted(package_files):
                items.append({"relative_path": rel, "operation": "create",
                              "expected_before_sha256": None,
                              "desired_sha256": package_files[rel]})
        else:
            if not receipt_path.is_file():
                raise ConflictError(f"no receipt to update: {receipt_path}")
            receipt, receipt_bytes = _load_receipt(receipt_path, root=target_root, with_bytes=True)
            receipt_before_hash = wio.sha256_bytes(receipt_bytes)
            if receipt["managed_root"] != str(managed.resolve() if managed.exists() else managed):
                conflicts.append({"path": "receipt", "blocking": True,
                                  "reason": "receipt managed_root does not match this target"})
            disk = _scan_disk(managed)
            receipt_files = receipt["files"]

            for rel in sorted(set(disk) - set(receipt_files)):
                conflicts.append({"path": rel, "blocking": True,
                                  "reason": "un-owned file present in the managed root"})

            def user_edited(rel):
                return rel in disk and disk[rel] != receipt_files.get(rel)

            for rel in sorted(set(receipt_files) | set(package_files)):
                if rel in package_files:
                    desired = package_files[rel]
                    if rel in receipt_files:
                        if user_edited(rel):
                            conflicts.append({"path": rel, "blocking": True,
                                              "reason": "managed file was edited by the user; refusing to overwrite"})
                            items.append({"relative_path": rel, "operation": "keep",
                                          "expected_before_sha256": disk.get(rel),
                                          "desired_sha256": desired})
                        elif disk.get(rel) == desired:
                            items.append({"relative_path": rel, "operation": "keep",
                                          "expected_before_sha256": desired,
                                          "desired_sha256": desired})
                        else:
                            items.append({"relative_path": rel, "operation": "replace",
                                          "expected_before_sha256": receipt_files[rel],
                                          "desired_sha256": desired})
                    else:
                        if rel in disk:
                            conflicts.append({"path": rel, "blocking": True,
                                              "reason": "un-owned file occupies a package path"})
                            items.append({"relative_path": rel, "operation": "keep",
                                          "expected_before_sha256": disk[rel],
                                          "desired_sha256": desired})
                        else:
                            items.append({"relative_path": rel, "operation": "create",
                                          "expected_before_sha256": None,
                                          "desired_sha256": desired})
                else:
                    if user_edited(rel) or rel not in disk:
                        conflicts.append({"path": rel, "blocking": True,
                                          "reason": "managed file changed since the receipt; "
                                                    "refusing to delete"})
                        items.append({"relative_path": rel, "operation": "keep",
                                      "expected_before_sha256": disk.get(rel),
                                      "desired_sha256": None})
                    else:
                        items.append({"relative_path": rel, "operation": "delete",
                                      "expected_before_sha256": receipt_files[rel],
                                      "desired_sha256": None})
    else:  # remove
        source_package = None
        source_artifact_hash = None
        package_files = None
        if not receipt_path.is_file():
            raise ConflictError(f"nothing staged (no receipt): {receipt_path}")
        receipt, receipt_bytes = _load_receipt(receipt_path, root=target_root, with_bytes=True)
        if receipt["managed_root"] != str(managed):
            raise ConflictError("receipt managed_root does not match this target; refusing remove")
        receipt_before_hash = wio.sha256_bytes(receipt_bytes)
        disk = _scan_disk(managed)
        for rel in sorted(receipt["files"]):
            current = disk.get(rel)
            if current is not None and current == receipt["files"][rel]:
                items.append({"relative_path": rel, "operation": "delete",
                              "expected_before_sha256": current,
                              "desired_sha256": None})
            else:
                conflicts.append({"path": rel, "blocking": False,
                                  "reason": "kept: content differs from the receipt "
                                            "(user edit or drift)"})
                items.append({"relative_path": rel, "operation": "keep",
                              "expected_before_sha256": current,
                              "desired_sha256": None})
        for rel in sorted(set(disk) - set(receipt["files"])):
            conflicts.append({"path": rel, "blocking": False,
                              "reason": "kept: un-owned file, never deleted by remove"})

    plan = {
        "schema_version": 1,
        "operation_id": operation_id,
        "action": action,
        "source_package": source_package,
        "source_artifact_hash": source_artifact_hash,
        "target_root": target_abs,
        "managed_root": str(managed),
        "receipt_before_hash": receipt_before_hash,
        "items": items,
        "conflicts": conflicts,
    }
    plan["plan_hash"] = _plan_hash(plan)
    return plan


def _write_pending(op_root: Path, plan: dict, applied: list) -> None:
    payload = {
        "operation_id": plan["operation_id"],
        "action": plan["action"],
        "started_at": wio.now_rfc3339(),
        "total_items": len(plan["items"]),
        "applied": applied,
        "recovery_basis": [
            {"relative_path": item["relative_path"], "operation": item["operation"],
             "expected_before_sha256": item["expected_before_sha256"],
             "desired_sha256": item["desired_sha256"]}
            for item in plan["items"] if item["operation"] != "keep"
        ],
    }
    path = op_root / "pending-operation.json"
    root = Path(plan["target_root"])
    before = wio.read_owned(path, root=root)
    wio.atomic_write(path, (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode(),
                     expected_before=before, root=root)


def apply_operation(plan: dict, expected_plan_hash: str) -> dict:
    if not isinstance(plan, dict) or set(plan) != _PLAN_KEYS:
        raise DataError("plan has unexpected fields")
    if not wio.is_strict_int(plan["schema_version"]) or plan["schema_version"] != 1:
        raise DataError("plan schema_version must be 1")
    if _plan_hash(plan) != plan["plan_hash"]:
        raise DataError("plan_hash does not match the plan content (plan file tampered)")
    if expected_plan_hash != plan["plan_hash"]:
        raise DataError("expected plan hash does not match the plan")

    target_root = Path(plan["target_root"])
    managed = Path(plan["managed_root"])
    receipt_path = receipt_file(target_root)
    lock = product_lock(target_root)

    if not isinstance(plan["operation_id"], str) or not OP_ID.fullmatch(plan["operation_id"]):
        raise DataError("invalid operation_id")
    if not target_root.is_absolute() or target_root != target_root.resolve():
        raise DataError("plan target_root must be canonical and absolute")
    if managed != managed_root(target_root):
        raise DataError("plan managed_root is outside the product target")
    _validate_roots(target_root)

    _require_no_pending(target_root)

    wio.ensure_directory(target_root, ".ai-workflow/receipts")
    wio.acquire_lock(lock, plan["operation_id"], root=target_root)
    try:
        source = Path(plan["source_package"]) if plan["source_package"] else None
        rederived = plan_operation(source, target_root, plan["action"],
                                   operation_id=plan["operation_id"])
        if rederived["plan_hash"] != plan["plan_hash"]:
            raise ConflictError(
                "target, source package or receipt changed after this plan was made; "
                "re-run files plan")
        if any(c.get("blocking") for c in rederived["conflicts"]):
            raise ConflictError(
                f"conflicts prevent apply: {[c['reason'] for c in rederived['conflicts'] if c.get('blocking')]}")

        changed_items = [i for i in rederived["items"] if i["operation"] != "keep"]
        before_receipt = wio.read_owned(receipt_path, root=target_root)
        before_hash = wio.sha256_bytes(before_receipt) if before_receipt is not None else None
        if before_hash != plan["receipt_before_hash"]:
            raise ConflictError("receipt changed before the operation")
        receipt = None
        if plan["action"] != "remove":
            source, report, _ = _checked_package(source)
            if report["content_hash"] != plan["source_artifact_hash"]:
                raise ConflictError("source package changed before the operation")
            receipt = {
                "schema_version": 1, "product_id": PRODUCT_ID, "version": report["version"],
                "managed_root": str(managed), "artifact_hash": report["content_hash"],
                "files": {i["relative_path"]: i["desired_sha256"]
                          for i in rederived["items"] if i["operation"] != "delete"},
                "last_operation_id": plan["operation_id"],
            }
        same_receipt = False
        if plan["action"] == "update" and before_receipt is not None:
            current_receipt = _load_receipt(receipt_path, root=target_root)
            same_receipt = all(current_receipt[key] == value for key, value in receipt.items()
                               if key != "last_operation_id")
        if not changed_items and same_receipt:
            return {"applied": False, "changed": False,
                    "operation_id": plan["operation_id"],
                    "applied_items": [], "kept_items": len(rederived["items"])}

        op_root = backups_root(target_root) / plan["operation_id"]
        if op_root.exists():
            raise ConflictError(
                f"recovery material for this operation already exists: {op_root}")
        wio.ensure_directory(target_root, op_root.relative_to(target_root).as_posix())
        if before_receipt is not None:
            wio.atomic_write(op_root / "receipt.json", before_receipt,
                             expected_before=None, root=target_root)
        pending_applied: list[str] = []
        _write_pending(op_root, plan, pending_applied)

        def conflict_abort(reason: str):
            _write_pending(op_root, plan, pending_applied)
            raise ConflictError(
                f"{reason}; applied so far: {pending_applied}; recovery material at {op_root}")

        for item in sorted(rederived["items"], key=lambda i: i["relative_path"]):
            rel = item["relative_path"]
            operation = item["operation"]
            if operation == "keep":
                continue
            dest = managed / rel
            if operation == "create":
                if dest.exists() or dest.is_symlink():
                    conflict_abort(f"create target already exists: {rel}")
                src = source / rel
                payload = wio.read_owned(src, root=source)
                if payload is None or wio.sha256_bytes(payload) != item["desired_sha256"]:
                    conflict_abort(f"source package content drift for {rel}")
                wio.ensure_directory(target_root, dest.parent.relative_to(target_root).as_posix())
                wio.atomic_write(dest, payload, expected_before=None, root=target_root)
            elif operation == "replace":
                current = wio.read_owned(dest, root=target_root)
                if current is None or wio.sha256_bytes(current) != item["expected_before_sha256"]:
                    conflict_abort(f"target changed before replace: {rel}")
                src = source / rel
                payload = wio.read_owned(src, root=source)
                if payload is None or wio.sha256_bytes(payload) != item["desired_sha256"]:
                    conflict_abort(f"source package content drift for {rel}")
                backup = op_root / "files" / rel
                wio.ensure_directory(target_root, backup.parent.relative_to(target_root).as_posix())
                wio.atomic_write(backup, current, expected_before=None, root=target_root)
                wio.atomic_write(dest, payload, expected_before=current, root=target_root)
            elif operation == "delete":
                if not dest.is_file():
                    conflict_abort(f"expected an owned file to delete: {rel}")
                current = wio.read_owned(dest, root=target_root)
                if current is None or wio.sha256_bytes(current) != item["expected_before_sha256"]:
                    conflict_abort(f"target changed before delete: {rel}")
                backup = op_root / "files" / rel
                wio.ensure_directory(target_root, backup.parent.relative_to(target_root).as_posix())
                wio.atomic_write(backup, current, expected_before=None, root=target_root)
                wio.delete_owned(dest, root=target_root, expected_before=current)
            else:  # pragma: no cover - plan validation covers this
                conflict_abort(f"unknown operation {operation!r} for {rel}")
            pending_applied.append(f"{operation}:{rel}")
            _write_pending(op_root, plan, pending_applied)

        expected_before = wio.read_owned(receipt_path, root=target_root)
        actual_hash = wio.sha256_bytes(expected_before) if expected_before is not None else None
        if actual_hash != plan["receipt_before_hash"]:
            conflict_abort("receipt changed during the operation")
        if plan["action"] == "remove":
            wio.delete_owned(receipt_path, root=target_root, expected_before=expected_before)
        else:
            wio.ensure_directory(target_root, ".ai-workflow/receipts")
            wio.atomic_write(
                receipt_path,
                (json.dumps(receipt, indent=2, sort_keys=True) + "\n").encode("utf-8"),
                expected_before=expected_before, root=target_root)

        pending = op_root / "pending-operation.json"
        wio.delete_owned(pending, root=target_root,
                         expected_before=wio.read_owned(pending, root=target_root))
        return {"applied": True, "changed": True,
                "operation_id": plan["operation_id"],
                "applied_items": pending_applied,
                "kept_items": sum(1 for i in rederived["items"] if i["operation"] == "keep"),
                "backup_dir": str(op_root)}
    finally:
        wio.release_lock(lock, plan["operation_id"], root=target_root)
