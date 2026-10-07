"""build module: reproducible two-host package generation."""

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from workflow import io as wio

REPO_ROOT = Path(__file__).resolve().parents[2]
HOSTS = ("zcode", "codex")


class BuildTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.td = tempfile.TemporaryDirectory()
        cls.out1 = Path(cls.td.name) / "dist1"
        from workflow import build as wbuild
        # CI normally builds a clean checkout. Provenance must be tested with
        # explicit contexts rather than the developer's current dirty tree.
        with patch.object(wbuild, "_git_state", return_value=("1" * 40, False)):
            cls.report = wbuild.build_packages(REPO_ROOT, list(HOSTS), cls.out1)

    @classmethod
    def tearDownClass(cls):
        cls.td.cleanup()

    def pkg(self, host):
        return self.out1 / host / "ai-code-workflow"

    def artifact(self, host):
        return wio.load_json(self.pkg(host) / "artifact.json")

    def test_build_report_and_layout(self):
        self.assertEqual(self.report["hosts"], list(HOSTS))
        for host in HOSTS:
            root = self.out1 / host
            pkg = root / "ai-code-workflow"
            market_rel = ".agents/plugins/marketplace.json" if host == "codex" else "marketplace.json"
            self.assertTrue((root / market_rel).is_file())
            self.assertTrue((root / f"ai-code-workflow-{self.artifact(host)['version']}.zip").is_file())
            self.assertTrue(pkg.is_dir())
            for rel in ("skills/workflow/SKILL.md", "skills/review-results/SKILL.md",
                        "skills/review/references/reviewer-contract.md",
                        "policies/collaborative.json", "policies/continuous.json",
                        "templates/task.json", "templates/evidence.json",
                        "schemas/product.schema.json", "tools/workflow_tool.py",
                        "tools/workflow/io.py", "LICENSE", "NOTICE",
                        "LICENSES/backend-engineering-lite.txt", "artifact.json"):
                self.assertTrue((pkg / rel).is_file(), f"{host}: missing {rel}")
        self.assertTrue((self.pkg("zcode") / ".zcode-plugin" / "plugin.json").is_file())
        self.assertTrue((self.pkg("zcode") / "agents" / "workflow-reviewer.md").is_file())
        self.assertTrue((self.pkg("codex") / "plugin.json").is_file())

    def test_artifact_contract_fields(self):
        for host in HOSTS:
            art = self.artifact(host)
            self.assertEqual(art["schema_version"], 1)
            self.assertEqual(art["product_id"], "ai-code-workflow")
            self.assertEqual(art["version"], wio.load_json(REPO_ROOT / "product.json")["version"])
            self.assertEqual(art["host"], host)
            self.assertEqual(art["profiles"], ["collaborative", "continuous"])
            self.assertIn("source_revision", art)
            self.assertIs(art["working_tree_dirty"], False,
                          "the explicit clean source fixture must remain clean")
            self.assertRegex(art["source_tree_hash"], r"^[0-9a-f]{64}$")
            paths = [entry[0] for entry in art["files"]]
            self.assertEqual(paths, sorted(paths))
            self.assertNotIn("artifact.json", paths)
            recomputed = wio.sha256_bytes(wio.canonical_json(art["files"]))
            self.assertEqual(recomputed, art["content_hash"])
            for rel, sha in art["files"]:
                self.assertEqual(wio.sha256_file(self.pkg(host) / rel), sha)

    def test_reproducible_across_builds(self):
        with tempfile.TemporaryDirectory() as td:
            out2 = Path(td) / "dist2"
            from workflow import build as wbuild
            with patch.object(wbuild, "_git_state", return_value=("1" * 40, False)):
                wbuild.build_packages(REPO_ROOT, list(HOSTS), out2)
            for host in HOSTS:
                a1, a2 = self.artifact(host), wio.load_json(out2 / host / "ai-code-workflow" / "artifact.json")
                self.assertEqual(a1["content_hash"], a2["content_hash"], host)
                zip1 = self.out1 / host / f"ai-code-workflow-{a1['version']}.zip"
                zip2 = out2 / host / f"ai-code-workflow-{a2['version']}.zip"
                self.assertEqual(wio.sha256_file(zip1), wio.sha256_file(zip2), host)

    def test_shared_content_identical_across_hosts(self):
        a1, a2 = self.artifact("zcode"), self.artifact("codex")
        map1 = {rel: sha for rel, sha in a1["files"]}
        map2 = {rel: sha for rel, sha in a2["files"]}
        for rel in ("skills/workflow/SKILL.md", "skills/tdd/SKILL.md",
                    "skills/debugging/SKILL.md", "skills/review/SKILL.md",
                    "skills/verification/SKILL.md", "skills/review-results/SKILL.md",
                    "skills/review/references/reviewer-contract.md",
                    "policies/collaborative.json", "policies/continuous.json"):
            self.assertIn(rel, map1)
            self.assertIn(rel, map2)
            self.assertEqual(map1[rel], map2[rel], rel)

    def test_reviewer_agent_embeds_shared_contract(self):
        contract = (self.pkg("zcode") / "skills" / "review" / "references" / "reviewer-contract.md").read_text()
        agent = (self.pkg("zcode") / "agents" / "workflow-reviewer.md").read_text()
        self.assertIn(contract, agent, "agent body must embed the shared contract verbatim")
        self.assertIn('model: inherit', agent)
        self.assertIn('"Read"', agent)

    def test_codex_generates_per_skill_openai_yaml(self):
        from workflow.product import parse_skill_meta
        for skill in ("workflow", "tdd", "debugging", "review", "verification", "review-results"):
            yaml_path = self.pkg("codex") / "skills" / skill / "agents" / "openai.yaml"
            self.assertTrue(yaml_path.is_file(), skill)
            meta = parse_skill_meta(self.pkg("codex") / "skills" / skill / "SKILL.md")
            self.assertEqual(meta["name"], skill)

    def test_marketplace_files_resolve_to_package(self):
        for host in HOSTS:
            market_rel = ".agents/plugins/marketplace.json" if host == "codex" else "marketplace.json"
            market = wio.load_json(self.out1 / host / market_rel)
            entry = market["plugins"][0]
            self.assertEqual(entry["name"], "ai-code-workflow")
            source = entry["source"]
            source_path = source["path"] if isinstance(source, dict) else source
            resolved = (self.out1 / host / source_path).resolve()
            self.assertTrue((resolved / "artifact.json").is_file(), host)
            self.assertEqual(entry["version"], self.artifact(host)["version"])

    def test_index_records_paths_and_hashes_without_time(self):
        index = wio.load_json(self.out1 / "index.json")
        self.assertEqual(index["product_id"], "ai-code-workflow")
        self.assertEqual(index["version"], wio.load_json(REPO_ROOT / "product.json")["version"])
        for host in HOSTS:
            entry = index["hosts"][host]
            self.assertEqual(entry["package_content_hash"], self.artifact(host)["content_hash"])
            self.assertEqual(
                wio.sha256_file(self.out1 / entry["zip"]), entry["zip_sha256"])
        self.assertNotIn("built_at", json.dumps(index))

    def test_existing_output_refused(self):
        from workflow import build as wbuild
        from workflow.io import DataError
        with self.assertRaises(DataError):
            wbuild.build_packages(REPO_ROOT, ["zcode"], self.out1)

    def test_zip_deterministic_entry_metadata(self):
        import zipfile
        zip_path = self.out1 / "zcode" / f"ai-code-workflow-{self.artifact('zcode')['version']}.zip"
        with zipfile.ZipFile(zip_path) as zf:
            infos = zf.infolist()
            names = [i.filename for i in infos]
            self.assertEqual(names, sorted(names))
            for info in infos:
                self.assertEqual(info.date_time, (1980, 1, 1, 0, 0, 0))

    def test_build_records_clean_dirty_and_no_git_provenance(self):
        from workflow import build as wbuild
        for revision, dirty in (("1" * 40, False), ("2" * 40, True), (None, False)):
            with self.subTest(revision=revision, dirty=dirty), tempfile.TemporaryDirectory() as td:
                with patch.object(wbuild, "_git_state", return_value=(revision, dirty)):
                    wbuild.build_packages(REPO_ROOT, ["codex"], Path(td) / "dist")
                art = wio.load_json(Path(td) / "dist/codex/ai-code-workflow/artifact.json")
                self.assertEqual(art["source_revision"], revision)
                self.assertIs(art["working_tree_dirty"], dirty)


