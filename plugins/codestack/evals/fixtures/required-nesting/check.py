#!/usr/bin/env python3
"""Run external Java contracts without treating nesting as an automatic score."""

import argparse
from pathlib import Path
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parent


def check(workspace):
    """Preserve context, compile allowed production sources and execute the oracle."""
    if (workspace / "README.md").read_bytes() != (ROOT / "seed/README.md").read_bytes():
        raise AssertionError("The task did not authorize project-context changes")
    for path in workspace.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(workspace)
        if relative == Path("README.md") or relative.parts[0] == ".agents":
            continue
        if relative.parts[0] != "src" or path.suffix != ".java":
            raise AssertionError(f"Unrequested project file: {relative}")
    sources = sorted((workspace / "src").rglob("*.java"))
    if not sources:
        raise AssertionError("Candidate production sources are missing")
    with tempfile.TemporaryDirectory(prefix="codestack-visitor-check-") as directory:
        subprocess.run(
            ["javac", "-encoding", "UTF-8", "-Xlint:all", "-d", directory,
             *map(str, sources), str(ROOT / "oracle/AttachmentUsageCheck.java")],
            check=True,
        )
        subprocess.run(["java", "-cp", directory, "AttachmentUsageCheck", directory], check=True)


def main():
    """Accept the operator's frozen candidate workspace."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("workspace", type=Path)
    args = parser.parse_args()
    check(args.workspace.resolve())


if __name__ == "__main__":
    main()
