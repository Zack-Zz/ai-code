"""Public versions exercised through registry, packages and release history."""

import json
from pathlib import Path
import tempfile
import unittest

from tests.tooling.test_registry import write_json
from tests.tooling.test_release import release_plugin
from plugin_tools.io import DataError
from plugin_tools.package_check import check_package, read_artifact
from plugin_tools.registry import load_catalog, VERSION_PATTERN as REGISTRY_VERSION_PATTERN
from plugin_tools.release import check_release, prepare_release, verify_release
from plugin_tools.release.integrity import historical
from plugin_tools.versions import VERSION_PATTERN, release_kind, version_key


class VersionTests(unittest.TestCase):
    def test_public_syntax_and_release_kind(self):
        self.assertIs(REGISTRY_VERSION_PATTERN, VERSION_PATTERN)
        for version, kind in (("0.0.0", "stable"), ("1.0.4", "stable"),
                              ("1.0.4-preview.0", "preview"), ("1.0.4-preview.10", "preview")):
            with self.subTest(version=version):
                self.assertIsNotNone(VERSION_PATTERN.fullmatch(version))
                self.assertEqual(release_kind(version), kind)

    def test_rejects_other_suffixes_metadata_leading_zeroes_and_non_strings(self):
        for version in ("01.0.4", "1.00.4", "1.0.04", "1.0.4-preview.01",
                        "1.0.4-preview", "1.0.4-preview.1.2", "1.0.4-rc.1",
                        "1.0.4-preview.-1", "1.0.4-preview.1+build", "1.0.4+build",
                        "v1.0.4", "1.0", "1.0.4\n", " 1.0.4", "１.0.4", "", None, 104):
            with self.subTest(version=version):
                for parse in (version_key, release_kind):
                    with self.assertRaises(DataError):
                        parse(version)

    def test_semver_numeric_precedence(self):
        expected = ["0.9.9", "1.0.4-preview.0", "1.0.4-preview.2", "1.0.4-preview.10",
                    "1.0.4", "1.0.5-preview.0", "1.2.0", "1.10.0", "2.0.0"]
        self.assertEqual(sorted(reversed(expected), key=version_key), expected)


class VersionIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="ai-version-test-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.root = self.base / "repo"
        self.plugin = release_plugin(self.root)

    def spec(self, version):
        for path in (self.plugin / "product.json", *sorted((self.plugin / "adapters").glob("*/plugin.json"))):
            manifest = json.loads(path.read_text())
            write_json(path, dict(manifest, version=version))
        return load_catalog(self.root)[0]

    def prepare(self, version):
        spec = self.spec(version)
        bundle = self.base / version
        report = prepare_release(self.root, spec, bundle)
        self.assertTrue(report["ok"], report)
        return spec, bundle

    def test_preview_bundle_packages_and_independent_verification(self):
        spec, bundle = self.prepare("1.0.4-preview.2")
        self.assertTrue(verify_release(self.root, spec, bundle)["ok"])
        for host in spec.hosts:
            package = bundle / "packages" / host / spec.product_id
            self.assertTrue(check_package(package, host, spec)["ok"])
            artifact = json.loads((package / "artifact.json").read_text())
            for invalid in ("01.0.4", "1.0.4-preview.02", "1.0.4-rc.2", "1.0.4+build"):
                with self.subTest(host=host, version=invalid):
                    write_json(package / "artifact.json", dict(artifact, version=invalid))
                    with self.assertRaisesRegex(DataError, "invalid artifact version"):
                        read_artifact(package)
            write_json(package / "artifact.json", artifact)

    def test_preview_history_uses_numeric_order_and_allows_same_core_stable(self):
        _, previous = self.prepare("1.0.4-preview.2")
        for version in ("1.0.4-preview.10", "1.0.4", "1.0.5-preview.0"):
            with self.subTest(version=version):
                report = check_release(self.root, self.spec(version), previous=previous)
                self.assertTrue(report["ok"], report)
        report = check_release(self.root, self.spec("1.0.4-preview.1"), previous=previous)
        self.assertFalse(report["ok"], report)
        self.assertIn("release version would downgrade the previous version", report["blockers"])

    def test_stable_history_rejects_same_core_preview_downgrade(self):
        _, previous = self.prepare("1.0.4")
        report = check_release(self.root, self.spec("1.0.4-preview.10"), previous=previous)
        self.assertFalse(report["ok"], report)
        self.assertIn("release version would downgrade the previous version", report["blockers"])

    def test_same_preview_is_idempotent_and_rejects_changed_bytes(self):
        spec, previous = self.prepare("1.0.4-preview.2")
        self.assertTrue(check_release(self.root, spec, previous=previous)["ok"])
        (self.plugin / "README.md").write_text("Changed plugin source\n")
        report = check_release(self.root, self.spec(spec.version), previous=previous)
        self.assertFalse(report["ok"], report)
        self.assertIn("immutable release version was reused for different source/package content", report["blockers"])

    def test_numeric_historical_bundle_keeps_original_draft_mode(self):
        spec, bundle = self.prepare("1.0.2")
        release, hashes = historical(bundle)
        self.assertEqual(release["version"], "1.0.2")
        self.assertEqual(release["mode"], "draft")
        self.assertEqual(set(hashes), set(spec.hosts))
        self.assertTrue(verify_release(self.root, spec, bundle)["ok"])