class BuildValidationTests(unittest.TestCase):
    def setUp(self):
        from workflow import product
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.source = self.base / "source"
        self.output = self.base / "dist"
        spec = product.load_product(REPO_ROOT)
        for file in [REPO_ROOT / "product.json", *(p for p, _ in spec.files)]:
            destination = self.source / file.relative_to(REPO_ROOT)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(file, destination)
        shutil.copytree(REPO_ROOT / "adapters", self.source / "adapters")

    def tearDown(self):
        self.temp.cleanup()

    def build(self, host="codex"):
        from workflow import build
        return build.build_packages(self.source, [host], self.output)

    def test_quotes_and_newlines_round_trip_in_generated_interface(self):
        path = self.source / "adapters/codex/interfaces.json"
        interfaces = wio.load_json(path)
        interfaces["skills"]["workflow"]["default_prompt"] = 'Use the "workflow" skill\nthen review'
        path.write_text(json.dumps(interfaces))
        self.build()
        emitted = (self.output / "codex/ai-code-workflow/skills/workflow/agents/openai.yaml").read_text()
        self.assertIn(r'default_prompt: "Use the \"workflow\" skill\nthen review"', emitted)

    def test_invalid_interface_contract_is_rejected_before_output(self):
        path = self.source / "adapters/codex/interfaces.json"
        original = wio.load_json(path)
        mutations = (
            lambda d: d.update(schema_version=True),
            lambda d: d.update(unexpected=True),
            lambda d: d["skills"]["workflow"].update(default_prompt=12),
            lambda d: d["skills"]["workflow"].update(allow_implicit_invocation="false"),
            lambda d: d["skills"]["workflow"].update(brand_color="blue"),
            lambda d: d["skills"]["workflow"].update(unknown="field"),
        )
        for index, mutate in enumerate(mutations):
            with self.subTest(mutate=mutate):
                self.output = self.base / f"dist-{index}"
                data = json.loads(json.dumps(original))
                mutate(data)
                path.write_text(json.dumps(data))
                with self.assertRaises(wio.DataError):
                    self.build()
                self.assertFalse(self.output.exists())

    def test_missing_required_resource_fails_without_touching_empty_output(self):
        path = self.source / "product.json"
        product = wio.load_json(path)
        product["resources"] = [r for r in product["resources"] if r["source"] != "NOTICE"]
        path.write_text(json.dumps(product))
        self.output.mkdir()
        with self.assertRaisesRegex(wio.DataError, "NOTICE"):
            self.build()
        self.assertEqual(list(self.output.iterdir()), [])

    def test_mid_build_failure_does_not_publish_partial_output(self):
        from workflow import build
        with patch.object(build, "_write_zip", side_effect=OSError("injected archive write failure")):
            with self.assertRaisesRegex(OSError, "injected archive"):
                self.build()
        self.assertFalse(self.output.exists())
        self.assertEqual(sorted(p.name for p in self.base.iterdir()), ["source"])

    def test_reviewer_static_restrictions_are_validated(self):
        path = self.source / "adapters/zcode/agents/workflow-reviewer.md"
        original = path.read_text()
        mutations = (
                ("model: inherit", "model: arbitrary-model"),
                ('tools: ["Read", "Grep", "Glob"]', 'tools: ["Read", "Grep", "Glob", "Write"]'),
                ("maxTurns: 12", "maxTurns: true"),
                ("maxTurns: 12", "maxTurns: 12\nunknown: value"))
        for index, (old, replacement) in enumerate(mutations):
            with self.subTest(replacement=replacement):
                self.output = self.base / f"dist-{index}"
                path.write_text(original.replace(old, replacement))
                with self.assertRaises(wio.DataError):
                    self.build("zcode")
                self.assertFalse(self.output.exists())

    def test_copy_time_source_change_cannot_disagree_with_provenance(self):
        from workflow import build
        original = (self.source / "NOTICE").read_bytes()
        baseline = self.build()
        baseline_hash = wio.load_json(Path(baseline["index"]))["source_tree_hash"]
        self.output = self.base / "changed-copy"
        copy = shutil.copyfile
        mutated = []

        def concurrent_edit(source, destination, *args, **kwargs):
            if Path(destination).name == "NOTICE" and "ai-code-workflow" in Path(destination).parts:
                (self.source / "NOTICE").write_bytes(original + b"\nconcurrent source edit\n")
                mutated.append(True)
            return copy(source, destination, *args, **kwargs)

        with patch.object(build.shutil, "copyfile", side_effect=concurrent_edit):
            self.build()
        self.assertTrue(mutated, "the copy-time source change must actually occur")
        package = self.output / "codex/ai-code-workflow"
        self.assertEqual((package / "NOTICE").read_bytes(), original)
        self.assertEqual(wio.load_json(package / "artifact.json")["source_tree_hash"], baseline_hash)

    def test_copy_time_mutate_restore_is_rejected_without_output(self):
        from workflow import build
        copy = shutil.copyfile
        mutated = []

        def mutate_copy_restore(source, destination, *args, **kwargs):
            if Path(destination).name != "NOTICE" or "ai-code-workflow" not in Path(destination).parts:
                return copy(source, destination, *args, **kwargs)
            path = Path(source)
            before = path.read_bytes()
            path.write_bytes(before + b"\ntransient copy-time change\n")
            try:
                mutated.append(True)
                return copy(source, destination, *args, **kwargs)
            finally:
                path.write_bytes(before)

        with patch.object(build.shutil, "copyfile", side_effect=mutate_copy_restore):
            with self.assertRaisesRegex(wio.DataError, "changed|snapshot|hash"):
                self.build()
        self.assertTrue(mutated)
        self.assertFalse(self.output.exists())

    def test_git_context_is_read_before_private_build_directories_exist(self):
        from workflow import build
        self.output = self.source / "fresh-dist"
        observed = []

        def git_context(root):
            self.assertEqual(Path(root), self.source)
            private = list(self.source.glob(".workflow-build-*"))
            observed.append(private)
            return "1" * 40, bool(private)

        with patch.object(build, "_git_state", side_effect=git_context):
            self.build()
        self.assertEqual(observed, [[]])
        artifact = wio.load_json(self.output / "codex/ai-code-workflow/artifact.json")
        self.assertIs(artifact["working_tree_dirty"], False)


if __name__ == "__main__":
    unittest.main()
