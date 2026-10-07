"""package_check module: package closure, identity and marketplace checks."""

import shutil
import os
import tempfile
import unittest
from pathlib import Path

from workflow import io as wio
from workflow import package_check as wpc
from workflow.io import DataError

REPO_ROOT = Path(__file__).resolve().parents[2]


class PackageCheckTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.td = tempfile.TemporaryDirectory()
        cls.out = Path(cls.td.name) / "dist"
        from workflow import build as wbuild
        wbuild.build_packages(REPO_ROOT, ["zcode", "codex"], cls.out)

    @classmethod
    def tearDownClass(cls):
        cls.td.cleanup()

    def fresh_copy(self, host="zcode"):
        copy_root = Path(self.td.name) / f"copy-{host}"
        if copy_root.exists():
            shutil.rmtree(copy_root)
        shutil.copytree(self.out / host, copy_root)
        return copy_root

    def test_both_hosts_pass(self):
        for host in ("zcode", "codex"):
            result = wpc.check_package(self.out / host / "ai-code-workflow", host)
            self.assertTrue(result["ok"], result["problems"])
            self.assertEqual(result["problems"], [])
            self.assertEqual(result["caches"], [])
            self.assertEqual(result["product_id"], "ai-code-workflow")
            self.assertEqual(result["version"], wio.load_json(REPO_ROOT / "product.json")["version"])
            self.assertEqual(result["files_checked"],
                             len(wio.load_json(self.out / host / "ai-code-workflow" / "artifact.json")["files"]))

    def test_tampered_registered_file_fails(self):
        root = self.fresh_copy()
        target = root / "ai-code-workflow" / "policies" / "collaborative.json"
        target.write_text("{}")
        result = wpc.check_package(root / "ai-code-workflow", "zcode")
        self.assertFalse(result["ok"])
        self.assertTrue(any("collaborative.json" in p for p in result["problems"]))

    def test_extra_active_file_fails_but_passive_cache_reported(self):
        root = self.fresh_copy()
        pkg = root / "ai-code-workflow"
        (pkg / "rogue.js").write_text("console.log('not mine')\n")
        cache_dir = pkg / "tools" / "workflow" / "__pycache__"
        cache_dir.mkdir()
        (cache_dir / "io.cpython-312.pyc").write_bytes(b"\x00pyc")
        result = wpc.check_package(pkg, "zcode")
        self.assertFalse(result["ok"])
        self.assertTrue(any("rogue.js" in p for p in result["problems"]))
        self.assertTrue(any("__pycache__" in c for c in result["caches"]))

    def test_extra_fifo_is_rejected_without_opening_it(self):
        pkg = self.fresh_copy() / "ai-code-workflow"
        os.mkfifo(pkg / "unregistered-hook.py")
        result = wpc.check_package(pkg, "zcode")
        self.assertFalse(result["ok"])
        self.assertTrue(any("unregistered-hook.py" in p for p in result["problems"]))

    def test_fifo_cannot_masquerade_as_a_passive_cache(self):
        pkg = self.fresh_copy() / "ai-code-workflow"
        cache = pkg / "tools/workflow/__pycache__"
        cache.mkdir()
        os.mkfifo(cache / "io.cpython-313.pyc")
        result = wpc.check_package(pkg, "zcode")
        self.assertFalse(result["ok"])
        self.assertEqual(result["caches"], [])
        self.assertTrue(any("io.cpython-313.pyc" in p for p in result["problems"]))

    def test_empty_directories_remain_inert(self):
        pkg = self.fresh_copy() / "ai-code-workflow"
        (pkg / "empty-docs").mkdir()
        self.assertTrue(wpc.check_package(pkg, "zcode")["ok"])

    def test_wrong_host_manifest_fails(self):
        root = self.fresh_copy("codex")
        pkg = root / "ai-code-workflow"
        result = wpc.check_package(pkg, "zcode")
        self.assertFalse(result["ok"])

    def test_version_mismatch_between_manifests_fails(self):
        root = self.fresh_copy()
        pkg = root / "ai-code-workflow"
        market = wio.load_json(root / "marketplace.json")
        market["plugins"][0]["version"] = "9.9.9"
        (root / "marketplace.json").write_text(wio_json_dumps(market))
        result = wpc.check_package(pkg, "zcode")
        self.assertFalse(result["ok"])
        self.assertTrue(any("version" in p.lower() for p in result["problems"]))

    def test_missing_marketplace_fails(self):
        root = self.fresh_copy()
        (root / "marketplace.json").unlink()
        result = wpc.check_package(root / "ai-code-workflow", "zcode")
        self.assertFalse(result["ok"])
        self.assertTrue(any("marketplace" in p for p in result["problems"]))

    def test_missing_artifact_fails(self):
        root = self.fresh_copy()
        (root / "ai-code-workflow" / "artifact.json").unlink()
        with self.assertRaises(DataError):
            wpc.check_package(root / "ai-code-workflow", "zcode")

    def test_missing_registered_skill_fails(self):
        root = self.fresh_copy()
        pkg = root / "ai-code-workflow"
        (pkg / "skills" / "tdd" / "SKILL.md").unlink()
        result = wpc.check_package(pkg, "zcode")
        self.assertFalse(result["ok"])
        self.assertTrue(any("SKILL.md" in p for p in result["problems"]))

    def test_symlink_substitution_fails(self):
        root = self.fresh_copy()
        pkg = root / "ai-code-workflow"
        target = pkg / "NOTICE"
        real = target.read_bytes()
        target.unlink()
        outside = Path(self.td.name) / "outside-NOTICE"
        outside.write_bytes(real)
        import os
        os.symlink(outside, target)
        result = wpc.check_package(pkg, "zcode")
        self.assertFalse(result["ok"])
        self.assertTrue(any("NOTICE" in p for p in result["problems"]))

    def rehash(self, pkg):
        path = pkg / "artifact.json"
        artifact = wio.load_json(path)
        artifact["files"] = [[rel, wio.sha256_file(pkg / rel)] for rel, _ in artifact["files"]]
        artifact["content_hash"] = wio.sha256_bytes(wio.canonical_json(artifact["files"]))
        path.write_text(wio_json_dumps(artifact))

    def test_invalid_provenance_is_rejected_even_when_payload_is_unchanged(self):
        for field, value in (("source_revision", {"not": "a SHA"}),
                             ("source_revision", "not-a-revision"),
                             ("working_tree_dirty", "false"),
                             ("working_tree_dirty", 1),
                             ("source_tree_hash", "broken"),
                             ("version", "v2.0.0"),
                             ("content_hash", "broken")):
            with self.subTest(field=field, value=value):
                pkg = self.fresh_copy() / "ai-code-workflow"
                path = pkg / "artifact.json"
                artifact = wio.load_json(path)
                artifact[field] = value
                path.write_text(wio_json_dumps(artifact))
                with self.assertRaises(DataError):
                    wpc.check_package(pkg, "zcode")

    def test_local_resource_closure_is_checked_after_rehashing(self):
        pkg = self.fresh_copy() / "ai-code-workflow"
        path = pkg / "skills/tdd/SKILL.md"
        path.write_text(path.read_text() + "\nRead [required guide](references/missing.md).\n")
        self.rehash(pkg)
        result = wpc.check_package(pkg, "zcode")
        self.assertFalse(result["ok"])
        self.assertTrue(any("missing.md" in p for p in result["problems"]))

    def test_packaged_skill_metadata_is_validated_after_rehashing(self):
        pkg = self.fresh_copy() / "ai-code-workflow"
        path = pkg / "skills/tdd/SKILL.md"
        path.write_text(path.read_text().replace("name: tdd", "name: wrong-skill"))
        self.rehash(pkg)
        result = wpc.check_package(pkg, "zcode")
        self.assertFalse(result["ok"])
        self.assertTrue(any("SKILL.md" in p for p in result["problems"]))

    def test_malformed_interface_is_rejected_after_rehashing(self):
        pkg = self.fresh_copy("codex") / "ai-code-workflow"
        path = pkg / "skills/workflow/agents/openai.yaml"
        original = path.read_text()
        display_line = next(line for line in original.splitlines()
                            if line.strip().startswith("display_name:"))
        for before, after in (
                (display_line, '  display_name: "Use "workflow""'),
                ("allow_implicit_invocation: true", 'allow_implicit_invocation: "false"'),
                ("policy:\n", "unknown_section:\n"),
                ("policy:\n", "interface:\n")):
            with self.subTest(after=after):
                corrupted = original.replace(before, after)
                self.assertNotEqual(corrupted, original, "the malformed fixture must actually change")
                path.write_text(corrupted)
                self.rehash(pkg)
                result = wpc.check_package(pkg, "codex")
                self.assertFalse(result["ok"])
                self.assertTrue(any("openai.yaml" in p for p in result["problems"]))

    def test_reviewer_restrictions_are_checked_after_rehashing(self):
        pkg = self.fresh_copy() / "ai-code-workflow"
        path = pkg / "agents/workflow-reviewer.md"
        original = path.read_text()
        for before, after in (("model: inherit", "model: arbitrary-model"),
                              ('tools: ["Read", "Grep", "Glob"]', 'tools: ["Read", "Write"]'),
                              ("maxTurns: 12", "maxTurns: 99")):
            with self.subTest(after=after):
                path.write_text(original.replace(before, after))
                self.rehash(pkg)
                result = wpc.check_package(pkg, "zcode")
                self.assertFalse(result["ok"])
                self.assertTrue(any("workflow-reviewer" in p for p in result["problems"]))


def wio_json_dumps(obj):
    import json
    return json.dumps(obj, indent=2, sort_keys=True) + "\n"


if __name__ == "__main__":
    unittest.main()
