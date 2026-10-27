"""DSH bundles cannot downgrade to release formats predating DSH support."""

import json
from pathlib import Path
import tempfile
import unittest

from plugin_tools import io
from plugin_tools.registry import load_catalog
from plugin_tools.release import check_release, prepare_release, verify_release
from plugin_tools.release import integrity, layout, metadata
from tests.tooling.test_registry import write_json
from tests.tooling.test_release import refresh_record, release_plugin


class DshReleaseSchemaTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="ai-release-schema-")
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name).resolve()
        self.root = self.base / "repo"
        plugin = release_plugin(self.root)
        product = json.loads((plugin / "product.json").read_text())
        product.update(schema_version=2, hosts=[*product["hosts"], "dsh"], host_resources={"dsh": [
            {"source": "adapters/dsh/cordis.patch.yml", "target": "cordis.patch.yml", "include": []}]})
        write_json(plugin / "product.json", product)
        write_json(plugin / "adapters/dsh/package.json", {"description": "Useful skills.", "type": "module",
            "engines": {"dsh": "0.2.1-rc.3"}, "dsh": {"bundle": {"patch": "./cordis.patch.yml"}}})
        (plugin / "adapters/dsh/cordis.patch.yml").write_text("- insert: []\n")
        config = json.loads((plugin / "release.json").read_text())
        config["acceptance"]["dsh"] = None
        write_json(plugin / "release.json", config)
        self.spec = load_catalog(self.root)[0]
        self.bundle = self.base / "bundle"

    def prepare(self):
        report = prepare_release(self.root, self.spec, self.bundle)
        self.assertTrue(report["ok"], report)

    def assert_rejected_by_both_verifiers(self):
        with self.subTest(verifier="source-bound"):
            report = verify_release(self.root, self.spec, self.bundle)
            self.assertFalse(report["ok"], report)
            self.assertRegex(" ".join(report["blockers"]), "DSH.*schema 3")
        with self.subTest(verifier="historical"):
            with self.assertRaisesRegex(io.DataError, "DSH.*schema 3"):
                integrity.historical(self.bundle)

    def test_schema_three_dsh_bundle_verifies_with_both_verifiers(self):
        self.prepare()
        self.assertEqual(integrity.historical(self.bundle)[0]["schema_version"], 3)
        self.assertTrue(verify_release(self.root, self.spec, self.bundle)["ok"])

    def test_rehashed_dsh_bundle_cannot_downgrade_release_schema(self):
        self.prepare()
        record_path = self.bundle / "release.json"
        for schema in (2, 1):
            with self.subTest(schema=schema):
                if schema == 1:
                    # This matches the complete legacy closure, including its absent installers.
                    for path in (self.bundle / "installers").iterdir():
                        path.unlink()
                record = json.loads(record_path.read_text())
                record["schema_version"] = schema
                write_json(record_path, record)
                refresh_record(self.bundle)
                self.assert_rejected_by_both_verifiers()

    def test_historical_dsh_bundle_cannot_downgrade_package_index_schema(self):
        self.prepare()
        index_path = self.bundle / "packages/index.json"
        index = json.loads(index_path.read_text())
        index["schema_version"] = 2
        write_json(index_path, index)
        refresh_record(self.bundle)
        self.assertFalse(verify_release(self.root, self.spec, self.bundle)["ok"])
        with self.assertRaisesRegex(io.DataError, "DSH.*schema 3"):
            integrity.historical(self.bundle)

    def test_layout_rejects_legacy_schemas_for_dsh_products(self):
        report = check_release(self.root, self.spec)
        capture = metadata.capture_release(self.spec)
        provenance = {key: report[key] for key in ("source_revision", "working_tree_dirty", "tag")}
        for schema in (1, 2):
            with self.subTest(schema=schema):
                with self.assertRaisesRegex(io.DataError, "DSH.*schema 3"):
                    layout.payload(self.spec, capture, provenance, report, schema_version=schema)
                with self.assertRaisesRegex(io.DataError, "DSH.*schema 3"):
                    layout.record(self.spec, provenance, report, {}, schema_version=schema)


if __name__ == "__main__":
    unittest.main()
