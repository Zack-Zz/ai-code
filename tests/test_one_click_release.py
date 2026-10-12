"""The main entry freezes truthful, reproducible bundles without remote writes."""

import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest

from tests.tooling.test_release import HOSTS, release_plugin
from tests.tooling.test_registry import write_json

ROOT = Path(__file__).resolve().parents[1]
MODULE = importlib.util.spec_from_file_location("one_click_prepare", ROOT / ".github/scripts/prepare_release.py")
manager = importlib.util.module_from_spec(MODULE)
MODULE.loader.exec_module(manager)


class OneClickReleaseTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name).resolve()
        self.root = self.base / "repo"
        self.plugin = release_plugin(self.root)
        self.git("init", "-b", "main")
        self.git("config", "user.name", "Test")
        self.git("config", "user.email", "test@example.com")
        self.commit()
        self.revision = self.git("rev-parse", "HEAD")

    def git(self, *args):
        result = subprocess.run(["git", *args], cwd=self.root, capture_output=True, text=True, check=True)
        return result.stdout.strip()

    def commit(self):
        self.git("add", ".")
        self.git("commit", "-m", "fixture")
        self.git("update-ref", "refs/remotes/origin/main", "HEAD")

    def freeze(self, revision=None):
        self.assertTrue(hasattr(manager, "freeze_current"), "main entry must resolve and freeze the source automatically")
        return manager.freeze_current(self.root, "ai-one", revision or self.git("rev-parse", "HEAD"))

    def test_main_freezes_canonical_tag_and_builds_all_native_downloads(self):
        result = self.freeze()
        self.assertEqual(result["tag"], "ai-one/v1.0.0")
        self.assertEqual(result["revision"], self.revision)
        self.assertEqual(result["kind"], "stable")
        bundle = self.base / "bundle"
        manager.prepare(self.root, "ai-one", result["tag"], bundle)
        record = json.loads((bundle / "release.json").read_text())["readiness"]
        self.assertEqual(record["pending_acceptance"], sorted(HOSTS))
        self.assertTrue(record["publication_ready"])
        for host in HOSTS:
            self.assertTrue((bundle / f"downloads/ai-one-1.0.0-{host}.zip").is_file())
        self.assertEqual(self.git("remote"), "")

    def test_dirty_source_and_wrong_dispatch_revision_fail_before_creating_tag(self):
        with self.assertRaisesRegex(ValueError, "revision"):
            self.freeze("0" * 40)
        (self.plugin / "release/NOTES.md").write_text("Changed after dispatch")
        with self.assertRaisesRegex(ValueError, "clean"):
            self.freeze()
        self.assertEqual(self.git("tag"), "")

    def test_assume_unchanged_public_bytes_are_bound_before_creating_tag(self):
        self.git("update-index", "--assume-unchanged", "plugins/ai-one/release/NOTES.md")
        (self.plugin / "release/NOTES.md").write_text("Hidden from git status")
        with self.assertRaisesRegex((ValueError, manager.io.ToolError), "bytes differ"):
            self.freeze()
        self.assertEqual(self.git("tag"), "")

    def test_retry_after_unrelated_main_commit_reuses_original_frozen_bytes(self):
        first = self.freeze()
        original = self.base / "original"
        manager.prepare(self.root, "ai-one", first["tag"], original)
        (self.root / "published").mkdir()
        (self.root / "published/receipt.json").write_text("{}")
        self.commit()
        dispatched = self.git("rev-parse", "HEAD")
        self.assertNotEqual(dispatched, self.revision)
        retry = self.freeze(dispatched)
        self.assertEqual(retry["revision"], self.revision)
        self.assertEqual(self.git("rev-parse", "HEAD"), self.revision)
        second = self.base / "second"
        manager.prepare(self.root, "ai-one", retry["tag"], second)
        bytes_at = lambda root: {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}
        self.assertEqual(bytes_at(original), bytes_at(second))

    def test_same_version_with_new_public_bytes_refuses_to_move_existing_tag(self):
        self.freeze()
        (self.plugin / "release/NOTES.md").write_text("Different version description")
        self.commit()
        with self.assertRaisesRegex((ValueError, manager.io.ToolError), "version|bytes differ"):
            self.freeze()
        self.assertEqual(self.git("rev-parse", "ai-one/v1.0.0^{commit}"), self.revision)

    def test_removing_optional_public_proof_is_also_a_same_version_change(self):
        proof = self.plugin / "release/acceptance-proof.json"
        proof.write_text('{}')
        self.commit()
        self.git("tag", "ai-one/v1.0.0")
        proof.unlink()
        self.commit()
        dispatched = self.git("rev-parse", "HEAD")
        with self.assertRaisesRegex(ValueError, "version"):
            self.freeze(dispatched)
        self.assertEqual(self.git("rev-parse", "HEAD"), dispatched)

    def test_hidden_deletion_of_head_proof_fails_before_creating_tag(self):
        proof = self.plugin / "release/acceptance-proof.json"
        proof.write_text('{}')
        self.commit()
        self.git("update-index", "--skip-worktree", "plugins/ai-one/release/acceptance-proof.json")
        proof.unlink()
        with self.assertRaisesRegex(ValueError, "proof"):
            self.freeze()
        self.assertEqual(self.git("tag"), "")

    def test_source_must_be_on_main_and_preview_kind_is_derived(self):
        manifest = json.loads((self.plugin / "product.json").read_text())
        manifest["version"] = "1.0.1-preview.2"
        write_json(self.plugin / "product.json", manifest)
        self.git("add", ".")
        self.git("commit", "-m", "preview")
        with self.assertRaisesRegex(ValueError, "main"):
            self.freeze()
        self.git("update-ref", "refs/remotes/origin/main", "HEAD")
        result = self.freeze()
        self.assertEqual(result["kind"], "preview")
        self.assertEqual(result["mode"], "draft")
        self.assertEqual(result["tag"], "ai-one/v1.0.1-preview.2")


if __name__ == "__main__":
    unittest.main()
