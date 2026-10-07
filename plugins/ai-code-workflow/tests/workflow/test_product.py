"""product module: product.json loading and validation."""

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from workflow import io as wio
from workflow import product as wp

REPO_ROOT = Path(__file__).resolve().parents[2]

VALID_SKILL = "---\nname: {name}\ndescription: one line description\n---\n\n# {name}\n\nBody.\n"


def make_source_root(td: Path) -> Path:
    """Build a minimal valid source tree mirroring the real repo layout."""
    for skill in ("workflow", "tdd", "review"):
        d = td / "skills" / skill
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text(VALID_SKILL.format(name=skill), encoding="utf-8")
    (td / "policies").mkdir()
    (td / "policies" / "collaborative.json").write_text('{"schema_version": 1}')
    (td / "scripts").mkdir()
    (td / "scripts" / "tool.py").write_text("# tool\n")
    return td


BASE_PRODUCT = {
    "schema_version": 1,
    "product_id": "ai-code-workflow",
    "display_name": "AI Code Workflow",
    "version": "2.0.0",
    "repository": "https://example.com/repo",
    "license": "MIT",
    "core_skills": ["workflow", "tdd"],
    "shared_skills": [],
    "resources": [
        {"source": "policies", "target": "policies", "include": ["collaborative.json"]},
        {"source": "scripts/tool.py", "target": "tools/tool.py", "include": []},
    ],
}


def write_product(td: Path, mutate=None):
    data = json.loads(json.dumps(BASE_PRODUCT))
    if mutate:
        mutate(data)
    (td / "product.json").write_text(json.dumps(data, indent=2), encoding="utf-8")


class ValidProductTests(unittest.TestCase):
    def test_loads_real_repo_product(self):
        spec = wp.load_product(REPO_ROOT)
        self.assertEqual(spec.product_id, "ai-code-workflow")
        self.assertEqual(spec.version, "2.0.0")
        self.assertEqual(
            sorted(spec.core_skills),
            ["debugging", "review", "tdd", "verification", "workflow"],
        )
        self.assertEqual(spec.shared_skills, ["review-results"])
        targets = [t for _, t in spec.files]
        self.assertIn("skills/workflow/SKILL.md", targets)
        self.assertIn("tools/workflow/io.py", targets)
        self.assertIn("policies/collaborative.json", targets)
        # every resolved target is unique (no mapping conflicts)
        self.assertEqual(len(targets), len(set(targets)))
        # resolved file list is sorted by target path
        self.assertEqual(targets, sorted(targets))

    def test_skill_component_files_exist(self):
        spec = wp.load_product(REPO_ROOT)
        for source, _ in spec.files:
            self.assertTrue(source.is_file(), source)


class InvalidProductTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.root = Path(self.td.name)
        make_source_root(self.root)

    def tearDown(self):
        self.td.cleanup()

    def load(self, mutate=None):
        write_product(self.root, mutate)
        return wp.load_product(self.root)

    def test_rejects_duplicate_skill_between_core_and_shared(self):
        with self.assertRaisesRegex(Exception, "duplicat"):
            self.load(lambda d: d.update(shared_skills=["workflow"]))

    def test_rejects_missing_skill_file(self):
        (self.root / "skills" / "tdd" / "SKILL.md").unlink()
        with self.assertRaisesRegex(Exception, "SKILL.md"):
            self.load()

    def test_rejects_bad_version(self):
        for bad in ("2.0", "v2.0.0", "2.0.0-beta", "2.0.0\n"):
            with self.subTest(bad=bad):
                with self.assertRaisesRegex(Exception, "version"):
                    self.load(lambda d, b=bad: d.update(version=b))

    def test_rejects_product_identity_with_trailing_newline(self):
        with self.assertRaisesRegex(wio.DataError, "product_id"):
            self.load(lambda d: d.update(product_id="ai-code-workflow\n"))

    def test_resources_requires_an_array_with_data_error(self):
        failure = None
        try:
            self.load(lambda d: d.update(resources=None))
        except Exception as exc:
            failure = exc
        self.assertIsInstance(failure, wio.DataError)

    def test_cache_file_source_cannot_be_registered(self):
        (self.root / "scripts/cached.pyc").write_bytes(b"not source")
        with self.assertRaisesRegex(wio.DataError, "cache"):
            self.load(lambda d: d["resources"].append({
                "source": "scripts/cached.pyc", "target": "tools/cached.pyc", "include": []}))

    def test_rejects_unknown_top_level_field(self):
        with self.assertRaisesRegex(Exception, "unknown"):
            self.load(lambda d: d.update(surprise=True))

    def test_rejects_absolute_source(self):
        with self.assertRaisesRegex(Exception, "absolute"):
            self.load(lambda d: d["resources"].append(
                {"source": "/etc/passwd", "target": "x", "include": []}))

    def test_rejects_parent_escape_target(self):
        with self.assertRaisesRegex(Exception, "escape|outside"):
            self.load(lambda d: d["resources"].append(
                {"source": "scripts", "target": "../escape", "include": ["tool.py"]}))

    def test_rejects_mapping_conflict(self):
        with self.assertRaisesRegex(Exception, "conflict"):
            self.load(lambda d: d["resources"].append(
                {"source": "policies", "target": "policies", "include": ["collaborative.json"]}))

    def test_rejects_wildcard_include(self):
        with self.assertRaisesRegex(Exception, "wildcard"):
            self.load(lambda d: d["resources"].append(
                {"source": "scripts", "target": "tools", "include": ["*.py"]}))

    def test_rejects_cache_entry_in_include(self):
        (self.root / "scripts" / "__pycache__").mkdir()
        (self.root / "scripts" / "__pycache__" / "x.py").write_text("x")
        with self.assertRaisesRegex(Exception, "cache"):
            self.load(lambda d: d["resources"].append(
                {"source": "scripts", "target": "tools", "include": ["__pycache__/x.py"]}))

    def test_rejects_missing_included_file(self):
        with self.assertRaisesRegex(Exception, "not exist|missing"):
            self.load(lambda d: d["resources"].append(
                {"source": "scripts", "target": "tools", "include": ["ghost.py"]}))

    def test_rejects_dir_source_with_empty_include(self):
        with self.assertRaisesRegex(Exception, "include"):
            self.load(lambda d: d["resources"].append(
                {"source": "scripts", "target": "tools2", "include": []}))

    def test_rejects_file_source_with_include_entries(self):
        with self.assertRaisesRegex(Exception, "include"):
            self.load(lambda d: d["resources"].append(
                {"source": "scripts/tool.py", "target": "tools/x.py", "include": ["a"]}))

    def test_rejects_bool_version_schema(self):
        with self.assertRaisesRegex(Exception, "schema_version"):
            self.load(lambda d: d.update(schema_version=True))

    def test_rejects_skill_frontmatter_name_mismatch(self):
        sk = self.root / "skills" / "tdd" / "SKILL.md"
        sk.write_text(VALID_SKILL.format(name="not-tdd"), encoding="utf-8")
        with self.assertRaisesRegex(Exception, "name"):
            self.load()


