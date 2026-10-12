"""Real isolated Git fixtures prove public source provenance and metadata output safety."""

import json
from pathlib import Path
import subprocess
import unittest

from tests.tooling import test_release as release_fixtures
from plugin_tools import io
from plugin_tools.build import build_plugins
from plugin_tools.release import check_release, prepare_release, verify_release


class ReleaseSourceGitTests(unittest.TestCase):
    def setUp(self):
        self.case = release_fixtures.ReleaseTests()
        self.case.setUp()
        self.addCleanup(self.case.doCleanups)
        self.root = self.case.root
        self.plugin = self.case.plugin
        self.git_store = self.case.base / "git-store"
        (self.root / ".gitignore").write_text("private/\n*-raw.txt\n*-accepted.json\n__pycache__/\n")

    def git(self, *args):
        result = subprocess.run(["git", *args], cwd=self.root, capture_output=True, text=True, timeout=30)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def commit(self, *, tag=True, separate=False):
        args = ["init", "-q", "-b", "main"]
        if separate:
            args += ["--separate-git-dir", str(self.git_store)]
        self.git(*args)
        self.git("add", "-A")
        self.git("-c", "user.name=Release Fixture", "-c", "user.email=fixture@example.invalid",
                 "commit", "--no-verify", "-qm", "isolated test fixture")
        if tag:
            self.git("tag", "ai-one/v1.0.0")
        self.assertEqual(self.git("status", "--porcelain=v1", "-uall"), "")

    def test_ignored_registered_resource_blocks_stable_even_with_clean_tagged_git(self):
        private = self.plugin / "private/generated.txt"
        private.parent.mkdir()
        private.write_text("Ignored installable bytes.\n")
        product = json.loads((self.plugin / "product.json").read_text())
        product["resources"].append({"source": "private/generated.txt", "target": "extras/generated.txt", "include": []})
        release_fixtures.write_json(self.plugin / "product.json", product)
        self.case.accept()
        self.commit()
        self.assertEqual(self.git("ls-tree", "HEAD", "--", "plugins/ai-one/private/generated.txt"), "")
        report = check_release(self.root, self.case.spec(), mode="stable")
        self.assertFalse(report["ok"], report)
        self.assertFalse(report["publication_ready"], report)
        self.assertTrue(any("HEAD" in item and "private/generated.txt" in item for item in report["blockers"]), report)

    def test_ignored_public_readme_cannot_make_draft_publication_ready(self):
        with (self.root / ".gitignore").open("a") as handle:
            handle.write("plugins/ai-one/release/README_CN.md\n")
        self.case.accept()
        self.commit()
        report = check_release(self.root, self.case.spec(), mode="draft")
        self.assertFalse(report["ok"], report)
        self.assertFalse(report["publication_ready"], report)
        self.assertTrue(any("README_CN.md" in item for item in report["blockers"]), report)

    def test_private_acceptance_records_need_not_be_committed_when_public_inputs_match_head(self):
        self.case.accept()
        self.commit()
        self.assertEqual(self.git("ls-tree", "HEAD", "--", "plugins/ai-one/release/claude-accepted.json"), "")
        self.assertEqual(self.git("ls-tree", "HEAD", "--", "plugins/ai-one/release/claude-raw.txt"), "")
        report = check_release(self.root, self.case.spec(), mode="stable")
        self.assertTrue(report["ok"], report)
        self.assertTrue(report["publication_ready"], report)
        prepared = prepare_release(self.root, self.case.spec(), self.case.output, mode="stable")
        self.assertTrue(prepared["ok"], prepared)

    def test_all_null_acceptance_allows_stable_prepare_and_verify_without_claiming_host_tests(self):
        self.commit()
        for committed in (False, True):
            with self.subTest(committed_acceptance=committed):
                output = self.case.base / f"stable-{committed}"
                report = prepare_release(self.root, self.case.spec(), output, mode="stable",
                                         committed_acceptance=committed)
                self.assertTrue(report["ok"], report)
                self.assertTrue(report["publication_ready"], report)
                self.assertEqual(report["readiness"]["accepted_hosts"], [])
                self.assertEqual(report["pending_acceptance"], sorted(self.case.spec().hosts))
                self.assertTrue(any("unverified" in item for item in report["limitations"]))
                verified = verify_release(self.root, self.case.spec(), output, mode="stable",
                                          committed_acceptance=committed)
                self.assertTrue(verified["ok"], verified)
                self.assertTrue(verified["publication_ready"], verified)
                self.assertEqual(verified["readiness"], report["readiness"])
                notes = (output / "release-notes.md").read_text()
                for host in self.case.spec().hosts:
                    self.assertIn(f"- {host}: unverified", notes)
                self.assertNotIn("accepted evidence", notes)

    def test_pending_host_does_not_skip_missing_public_head_input(self):
        with (self.root / ".gitignore").open("a") as handle:
            handle.write("plugins/ai-one/release/README_CN.md\n")
        self.commit()
        report = check_release(self.root, self.case.spec(), mode="stable")
        self.assertFalse(report["ok"], report)
        self.assertTrue(any("HEAD" in item and "README_CN.md" in item for item in report["blockers"]), report)

    def test_pending_hosts_do_not_skip_changed_public_bytes_hidden_from_git_status(self):
        self.commit()
        self.git("update-index", "--assume-unchanged", "plugins/ai-one/release/NOTES.md")
        (self.plugin / "release/NOTES.md").write_text("Changed public notes hidden from status.\n")
        self.assertEqual(self.git("status", "--porcelain=v1", "-uall"), "")
        report = prepare_release(self.root, self.case.spec(), self.case.output, mode="stable")
        self.assertFalse(report["ok"], report)
        self.assertTrue(any("bytes differ from Git HEAD" in item for item in report["blockers"]), report)
        self.assertFalse(self.case.output.exists())

    def test_all_null_acceptance_still_requires_clean_git_and_correct_tag(self):
        self.commit(tag=False)
        self.git("tag", "wrong/v1.0.0")
        report = prepare_release(self.root, self.case.spec(), self.case.output, mode="stable")
        self.assertFalse(report["ok"], report)
        self.assertTrue(any("identity/version tag" in item for item in report["blockers"]), report)
        self.git("tag", "ai-one/v1.0.0")
        (self.plugin / "release/NOTES.md").write_text("Dirty public notes.\n")
        report = prepare_release(self.root, self.case.spec(), self.case.output, mode="stable")
        self.assertFalse(report["ok"], report)
        self.assertTrue(any("clean working tree" in item for item in report["blockers"]), report)
        self.assertFalse(self.case.output.exists())

    def test_ordinary_nongit_and_dirty_unverified_drafts_stay_available(self):
        report = check_release(self.root, self.case.spec())
        self.assertTrue(report["ok"], report)
        self.assertFalse(report["publication_ready"])
        self.commit()
        (self.plugin / "README.md").write_text("An honest dirty candidate.\n")
        report = check_release(self.root, self.case.spec())
        self.assertTrue(report["ok"], report)
        self.assertTrue(report["working_tree_dirty"])
        self.assertFalse(report["publication_ready"])

    def test_release_cannot_fill_empty_git_tag_directory(self):
        self.commit(tag=False)
        tags = self.root / ".git/refs/tags"
        self.assertEqual(list(tags.iterdir()), [])
        report = prepare_release(self.root, self.case.spec(), tags)
        self.assertFalse(report["ok"], report)
        self.assertTrue(any("Git metadata" in item for item in report["blockers"]), report)
        self.assertEqual(list(tags.iterdir()), [])

    def test_public_build_cannot_fill_git_metadata_directory(self):
        self.commit(tag=False)
        tags = self.root / ".git/refs/tags"
        with self.assertRaisesRegex(io.DataError, "Git metadata"):
            build_plugins(self.root, [self.case.spec()], tags)
        self.assertEqual(list(tags.iterdir()), [])

    def test_separate_git_dir_alias_is_rejected_by_both_artifact_producers(self):
        self.commit(tag=False, separate=True)
        alias = self.case.base / "git-alias"
        alias.symlink_to(self.git_store, target_is_directory=True)
        tags = alias / "refs/tags"
        report = prepare_release(self.root, self.case.spec(), tags)
        self.assertFalse(report["ok"], report)
        self.assertTrue(any("Git metadata" in item for item in report["blockers"]), report)
        with self.assertRaisesRegex(io.DataError, "Git metadata"):
            build_plugins(self.root, [self.case.spec()], tags)
        self.assertEqual(list(tags.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
