"""Installer ZIPs contain exactly the checked native package, without a market."""

from io import BytesIO
import json
from pathlib import Path
import stat
import tempfile
import unittest
import warnings
import zipfile

from plugin_tools import io
from plugin_tools.registry import load_catalog
from plugin_tools.release import check_release, prepare_release, verify_release
from plugin_tools.release import integrity, layout, metadata
from tests.tooling.test_release import HOSTS, refresh_record, release_plugin


class InstallerTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="ai-installers-test-")
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name).resolve()
        self.root = self.base / "repo"
        release_plugin(self.root)
        self.spec = load_catalog(self.root)[0]
        self.bundle = self.base / "bundle"

    def prepare(self):
        result = prepare_release(self.root, self.spec, self.bundle)
        self.assertTrue(result["ok"], result)

    def installer(self, host):
        return self.bundle / f"installers/ai-one-1.0.0-{host}-plugin.zip"

    def test_prepare_installers_are_exact_native_packages_with_one_root(self):
        self.prepare()
        for host in HOSTS:
            with self.subTest(host=host):
                self.assertTrue(self.installer(host).is_file(), "missing native installer")
                package = self.bundle / f"packages/{host}/ai-one"
                expected = {f"ai-one/{p.relative_to(package).as_posix()}": p.read_bytes()
                            for p in package.rglob("*") if p.is_file()}
                with zipfile.ZipFile(self.installer(host)) as archive:
                    self.assertEqual(archive.namelist(), sorted(expected))
                    self.assertEqual({name: archive.read(name) for name in archive.namelist()}, expected)
                    self.assertIn("ai-one/artifact.json", archive.namelist())
        self.assertEqual(json.loads((self.bundle / "release.json").read_text())["schema_version"], 2)
        self.assertTrue(verify_release(self.root, self.spec, self.bundle)["ok"])
        self.assertEqual(integrity.historical(self.bundle)[0]["schema_version"], 2)

    def test_schema_one_historical_bundle_verifies_and_can_be_previous(self):
        self.prepare()
        # Convert the independently prepared bundle to the exact historical layout.
        for path in (self.bundle / "installers").glob("*"):
            path.unlink()
        record = json.loads((self.bundle / "release.json").read_text())
        record["schema_version"] = 1
        (self.bundle / "release.json").write_bytes(io.dump_json(record))
        refresh_record(self.bundle)
        self.assertTrue(verify_release(self.root, self.spec, self.bundle)["ok"])
        self.assertEqual(integrity.historical(self.bundle)[0]["schema_version"], 1)
        self.assertTrue(check_release(self.root, self.spec, previous=self.bundle)["ok"])
        report = check_release(self.root, self.spec)
        capture = metadata.capture_release(self.spec)
        provenance = {key: report[key] for key in ("source_revision", "working_tree_dirty", "tag")}
        files = layout.payload(self.spec, capture, provenance, report, schema_version=1)
        self.assertFalse(any(name.startswith("installers/") for name in files))
        self.assertEqual(layout.record(self.spec, provenance, report, files, schema_version=1)["schema_version"], 1)

    def test_schema_two_rejects_tampered_or_extra_installer_members_even_with_rehashed_record(self):
        self.prepare()
        path = self.installer("codex")
        self.assertTrue(path.is_file(), "missing native installer")
        original = path.read_bytes()
        with zipfile.ZipFile(BytesIO(original)) as archive:
            expected = {name: archive.read(name) for name in archive.namelist()}
        mutations = [dict(expected, **{"ai-one/extra.txt": b"extra"}),
                     dict(expected, **{"other/plugin.json": b"{}"}),
                     dict(expected, **{"ai-one/skills/ask/SKILL.md": b"tampered"}),
                     {name: value for name, value in expected.items() if name != "ai-one/artifact.json"}]
        for contents in mutations:
            with self.subTest(members=sorted(contents)):
                path.write_bytes(layout.zip_bytes(contents))
                refresh_record(self.bundle)
                self.assertFalse(verify_release(self.root, self.spec, self.bundle)["ok"])
                with self.assertRaisesRegex(io.DataError, "installer"):
                    integrity.historical(self.bundle)
        path.write_bytes(original)
        refresh_record(self.bundle)
        self.assertTrue(verify_release(self.root, self.spec, self.bundle)["ok"])

    def test_schema_version_controls_installer_closure(self):
        self.prepare()
        path = self.installer("codex")
        self.assertTrue(path.is_file(), "missing native installer")
        path.unlink()
        refresh_record(self.bundle)
        with self.assertRaisesRegex(io.DataError, "installer"):
            integrity.historical(self.bundle)
        self.assertFalse(verify_release(self.root, self.spec, self.bundle)["ok"])

    def test_schema_one_cannot_claim_the_new_installer_closure(self):
        self.prepare()
        record = json.loads((self.bundle / "release.json").read_text())
        record["schema_version"] = 1
        (self.bundle / "release.json").write_bytes(io.dump_json(record))
        refresh_record(self.bundle)
        self.assertFalse(verify_release(self.root, self.spec, self.bundle)["ok"])
        with self.assertRaisesRegex(io.DataError, "closure"):
            integrity.historical(self.bundle)

    def test_installer_duplicate_and_symlink_members_are_rejected(self):
        self.prepare()
        path = self.installer("codex")
        self.assertTrue(path.is_file(), "missing native installer")
        with zipfile.ZipFile(path) as archive:
            expected = {name: archive.read(name) for name in archive.namelist()}
        for kind in ("duplicate", "symlink"):
            with self.subTest(kind=kind):
                raw = BytesIO()
                with zipfile.ZipFile(raw, "w") as archive:
                    for index, (name, value) in enumerate(sorted(expected.items())):
                        member = zipfile.ZipInfo(name)
                        member.external_attr = (stat.S_IFLNK if kind == "symlink" and index == 0
                                                else stat.S_IFREG) << 16
                        archive.writestr(member, value)
                        if kind == "duplicate" and index == 0:
                            # Construct an actual duplicate central-directory entry.
                            with warnings.catch_warnings():
                                warnings.simplefilter("ignore", UserWarning)
                                archive.writestr(member, value)
                path.write_bytes(raw.getvalue())
                refresh_record(self.bundle)
                with self.assertRaisesRegex(io.DataError, "installer"):
                    integrity.historical(self.bundle)
                self.assertFalse(verify_release(self.root, self.spec, self.bundle)["ok"])

    def test_layout_rejects_unsupported_or_boolean_schema_versions(self):
        report = check_release(self.root, self.spec)
        capture = metadata.capture_release(self.spec)
        provenance = {key: report[key] for key in ("source_revision", "working_tree_dirty", "tag")}
        for schema in (0, 3, True, "2", None):
            with self.subTest(schema=schema):
                with self.assertRaises(io.DataError):
                    layout.payload(self.spec, capture, provenance, report, schema_version=schema)
                with self.assertRaises(io.DataError):
                    layout.record(self.spec, provenance, report, {}, schema_version=schema)


if __name__ == "__main__":
    unittest.main()