class SkillMetaTests(unittest.TestCase):
    def test_parses_first_frontmatter_only(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "SKILL.md"
            p.write_text(
                "---\nname: demo\ndescription: first block wins\norigin: ai-code\n---\n"
                "Body with ---\n---\nname: ghost\n---\n",
                encoding="utf-8",
            )
            meta = wp.parse_skill_meta(p)
            self.assertEqual(meta["name"], "demo")
            self.assertEqual(meta["origin"], "ai-code")

    def test_rejects_multiline_description(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "SKILL.md"
            p.write_text("---\nname: demo\ndescription:\n  folded line\n---\n", encoding="utf-8")
            with self.assertRaisesRegex(Exception, "single-line|description"):
                wp.parse_skill_meta(p)

    def test_real_repo_skills_parse(self):
        spec = wp.load_product(REPO_ROOT)
        for source, target in spec.files:
            if target.endswith("SKILL.md"):
                meta = wp.parse_skill_meta(source)
                self.assertEqual(meta["name"], target.split("/")[1])
                self.assertIn("description", meta)


class ResourceReferenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        make_source_root(self.root)
        write_product(self.root)
        self.skill = self.root / "skills/workflow/SKILL.md"

    def tearDown(self):
        self.temp.cleanup()

    def append(self, text):
        self.skill.write_text(self.skill.read_text() + "\n" + text)

    def test_missing_inline_local_resource_is_rejected(self):
        self.append("Read [guide](references/missing.md).")
        with self.assertRaisesRegex(wio.DataError, "missing.md"):
            wp.load_product(self.root)

    def test_missing_reference_style_resource_is_rejected(self):
        self.append("Read [guide][details].\n\n[details]: references/missing.md")
        with self.assertRaisesRegex(wio.DataError, "missing.md"):
            wp.load_product(self.root)

    def test_existing_but_unregistered_resource_is_rejected(self):
        ref = self.skill.parent / "references/guide.md"
        ref.parent.mkdir()
        ref.write_text("Required guide.")
        self.append("Read [guide](references/guide.md).")
        with self.assertRaisesRegex(wio.DataError, "guide.md"):
            wp.load_product(self.root)

    def test_relative_resource_cannot_escape_the_package(self):
        self.append("Read [guide](../../../outside.md).")
        with self.assertRaisesRegex(wio.DataError, "outside|escape"):
            wp.load_product(self.root)

    def test_registered_resource_can_be_linked_under_its_packaged_target(self):
        (self.root / "scripts/guide.md").write_text("Packaged guide.")
        write_product(self.root, lambda d: d["resources"].append({
            "source": "scripts/guide.md", "target": "skills/workflow/references/guide.md", "include": []}))
        self.append("Read [guide](references/guide.md#section), [tdd](../tdd/SKILL.md).")
        self.assertIn("skills/workflow/references/guide.md", wp.load_product(self.root).targets())

    def test_external_runtime_and_fenced_examples_are_not_package_resources(self):
        self.append('''[web](https://example.com/guide) [section](#local) [runtime](/absolute/project/file.py:3)
```md
[example](references/not-a-resource.md)
```
`[inline example](missing.md)`''')
        self.assertTrue(wp.load_product(self.root).files)


if __name__ == "__main__":
    unittest.main()
