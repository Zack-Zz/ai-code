"""Standalone builds never misstate Git cleanliness or write into Git metadata."""

from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest import mock

from workflow import build
from workflow.io import DataError


PLUGIN = Path(__file__).resolve().parents[2]


class GitBuildBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="workflow-git-boundary-")
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.repo = self.base / "repo"
        self.source = self.repo / "plugin"
        shutil.copytree(PLUGIN, self.source, ignore=shutil.ignore_patterns("__pycache__", "tests"))
        subprocess.run(["git", "init", "--quiet", str(self.repo)], check=True,
                       capture_output=True, text=True)

    def test_status_failure_for_known_head_cannot_publish_a_clean_artifact(self):
        run = subprocess.run

        def fail_status(command, **kwargs):
            if command == ["git", "rev-parse", "HEAD"]:
                return subprocess.CompletedProcess(command, 0, stdout="1" * 40 + "\n", stderr="")
            if command[:2] == ["git", "status"]:
                return subprocess.CompletedProcess(command, 128, stdout="", stderr="status unavailable")
            return run(command, **kwargs)

        output = self.base / "dist"
        with mock.patch.object(build.subprocess, "run", side_effect=fail_status):
            with self.assertRaisesRegex(DataError, "status|cleanliness"):
                build.build_packages(self.source, ["codex"], output)
        self.assertFalse(output.exists())

    def test_git_directory_and_common_directory_reject_canonical_and_alias_outputs(self):
        worktree = self.base / "linked"
        worktree.mkdir()
        metadata = self.repo / ".git/worktrees/linked"
        metadata.mkdir(parents=True)
        (metadata / "HEAD").write_text((self.repo / ".git/HEAD").read_text())
        (metadata / "commondir").write_text("../..\n")
        (metadata / "gitdir").write_text(str(worktree / ".git") + "\n")
        (worktree / ".git").write_text("gitdir: " + str(metadata) + "\n")
        source = worktree / "plugin"
        shutil.copytree(self.source, source)
        for git_root in (metadata, self.repo / ".git"):
            for alias in (False, True):
                with self.subTest(metadata=git_root, alias=alias):
                    shutil.rmtree(git_root / "forbidden-dist", ignore_errors=True)
                    selected = git_root
                    if alias:
                        selected = self.base / ("alias-worktree" if git_root == metadata else "alias-common")
                        selected.symlink_to(git_root, target_is_directory=True)
                    output = selected / "forbidden-dist"
                    with self.assertRaisesRegex(DataError, "Git.*metadata|Git.*directory"):
                        build.build_packages(source, ["codex"], output)
                    self.assertFalse(output.exists())

    def test_unborn_git_repository_with_failed_status_cannot_be_reported_clean(self):
        run = subprocess.run

        def fail_status(command, **kwargs):
            if command[:2] == ["git", "status"]:
                return subprocess.CompletedProcess(command, 128, stdout="", stderr="status unavailable")
            return run(command, **kwargs)

        output = self.base / "dist"
        with mock.patch.object(build.subprocess, "run", side_effect=fail_status):
            with self.assertRaisesRegex(DataError, "status|cleanliness"):
                build.build_packages(self.source, ["codex"], output)
        self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
