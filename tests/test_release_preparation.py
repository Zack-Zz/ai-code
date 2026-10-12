"""Version preparation edits only declared metadata and preserves release history."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from tests.tooling.test_registry import TOOL, write_json
from tests.tooling.test_release import release_plugin
from plugin_tools import io
from plugin_tools.registry import load_catalog


BODY = "### English\n\n- Prepare a useful release.\n\n### 中文\n\n- 准备实用版本。\n"


class ReleasePreparationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.root = self.base / "repo"
        self.plugin = release_plugin(self.root)
        self.notes = self.base / "body.md"
        self.notes.write_text(BODY, encoding="utf-8")
        (self.plugin / "release/NOTES.md").write_text(
            "# Notes\n\nOriginal introduction.\n\n## 1.0.0 — historical\n\nOriginal history.\n", encoding="utf-8")

    def run_tool(self, *args, version="1.1.0"):
        return subprocess.run([sys.executable, str(TOOL), "release", "prepare-version",
            "--plugin", "ai-one", "--version", version, "--notes-file", str(self.notes),
            *args, "--root", str(self.root)], capture_output=True, text=True, timeout=30)

    def snapshot(self):
        return {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}

    def test_preview_reports_exact_changes_without_writing(self):
        before = self.snapshot()
        result = self.run_tool()
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["status"], "preview")
        self.assertEqual(report["old_version"], "1.0.0")
        self.assertEqual(report["version"], "1.1.0")
        self.assertEqual({item["path"] for item in report["changes"]},
                         {"plugins/ai-one/product.json", "plugins/ai-one/release/NOTES.md"})
        self.assertEqual(report["verification"]["host_acceptance"], "unverified")
        self.assertEqual(before, self.snapshot())

    def test_apply_preserves_history_other_metadata_and_is_idempotent(self):
        before = self.snapshot()
        result = self.run_tool("--apply")
        self.assertEqual(result.returncode, 0, result.stderr)
        after = self.snapshot()
        self.assertEqual(json.loads(after["plugins/ai-one/product.json"])["version"], "1.1.0")
        expected = before["plugins/ai-one/release/NOTES.md"].decode().replace(
            "## 1.0.0", "## 1.1.0\n\n" + BODY + "\n## 1.0.0", 1)
        self.assertEqual(after["plugins/ai-one/release/NOTES.md"].decode(), expected)
        for name in before.keys() - {"plugins/ai-one/product.json", "plugins/ai-one/release/NOTES.md"}:
            self.assertEqual(before[name], after[name], name)
        again = self.run_tool("--apply")
        self.assertEqual(again.returncode, 0, again.stderr)
        self.assertEqual(json.loads(again.stdout)["changes"], [])
        self.assertEqual(after, self.snapshot())

    def test_conflicting_version_section_is_rejected(self):
        before = self.snapshot()
        result = self.run_tool("--apply", version="1.0.0")
        self.assertEqual(result.returncode, 3, result.stdout + result.stderr)
        self.assertIn("already", result.stderr)
        self.assertEqual(before, self.snapshot())

    def test_invalid_or_lower_versions_are_rejected(self):
        before = self.snapshot()
        for version in ("01.1.0", "1.1.0-beta.1", "1.1.0-preview.01", "0.9.0", "1.0.0-preview.9"):
            with self.subTest(version=version):
                result = self.run_tool("--apply", version=version)
                self.assertEqual(result.returncode, 2, result.stderr)
        self.assertEqual(before, self.snapshot())

    def test_body_requires_nonempty_utf8_and_both_languages(self):
        before = self.snapshot()
        for payload in (b"", b"\xff", b"Only English", "### English\n\nUseful.\n\n### 中文\n".encode()):
            self.notes.write_bytes(payload)
            result = self.run_tool("--apply")
            self.assertEqual(result.returncode, 2, result.stderr)
        self.assertEqual(before, self.snapshot())

    def test_resets_acceptance_without_deleting_private_materials(self):
        config = json.loads((self.plugin / "release.json").read_text())
        config["acceptance"]["codex"] = "release/private-codex.json"
        write_json(self.plugin / "release.json", config)
        private = self.plugin / "release/private-codex.json"
        private.write_text("private material is retained")
        result = self.run_tool()
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertIn("plugins/ai-one/release.json", [item["path"] for item in report["changes"]])
        self.assertEqual(report["invalidated_acceptance"]["hosts"], ["codex"])
        result = self.run_tool("--apply")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads((self.plugin / "release.json").read_text())["acceptance"],
                         {host: None for host in config["acceptance"]})
        self.assertEqual(private.read_text(), "private material is retained")

    def test_absent_private_evidence_can_be_reset_in_clean_checkout(self):
        config = json.loads((self.plugin / "release.json").read_text())
        config["acceptance"]["codex"] = "release/private-codex.json"
        write_json(self.plugin / "release.json", config)
        result = self.run_tool("--apply")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIsNone(json.loads((self.plugin / "release.json").read_text())["acceptance"]["codex"])
        self.assertFalse((self.plugin / "release/private-codex.json").exists())

    def test_generated_proof_removal_is_previewed_and_leaves_private_and_published_bytes(self):
        from tests.tooling.test_distribution import accept_fixture
        from plugin_tools.release.acceptance import export_acceptance, PROOF_PATH
        accept_fixture(self.root, "ai-one")
        export_acceptance(load_catalog(self.root)[0])
        write_json(self.root / "published/index.json", {"historical": True})
        before = self.snapshot()
        result = self.run_tool()
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        proof_name = "plugins/ai-one/" + PROOF_PATH
        removal = next(item for item in report["changes"] if item["path"] == proof_name)
        self.assertEqual(removal["action"], "remove")
        self.assertIsNone(removal["new"])
        self.assertEqual(before, self.snapshot())
        result = self.run_tool("--apply")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.plugin / PROOF_PATH).exists())
        after = self.snapshot()
        for name in before.keys() - {"plugins/ai-one/product.json", "plugins/ai-one/release/NOTES.md",
                                    "plugins/ai-one/release.json", proof_name}:
            self.assertEqual(before[name], after[name], name)

    def test_arbitrary_or_foreign_proof_is_never_removed(self):
        from tests.tooling.test_distribution import accept_fixture
        from plugin_tools.release.acceptance import export_acceptance, PROOF_PATH
        accept_fixture(self.root, "ai-one")
        export_acceptance(load_catalog(self.root)[0])
        proof_path = self.plugin / PROOF_PATH
        valid = json.loads(proof_path.read_text())
        for proof in ({"user": "file"}, {**valid, "product_id": "ai-other"},
                      {**valid, "hosts": {"codex": {}}}):
            write_json(proof_path, proof)
            before = self.snapshot()
            result = self.run_tool("--apply")
            self.assertEqual(result.returncode, 3, result.stderr)
            self.assertEqual(before, self.snapshot())

    def test_preview_sequence_uses_numeric_precedence(self):
        product = json.loads((self.plugin / "product.json").read_text())
        product["version"] = "1.1.0-preview.9"
        write_json(self.plugin / "product.json", product)
        for version in ("1.1.0-preview.10", "1.1.0"):
            result = self.run_tool(version=version)
            self.assertEqual(result.returncode, 0, result.stderr)
        result = self.run_tool(version="1.1.0-preview.8")
        self.assertEqual(result.returncode, 2, result.stderr)

    def test_notes_file_and_generated_proof_symlinks_are_rejected(self):
        self.notes.unlink()
        self.notes.symlink_to(self.plugin / "release/NOTES.md")
        result = self.run_tool("--apply")
        self.assertEqual(result.returncode, 2, result.stderr)
        self.notes.unlink()
        self.notes.write_text(BODY, encoding="utf-8")
        (self.plugin / "release/acceptance-proof.json").symlink_to(self.notes)
        before = self.snapshot()
        result = self.run_tool("--apply")
        self.assertEqual(result.returncode, 2, result.stderr)
        self.assertEqual(before, self.snapshot())

    def test_race_after_first_write_rolls_back_only_own_bytes(self):
        from plugin_tools.release import preparation
        spec = load_catalog(self.root)[0]
        before = self.snapshot()
        original = preparation._write_market
        edited_notes = "User concurrent release notes\n"
        first = True

        def race(root, relative, new, old):
            nonlocal first
            original(root, relative, new, old)
            if first:
                first = False
                (self.plugin / "release/NOTES.md").write_text(edited_notes)

        with mock.patch.object(preparation, "_write_market", side_effect=race):
            with self.assertRaisesRegex(io.ConflictError, "changed"):
                preparation.prepare_version(self.root, spec, "1.1.0", self.notes, apply=True)
        after = self.snapshot()
        self.assertEqual(after["plugins/ai-one/release/NOTES.md"].decode(), edited_notes)
        for name in before.keys() - {"plugins/ai-one/release/NOTES.md"}:
            self.assertEqual(before[name], after[name], name)

    def test_stale_catalog_selection_is_rejected(self):
        from plugin_tools.release import preparation
        from tests.tooling.test_registry import add_plugin
        spec = load_catalog(self.root)[0]
        add_plugin(self.root, "ai-two")
        write_json(self.root / "catalog.json", {"schema_version": 1, "plugins": [{"path": "plugins/ai-two"}]})
        before = self.snapshot()
        with self.assertRaisesRegex(io.ConflictError, "changed"):
            preparation.prepare_version(self.root, spec, "1.1.0", self.notes, apply=True)
        self.assertEqual(before, self.snapshot())

    def test_body_race_during_apply_rolls_back_changes(self):
        from plugin_tools.release import preparation
        spec = load_catalog(self.root)[0]
        before = self.snapshot()
        original = preparation._write_market
        first = True

        def race(root, relative, new, old):
            nonlocal first
            original(root, relative, new, old)
            if first:
                first = False
                self.notes.write_text(BODY.replace("useful", "changed"), encoding="utf-8")

        with mock.patch.object(preparation, "_write_market", side_effect=race):
            with self.assertRaisesRegex(io.ConflictError, "changed"):
                preparation.prepare_version(self.root, spec, "1.1.0", self.notes, apply=True)
        self.assertEqual(before, self.snapshot())

    def test_unsafe_paths_and_resource_collisions_are_rejected(self):
        config_path = self.plugin / "release.json"
        original = json.loads(config_path.read_text())
        for path in ("../body.md", "/tmp/body.md", "release/README.md"):
            config = {**original, "notes": path}
            write_json(config_path, config)
            before = self.snapshot()
            result = self.run_tool("--apply")
            self.assertEqual(result.returncode, 2, result.stderr)
            self.assertEqual(before, self.snapshot())
        write_json(config_path, original)
        source_notes = self.plugin / "release/NOTES.md"
        source_notes.unlink()
        source_notes.symlink_to(self.notes)
        self.assertEqual(self.run_tool("--apply").returncode, 2)
        source_notes.unlink()
        source_notes.write_text("History")
        product = json.loads((self.plugin / "product.json").read_text())
        product["resources"].append(product["resources"][0])
        write_json(self.plugin / "product.json", product)
        self.assertEqual(self.run_tool("--apply").returncode, 2)

    def test_concurrent_source_change_is_rejected_before_writes(self):
        from plugin_tools.release import preparation
        spec = load_catalog(self.root)[0]
        before = self.snapshot()
        original = preparation._apply_changes

        def race(*args):
            (self.plugin / "README.md").write_text("User concurrent edit")
            return original(*args)

        with mock.patch.object(preparation, "_apply_changes", side_effect=race):
            with self.assertRaisesRegex(io.ConflictError, "changed"):
                preparation.prepare_version(self.root, spec, "1.1.0", self.notes, apply=True)
        after = self.snapshot()
        for name in before.keys() - {"plugins/ai-one/README.md"}:
            self.assertEqual(before[name], after[name], name)


if __name__ == "__main__":
    unittest.main()
