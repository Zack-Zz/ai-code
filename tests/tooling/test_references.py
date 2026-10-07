"""Skill links resolve against packaged target paths and the explicit whitelist."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

try:
    from .test_registry import TOOL, add_plugin, write_json
except ImportError:
    from test_registry import TOOL, add_plugin, write_json


class SkillReferenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="plugin-references-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "repo"
        self.plugin = add_plugin(self.root, skills=("ask",))
        self.skill = self.plugin / "skills/ask/SKILL.md"
        write_json(self.root / "catalog.json", {"schema_version": 1,
                                               "plugins": [{"path": "plugins/ai-one"}]})

    def run_tool(self, *args):
        return subprocess.run([sys.executable, str(TOOL), *args, "--root", str(self.root)],
                              capture_output=True, text=True, timeout=30)

    def append_skill(self, body):
        self.skill.write_text(self.skill.read_text() + body)

    def register(self, source, target):
        data = json.loads((self.plugin / "product.json").read_text())
        data["resources"].append({"source": source, "target": target, "include": []})
        write_json(self.plugin / "product.json", data)

    def test_missing_local_reference_fails_validate_and_build_without_publication(self):
        self.append_skill("[required guide](references/missing.md)\n")
        validated = self.run_tool("validate", "--all")
        self.assertEqual(validated.returncode, 2, validated.stdout + validated.stderr)
        self.assertIn("missing or unregistered", validated.stderr)
        output = Path(self.temp.name) / "dist"
        built = self.run_tool("build", "--all", "--output", str(output))
        self.assertEqual(built.returncode, 2, built.stdout + built.stderr)
        self.assertFalse(output.exists())

    def test_existing_but_unregistered_guide_is_not_in_reference_closure(self):
        guide = self.plugin / "skills/ask/references/guide.md"
        guide.parent.mkdir(parents=True)
        guide.write_text("This exists only in the source checkout.\n")
        self.append_skill("[guide](references/guide.md)\n")
        result = self.run_tool("validate", "--all")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("missing or unregistered", result.stderr)

    def test_reference_cannot_escape_above_the_package_root(self):
        self.append_skill("[outside](../../../external.md)\n")
        result = self.run_tool("validate", "--all")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("reference", result.stderr)

    def test_relocated_resource_links_resolve_from_packaged_targets(self):
        (self.plugin / "author-guide.md").write_text("Registered guide.\n")
        self.register("author-guide.md", "skills/ask/references/guide.md")
        self.append_skill("[guide](references/guide.md#details)\n")
        result = self.run_tool("validate", "--all")
        self.assertEqual(result.returncode, 0, result.stderr)
        output = Path(self.temp.name) / "dist"
        result = self.run_tool("build", "--all", "--output", str(output))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual((output / "codex/ai-one/skills/ask/references/guide.md").read_text(), "Registered guide.\n")
        self.assertFalse((output / "codex/ai-one/author-guide.md").exists())

    def test_packaged_resource_reference_definitions_and_code_examples(self):
        (self.plugin / "guide source.md").write_text("Guide body.\n")
        self.register("guide source.md", "guides/AI guide.md")
        self.append_skill("""
[guide][usage]
[usage]: ../../guides/AI%20guide.md#usage
[readme](../../README.md)
[remote](https://example.com/a/missing.md)
[section](#usage)
`[inline example](references/absent.md)`
<!-- [comment example](references/absent.md) -->
```markdown
[fenced example](references/absent.md)
```
~~~markdown
[other fenced example](references/absent.md)
~~~
""")
        result = self.run_tool("validate", "--all")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_relocated_markdown_resource_uses_its_target_for_followup_links(self):
        (self.plugin / "guide.md").write_text("[readme](../../../README.md)\n")
        self.register("guide.md", "skills/ask/references/guide.md")
        self.append_skill("[guide](references/guide.md)\n")
        result = self.run_tool("validate", "--all")
        self.assertEqual(result.returncode, 0, result.stderr)
        (self.plugin / "guide.md").write_text("[unregistered](missing.md)\n")
        result = self.run_tool("validate", "--all")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("skills/ask/references/missing.md", result.stderr)

    def test_balanced_parentheses_and_escaped_parentheses_resolve_complete_paths(self):
        for name in ("reference(advanced).md", "nested(deep(topic)).md", "literal).md"):
            (self.plugin / "skills/ask" / name).write_text("Registered guide.\n")
            self.register(f"skills/ask/{name}", f"skills/ask/{name}")
        self.append_skill(
            '[advanced](reference(advanced).md "Advanced guide")\n'
            '[nested](nested(deep(topic)).md)\n'
            '[escaped](literal\\).md)\n'
            '[angle](<reference(advanced).md>)\n')
        result = self.run_tool("validate", "--all")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        output = Path(self.temp.name) / "dist"
        result = self.run_tool("build", "--all", "--output", str(output))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        checked = self.run_tool("package", "check", "--path", str(output / "codex/ai-one"), "--host", "codex")
        self.assertEqual(checked.returncode, 0, checked.stdout + checked.stderr)

    def test_missing_balanced_reference_reports_the_complete_target(self):
        self.append_skill('[missing](reference(advanced).md)\n')
        result = self.run_tool("validate", "--all")
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertIn("skills/ask/reference(advanced).md", result.stderr)


if __name__ == "__main__":
    unittest.main()
