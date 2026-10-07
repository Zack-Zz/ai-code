"""owned_files module: staged-file ownership, plans, receipts and safe apply."""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from workflow import build as wbuild
from workflow import io as wio
from workflow import owned_files as wof
from workflow.io import ConflictError, DataError

REPO_ROOT = Path(__file__).resolve().parents[2]


def managed(target: Path) -> Path:
    return target / ".ai-workflow" / "staged" / "ai-code-workflow"


def receipt_path(target: Path) -> Path:
    return target / ".ai-workflow" / "receipts" / "ai-code-workflow.json"


class OwnedFilesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.td = tempfile.TemporaryDirectory()
        cls.pkg_root = Path(cls.td.name) / "pkg"
        wbuild.build_packages(REPO_ROOT, ["zcode"], cls.pkg_root)
        cls.package = cls.pkg_root / "zcode" / "ai-code-workflow"

    @classmethod
    def tearDownClass(cls):
        cls.td.cleanup()

    def setUp(self):
        self.ws_td = tempfile.TemporaryDirectory()
        self.target = Path(self.ws_td.name) / "project"
        self.target.mkdir()

    def tearDown(self):
        self.ws_td.cleanup()

    def disk_map(self):
        root = managed(self.target)
        if not root.is_dir():
            return {}
        return {p.relative_to(root).as_posix(): wio.sha256_file(p)
                for p in sorted(root.rglob("*")) if p.is_file()}

    def test_stage_plan_is_readonly_then_apply_stages(self):
        plan = wof.plan_operation(self.package, self.target, "stage")
        self.assertEqual(self.disk_map(), {}, "plan must not touch the target")
        self.assertEqual(plan["action"], "stage")
        self.assertEqual(plan["source_artifact_hash"], self._artifact_hash())
        self.assertTrue(all(item["operation"] == "create" for item in plan["items"]))
        self.assertIn("plan_hash", plan)

        result = wof.apply_operation(plan, plan["plan_hash"])
        self.assertTrue(result["applied"])
        self.assertTrue(managed(self.target).is_dir())
        self.assertTrue(receipt_path(self.target).is_file())
        receipt = wio.load_json(receipt_path(self.target))
        self.assertEqual(receipt["product_id"], "ai-code-workflow")
        self.assertEqual(receipt["artifact_hash"], self._artifact_hash())
        self.assertEqual(len(receipt["files"]), len(plan["items"]))

    def _artifact_hash(self):
        return wio.load_json(self.package / "artifact.json")["content_hash"]

    def test_stage_twice_conflicts(self):
        self.stage()
        with self.assertRaises(ConflictError):
            wof.plan_operation(self.package, self.target, "stage")

    def stage(self):
        plan = wof.plan_operation(self.package, self.target, "stage")
        return wof.apply_operation(plan, plan["plan_hash"])

    def test_update_noop_when_identical(self):
        self.stage()
        backups_before = self._backup_dirs()
        plan = wof.plan_operation(self.package, self.target, "update")
        self.assertTrue(all(item["operation"] == "keep" for item in plan["items"]))
        result = wof.apply_operation(plan, plan["plan_hash"])
        self.assertFalse(result["changed"])
        self.assertFalse(result["applied"])
        self.assertEqual(self._backup_dirs(), backups_before, "no-op must not create backups")
        receipt = wio.load_json(receipt_path(self.target))
        self.assertEqual(receipt["last_operation_id"],
                         wio.load_json(receipt_path(self.target))["last_operation_id"])
        # no-op leaves the receipt untouched: compare against the pre-stage copy
        self.assertEqual(receipt["files"], self.disk_map())

    def _backup_dirs(self):
        root = self.target / ".ai-workflow" / "backups"
        return sorted(p.name for p in root.iterdir()) if root.is_dir() else []

    def test_update_replaces_changed_source(self):
        self.stage()
        mutated_host = Path(self.ws_td.name) / "pkg2" / "zcode"
        mutated_host.mkdir(parents=True)
        shutil.copytree(self.pkg_root / "zcode", mutated_host, dirs_exist_ok=True)
        mutated = mutated_host / "ai-code-workflow"
        (mutated / "NOTICE").write_text("changed notice\n")
        # regenerate artifact for the mutated package
        from workflow import package_check as wpc
        art = wio.load_json(mutated / "artifact.json")
        art["files"] = sorted(
            (rel, wio.sha256_file(mutated / rel) if rel == "NOTICE" else sha)
            for rel, sha in art["files"])
        art["content_hash"] = wio.sha256_bytes(wio.canonical_json(art["files"]))
        (mutated / "artifact.json").write_text(json.dumps(art, indent=2, sort_keys=True) + "\n")
        self.assertTrue(wpc.check_package(mutated, "zcode")["ok"], "mutated package must stay valid")

        plan = wof.plan_operation(mutated, self.target, "update")
        ops = {item["operation"] for item in plan["items"]}
        self.assertIn("replace", ops)
        result = wof.apply_operation(plan, plan["plan_hash"])
        self.assertTrue(result["applied"])
        self.assertIn("changed notice", managed(self.target).joinpath("NOTICE").read_text())
        receipt = wio.load_json(receipt_path(self.target))
        self.assertEqual(receipt["artifact_hash"], art["content_hash"])

    def test_user_edited_managed_file_blocks_update(self):
        self.stage()
        notice = managed(self.target) / "NOTICE"
        notice.write_text("user's own edit\n")
        plan = wof.plan_operation(self.package, self.target, "update")
        blocking = [c for c in plan["conflicts"] if c.get("blocking")]
        self.assertTrue(any(c.get("path") == "NOTICE" for c in blocking))
        with self.assertRaises(ConflictError):
            wof.apply_operation(plan, plan["plan_hash"])

    def test_unowned_extra_file_blocks_update_but_not_remove(self):
        self.stage()
        extra = managed(self.target) / "extra-config.json"
        extra.write_text("{}")
        plan = wof.plan_operation(self.package, self.target, "update")
        self.assertTrue(any(c.get("blocking") for c in plan["conflicts"]))

        remove_plan = wof.plan_operation(None, self.target, "remove")
        self.assertTrue(extra.is_file())  # remove plan did not touch anything
        remove_result = wof.apply_operation(remove_plan, remove_plan["plan_hash"])
        self.assertTrue(remove_result["applied"])
        self.assertTrue(extra.is_file(), "unowned file must survive remove")
        self.assertFalse(receipt_path(self.target).exists())
        self.assertFalse((managed(self.target) / "NOTICE").exists(),
                         "owned unmodified files must be removed")

    def test_remove_keeps_user_edited_owned_file(self):
        self.stage()
        notice = managed(self.target) / "NOTICE"
        notice.write_text("user edit\n")
        plan = wof.plan_operation(None, self.target, "remove")
        notice_item = next(i for i in plan["items"] if i["relative_path"] == "NOTICE")
        self.assertEqual(notice_item["operation"], "keep")
        result = wof.apply_operation(plan, plan["plan_hash"])
        self.assertTrue(result["applied"])
        self.assertTrue(notice.is_file(), "user-edited owned file must survive remove")

    def test_apply_rejects_wrong_expected_hash(self):
        self.stage_reset()
        plan = wof.plan_operation(self.package, self.target, "stage")
        with self.assertRaises(DataError):
            wof.apply_operation(plan, "0" * 64)

    def stage_reset(self):
        if managed(self.target).exists():
            shutil.rmtree(managed(self.target))
        if receipt_path(self.target).exists():
            receipt_path(self.target).unlink()

    def test_apply_rejects_stale_plan_after_disk_change(self):
        self.stage()
        plan = wof.plan_operation(self.package, self.target, "update")  # all keep
        # user drops an unowned file between planning and apply
        (managed(self.target) / "sneaky.txt").write_text("x")
        with self.assertRaises(ConflictError):
            wof.apply_operation(plan, plan["plan_hash"])
        (managed(self.target) / "sneaky.txt").unlink()

    def test_operation_id_is_reused_on_rederive(self):
        self.stage()
        plan1 = wof.plan_operation(self.package, self.target, "update")
        plan2 = wof.plan_operation(self.package, self.target, "update",
                                   operation_id=plan1["operation_id"])
        self.assertEqual(plan1["operation_id"], plan2["operation_id"])
        self.assertEqual(plan1["plan_hash"], plan2["plan_hash"],
                         "same operation_id must re-derive the identical plan")

    def test_leftover_pending_operation_reports_recovery(self):
        self.stage()
        op_root = self.target / ".ai-workflow" / "backups" / "op-x"
        op_root.mkdir(parents=True)
        (op_root / "pending-operation.json").write_text('{"operation_id": "op-x"}')
        with self.assertRaises(ConflictError) as ctx:
            wof.plan_operation(self.package, self.target, "update")
        self.assertIn("pending", str(ctx.exception).lower())

    def test_no_receipt_update_conflicts(self):
        with self.assertRaises(ConflictError):
            wof.plan_operation(self.package, self.target, "update")

    def test_remove_without_receipt_conflicts(self):
        with self.assertRaises(ConflictError):
            wof.plan_operation(None, self.target, "remove")

    def test_plan_rejects_escaped_target(self):
        with self.assertRaises(DataError):
            wof.plan_operation(self.package, Path(self.ws_td.name) / "ghost" / ".." / "escape", "stage")

    def test_plan_requires_package_for_stage(self):
        with self.assertRaises(DataError):
            wof.plan_operation(None, self.target, "stage")


if __name__ == "__main__":
    unittest.main()
