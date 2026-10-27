#!/usr/bin/env python3
"""Run evaluator-owned Java checks without prescribing private type structure."""

import argparse
from pathlib import Path
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parent
CASES = {"business-result": "DispatchCheck", "jdk-iterator": "IteratorCheck"}


def check_scope(case, workspace):
    """Preserve seed context and allow only the Java source scope of each task."""
    original = ROOT / case
    if (workspace / "README.md").read_bytes() != (original / "README.md").read_bytes():
        raise AssertionError("The task did not authorize changes to project context")
    for path in workspace.rglob("*"):
        if not path.is_file():
            continue
        relative = path.relative_to(workspace)
        if relative.parts[0] == ".agents":
            continue
        if relative == Path("README.md"):
            continue
        allowed = (
            relative.parts[0] == "src" and path.suffix == ".java"
            if case == "business-result"
            else relative == Path("src/MessageWindow.java")
        )
        if not allowed:
            raise AssertionError(f"Unrequested project file added: {relative}")


def check(case, workspace):
    """Compile candidate production Java with a frozen external behavior oracle."""
    check_scope(case, workspace)
    sources = sorted((workspace / "src").rglob("*.java"))
    if not sources:
        raise AssertionError("Candidate production source is missing")
    with tempfile.TemporaryDirectory(prefix="codestack-nested-check-") as directory:
        subprocess.run(
            ["javac", "-encoding", "UTF-8", "-Xlint:all", "-d", directory,
             *map(str, sources), str(ROOT / "oracle" / f"{CASES[case]}.java")],
            check=True,
        )
        subprocess.run(["java", "-cp", directory, CASES[case]], check=True)


def main():
    """Select the operator's frozen task without interpreting model explanations."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", choices=CASES)
    parser.add_argument("workspace", type=Path)
    args = parser.parse_args()
    check(args.case, args.workspace.resolve())


if __name__ == "__main__":
    main()
