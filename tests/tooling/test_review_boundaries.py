"""A catalog child never becomes a new trust root after source selection."""

from pathlib import Path
import shutil
import tempfile
import unittest
from unittest import mock

from .test_registry import add_plugin, write_json
from plugin_tools import build, io, registry


class CatalogSourceBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="catalog-boundary-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.repo = self.base / "repo"
        self.plugin = add_plugin(self.repo, hosts=("codex",))
        write_json(self.repo / "catalog.json", {
            "schema_version": 1, "plugins": [{"path": "plugins/ai-one"}],
        })

    def swap_parent(self, external):
        (self.repo / "plugins").rename(self.repo / "original-plugins")
        (self.repo / "plugins").symlink_to(external / "plugins", target_is_directory=True)

    def test_parent_replacement_after_selection_cannot_capture_external_source(self):
        external = self.base / "external"
        add_plugin(external, version="9.9.9", hosts=("codex",))
        original_member = io.member
        swapped = False

        def replace_after_selection(root, relative, **kwargs):
            nonlocal swapped
            result = original_member(root, relative, **kwargs)
            if Path(root) == self.repo and relative == "plugins/ai-one" and not swapped:
                swapped = True
                self.swap_parent(external)
            return result

        with mock.patch.object(io, "member", side_effect=replace_after_selection):
            with self.assertRaises(io.DataError):
                registry.load_catalog(self.repo)
        self.assertTrue(swapped, "the source selection race must actually occur")

    def test_build_rejects_replaced_parent_even_if_external_bytes_are_identical(self):
        specs = registry.load_catalog(self.repo)
        external = self.base / "external"
        shutil.copytree(self.repo / "plugins", external / "plugins")
        self.swap_parent(external)
        output = self.base / "dist"
        with self.assertRaises(io.DataError):
            build.build_plugins(self.repo, specs, output, hosts=("codex",))
        self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
