"""Host market branding is opt-in, source-bound and independent of native manifests."""

import copy
import json
from pathlib import Path
import tempfile
import unittest

from plugin_tools import io, markets
from plugin_tools.build import build_plugins
from plugin_tools.registry import load_catalog
from plugin_tools.rendering import marketplace_entry, package_files
from tests.tooling.test_registry import add_plugin, write_json
from tests.tooling.test_release import png
from tests.tooling import test_public_markets as public_fixtures

ROOT = Path(__file__).resolve().parents[2]
REVISION = "a" * 40
PATHS = public_fixtures.PATHS
ABSENT = object()


class HostListingTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "repo"
        self.plugin = add_plugin(self.root, hosts=("claude", "codex", "zcode"))
        write_json(self.root / "catalog.json", {"schema_version": 1,
            "plugins": [{"path": "plugins/ai-one"}]})
        self.product = json.loads((self.plugin / "product.json").read_text())
        self.product.update(display_name="AI One", repository="https://github.com/Example/ai-code")
        (self.plugin / "images").mkdir()
        (self.plugin / "images/icon.png").write_bytes(png(64))
        self.product["resources"].append({"source": "images/icon.png", "target": "assets/icon.png", "include": []})
        self.icon_url = f"https://raw.githubusercontent.com/Example/ai-code/{REVISION}/plugins/ai-one/images/icon.png"
        self.listing = {"icon_path": "assets/icon.png", "icon_url": self.icon_url}

    def spec(self, listings=ABSENT):
        product = copy.deepcopy(self.product)
        if listings is not ABSENT:
            product["host_listings"] = listings
        write_json(self.plugin / "product.json", product)
        return load_catalog(self.root)[0]

    def test_local_market_and_download_use_existing_icon_and_product_name(self):
        spec = self.spec({"zcode": self.listing, "claude": {}})
        output = Path(self.temporary.name) / "packages"
        build_plugins(self.root, [spec], output)
        for host in ("claude", "zcode"):
            entry = json.loads((output / host / PATHS[host]).read_text())["plugins"][0]
            self.assertEqual(entry["displayName"], "AI One")
            self.assertEqual(entry["name"], "ai-one")
            self.assertEqual(entry["source"], "./ai-one")
            if host == "zcode":
                self.assertEqual(entry["icon"], self.icon_url)
            else:
                self.assertNotIn("icon", entry)
        self.assertEqual((output / "zcode/ai-one/assets/icon.png").read_bytes(),
                         (self.plugin / "images/icon.png").read_bytes())

    def test_listing_name_is_derived_without_altering_native_manifests(self):
        before = package_files(self.spec(), "zcode")
        spec = self.spec({"zcode": self.listing, "claude": {}})
        self.assertEqual(package_files(spec, "zcode"), before)
        self.product["display_name"] = "Renamed Product"
        for host in ("claude", "zcode"):
            entry = marketplace_entry(self.spec({"zcode": self.listing, "claude": {}}), host)
            self.assertEqual(entry["displayName"], "Renamed Product")

    def test_no_opt_in_preserves_original_market_shape(self):
        spec = self.spec()
        for host in ("claude", "zcode"):
            self.assertEqual(marketplace_entry(spec, host), {
                "name": "ai-one", "version": "1.0.0", "source": "./ai-one",
                "description": "AI capability ai-one"})
        self.assertNotIn("displayName", marketplace_entry(spec, "codex"))

    def test_invalid_host_listing_shapes_are_rejected(self):
        for listings in (None, [], "zcode", {"unknown": {}}, {"codex": {}},
                         {"claude": {"icon": self.icon_url}}, {"claude": None},
                         {"zcode": {}}, {"zcode": {**self.listing, "displayName": "Other"}}):
            with self.subTest(listings=listings):
                with self.assertRaises(io.DataError):
                    self.spec(listings)
        self.product["hosts"] = ["codex"]
        with self.assertRaisesRegex(io.DataError, "declared hosts"):
            self.spec({"zcode": self.listing})

    def test_icon_must_be_a_registered_image_target(self):
        for path in ("assets/missing.png", "README.md", "../icon.png", "/icon.png", True):
            with self.subTest(path=path):
                with self.assertRaisesRegex(io.DataError, "icon_path"):
                    self.spec({"zcode": {**self.listing, "icon_path": path}})

    def test_icon_url_must_pin_the_actual_resource_source_in_this_repository(self):
        urls = [self.icon_url.replace("https:", "http:"),
                self.icon_url.replace(REVISION, "main"),
                self.icon_url.replace("Example/ai-code", "Other/repo"),
                self.icon_url.replace("/images/icon.png", "/assets/icon.png"),
                self.icon_url.replace("raw.githubusercontent.com", "user@raw.githubusercontent.com"),
                self.icon_url + "?token=secret", self.icon_url + "#icon", self.icon_url + "\n", 42]
        for url in urls:
            with self.subTest(url=url):
                with self.assertRaisesRegex(io.DataError, "icon_url"):
                    self.spec({"zcode": {**self.listing, "icon_url": url}})

    def test_resource_source_path_is_canonically_url_encoded(self):
        (self.plugin / "images/icon.png").rename(self.plugin / "images/Code Vow.png")
        self.product["resources"][-1]["source"] = "images/Code Vow.png"
        url = self.icon_url.replace("icon.png", "Code%20Vow.png")
        spec = self.spec({"zcode": {**self.listing, "icon_url": url}})
        self.assertEqual(marketplace_entry(spec, "zcode")["icon"], url)
        with self.assertRaisesRegex(io.DataError, "icon_url"):
            self.spec({"zcode": {**self.listing, "icon_url": url.replace("%20", " ")}})

    def test_codevow_opts_in_to_existing_name_and_image(self):
        spec = next(spec for spec in load_catalog(ROOT) if spec.product_id == "ai-code-workflow")
        zcode = marketplace_entry(spec, "zcode")
        claude = marketplace_entry(spec, "claude")
        self.assertEqual(zcode.get("displayName"), "CodeVow")
        self.assertEqual(claude.get("displayName"), "CodeVow")
        self.assertNotIn("icon", claude)
        listing = spec.manifest["host_listings"]["zcode"]
        self.assertEqual(listing["icon_path"], "assets/codevow.png")
        self.assertEqual(zcode["icon"], listing["icon_url"])

    def test_previously_published_codevow_still_checks_from_its_frozen_source(self):
        self.assertTrue(markets.check_public_markets(ROOT)["ok"])


