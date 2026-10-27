"""Executable fixtures and evidence plumbing; these do not grade agent behavior."""

import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[2]
EVALS = PLUGIN / "evals"


def run_py(script, *args, cwd=PLUGIN):
    return subprocess.run([sys.executable, "-B", str(script), *args], cwd=cwd,
                          capture_output=True, text=True, timeout=60)


class ConcurrencyEvalTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def prepare(self, case_id):
        output = self.base / case_id
        result = run_py(EVALS / "prepare.py", "--case", case_id, "--output", str(output))
        self.assertEqual(result.returncode, 0, result.stderr)
        return output, json.loads((output / "prepared.json").read_text())

    def test_prepare_copies_complete_fixture_and_binds_case_inputs(self):
        source = json.loads((EVALS / "cases.json").read_text())
        for case_id in ("A37", "A38", "A39"):
            with self.subTest(case=case_id):
                output, record = self.prepare(case_id)
                self.assertEqual(record["fixture"], "concurrency_review")
                case = next(item for item in source["cases"] if item["case_id"] == case_id)
                self.assertEqual(case["kind"], "agent")
                self.assertEqual(record["turns"], case["turns"])
                self.assertEqual(record["cases_sha256"], hashlib.sha256(
                    (EVALS / "cases.json").read_bytes()).hexdigest())
                fixture = EVALS / "fixtures/concurrency_review"
                expected = {"workspace/" + path.relative_to(fixture).as_posix():
                            hashlib.sha256(path.read_bytes()).hexdigest()
                            for path in fixture.rglob("*") if path.is_file()}
                self.assertTrue(expected)
                self.assertEqual(record["baseline"], expected)
                self.assertEqual(record["baseline_directories"], ["workspace"])
                for relative, digest in expected.items():
                    self.assertEqual(hashlib.sha256((output / relative).read_bytes()).hexdigest(), digest)

    def test_independent_connections_exercise_unique_atomic_and_lost_updates(self):
        output, record = self.prepare("A38")
        workspace = output / "workspace"
        result = run_py(workspace / "exercise.py", cwd=workspace)
        self.assertEqual(result.returncode, 0, result.stderr)
        observed = json.loads(result.stdout)
        registration = observed["registration"]
        self.assertEqual(registration["initial_lookups"], [None, None])
        self.assertEqual(registration["request_ids"], [1, 1])
        self.assertEqual(registration["registration_rows"], 1)
        self.assertEqual(registration["outbox_rows"], 1)
        self.assertEqual(registration["other_tenant_id"], 2)
        self.assertEqual(registration["first_payload"], "first payload")
        self.assertEqual(observed["counter_after"]["reads"], [10, 10])
        self.assertEqual(observed["counter_after"]["writes"], [11, 11])
        self.assertEqual(observed["counter_after"]["final"], 11)
        self.assertEqual(observed["counter_before"]["final"], 12)
        self.assertEqual(observed["counter_after"]["connections"], 2)
        # The fixture is copied byte-for-byte and running it leaves no databases/caches behind.
        actual = {"workspace/" + path.name: hashlib.sha256(path.read_bytes()).hexdigest()
                  for path in workspace.iterdir() if path.is_file()}
        self.assertEqual(actual, record["baseline"])
        self.assertEqual(sorted(p.name for p in workspace.iterdir()),
                         sorted(Path(key).name for key in record["baseline"]))

    def test_captured_fixture_material_is_hashed_and_does_not_claim_agent_pass(self):
        output, prepared = self.prepare("A39")
        observations = run_py(output / "workspace/exercise.py", cwd=output / "workspace")
        self.assertEqual(observations.returncode, 0, observations.stderr)
        material = self.base / "observations.json"
        material.write_text(observations.stdout)
        baseline_bytes = json.dumps(prepared["baseline"], sort_keys=True,
                                    separators=(",", ":"), ensure_ascii=True).encode()
        manifest = {
            "schema_version": 1, "case_id": "A39", "host": "codex", "host_version": None,
            "model": None, "package_content_hash": None, "policy_hash": None,
            "comparison_mode": "plugin", "workspace_root": str(output / "workspace"),
            "fixture_baseline_hash": hashlib.sha256(baseline_bytes).hexdigest(),
            "raw_files": [{"source_path": str(material), "target_path": "raw/observations.json"}],
            "artifact_files": [
                {"source_path": str(output / "prepared.json"), "target_path": "inputs/prepared.json"},
                {"source_path": str(output / "workspace/proposal.md"), "target_path": "inputs/proposal.md"}],
            "events": [], "converter_id": None, "started_at": None, "finished_at": None,
        }
        path = self.base / "manifest.json"
        path.write_text(json.dumps(manifest))
        for name in ("fresh", "tampered"):
            run_dir = self.base / name
            result = run_py(EVALS / "collect.py", "--case", "A39", "--input", str(path),
                            "--origin", "manual_annotation", "--output", str(run_dir))
            self.assertEqual(result.returncode, 0, result.stderr)
            index = json.loads((run_dir / "index.json").read_text())
            self.assertEqual(index["fixture_baseline_hash"], manifest["fixture_baseline_hash"])
            for ref in index["raw_refs"] + index["artifacts"]:
                self.assertEqual(hashlib.sha256((run_dir / ref["target_path"]).read_bytes()).hexdigest(),
                                 ref["content_sha256"])
            if name == "tampered":
                (run_dir / "inputs/proposal.md").write_text("changed material")
            graded = run_py(EVALS / "grade.py", "--run", str(run_dir))
            if name == "tampered":
                self.assertEqual(graded.returncode, 2, graded.stderr)
                self.assertIn("collected material changed", graded.stderr)
                self.assertFalse((run_dir / "grade.json").exists())
            else:
                self.assertEqual(graded.returncode, 0, graded.stderr)
                grade = json.loads((run_dir / "grade.json").read_text())
                self.assertEqual(grade["overall"], "manual_review")
                self.assertTrue(all(check["result"] == "not_run" for check in grade["checks"]))


if __name__ == "__main__":
    unittest.main()
