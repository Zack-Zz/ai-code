"""Initialization preserves human edits and resumes interrupted owned migrations."""

from unittest.mock import patch
import unittest

from plugin_tools import io, markets
from plugin_tools.registry import load_catalog
from tests.tooling import test_public_markets as fixtures

PATHS = fixtures.PATHS


class InitializationTests(unittest.TestCase):
    def setUp(self):
        self.case = fixtures.PublicMarketTests()
        self.case.setUp()
        self.addCleanup(self.case.doCleanups)
        self.root = self.case.root
        for path in ("published/index.json", "published/marketplaces.lock.json"):
            (self.root / path).unlink()
        (self.root / "published").rmdir()
        legacy = {path: io.dump_json(markets._project_market(load_catalog(self.root), host))
                  for host, path in PATHS.items()}
        for path, raw in legacy.items():
            (self.root / path).write_bytes(raw)
        (self.root / "marketplaces.lock.json").write_bytes(io.dump_json({"schema_version": 1,
            "files": {path: io.sha256(raw) for path, raw in legacy.items()}}))

    def test_edit_after_validated_snapshot_is_preserved_and_rejected(self):
        target = self.root / PATHS["claude"]
        manual = b'{"human-edit":"preserve"}\n'
        reader = markets.read_public_files

        def edit_after_snapshot(root):
            snapshot = reader(root)
            target.write_bytes(manual)
            return snapshot

        with patch.object(markets, "read_public_files", edit_after_snapshot):
            with self.assertRaises(io.ConflictError):
                markets.initialize_public_market(self.root, migrate=True)
        self.assertEqual(target.read_bytes(), manual)

    def interrupt(self, position):
        from plugin_tools.distribution import bootstrap_files
        destinations = set(bootstrap_files())
        writer = markets._write_market
        count = 0

        def interrupt_write(root, path, raw, previous):
            nonlocal count
            if path in destinations:
                count += 1
                if count == position:
                    raise OSError("interrupted destination write")
            return writer(root, path, raw, previous)

        with patch.object(markets, "_write_market", interrupt_write):
            with self.assertRaisesRegex(OSError, "interrupted"):
                markets.initialize_public_market(self.root, migrate=True)

    def test_retry_resumes_after_each_possible_partial_destination_write(self):
        from plugin_tools.distribution import bootstrap_files
        for position in range(2, len(bootstrap_files()) + 1):
            with self.subTest(position=position):
                self.setUp()
                self.interrupt(position)
                result = markets.initialize_public_market(self.root, migrate=True)
                self.assertTrue(result["ok"], result)
                self.assertTrue(markets.check_public_markets(self.root)["ok"])
                self.assertFalse((self.root / "marketplaces.lock.json").exists())

    def test_resume_refuses_new_human_edit_without_overwriting_it(self):
        self.interrupt(2)
        target = self.root / PATHS["claude"]
        manual = b'{"human-edit":"preserve after interruption"}\n'
        target.write_bytes(manual)
        with self.assertRaises(io.ConflictError):
            markets.initialize_public_market(self.root, migrate=True)
        self.assertEqual(target.read_bytes(), manual)

    def test_later_edit_of_completed_file_keeps_recovery_record_and_fails(self):
        writer = markets._write_market
        target = self.root / PATHS["claude"]
        manual = b'{"human-edit":"after first write"}\n'

        def edit_previous_destination(root, path, raw, previous):
            writer(root, path, raw, previous)
            if path == PATHS["codex"]:
                target.write_bytes(manual)

        with patch.object(markets, "_write_market", edit_previous_destination):
            with self.assertRaises(io.ConflictError):
                markets.initialize_public_market(self.root, migrate=True)
        self.assertEqual(target.read_bytes(), manual)
        self.assertTrue((self.root / ".marketplace-initialize.json").exists())

    def test_empty_root_cannot_delete_an_unknown_existing_ownership_receipt(self):
        for path in PATHS.values():
            (self.root / path).unlink()
        receipt = self.root / "marketplaces.lock.json"
        unknown = io.dump_json({"schema_version": 1, "files": {PATHS["claude"]: "0" * 64}})
        receipt.write_bytes(unknown)
        for migrate in (False, True):
            with self.subTest(migrate=migrate):
                with self.assertRaises(io.ConflictError):
                    markets.initialize_public_market(self.root, migrate=migrate)
                self.assertEqual(receipt.read_bytes(), unknown)
                self.assertFalse((self.root / ".marketplace-initialize.json").exists())


if __name__ == "__main__":
    unittest.main()
