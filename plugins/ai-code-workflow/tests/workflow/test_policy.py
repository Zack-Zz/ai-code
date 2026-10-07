"""policy module: profile loading, override resolution and precedence."""

import json
import tempfile
import unittest
from pathlib import Path

from workflow import policy as pl

REPO_ROOT = Path(__file__).resolve().parents[2]


def make_plugin_root(td: Path) -> Path:
    """Mirror a plugin package layout with both profiles."""
    pol = td / "policies"
    pol.mkdir(parents=True)
    base = {
        "schema_version": 1,
        "mode": "collaborative",
        "review_level": "critical",
        "max_parallel_tasks": 2,
        "response_language": "auto",
        "verification_notes": [],
    }
    (pol / "collaborative.json").write_text(json.dumps(base), encoding="utf-8")
    cont = dict(base, mode="continuous")
    (pol / "continuous.json").write_text(json.dumps(cont), encoding="utf-8")
    return td


class ProfileTests(unittest.TestCase):
    def test_real_repo_profiles_valid_and_differ_only_by_mode(self):
        coll = pl.load_profile(REPO_ROOT, "collaborative")
        cont = pl.load_profile(REPO_ROOT, "continuous")
        self.assertEqual(coll["mode"], "collaborative")
        self.assertEqual(cont["mode"], "continuous")
        coll.pop("mode"), cont.pop("mode")
        self.assertEqual(coll, cont)

    def test_rejects_profile_with_wrong_mode_inside(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_plugin_root(Path(td))
            p = root / "policies" / "continuous.json"
            data = json.loads(p.read_text())
            data["mode"] = "collaborative"
            p.write_text(json.dumps(data))
            with self.assertRaisesRegex(Exception, "mode"):
                pl.load_profile(root, "continuous")

    def test_rejects_incomplete_profile(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_plugin_root(Path(td))
            p = root / "policies" / "collaborative.json"
            data = json.loads(p.read_text())
            del data["review_level"]
            p.write_text(json.dumps(data))
            with self.assertRaisesRegex(Exception, "review_level"):
                pl.load_profile(root, "collaborative")

    def test_rejects_unknown_profile_field(self):
        with tempfile.TemporaryDirectory() as td:
            root = make_plugin_root(Path(td))
            p = root / "policies" / "collaborative.json"
            data = json.loads(p.read_text())
            data["approved"] = True
            p.write_text(json.dumps(data))
            with self.assertRaisesRegex(Exception, "unknown|approved"):
                pl.load_profile(root, "collaborative")


class ResolveTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.plugin = make_plugin_root(Path(self.td.name) / "plugin")
        (Path(self.td.name) / "plugin").mkdir(parents=True, exist_ok=True)
        # recreate properly: plugin dir already made by make_plugin_root parent handling
        self.ws = Path(self.td.name) / "workspace"
        self.ws.mkdir()

    def tearDown(self):
        self.td.cleanup()

    def write_project_file(self, payload):
        ai = self.ws / ".ai-workflow"
        ai.mkdir(exist_ok=True)
        (ai / "policy.json").write_text(payload, encoding="utf-8")

    def test_default_is_collaborative_with_plugin_sources(self):
        result = pl.resolve_policy(self.plugin, self.ws, None)
        self.assertEqual(result["effective_policy"]["mode"], "collaborative")
        self.assertEqual(
            result["sources"]["mode"], "plugin:policies/collaborative.json")
        self.assertEqual(len(result["warnings"]), 0)
        self.assertRegex(result["policy_hash"], r"^[0-9a-f]{64}$")

    def test_explicit_mode_selects_continuous_profile(self):
        result = pl.resolve_policy(self.plugin, self.ws, {"mode": "continuous"})
        self.assertEqual(result["effective_policy"]["mode"], "continuous")
        self.assertEqual(
            result["sources"]["mode"], "user:explicit")
        self.assertTrue(any("continuous" in w for w in result["warnings"]))

    def test_project_file_overrides_base_fields(self):
        self.write_project_file(
            '{"schema_version": 1, "review_level": "all", "max_parallel_tasks": 4}')
        result = pl.resolve_policy(self.plugin, self.ws, None)
        self.assertEqual(result["effective_policy"]["review_level"], "all")
        self.assertEqual(result["effective_policy"]["max_parallel_tasks"], 4)
        self.assertEqual(
            result["sources"]["review_level"], "project:.ai-workflow/policy.json")

    def test_explicit_beats_project_file(self):
        self.write_project_file(
            '{"schema_version": 1, "review_level": "all"}')
        result = pl.resolve_policy(
            self.plugin, self.ws, {"review_level": "critical"})
        self.assertEqual(result["effective_policy"]["review_level"], "critical")
        self.assertEqual(result["sources"]["review_level"], "user:explicit")

    def test_project_file_without_schema_version_rejected(self):
        self.write_project_file('{"review_level": "all"}')
        with self.assertRaisesRegex(Exception, "schema_version"):
            pl.resolve_policy(self.plugin, self.ws, None)

    def test_project_file_unknown_field_rejected(self):
        self.write_project_file('{"schema_version": 1, "auto_commit": true}')
        with self.assertRaisesRegex(Exception, "unknown|auto_commit"):
            pl.resolve_policy(self.plugin, self.ws, None)

    def test_project_file_with_duplicate_keys_rejected(self):
        self.write_project_file(
            '{"schema_version": 1, "review_level": "all", "review_level": "critical"}')
        with self.assertRaisesRegex(Exception, "duplicate"):
            pl.resolve_policy(self.plugin, self.ws, None)

    def test_bool_masquerading_as_int_rejected(self):
        with self.assertRaisesRegex(Exception, "max_parallel_tasks"):
            pl.resolve_policy(self.plugin, self.ws, {"max_parallel_tasks": True})

    def test_invalid_language_tag_rejected(self):
        with self.assertRaisesRegex(Exception, "response_language"):
            pl.resolve_policy(self.plugin, self.ws, {"response_language": "??bad??"})

    def test_valid_language_tag_accepted(self):
        result = pl.resolve_policy(self.plugin, self.ws, {"response_language": "zh-CN"})
        self.assertEqual(result["effective_policy"]["response_language"], "zh-CN")

    def test_verification_notes_bounds(self):
        too_many = {"verification_notes": [f"note-{i}" for i in range(17)]}
        with self.assertRaisesRegex(Exception, "verification_notes"):
            pl.resolve_policy(self.plugin, self.ws, too_many)
        too_long = {"verification_notes": ["x" * 513]}
        with self.assertRaisesRegex(Exception, "verification_notes"):
            pl.resolve_policy(self.plugin, self.ws, too_long)

    def test_hash_stable_for_same_effective_policy(self):
        a = pl.resolve_policy(self.plugin, self.ws, {"mode": "continuous"})
        b = pl.resolve_policy(self.plugin, self.ws, {"mode": "continuous"})
        self.assertEqual(a["policy_hash"], b["policy_hash"])

    def test_explicit_mode_after_project_continuous_still_wins(self):
        self.write_project_file('{"schema_version": 1, "mode": "continuous"}')
        result = pl.resolve_policy(self.plugin, self.ws, {"mode": "collaborative"})
        self.assertEqual(result["effective_policy"]["mode"], "collaborative")

    def test_real_repo_policy_resolves(self):
        result = pl.resolve_policy(REPO_ROOT, self.ws, {"mode": "continuous"})
        self.assertEqual(result["effective_policy"]["mode"], "continuous")
        self.assertEqual(result["effective_policy"]["max_parallel_tasks"], 2)


if __name__ == "__main__":
    unittest.main()
