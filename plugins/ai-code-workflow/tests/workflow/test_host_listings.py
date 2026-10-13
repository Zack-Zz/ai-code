"""Opt-in host listing metadata through the native loader and build path."""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from workflow import build as wb
from workflow import io as wio
from workflow import product as wp

PLUGIN_ROOT = Path(__file__).resolve().parents[2]
ICON_URL = (
    "https://raw.githubusercontent.com/Zack-Zz/ai-code/"
    "91dec3a64731f8de2fb68e49bce9f4228289bbbd/"
    "plugins/ai-code-workflow/assets/codevow.png"
)
LISTING = {"icon_path": "assets/codevow.png", "icon_url": ICON_URL}


class HostListingTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name) / "source"
        shutil.copytree(PLUGIN_ROOT, self.root,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        self.data = wio.load_json(self.root / "product.json")
        self.data.pop("host_listings", None)

    def tearDown(self):
        self.temporary.cleanup()

    def load(self, listing=None):
        if listing is not None:
            self.data["host_listings"] = listing
        (self.root / "product.json").write_text(json.dumps(self.data), encoding="utf-8")
        return wp.load_product(self.root)

    def build(self, listing=None, host="zcode"):
        self.load(listing)
        output = Path(self.temporary.name) / "build"
        wb.build_packages(self.root, [host], output)
        return output / host

    def test_claude_opt_in_renders_listing_name_and_preserves_native_manifest(self):
        output = self.build({"claude": {}}, host="claude")
        entry = wio.load_json(output / ".claude-plugin/marketplace.json")["plugins"][0]
        self.assertEqual(entry["displayName"], self.data["display_name"])
        self.assertNotIn("icon", entry)
        manifest = wio.load_json(output / "ai-code-workflow/.claude-plugin/plugin.json")
        self.assertEqual(manifest["displayName"], self.data["display_name"])
        self.assertNotIn("icon", manifest)

    def test_claude_no_opt_in_preserves_old_listing(self):
        output = self.build(host="claude")
        entry = wio.load_json(output / ".claude-plugin/marketplace.json")["plugins"][0]
        self.assertNotIn("displayName", entry)
        self.assertNotIn("icon", entry)

    def test_native_build_renders_opted_in_listing_without_changing_manifest(self):
        output = self.build({"zcode": LISTING})
        entry = wio.load_json(output / "marketplace.json")["plugins"][0]
        self.assertEqual(entry["displayName"], self.data["display_name"])
        self.assertEqual(entry["icon"], ICON_URL)
        self.assertEqual(entry["name"], self.data["product_id"])
        self.assertEqual(entry["version"], self.data["version"])
        self.assertEqual(entry["source"], "./ai-code-workflow")
        manifest = wio.load_json(output / "ai-code-workflow/.zcode-plugin/plugin.json")
        self.assertNotIn("displayName", manifest)
        self.assertNotIn("icon", manifest)

    def test_no_listing_preserves_old_marketplace_and_native_manifest(self):
        output = self.build()
        entry = wio.load_json(output / "marketplace.json")["plugins"][0]
        manifest = wio.load_json(output / "ai-code-workflow/.zcode-plugin/plugin.json")
        expected_market = wio.load_json(self.root / "adapters/zcode/marketplace.json")["plugins"][0]
        expected_market.update(name=self.data["product_id"], version=self.data["version"])
        expected_manifest = wio.load_json(self.root / "adapters/zcode/plugin.json")
        expected_manifest.update(name=self.data["product_id"], version=self.data["version"],
                                 author=self.data["publisher"])
        self.assertEqual(entry, expected_market)
        self.assertEqual(manifest, expected_manifest)

    def test_icon_target_can_differ_from_registered_source(self):
        resource = next(entry for entry in self.data["resources"]
                        if entry["source"] == "assets/codevow.png")
        resource["target"] = "brand/codevow.png"
        listing = dict(LISTING, icon_path="brand/codevow.png")
        spec = self.load({"zcode": listing})
        self.assertEqual(spec.host_listings["zcode"], listing)
        wrong_url = ICON_URL.replace("/assets/", "/brand/")
        with self.assertRaisesRegex(wio.DataError, "host_listings.*icon_url"):
            self.load({"zcode": dict(listing, icon_url=wrong_url)})

    def test_resource_source_path_is_canonically_url_encoded(self):
        (self.root / "assets/codevow.png").rename(self.root / "assets/Code Vow.png")
        resource = next(entry for entry in self.data["resources"] if entry["source"] == "assets/codevow.png")
        resource["source"] = "assets/Code Vow.png"
        url = ICON_URL.replace("codevow.png", "Code%20Vow.png")
        spec = self.load({"zcode": dict(LISTING, icon_url=url)})
        self.assertEqual(spec.host_listings["zcode"]["icon_url"], url)
        with self.assertRaisesRegex(wio.DataError, "host_listings.*icon_url"):
            self.load({"zcode": dict(LISTING, icon_url=url.replace("%20", " "))})

    def test_rejects_closed_contract_and_invalid_listing_types(self):
        bad_listings = [None, [], "zcode", {"codex": LISTING}, {"claude": LISTING},
                        {"other": LISTING}, {"claude": {"displayName": "Other"}},
                        {"claude": None}, {"claude": []}, {"zcode": None}, {"zcode": []},
                        {"zcode": {}}, {"zcode": dict(LISTING, display_name="Other")},
                        {"zcode": {"icon_path": "assets/codevow.png"}},
                        {"zcode": dict(LISTING, icon_url=42)},
                        {"zcode": dict(LISTING, icon_path=42)}]
        for value in bad_listings:
            with self.subTest(value=value):
                self.data["host_listings"] = value
                with self.assertRaisesRegex(wio.DataError, "host_listings"):
                    self.load()

    def test_rejects_listing_for_undeclared_host(self):
        self.data["hosts"] = ["codex"]
        self.data["generated_agents"] = []
        with self.assertRaisesRegex(wio.DataError, "host_listings"):
            self.load({"zcode": LISTING})

    def test_rejects_unregistered_nonimage_and_unnormalized_icon_targets(self):
        for path in ("assets/missing.png", "LICENSE", "../assets/codevow.png",
                     "assets//codevow.png", "assets/./codevow.png", "/assets/codevow.png"):
            with self.subTest(path=path):
                with self.assertRaisesRegex(wio.DataError, "host_listings.*icon_path"):
                    self.load({"zcode": dict(LISTING, icon_path=path)})

    def test_rejects_mutable_foreign_credentialed_or_mismapped_icon_urls(self):
        values = [ICON_URL.replace("https:", "http:"),
                  ICON_URL.replace("91dec3a64731f8de2fb68e49bce9f4228289bbbd", "main"),
                  ICON_URL.replace("Zack-Zz/ai-code/", "Other/repo/"),
                  ICON_URL.replace("raw.githubusercontent.com", "user@raw.githubusercontent.com"),
                  ICON_URL.replace("raw.githubusercontent.com", "raw.githubusercontent.com:443"),
                  ICON_URL.replace("codevow.png", "codevow.svg"),
                  ICON_URL + "?download=1", ICON_URL + "#icon", ICON_URL + "\n"]
        for url in values:
            with self.subTest(url=url):
                with self.assertRaisesRegex(wio.DataError, "host_listings.*icon_url"):
                    self.load({"zcode": dict(LISTING, icon_url=url)})

    def test_repository_identity_must_match_icon_url(self):
        self.data["repository"] = "https://github.com/Other/repo"
        with self.assertRaisesRegex(wio.DataError, "host_listings.*icon_url"):
            self.load({"zcode": LISTING})

    def test_repository_identity_cannot_contain_dot_segments_or_whitespace(self):
        for repository, path in (("https://github.com/./ai-code", "./ai-code"),
                                 ("https://github.com/Zack-Zz/..", "Zack-Zz/.."),
                                 ("\nhttps://github.com/Zack-Zz/ai-code", "Zack-Zz/ai-code")):
            with self.subTest(repository=repository):
                self.data["repository"] = repository
                url = ICON_URL.replace("Zack-Zz/ai-code", path)
                with self.assertRaisesRegex(wio.DataError, "host_listings.*icon_url"):
                    self.load({"zcode": dict(LISTING, icon_url=url)})

    def test_empty_listing_object_is_backward_compatible(self):
        spec = self.load({})
        self.assertEqual(spec.host_listings, {})

    def test_schema_documents_host_opt_in_closed_fields(self):
        schema = wio.load_json(PLUGIN_ROOT / "schemas/product.schema.json")
        listings = schema["properties"]["host_listings"]
        self.assertFalse(listings["additionalProperties"])
        self.assertEqual(set(listings["properties"]), {"claude", "zcode"})
        claude = listings["properties"]["claude"]
        self.assertEqual(claude["type"], "object")
        self.assertFalse(claude["additionalProperties"])
        self.assertEqual(claude["properties"], {})
        zcode = listings["properties"]["zcode"]
        self.assertFalse(zcode["additionalProperties"])
        self.assertEqual(set(zcode["required"]), {"icon_path", "icon_url"})
        self.assertEqual(set(zcode["properties"]), {"icon_path", "icon_url"})
