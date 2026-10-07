"""A draft's recorded provenance cannot promote current source publication eligibility."""

import json
from pathlib import Path
import unittest
from unittest import mock

from plugin_tools import io
from plugin_tools.release import check_release, prepare_release, verify_release
from plugin_tools.release import core, layout, metadata
from tests.tooling import test_release_source_git as git_fixtures


class VerifyProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.fixture = git_fixtures.ReleaseSourceGitTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.case = self.fixture.case
        self.root = self.case.root
        self.bundle = self.case.base / "bundle"

    def new_commit(self):
        self.fixture.git("add", "-A")
        self.fixture.git("-c", "user.name=Release Fixture", "-c", "user.email=fixture@example.invalid",
                         "commit", "--no-verify", "-qm", "later isolated fixture commit")

    def prepare(self):
        result = prepare_release(self.root, self.case.spec(), self.bundle)
        self.assertTrue(result["ok"], result)
        return json.loads((self.bundle / "release.json").read_text())

    def test_resealed_clean_draft_cannot_upgrade_a_dirty_source_or_uncommitted_bytes(self):
        self.case.accept()
        self.fixture.commit()
        (self.case.plugin / "README.md").write_text("Changed public bytes outside HEAD.\n")
        self.case.accept()
        spec = self.case.spec()
        capture = metadata.capture_release(spec)
        current = metadata.git_provenance(self.root, spec.product_id, spec.version)
        self.assertTrue(current["working_tree_dirty"])
        forged = dict(current, working_tree_dirty=False)
        report = core._report(spec, "draft", capture, forged)
        payload = layout.payload(spec, capture, forged, report)
        payload["release.json"] = io.dump_json(layout.record(spec, forged, report, payload))
        self.bundle.mkdir()
        for relative, data in payload.items():
            path = self.bundle / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(data)
        original = (self.bundle / "release.json").read_bytes()
        self.assertFalse(check_release(self.root, spec)["publication_ready"])
        verified = verify_release(self.root, spec, self.bundle)
        self.assertFalse(verified["ok"], verified)
        self.assertFalse(verified["publication_ready"], verified)
        self.assertEqual((self.bundle / "release.json").read_bytes(), original)

    def test_valid_dirty_historical_draft_retains_origin_bytes_after_source_is_committed(self):
        self.fixture.commit()
        (self.case.plugin / "README.md").write_text("An honest dirty candidate.\n")
        recorded = self.prepare()
        self.assertTrue(recorded["working_tree_dirty"])
        original = (self.bundle / "release.json").read_bytes()
        self.new_commit()
        verified = verify_release(self.root, self.case.spec(), self.bundle)
        self.assertTrue(verified["ok"], verified)
        self.assertFalse(verified["publication_ready"])
        self.assertEqual(verified["bundle_provenance"]["source_revision"], recorded["source_revision"])
        self.assertNotEqual(verified["current_source"]["source_revision"], recorded["source_revision"])
        self.assertEqual((self.bundle / "release.json").read_bytes(), original)

    def test_valid_ready_historical_draft_is_integrity_valid_after_head_moves_but_not_publishable(self):
        self.case.accept()
        self.fixture.commit()
        recorded = self.prepare()
        self.assertTrue(recorded["readiness"]["publication_ready"])
        original = (self.bundle / "release.json").read_bytes()
        (self.root / "unrelated.txt").write_text("Other repository maintenance.\n")
        self.new_commit()
        verified = verify_release(self.root, self.case.spec(), self.bundle)
        self.assertTrue(verified["ok"], verified)
        self.assertFalse(verified["publication_ready"], verified)
        self.assertTrue(verified["bundle_readiness"]["publication_ready"])
        self.assertFalse(verified["current_source"]["publication_ready"])
        self.assertEqual((self.bundle / "release.json").read_bytes(), original)

    def test_tag_rebound_to_new_head_cannot_promote_a_bundle_from_the_previous_commit(self):
        self.case.accept()
        self.fixture.commit()
        recorded = self.prepare()
        (self.root / "unrelated.txt").write_text("Other repository maintenance.\n")
        self.new_commit()
        self.fixture.git("tag", "-f", "ai-one/v1.0.0")
        self.assertTrue(check_release(self.root, self.case.spec())["publication_ready"])
        verified = verify_release(self.root, self.case.spec(), self.bundle)
        self.assertTrue(verified["ok"], verified)
        self.assertFalse(verified["publication_ready"], verified)
        self.assertEqual(verified["bundle_provenance"]["source_revision"], recorded["source_revision"])

    def test_source_cleanliness_is_rechecked_after_integrity_validation(self):
        self.case.accept()
        self.fixture.commit()
        self.prepare()
        original = core.integrity.historical
        def dirty_after_integrity(path):
            result = original(path)
            (self.root / "late-unrelated.txt").write_text("Concurrent repository edit.\n")
            return result
        with mock.patch.object(core.integrity, "historical", side_effect=dirty_after_integrity):
            verified = verify_release(self.root, self.case.spec(), self.bundle)
        self.assertTrue(verified["ok"], verified)
        self.assertFalse(verified["publication_ready"], verified)
        self.assertTrue(verified["current_source"]["working_tree_dirty"])

    def test_stable_verification_rejects_a_late_dirty_current_checkout(self):
        self.case.accept()
        self.fixture.commit()
        prepared = prepare_release(self.root, self.case.spec(), self.bundle, mode="stable")
        self.assertTrue(prepared["ok"], prepared)
        original = core.integrity.historical
        def dirty_after_integrity(path):
            result = original(path)
            (self.root / "late-unrelated.txt").write_text("Concurrent repository edit.\n")
            return result
        with mock.patch.object(core.integrity, "historical", side_effect=dirty_after_integrity):
            verified = verify_release(self.root, self.case.spec(), self.bundle)
        self.assertFalse(verified["ok"], verified)
        self.assertFalse(verified["publication_ready"], verified)
        self.assertTrue(any("clean working tree" in item for item in verified["blockers"]), verified)
