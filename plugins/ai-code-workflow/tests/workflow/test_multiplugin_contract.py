"""Workflow-specific loading retains its rules under catalog packaging metadata."""

import tempfile
import unittest
from pathlib import Path

from workflow import product
from workflow.io import DataError
from .test_product import make_source_root, write_product


class CatalogPackagingMetadataTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = make_source_root(Path(self.tmp.name))
        template = self.root / "adapters/zcode/agents/workflow-reviewer.md"
        template.parent.mkdir(parents=True)
        template.write_text("---\nname: workflow-reviewer\n---\n")
        body = self.root / "skills/review/references/reviewer-contract.md"
        body.parent.mkdir(parents=True)
        body.write_text("Review instructions.\n")

    def write(self, **changes):
        def update(data):
            data.update(hosts=["zcode", "codex"], profiles=["collaborative", "continuous"],
                        generated_agents=[{
                            "host": "zcode",
                            "template": "adapters/zcode/agents/workflow-reviewer.md",
                            "body": "skills/review/references/reviewer-contract.md",
                            "target": "agents/workflow-reviewer.md",
                        }])
            data.update(changes)
        write_product(self.root, update)

    def test_catalog_metadata_preserves_workflow_resource_resolution(self):
        self.write()
        try:
            spec = product.load_product(self.root)
        except DataError as exc:
            self.fail(f"valid catalog packaging metadata must load: {exc}")
        self.assertEqual(spec.product_id, "ai-code-workflow")
        self.assertIn("tools/tool.py", spec.targets())

    def test_workflow_rejects_invalid_catalog_metadata(self):
        bad = [
            {"hosts": ["codex", "codex"]}, {"hosts": []}, {"hosts": ["unknown"]},
            {"profiles": ["continuous"]},
            {"generated_agents": [{"host": "zcode", "template": "../outside", "body": "x", "target": "agents/x.md"}]},
        ]
        for changes in bad:
            with self.subTest(changes=changes):
                self.write(**changes)
                with self.assertRaises(DataError):
                    product.load_product(self.root)

    def test_catalog_metadata_does_not_relax_workflow_core_skills(self):
        self.write(core_skills=[])
        with self.assertRaisesRegex(DataError, "core_skills must not be empty"):
            product.load_product(self.root)


if __name__ == "__main__":
    unittest.main()
