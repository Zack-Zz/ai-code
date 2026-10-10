"""Offline checks for the only optional remote write in release automation."""

import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock
import zipfile

from plugin_tools.registry import load_catalog
from plugin_tools.release import prepare_release
from plugin_tools.release import source_git
from tests.tooling.test_release import refresh_record, release_plugin

SCRIPT = Path(__file__).resolve().parents[1] / ".github/scripts/create_release_draft.py"
module_spec = importlib.util.spec_from_file_location("release_draft", SCRIPT)
draft = importlib.util.module_from_spec(module_spec)
module_spec.loader.exec_module(draft)
SHA = "a" * 40


class DraftTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="ai-draft-test-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.root = self.base / "repo"
        release_plugin(self.root)
        product_path = self.root / "plugins/ai-one/product.json"
        product = json.loads(product_path.read_text())
        product["repository"] = "https://github.com/example/ai-code"
        product_path.write_text(json.dumps(product))
        self.bundle = self.base / "candidate"
        result = prepare_release(self.root, load_catalog(self.root)[0], self.bundle)
        self.assertTrue(result["ok"], result)
        # Keep this candidate deliberately unbound, but give HEAD readers a real
        # repository. These API-contract tests mock eligibility separately;
        # clean tagged acceptance is exercised by the handoff integration tests.
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=self.root, check=True)
        subprocess.run(["git", "add", "."], cwd=self.root, check=True)
        subprocess.run(["git", "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                        "commit", "-qm", "source without an acceptance statement"], cwd=self.root, check=True)
        self.calls = []
        self.remote = {"type": "commit", "sha": SHA}
        self.existing = ""
        self.failure = False
        self.report = {"ok": True, "source_revision": SHA, "working_tree_dirty": False,
                       "tag": "ai-one/v1.0.0", "mode": "stable", "publication_ready": True}
        binding = mock.patch.object(draft, "source_binding", return_value=SHA)
        binding.start()
        self.addCleanup(binding.stop)
        git = mock.patch.object(draft.metadata, "git_provenance", return_value=dict(self.report, tag_commit=SHA))
        git.start()
        self.addCleanup(git.stop)
        blobs = mock.patch.object(source_git, "_head_blob", side_effect=lambda root, revision, relative: (Path(root) / relative).read_bytes())
        blobs.start()
        self.addCleanup(blobs.stop)

    def run_gh(self, args, **kwargs):
        self.calls.append(args)
        if args[1:3] == ["release", "create"]:
            self.assertIn("--draft", args)
            self.assertIn("--verify-tag", args)
            self.assertNotIn("--clobber", args)
            paths = [Path(arg) for arg in args[4:args.index("--repo")] if Path(arg).is_file()]
            self.assertEqual(len({p.name for p in paths}), len(paths))
            archive = next(p for p in paths if p.name.endswith("-release-bundle.zip"))
            with zipfile.ZipFile(archive) as zipped:
                self.assertIn("submissions/claude/plugins/ai-one/.claude-plugin/plugin.json", zipped.namelist())
                self.assertIn("release.json", zipped.namelist())
            return subprocess.CompletedProcess(args, 0, "https://github.com/example/ai-code/releases/tag/ai-one/v1.0.0\n", "")
        if self.failure:
            return subprocess.CompletedProcess(args, 1, "", "network unavailable")
        if "--paginate" in args:
            return subprocess.CompletedProcess(args, 0, self.existing, "")
        return subprocess.CompletedProcess(args, 0, json.dumps({"object": self.remote}), "")

    def call(self):
        return draft.create_draft(self.root, "ai-one", self.bundle, "example/ai-code", run=self.run_gh)

    def test_unbound_real_bundle_cannot_make_any_network_call(self):
        with self.assertRaises(ValueError):
            self.call()
        self.assertEqual(self.calls, [])

    def test_publication_cannot_target_a_repository_other_than_the_source(self):
        with mock.patch.object(draft, "verify_release", return_value=self.report):
            with self.assertRaisesRegex(ValueError, "repository"):
                draft.create_draft(self.root, "ai-one", self.bundle, "other/repo", run=self.run_gh)
        self.assertEqual(self.calls, [])

    def test_tagged_draft_remains_draft_and_uploads_complete_unique_assets(self):
        with mock.patch.object(draft, "verify_release", return_value=self.report):
            result = self.call()
        self.assertTrue(result["ok"])
        self.assertTrue(result["draft"])
        self.assertEqual(sum(args[1:3] == ["release", "create"] for args in self.calls), 1)
        created = next(args for args in self.calls if args[1:3] == ["release", "create"])
        self.assertNotIn('--prerelease', created)

    def test_new_numeric_release_without_stable_acceptance_cannot_create_prerelease(self):
        report = dict(self.report, mode="draft", publication_ready=False)
        with mock.patch.object(draft, "verify_release", return_value=report):
            with self.assertRaisesRegex(ValueError, "stable"):
                self.call()
        self.assertEqual(self.calls, [])

    def test_draft_uploads_installers_and_the_bundle_sha256sums(self):
        with mock.patch.object(draft, "verify_release", return_value=self.report):
            result = self.call()
        expected = {"SHA256SUMS", "release.json", "release-notes.md",
                    "ai-one-1.0.0-release-bundle.zip", "ai-one-1.0.0-release-bundle.sha256"}
        expected.update(f"ai-one-1.0.0-{host}.zip" for host in ("claude", "codex", "zcode"))
        expected.update(f"ai-one-1.0.0-{host}-plugin.zip" for host in ("claude", "codex", "zcode"))
        self.assertEqual(set(result["assets"]), expected)

    def test_schema_one_draft_retains_historical_assets_without_installers(self):
        for path in (self.bundle / "installers").glob("*"):
            path.unlink()
        record = json.loads((self.bundle / "release.json").read_text())
        record["schema_version"] = 1
        (self.bundle / "release.json").write_text(json.dumps(record))
        refresh_record(self.bundle)
        with mock.patch.object(draft, "verify_release", return_value=self.report):
            result = self.call()
        self.assertTrue(result["ok"])
        self.assertIn("SHA256SUMS", result["assets"])
        self.assertFalse(any(name.endswith("-plugin.zip") for name in result["assets"]))

    def test_dirty_wrong_tag_or_unverified_source_prevents_remote_write(self):
        for update in ({"ok": False}, {"working_tree_dirty": True}, {"tag": "other/v1.0.0"}, {"source_revision": None}):
            with self.subTest(update=update), mock.patch.object(draft, "verify_release", return_value=dict(self.report, **update)):
                with self.assertRaises(ValueError):
                    self.call()
        self.assertEqual(self.calls, [])

    def test_existing_release_or_network_failure_never_creates_or_overwrites(self):
        for existing, failure in (("ai-one/v1.0.0\n", False), ("", True)):
            self.calls = []
            self.existing, self.failure = existing, failure
            with mock.patch.object(draft, "verify_release", return_value=self.report):
                with self.assertRaises(ValueError):
                    self.call()
            self.assertFalse(any(args[1:3] == ["release", "create"] for args in self.calls))

    def test_remote_tag_moved_from_reviewed_commit_prevents_creation(self):
        self.remote["sha"] = "b" * 40
        with mock.patch.object(draft, "verify_release", return_value=self.report):
            with self.assertRaises(ValueError):
                self.call()
        self.assertFalse(any(args[1:3] == ["release", "create"] for args in self.calls))

    def test_tag_moved_during_final_local_verification_prevents_remote_write(self):
        verified = [0]
        def verify(*arguments, **options):
            verified[0] += 1
            if verified[0] == 2:
                self.remote["sha"] = "b" * 40
            return self.report
        with mock.patch.object(draft, "verify_release", side_effect=verify):
            with self.assertRaises(ValueError):
                self.call()
        self.assertFalse(any(args[1:3] == ["release", "create"] for args in self.calls))

    def test_post_creation_tag_move_reports_the_existing_draft_for_manual_review(self):
        original = self.run_gh
        def move_after_create(arguments, **options):
            result = original(arguments, **options)
            if arguments[1:3] == ["release", "create"]:
                self.remote["sha"] = "b" * 40
            return result
        with mock.patch.object(draft, "verify_release", return_value=self.report):
            report = draft.create_draft(self.root, "ai-one", self.bundle, "example/ai-code", run=move_after_create)
        self.assertFalse(report["ok"], report)
        self.assertTrue(report["draft"])
        self.assertTrue(report["url"].startswith("https://github.com/"))
        self.assertIn("manual", report["error"])
        self.assertEqual(sum(arguments[1:3] == ["release", "create"] for arguments in self.calls), 1)
        self.assertFalse(any(arguments[1:3] == ["release", "delete"] for arguments in self.calls))

    def test_post_creation_network_failure_keeps_draft_url_and_does_not_retry(self):
        original = self.run_gh
        def fail_after_create(arguments, **options):
            result = original(arguments, **options)
            if arguments[1:3] == ["release", "create"]:
                self.failure = True
            return result
        with mock.patch.object(draft, "verify_release", return_value=self.report):
            report = draft.create_draft(self.root, "ai-one", self.bundle, "example/ai-code", run=fail_after_create)
        self.assertFalse(report["ok"], report)
        self.assertTrue(report["url"])
        self.assertEqual(sum(arguments[1:3] == ["release", "create"] for arguments in self.calls), 1)

    def test_cli_failure_after_creation_retains_result_but_exits_nonzero(self):
        result = {"ok": False, "draft": True, "url": "https://github.com/example/review", "error": "manual review"}
        arguments = [str(SCRIPT), "--plugin", "ai-one", "--bundle", str(self.bundle), "--repository", "example/ai-code"]
        with mock.patch.object(draft, "create_draft", return_value=result), mock.patch.object(draft.sys, "argv", arguments):
            self.assertEqual(draft.main(), 1)

    def test_clean_bundle_record_cannot_hide_current_dirty_or_changed_git(self):
        for update in ({"working_tree_dirty": True}, {"source_revision": "b" * 40}):
            self.calls = []
            with self.subTest(update=update), mock.patch.object(draft, "verify_release", return_value=self.report), \
                    mock.patch.object(draft.metadata, "git_provenance", return_value=dict(self.report, **update)):
                with self.assertRaises(ValueError):
                    self.call()
            self.assertEqual(self.calls, [])

    def test_stable_draft_still_requires_public_inputs_bound_to_head(self):
        with mock.patch.object(draft, "verify_release", return_value=self.report), \
                mock.patch.object(source_git, "_head_blob", return_value=b"different ignored source bytes"):
            with self.assertRaises(draft.io.DataError):
                self.call()
        self.assertEqual(self.calls, [])

    def test_invalid_repository_never_reaches_gh(self):
        with self.assertRaises(ValueError):
            draft.create_draft(self.root, "ai-one", self.bundle, "--repo=attacker/other", run=self.run_gh)
        self.assertEqual(self.calls, [])
