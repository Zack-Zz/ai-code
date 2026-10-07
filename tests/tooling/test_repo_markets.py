"""Native repository markets point only to trusted, built plugin directories."""

import json
from io import BytesIO
import hashlib
from pathlib import Path
import shutil
import tempfile
import unittest
import zipfile
from unittest import mock

try:
    from .test_registry import add_plugin, write_json
except ImportError:
    from test_registry import add_plugin, write_json

from plugin_tools import io
from plugin_tools.build import build_plugins
from plugin_tools.markets import sync_markets
from plugin_tools.registry import load_catalog

ROOT_MARKETS = {"claude": ".claude-plugin/marketplace.json",
                "codex": ".agents/plugins/marketplace.json", "zcode": "marketplace.json"}


class RepositoryMarketTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="repo-markets-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / "repo"
        add_plugin(self.root, hosts=("claude", "codex", "zcode"), skills=("ask",))
        add_plugin(self.root, "ai-two", "3.2.1", hosts=("claude",))
        write_json(self.root / "catalog.json", {"schema_version": 1, "plugins": [
            {"path": "plugins/ai-one"}, {"path": "plugins/ai-two"},
        ]})
        build_plugins(self.root, load_catalog(self.root), self.root / "dist")

    def market_files(self):
        return {relative: (self.root / relative).read_bytes() for relative in ROOT_MARKETS.values()
                if (self.root / relative).is_file()}

    def test_sync_builds_native_root_markets_from_actual_packages_and_is_reproducible(self):
        before = {path.relative_to(self.root).as_posix(): path.read_bytes()
                  for path in self.root.rglob("*") if path.is_file()}
        synced = sync_markets(self.root)
        self.assertTrue(synced["ok"], synced)
        for host, relative in ROOT_MARKETS.items():
            data = json.loads((self.root / relative).read_text())
            expected = [("ai-one", "1.0.0")]
            if host == "claude":
                self.assertEqual(data["owner"], {"name": "ai-code"})
                expected.append(("ai-two", "3.2.1"))
            self.assertEqual([(item["name"], item["version"]) for item in data["plugins"]], expected)
            for item in data["plugins"]:
                source = item["source"]["path"] if host == "codex" else item["source"]
                self.assertEqual(source, f"./dist/{host}/{item['name']}")
                self.assertTrue((self.root / source / "artifact.json").is_file())
        after = {path.relative_to(self.root).as_posix(): path.read_bytes()
                 for path in self.root.rglob("*") if path.is_file()}
        self.assertEqual(set(after) - set(before), set(ROOT_MARKETS.values()) | {"marketplaces.lock.json"})
        self.assertTrue(all(after[relative] == payload for relative, payload in before.items()))
        first = self.market_files()
        self.assertTrue(sync_markets(self.root)["ok"])
        self.assertEqual(self.market_files(), first)
        self.assertTrue(sync_markets(self.root, check=True)["ok"])
        receipt = json.loads((self.root / "marketplaces.lock.json").read_text())
        self.assertEqual(receipt, {"schema_version": 1, "files": {
            relative: hashlib.sha256(payload).hexdigest() for relative, payload in first.items()}})

    def test_check_reports_missing_and_drifted_market_without_writing(self):
        checked = sync_markets(self.root, check=True)
        self.assertFalse(checked["ok"])
        self.assertTrue(any("marketplace.json" in problem for problem in checked["problems"]))
        self.assertEqual(self.market_files(), {})
        self.assertTrue(sync_markets(self.root)["ok"])
        path = self.root / "marketplace.json"
        market = json.loads(path.read_text())
        market["plugins"][0]["source"] = "./plugins/ai-one"
        write_json(path, market)
        before = self.market_files()
        checked = sync_markets(self.root, check=True)
        self.assertFalse(checked["ok"])
        self.assertEqual(self.market_files(), before)

    def test_invalid_dist_identity_paths_and_missing_payload_prevent_all_writes(self):
        path = self.root / "dist/index.json"
        original = json.loads(path.read_text())
        for field, value in (("package_dir", "../elsewhere"), ("package_content_hash", "0" * 64)):
            with self.subTest(field=field):
                data = json.loads(json.dumps(original))
                data["plugins"]["ai-one"]["hosts"]["codex"][field] = value
                write_json(path, data)
                with self.assertRaises(io.DataError):
                    sync_markets(self.root)
                self.assertEqual(self.market_files(), {})
        write_json(path, original)
        (self.root / "dist/codex/ai-one/README.md").unlink()
        with self.assertRaises(io.DataError):
            sync_markets(self.root)
        self.assertEqual(self.market_files(), {})

    def test_unknown_or_user_edited_market_is_preserved_before_any_other_write(self):
        path = self.root / "marketplace.json"
        write_json(path, {"name": "user-market", "plugins": []})
        before = path.read_bytes()
        with self.assertRaises(io.ConflictError):
            sync_markets(self.root)
        self.assertEqual(path.read_bytes(), before)
        self.assertFalse((self.root / ROOT_MARKETS["claude"]).exists())
        self.assertFalse((self.root / ROOT_MARKETS["codex"]).exists())

    def test_symlinked_destination_and_dist_market_are_rejected_without_external_writes(self):
        outside = self.base / "outside"
        outside.mkdir()
        (self.root / ".agents").mkdir()
        (self.root / ".agents/plugins").symlink_to(outside, target_is_directory=True)
        with self.assertRaises(io.DataError):
            sync_markets(self.root)
        self.assertEqual(list(outside.iterdir()), [])
        self.assertFalse((self.root / ROOT_MARKETS["claude"]).exists())
        (self.root / ".agents/plugins").unlink()
        market = self.root / "dist/claude/.claude-plugin/marketplace.json"
        payload = outside / "marketplace.json"
        payload.write_bytes(market.read_bytes())
        market.unlink()
        market.symlink_to(payload)
        with self.assertRaises(io.DataError):
            sync_markets(self.root)

    def test_owned_stale_market_can_update_after_source_and_dist_version_change(self):
        self.assertTrue(sync_markets(self.root)["ok"])
        before = self.market_files()
        manifest_path = self.root / "plugins/ai-two/product.json"
        manifest = json.loads(manifest_path.read_text())
        manifest["version"] = "3.3.0"
        write_json(manifest_path, manifest)
        shutil.rmtree(self.root / "dist")
        build_plugins(self.root, load_catalog(self.root), self.root / "dist")
        self.assertFalse(sync_markets(self.root, check=True)["ok"])
        try:
            updated = sync_markets(self.root)
        except io.ConflictError as exc:
            self.fail(f"owned generated market should update: {exc}")
        self.assertTrue(updated["ok"])
        after = self.market_files()
        self.assertNotEqual(before[ROOT_MARKETS["claude"]], after[ROOT_MARKETS["claude"]])
        self.assertEqual(before[ROOT_MARKETS["codex"]], after[ROOT_MARKETS["codex"]])
        self.assertEqual(before[ROOT_MARKETS["zcode"]], after[ROOT_MARKETS["zcode"]])
        data = json.loads(after[ROOT_MARKETS["claude"]])
        self.assertEqual(data["plugins"][1]["version"], "3.3.0")
        self.assertTrue(sync_markets(self.root, check=True)["ok"])

    def test_owned_market_user_edit_and_unknown_receipt_fields_are_preserved(self):
        self.assertTrue(sync_markets(self.root)["ok"])
        native = self.root / "marketplace.json"
        data = json.loads(native.read_text())
        data["plugins"][0]["description"] = "User customization"
        write_json(native, data)
        before = self.market_files()
        receipt = self.root / "marketplaces.lock.json"
        self.assertTrue(receipt.is_file(), "successful synchronization must record native ownership")
        receipt_before = receipt.read_bytes()
        with self.assertRaises(io.ConflictError):
            sync_markets(self.root)
        self.assertEqual(self.market_files(), before)
        self.assertEqual(receipt.read_bytes(), receipt_before)
        for invalid in ({"schema_version": 1, "files": {"../outside.json": "0" * 64}},
                        {"schema_version": 1, "files": {}, "approved": True},
                        {"schema_version": True, "files": {}}):
            with self.subTest(receipt=invalid):
                write_json(receipt, invalid)
                with self.assertRaises(io.DataError):
                    sync_markets(self.root)
                self.assertEqual(self.market_files(), before)

    def test_late_second_market_conflict_keeps_first_success_owned(self):
        from plugin_tools import markets

        write_market = markets._write_market
        user_market = {"name": "late-user-market", "plugins": []}

        def inject_second_market(root, relative, payload, previous):
            write_market(root, relative, payload, previous)
            if relative == ROOT_MARKETS["claude"]:
                write_json(root / ROOT_MARKETS["codex"], user_market)

        with mock.patch.object(markets, "_write_market", side_effect=inject_second_market):
            with self.assertRaises(io.ConflictError):
                sync_markets(self.root)
        self.assertEqual(json.loads((self.root / ROOT_MARKETS["codex"]).read_text()), user_market)
        self.assertTrue((self.root / "marketplaces.lock.json").is_file(), "first successful native write must stay owned")
        receipt = json.loads((self.root / "marketplaces.lock.json").read_text())
        self.assertEqual(receipt["files"], {ROOT_MARKETS["claude"]:
                         hashlib.sha256((self.root / ROOT_MARKETS["claude"]).read_bytes()).hexdigest()})
        self.assertFalse((self.root / ROOT_MARKETS["zcode"]).exists())

    def test_catalog_change_after_distribution_validation_prevents_publication(self):
        from plugin_tools import markets

        validate = markets._validate_dist

        def alter_catalog(root, specs):
            result = validate(root, specs)
            write_json(root / "catalog.json", {"schema_version": 1, "plugins": [{"path": "plugins/ai-one"}]})
            return result

        with mock.patch.object(markets, "_validate_dist", side_effect=alter_catalog):
            with self.assertRaisesRegex(io.DataError, "catalog.*changed"):
                sync_markets(self.root)
        self.assertEqual(self.market_files(), {})
        self.assertFalse((self.root / "marketplaces.lock.json").exists())

    def test_final_distribution_capture_cannot_adopt_payload_or_zip_drift(self):
        from plugin_tools import markets

        verify_zip = markets._verify_zip
        package_file = self.root / "dist/codex/ai-one/README.md"
        archive_file = self.root / "dist/codex/ai-one-1.0.0.zip"
        original_package = package_file.read_bytes()
        original_archive = archive_file.read_bytes()
        for mutation in ("package", "archive"):
            with self.subTest(mutation=mutation):
                for relative in (*ROOT_MARKETS.values(), "marketplaces.lock.json"):
                    (self.root / relative).unlink(missing_ok=True)
                package_file.write_bytes(original_package)
                archive_file.write_bytes(original_archive)
                mutated = False

                def change_after_trusted_validation(path, spec, host, artifact):
                    nonlocal mutated
                    verify_zip(path, spec, host, artifact)
                    if host == "codex" and spec.product_id == "ai-one":
                        if mutation == "package":
                            package_file.write_bytes(b"Changed after trusted validation\n")
                        else:
                            archive_file.write_bytes(original_archive + b"Changed after trusted validation")
                        mutated = True

                with mock.patch.object(markets, "_verify_zip", side_effect=change_after_trusted_validation):
                    with self.assertRaisesRegex(io.DataError, "distribution.*changed|distribution.*differs"):
                        sync_markets(self.root)
                self.assertTrue(mutated, "the fixture must change bytes after real validation")
                self.assertEqual(self.market_files(), {})
                self.assertFalse((self.root / "marketplaces.lock.json").exists())

    def test_archive_verification_uses_the_same_bytes_as_its_checked_hash(self):
        from plugin_tools import markets

        archive = self.root / "dist/codex/ai-one-1.0.0.zip"
        good_bytes = archive.read_bytes()
        buffer = BytesIO(good_bytes)
        with zipfile.ZipFile(buffer, "a") as output:
            output.writestr("ai-two/untrusted.txt", b"foreign archive input")
        hostile_bytes = buffer.getvalue()
        archive.write_bytes(hostile_bytes)
        index_path = self.root / "dist/index.json"
        index = json.loads(index_path.read_text())
        index["plugins"]["ai-one"]["hosts"]["codex"]["zip_sha256"] = hashlib.sha256(hostile_bytes).hexdigest()
        write_json(index_path, index)
        verify_zip = markets._verify_zip

        def temporarily_show_different_archive(candidate, spec, host, artifact):
            if host == "codex" and spec.product_id == "ai-one" and isinstance(candidate, (str, Path)):
                archive.write_bytes(good_bytes)
                try:
                    verify_zip(candidate, spec, host, artifact)
                finally:
                    archive.write_bytes(hostile_bytes)
            else:
                verify_zip(candidate, spec, host, artifact)

        with mock.patch.object(markets, "_verify_zip", side_effect=temporarily_show_different_archive):
            with self.assertRaisesRegex(io.DataError, "ZIP|archive"):
                sync_markets(self.root)
        self.assertEqual(self.market_files(), {})
        self.assertFalse((self.root / "marketplaces.lock.json").exists())

    def test_exact_existing_market_can_be_adopted_without_receipt_and_receipt_link_is_rejected(self):
        self.assertTrue(sync_markets(self.root)["ok"])
        receipt = self.root / "marketplaces.lock.json"
        before = self.market_files()
        receipt.unlink()
        self.assertTrue(sync_markets(self.root)["ok"])
        self.assertEqual(self.market_files(), before)
        self.assertTrue(sync_markets(self.root, check=True)["ok"])
        outside = self.base / "receipt.json"
        outside.write_bytes(receipt.read_bytes())
        receipt.unlink()
        receipt.symlink_to(outside)
        with self.assertRaises(io.DataError):
            sync_markets(self.root)
        self.assertEqual(self.market_files(), before)


if __name__ == "__main__":
    unittest.main()
