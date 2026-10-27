"""io module: controlled JSON and path operations."""

import json
import os
import tempfile
import unittest
from pathlib import Path

from workflow import io as wio


class LoadJsonTests(unittest.TestCase):
    def test_rejects_duplicate_keys(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "dup.json"
            p.write_text('{"a": 1, "a": 2}')
            with self.assertRaisesRegex(Exception, "duplicate"):
                wio.load_json(p)

    def test_rejects_oversized_file(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "big.json"
            p.write_text('{"a": "' + "x" * (wio.MAX_JSON_BYTES) + '"}')
            with self.assertRaisesRegex(Exception, "1 MiB"):
                wio.load_json(p)

    def test_rejects_invalid_json(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "bad.json"
            p.write_text("{not json")
            with self.assertRaisesRegex(Exception, "JSON"):
                wio.load_json(p)

    def test_loads_plain_object(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "ok.json"
            p.write_text('{"b": 2, "a": 1}')
            self.assertEqual(wio.load_json(p), {"a": 1, "b": 2})


class ResolveMemberTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.root = Path(self.td.name)
        (self.root / "sub").mkdir()
        (self.root / "sub" / "file.txt").write_text("x")

    def tearDown(self):
        self.td.cleanup()

    def test_resolves_normal_relative_path(self):
        p = wio.resolve_member(self.root, "sub/file.txt")
        self.assertEqual(p, self.root / "sub" / "file.txt")

    def test_rejects_absolute_path(self):
        with self.assertRaisesRegex(Exception, "absolute"):
            wio.resolve_member(self.root, "/etc/passwd")

    def test_rejects_parent_escape(self):
        for rel in ("../x", "sub/../../x", ".."):
            with self.subTest(rel=rel):
                with self.assertRaisesRegex(Exception, "escape|outside"):
                    wio.resolve_member(self.root, rel)

    def test_rejects_symlink_component(self):
        os.symlink(self.root / "sub", self.root / "link")
        with self.assertRaisesRegex(Exception, "symlink"):
            wio.resolve_member(self.root, "link/file.txt")

    def test_rejects_non_regular_file(self):
        with self.assertRaisesRegex(Exception, "regular"):
            wio.resolve_member(self.root, "sub")

    def test_missing_required_file_rejected(self):
        with self.assertRaisesRegex(Exception, "not exist|missing"):
            wio.resolve_member(self.root, "sub/nope.txt")

    def test_allows_missing_target_when_existence_not_required(self):
        p = wio.resolve_member(self.root, "sub/new.txt", must_exist=False)
        self.assertEqual(p.name, "new.txt")


class AtomicWriteTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.path = Path(self.td.name) / "f.json"
        self.path.write_bytes(b'{"v": 1}')

    def tearDown(self):
        self.td.cleanup()

    def test_replaces_when_expected_before_matches(self):
        wio.atomic_write(self.path, b'{"v": 2}', expected_before=b'{"v": 1}')
        self.assertEqual(self.path.read_bytes(), b'{"v": 2}')

    def test_conflicts_when_content_drifted(self):
        self.path.write_bytes(b'{"v": 99}')
        with self.assertRaisesRegex(Exception, "conflict|changed"):
            wio.atomic_write(self.path, b'{"v": 2}', expected_before=b'{"v": 1}')

    def test_conflicts_when_file_unexpectedly_exists(self):
        with self.assertRaises(Exception):
            wio.atomic_write(self.path, b"new", expected_before=None)

    def test_preserves_target_permissions(self):
        import os
        self.path.chmod(0o755)  # non-default: distinguishes preserve vs hardcode
        wio.atomic_write(self.path, b"data", expected_before=b'{"v": 1}')
        self.assertEqual(os.stat(self.path).st_mode & 0o777, 0o755)
        self.path.chmod(0o600)
        wio.atomic_write(self.path, b"data", expected_before=b"data")
        self.assertEqual(os.stat(self.path).st_mode & 0o777, 0o600)

    def test_creates_with_default_0644(self):
        import os
        target = Path(self.td.name) / "new-file"
        wio.atomic_write(target, b"data", expected_before=None)
        self.assertEqual(os.stat(target).st_mode & 0o777, 0o644)

    def test_creates_when_absent_and_none_expected(self):
        target = Path(self.td.name) / "g.json"
        wio.atomic_write(target, b"data", expected_before=None)
        self.assertEqual(target.read_bytes(), b"data")


class LockTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.lock = Path(self.td.name) / ".write.lock"

    def tearDown(self):
        self.td.cleanup()

    def test_exclusive_acquire_and_release(self):
        wio.acquire_lock(self.lock, "op-1")
        with self.assertRaisesRegex(Exception, "lock"):
            wio.acquire_lock(self.lock, "op-2")
        wio.release_lock(self.lock, "op-1")
        wio.acquire_lock(self.lock, "op-3")

    def test_release_refuses_foreign_lock(self):
        wio.acquire_lock(self.lock, "op-1")
        with self.assertRaisesRegex(Exception, "another operation"):
            wio.release_lock(self.lock, "op-2")
        self.assertTrue(self.lock.exists())

    def test_release_lock_with_unparseable_content_gives_manual_guidance(self):
        self.lock.write_text("{not json")
        with self.assertRaisesRegex(Exception, "torn write|manually"):
            wio.release_lock(self.lock, "op-1")

    def test_check_relative_rejects_backslash_and_drive_forms(self):
        for bad in ("a\\b", "C:/x", "a//b", "a/"):
            with self.subTest(bad=bad):
                with self.assertRaisesRegex(Exception, "invalid"):
                    wio.check_relative(bad)

    def test_torn_lock_write_does_not_leave_lock_behind(self):
        # fail mid-write (after creation) so the unlink cleanup branch runs
        import unittest.mock as mock
        with mock.patch("workflow.io.os.fsync", side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                wio.acquire_lock(self.lock, "op-x")
        self.assertFalse(self.lock.exists(), "half-written lock must not linger")

    def test_lock_content_records_operation(self):
        wio.acquire_lock(self.lock, "op-1")
        data = json.loads(self.lock.read_text())
        self.assertEqual(data["operation_id"], "op-1")
        self.assertIn("pid", data)
        self.assertIn("created_at", data)


class HelperTests(unittest.TestCase):
    def test_strict_int_excludes_bool(self):
        self.assertTrue(wio.is_strict_int(3))
        self.assertFalse(wio.is_strict_int(True))
        self.assertFalse(wio.is_strict_int(3.0))
        self.assertFalse(wio.is_strict_int("3"))

    def test_canonical_json_is_stable(self):
        a = wio.canonical_json({"b": 1, "a": {"y": [1, 2], "x": "s"}})
        b = wio.canonical_json({"a": {"x": "s", "y": [1, 2]}, "b": 1})
        self.assertEqual(a, b)

    def test_now_rfc3339_format(self):
        value = wio.now_rfc3339()
        self.assertRegex(value, r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


if __name__ == "__main__":
    unittest.main()
