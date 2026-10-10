"""Private acceptance is checked locally; frozen hashes survive clean CI checkouts."""

from pathlib import Path
import json
import shutil
import subprocess
import sys
import tempfile
import unittest

from plugin_tools.registry import load_catalog
from plugin_tools import io
from plugin_tools.release import prepare_release, verify_release
from plugin_tools.release.integrity import read_tree
from tests.tooling.test_distribution import accept_fixture
from tests.tooling.test_release import release_plugin
from tests.tooling.test_registry import write_json
from tests import test_release_publish as publishing
from tests import test_marketplace_deploy as deploying

ROOT = Path(__file__).resolve().parents[1]
PROOF = "release/acceptance-proof.json"


class AcceptanceHandoffTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="ai-code-acceptance-handoff-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name).resolve()
        self.root = self.base / "local"
        self.plugin = release_plugin(self.root)
        product = json.loads((self.plugin / "product.json").read_text())
        product["repository"] = "https://github.com/Example/ai-code"
        write_json(self.plugin / "product.json", product)
        (self.root / "distribution.json").write_bytes((ROOT / "distribution.json").read_bytes())
        accept_fixture(self.root, "ai-one")
        (self.root / ".gitignore").write_text("plugins/*/release/*-raw.txt\nplugins/*/release/*-accepted.json\n")
        self.tag = "ai-one/v1.0.0"

    def export(self):
        result = subprocess.run([sys.executable, str(ROOT / "tooling/plugin_tool.py"),
            "release", "acceptance-export", "--root", str(self.root), "--plugin", "ai-one"],
            capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return (self.plugin / PROOF).read_bytes()

    def git(self, *arguments, root=None):
        result = subprocess.run(["git", "-c", "user.name=Fixture", "-c",
            "user.email=fixture@example.invalid", *arguments], cwd=root or self.root,
            capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout.strip()

    def freeze(self, change=None):
        proof = self.export()
        if change is not None:
            change()
        self.git("init", "-b", "main")
        self.git("add", ".")
        self.git("commit", "-qm", "frozen source and public acceptance hashes")
        self.revision = self.git("rev-parse", "HEAD")
        self.git("tag", self.tag)
        self.clean = self.base / "clean"
        self.git("clone", "-q", "--no-local", str(self.root), str(self.clean))
        self.git("checkout", "-q", self.tag, root=self.clean)
        self.assertEqual(self.git("status", "--porcelain", root=self.clean), "")
        self.assertFalse(list((self.clean / "plugins/ai-one/release").glob("*-raw.txt")))
        return proof

    def test_clean_checkout_prepares_publishes_and_plans_the_same_stable_bytes(self):
        self.freeze()
        local_bundle = self.base / "local-bundle"
        local = prepare_release(self.root, load_catalog(self.root)[0], local_bundle, mode="stable")
        self.assertTrue(local["publication_ready"], local)
        clean_bundle = self.base / "clean-bundle"
        prepared = publishing.prepare.prepare(self.clean, "ai-one", self.tag, clean_bundle)
        self.assertEqual(prepared["mode"], "stable")
        self.assertEqual(read_tree(local_bundle), read_tree(clean_bundle))
        github = publishing.FakeGitHub(self.revision)
        self.addCleanup(github.close)
        result = publishing.publish.publish_release(self.clean, "ai-one", self.tag,
            clean_bundle, "Example/ai-code", run=github.run)
        self.assertTrue(result["ok"], result)
        self.assertFalse(result["prerelease"])

        class PublicAPI:
            repository = "Example/ai-code"
            def tag(inner, tag):
                return self.revision
            def release(inner, tag):
                return {"id": 73, "tag_name": tag, "draft": False, "prerelease": False,
                    "html_url": "https://github.com/Example/ai-code/releases/tag/ai-one%2Fv1.0.0",
                    "assets": [{"id": number, "name": name, "size": len(github.assets[number]),
                        "browser_download_url": "https://github.com/Example/ai-code/releases/download/ai-one%2Fv1.0.0/" + name}
                        for number, name in github.names.items()]}
            def download(inner, asset, tag):
                return github.assets[asset["id"]]
            def market(inner, revision):
                return self.revision, {}

        plan = deploying.implementation().deploy(self.clean, "ai-one", self.tag, "stable",
            PublicAPI(), action="plan")
        self.assertEqual(plan["status"], "plan_ready")

    def test_export_does_not_publish_evidence_or_raw_bodies(self):
        proof = self.export()
        for path in self.plugin.glob("release/*-raw.txt"):
            self.assertNotIn(path.read_bytes(), proof)
        for path in self.plugin.glob("release/*-accepted.json"):
            evidence = json.loads(path.read_text())
            self.assertNotIn(evidence["summary"].encode(), proof)
            self.assertNotIn(path.read_bytes(), proof)

    def test_default_local_verification_still_requires_real_private_files(self):
        self.freeze()
        bundle = self.base / "ci-bundle"
        publishing.prepare.prepare(self.clean, "ai-one", self.tag, bundle)
        result = verify_release(self.clean, load_catalog(self.clean)[0], bundle)
        self.assertFalse(result["ok"], result)
        self.assertIn("accepted.json", result["blockers"][0])

    def test_export_rejects_missing_or_corrupt_actual_private_logs(self):
        raw = next(self.plugin.glob("release/*-raw.txt"))
        for value in (None, b"changed private evidence"):
            with self.subTest(value=value):
                if value is None:
                    raw.unlink()
                else:
                    raw.write_bytes(value)
                result = subprocess.run([sys.executable, str(ROOT / "tooling/plugin_tool.py"),
                    "release", "acceptance-export", "--root", str(self.root), "--plugin", "ai-one"],
                    capture_output=True, text=True)
                self.assertNotEqual(result.returncode, 0)
                self.assertFalse((self.plugin / PROOF).exists())

    def test_export_rejects_pending_hosts(self):
        config = json.loads((self.plugin / "release.json").read_text())
        config["acceptance"]["codex"] = None
        write_json(self.plugin / "release.json", config)
        result = subprocess.run([sys.executable, str(ROOT / "tooling/plugin_tool.py"),
            "release", "acceptance-export", "--root", str(self.root), "--plugin", "ai-one"],
            capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.plugin / PROOF).exists())

    def test_statement_cannot_be_replaced_by_uncommitted_bytes(self):
        self.freeze()
        proof = self.clean / "plugins/ai-one" / PROOF
        proof.write_bytes(proof.read_bytes() + b" ")
        with self.assertRaisesRegex(ValueError, "clean canonical tagged"):
            publishing.prepare.prepare(self.clean, "ai-one", self.tag, self.base / "invalid-bundle")

    def test_hidden_deletion_of_frozen_statement_cannot_fall_back_to_raw(self):
        self.freeze()
        clean_plugin = self.clean / "plugins/ai-one"
        for path in self.plugin.glob("release/*-raw.txt"):
            shutil.copy2(path, clean_plugin / "release" / path.name)
        for path in self.plugin.glob("release/*-accepted.json"):
            shutil.copy2(path, clean_plugin / "release" / path.name)
        self.git("update-index", "--skip-worktree", "plugins/ai-one/" + PROOF, root=self.clean)
        (clean_plugin / PROOF).unlink()
        self.assertEqual(self.git("status", "--porcelain", root=self.clean), "")
        with self.assertRaises(ValueError):
            publishing.prepare.prepare(self.clean, "ai-one", self.tag, self.base / "invalid-bundle")

    def test_export_cannot_produce_a_statement_larger_than_the_ci_read_limit(self):
        directory = self.plugin / "release/proof-size" / ("x" * 192)
        directory.mkdir(parents=True)
        artifacts = []
        for number in range(2000):
            path = directory / (f"{number:064d}" + ".txt")
            raw = f"Private raw artifact {number}".encode()
            path.write_bytes(raw)
            artifacts.append({"path": path.relative_to(self.plugin).as_posix(), "sha256": io.sha256(raw)})
        for path in self.plugin.glob("release/*-accepted.json"):
            record = json.loads(path.read_text())
            record["artifacts"] = artifacts
            write_json(path, record)
            self.assertLess(path.stat().st_size, 1024 * 1024)
        result = subprocess.run([sys.executable, str(ROOT / "tooling/plugin_tool.py"),
            "release", "acceptance-export", "--root", str(self.root), "--plugin", "ai-one"],
            capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("limit", result.stderr)
        self.assertFalse((self.plugin / PROOF).exists())

    def test_committed_statement_rejects_stale_release_documents(self):
        def change_document():
            (self.plugin / "release/NOTES.md").write_text("Changed after acceptance export\n")
        self.freeze(change_document)
        with self.assertRaisesRegex(ValueError, "public input bindings"):
            publishing.prepare.prepare(self.clean, "ai-one", self.tag, self.base / "invalid-bundle")

    def test_committed_statement_rejects_unknown_fields_and_bad_host_bindings(self):
        changes = (
            lambda proof: proof.update(extra="not allowed"),
            lambda proof: proof["hosts"].pop("codex"),
            lambda proof: proof["package_content_hashes"].update(codex="0" * 64),
            lambda proof: proof["hosts"]["codex"]["evidence"].update(path="release/../private.json"),
            lambda proof: proof["hosts"]["codex"].update(artifacts=[]),
        )
        for change in changes:
            with self.subTest(change=change):
                self.setUp()
                def mutate():
                    path = self.plugin / PROOF
                    proof = json.loads(path.read_text())
                    change(proof)
                    path.write_bytes(io.dump_json(proof))
                self.freeze(mutate)
                with self.assertRaises(ValueError):
                    publishing.prepare.prepare(self.clean, "ai-one", self.tag, self.base / "invalid-bundle")


if __name__ == "__main__":
    unittest.main()