class FrozenHostListingTests(public_fixtures.FrozenPublicSourceTests):
    def configure_source(self):
        path = self.case.plugin / "product.json"
        product = json.loads(path.read_text())
        product["host_listings"] = {"claude": {}, "zcode": {
            "icon_path": "assets/icon.svg",
            "icon_url": f"https://raw.githubusercontent.com/Example/ai-code/{REVISION}/plugins/ai-one/assets/icon.svg"}}
        write_json(path, product)

    def test_branding_survives_plan_and_finalize(self):
        record = json.loads((self.root / "published/releases/ai-one/1.0.0.json").read_text())
        for host in ("claude", "zcode"):
            entry = record["hosts"][host]["entry"]
            native = json.loads((self.root / PATHS[host]).read_text())["plugins"][0]
            self.assertEqual(entry["displayName"], "AI One")
            self.assertEqual(native["displayName"], "AI One")
            if host == "zcode":
                self.assertEqual(entry["icon"], native["icon"])
        self.assertTrue(markets.check_public_markets(self.root)["ok"])

    def test_resealed_branding_cannot_override_the_frozen_declaration(self):
        for field, value in (("displayName", "Other Product"),
                             ("icon", f"https://raw.githubusercontent.com/Example/ai-code/{'b' * 40}/plugins/ai-one/assets/icon.svg")):
            with self.subTest(field=field):
                files = markets.read_public_files(self.root)
                record_path = "published/releases/ai-one/1.0.0.json"
                record = json.loads(files[record_path])
                record["hosts"]["zcode"]["entry"][field] = value
                native_path = PATHS["zcode"]
                native = json.loads(files[native_path])
                native["plugins"][0][field] = value
                raw = io.dump_json(native)
                lock_path = "published/marketplaces.lock.json"
                lock = json.loads(files[lock_path])
                lock["files"][native_path] = io.sha256(raw)
                self.write({record_path: io.dump_json(record), native_path: raw, lock_path: io.dump_json(lock)})
                with self.assertRaisesRegex(io.DataError, "metadata"):
                    markets.check_public_markets(self.root)
                self.write(files)

    def test_frozen_branding_fields_are_closed_typed_and_paired(self):
        path = self.root / "published/releases/ai-one/1.0.0.json"
        record = json.loads(path.read_text())
        cases = []
        for field in ("icon", "displayName"):
            entry = dict(record["hosts"]["zcode"]["entry"])
            del entry[field]
            cases.append(("zcode", entry))
        cases.extend([
            ("zcode", {**record["hosts"]["zcode"]["entry"], "displayName": None}),
            ("zcode", {**record["hosts"]["zcode"]["entry"], "icon": "http://example.com/icon.png"}),
            ("zcode", {**record["hosts"]["zcode"]["entry"], "other": "metadata"}),
            ("claude", {**record["hosts"]["claude"]["entry"], "icon": "https://example.com/icon.png"}),
            ("claude", {**record["hosts"]["claude"]["entry"], "displayName": ""}),
        ])
        for host, entry in cases:
            with self.subTest(host=host, entry=entry):
                bad = copy.deepcopy(record)
                bad["hosts"][host]["entry"] = entry
                write_json(path, bad)
                with self.assertRaises(io.DataError):
                    markets.check_public_markets(self.root)
        write_json(path, record)
