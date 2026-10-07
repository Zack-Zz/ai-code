"""Read-only Git metadata boundaries for local artifact output directories."""

from pathlib import Path
import subprocess

from .io import DataError


def _git_directory(root, flag):
    try:
        result = subprocess.run(["git", "rev-parse", flag], cwd=root,
                                capture_output=True, text=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0 or not result.stdout.strip():
        return None
    path = Path(result.stdout.strip())
    return (path if path.is_absolute() else root / path).resolve()


def reject_git_output(root, output):
    root = Path(root).resolve()
    output = Path(output).absolute()
    if ".git" in output.parts:
        raise DataError("artifact output cannot modify Git metadata")
    destination = output.parent.resolve() / output.name
    directories = [_git_directory(root, "--absolute-git-dir"), _git_directory(root, "--git-common-dir")]
    if any(directory is not None and (destination == directory or directory in destination.parents)
           for directory in directories):
        raise DataError("artifact output cannot modify Git metadata or its directory aliases")
