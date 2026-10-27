"""DSH native bundles use trusted host resources and npm tarball installation."""

from io import BytesIO
import json
from pathlib import Path
import tarfile
import tempfile
import unittest
from unittest import mock

from .test_registry import add_plugin, write_json
from plugin_tools import io
from plugin_tools.build import build_plugins
from plugin_tools.package_check import check_package
from plugin_tools.registry import load_catalog
from plugin_tools.rendering import package_files


class DshBundleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="native-dsh-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "repo"
        self.plugin = add_plugin(self.root, "example", hosts=("codex",), skills=("guide",))
        product = json.loads((self.plugin / "product.json").read_text())
        product.update(schema_version=2, hosts=["codex", "dsh"], host_resources={"dsh": [
            {"source": "adapters/dsh/cordis.patch.yml", "target": "cordis.patch.yml", "include": []}]},
            generated_resources=[{"host": "dsh", "source": "README.md", "target": "persona.json", "format": "json-string"}])
        write_json(self.plugin / "product.json", product)
        write_json(self.plugin / "adapters/dsh/package.json", {
            "description": "Example skills.", "type": "module", "license": "MIT",
            "engines": {"dsh": "0.2.1-rc.3"},
            "exports": {"./package.json": "./package.json"},
            "dsh": {"bundle": {"patch": "./cordis.patch.yml"}}})
        (self.plugin / "adapters/dsh/cordis.patch.yml").write_text("- insert: []\n")
        write_json(self.root / "catalog.json", {"schema_version": 1, "plugins": [{"path": "plugins/example"}]})
        self.output = Path(self.temp.name) / "build"

    def test_build_native_manifest_host_closure_and_independent_package_check(self):
        spec = load_catalog(self.root)[0]
        build_plugins(self.root, [spec], self.output)
        package = self.output / "dsh/example"
        manifest = json.loads((package / "package.json").read_text())
        self.assertEqual((manifest["name"], manifest["version"]), ("example", "1.0.0"))
        self.assertEqual(set(manifest["files"]), set(package_files(spec, "dsh")) | {"artifact.json"})
        self.assertNotIn("scripts", manifest)
        self.assertEqual(json.loads((package / "persona.json").read_text()), "Plugin example\n")
        self.assertFalse((self.output / "codex/example/cordis.patch.yml").exists())
        self.assertFalse((self.output / "codex/example/persona.json").exists())
        self.assertTrue(check_package(package, "dsh", spec)["ok"])
        (package / "cordis.patch.yml").write_text("malicious\n")
        self.assertFalse(check_package(package, "dsh", spec)["ok"])

    def test_dsh_installer_is_reproducible_npm_tgz_with_exact_package_files(self):
        from plugin_tools.archives import read_installer
        spec = load_catalog(self.root)[0]
        build_plugins(self.root, [spec], self.output)
        second = Path(self.temp.name) / "again"
        build_plugins(self.root, [spec], second)
        archive = self.output / "dsh/example-1.0.0.tgz"
        self.assertEqual(archive.read_bytes(), (second / "dsh/example-1.0.0.tgz").read_bytes())
        files = read_installer(archive.read_bytes(), "example", "dsh")
        actual = {p.relative_to(self.output / "dsh/example").as_posix(): p.read_bytes()
                  for p in (self.output / "dsh/example").rglob("*") if p.is_file()}
        self.assertEqual(files, actual)

    def test_rejects_host_resource_collision_and_unknown_generated_format(self):
        p = json.loads((self.plugin / "product.json").read_text())
        p["host_resources"]["dsh"][0]["target"] = "README.md"
        write_json(self.plugin / "product.json", p)
        with self.assertRaisesRegex(io.DataError, "collision"):
            load_catalog(self.root)
        p["host_resources"]["dsh"][0]["target"] = "cordis.patch.yml"
        p["generated_resources"][0]["format"] = "execute-code"
        write_json(self.plugin / "product.json", p)
        with self.assertRaisesRegex(io.DataError, "format"):
            load_catalog(self.root)

    def test_rejects_install_scripts_and_missing_bundle_patch(self):
        p = self.plugin / "adapters/dsh/package.json"
        manifest = json.loads(p.read_text())
        write_json(p, dict(manifest, scripts={"prepare": "unexpected command"}))
        with self.assertRaisesRegex(io.DataError, "script"):
            load_catalog(self.root)
        write_json(p, dict(manifest, dsh={"bundle": {"patch": "./not-packaged.yml"}}))
        with self.assertRaisesRegex(io.DataError, "patch"):
            load_catalog(self.root)

    def test_generated_resources_cannot_hide_in_cache_directories(self):
        p = self.plugin / "product.json"
        product = json.loads(p.read_text())
        product["generated_resources"][0]["target"] = "__pycache__/persona.json"
        write_json(p, product)
        with self.assertRaisesRegex(io.DataError, "cache"):
            load_catalog(self.root)

    def test_dsh_exports_must_resolve_to_packaged_resources(self):
        p = self.plugin / "adapters/dsh/package.json"
        manifest = json.loads(p.read_text())
        manifest["exports"]["./missing"] = "./outside.js"
        write_json(p, manifest)
        with self.assertRaisesRegex(io.DataError, "export"):
            load_catalog(self.root)

    def test_rejects_tgz_traversal_duplicates_links_and_unknown_bytes(self):
        from plugin_tools.archives import read_installer, verify_installer
        for names, link in [(["package/../escape"], False), (["package/a", "package/a"], False),
                            (["package/a"], True), (["wrong/a"], False)]:
            with self.subTest(names=names, link=link):
                raw = BytesIO()
                with tarfile.open(fileobj=raw, mode="w:gz") as archive:
                    for name in names:
                        member = tarfile.TarInfo(name)
                        member.size = 1
                        if link:
                            member.type = tarfile.SYMTYPE
                            member.linkname = "/etc/passwd"
                        archive.addfile(member, BytesIO(b"x") if not link else None)
                with self.assertRaises(io.DataError):
                    read_installer(raw.getvalue(), "example", "dsh")
        from plugin_tools.archives import installer_bytes
        raw = installer_bytes({"a": b"changed"}, "example", "dsh")
        with self.assertRaisesRegex(io.DataError, "differ"):
            verify_installer(raw, {"a": b"trusted"}, "example", "dsh")

    def test_tgz_metadata_counts_toward_total_decompression_budget(self):
        from plugin_tools import archives
        raw = BytesIO()
        with tarfile.open(fileobj=raw, mode="w:gz", format=tarfile.PAX_FORMAT) as archive:
            member = tarfile.TarInfo("package/package.json")
            member.size = 2
            member.pax_headers = {"comment": "x" * 100000}
            archive.addfile(member, BytesIO(b"{}"))
        self.assertLess(len(raw.getvalue()), 81920)
        with mock.patch.object(archives, "MAX_BYTES", 81920):
            with self.assertRaisesRegex(io.DataError, "decompress|size"):
                archives.read_installer(raw.getvalue(), "example", "dsh")

    def test_tgz_sparse_member_is_rejected_even_with_matching_empty_payload(self):
        from plugin_tools.archives import verify_installer
        raw = BytesIO()
        with tarfile.open(fileobj=raw, mode="w:gz", format=tarfile.GNU_FORMAT) as archive:
            member = tarfile.TarInfo("package/empty")
            member.type = tarfile.GNUTYPE_SPARSE
            member.size = 0
            archive.addfile(member, BytesIO(b""))
        with self.assertRaisesRegex(io.DataError, "type|regular|sparse"):
            verify_installer(raw.getvalue(), {"empty": b""}, "example", "dsh")


class DshReleaseTests(unittest.TestCase):
    def test_four_host_release_prepares_and_reverifies_native_tgz_without_git_writes(self):
        from .test_release import release_plugin
        from plugin_tools.release import prepare_release, verify_release
        from plugin_tools.release.integrity import historical
        with tempfile.TemporaryDirectory(prefix="dsh-release-") as temporary:
            base = Path(temporary)
            root = base / "repo"
            plugin = release_plugin(root)
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
            spec = load_catalog(root)[0]
            bundle = base / "release"
            report = prepare_release(root, spec, bundle)
            self.assertTrue(report["ok"], report)
            self.assertEqual(set(report["pending_acceptance"]), {"claude", "codex", "zcode", "dsh"})
            self.assertTrue((bundle / "installers/ai-one-1.0.0-dsh-plugin.tgz").is_file())
            self.assertFalse((bundle / "installers/ai-one-1.0.0-dsh-plugin.zip").exists())
            self.assertEqual(historical(bundle)[0]["schema_version"], 3)
            self.assertTrue(verify_release(root, spec, bundle)["ok"])
            self.assertFalse((root / ".git").exists())


if __name__ == "__main__":
    unittest.main()
