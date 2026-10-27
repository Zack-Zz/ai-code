#!/usr/bin/env python3
"""Check contracts and real old-client linkage without classifying abstractions."""

import argparse
import os
from pathlib import Path
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parent
CASES = ("incompatible-reuse", "public-nested-api")


def check_scope(case, workspace):
    """Preserve original context and each task's exact permitted source scope."""
    seed = ROOT / case
    original = {path.relative_to(seed) for path in seed.rglob("*") if path.is_file()}
    actual = {path.relative_to(workspace) for path in workspace.rglob("*") if path.is_file()
              and path.relative_to(workspace).parts[0] != ".agents"}
    if not original.issubset(actual):
        raise AssertionError("An existing input file was removed")
    for relative in actual:
        permitted = (relative == Path("src/PreviewService.java") if case == "incompatible-reuse"
                     else relative.parts[0] == "src" and relative.suffix == ".java")
        if not permitted and (relative not in original
                              or (workspace / relative).read_bytes() != (seed / relative).read_bytes()):
            raise AssertionError(f"Unrequested input or file changed: {relative}")


def compile_java(output, sources):
    """Compile frozen or candidate sources into a fresh output directory."""
    output.mkdir(parents=True, exist_ok=True)
    subprocess.run(["javac", "-encoding", "UTF-8", "-Xlint:all", "-d", str(output),
                    *map(str, sources)], check=True)


def run_java(classpath, entry, *args):
    """Execute one evaluator-owned entry point."""
    subprocess.run(["java", "-cp", os.pathsep.join(map(str, classpath)), entry, *args], check=True)


def check(case, workspace, mode=None):
    """Check candidate behavior and, where applicable, original deployed bytecode."""
    check_scope(case, workspace)
    sources = sorted((workspace / "src").rglob("*.java"))
    with tempfile.TemporaryDirectory(prefix="codestack-contract-check-") as directory:
        output = Path(directory)
        library = output / "library"
        if case == "incompatible-reuse":
            compile_java(library, [*sources, ROOT / "oracle/PreviewCheck.java"])
            run_java([library], "PreviewCheck", *([mode] if mode else []))
            return
        original = output / "original"
        client = output / "deployed-client"
        compile_java(original, [*sorted((ROOT / case / "src").rglob("*.java")),
                                ROOT / "oracle/LegacyShipmentCaller.java"])
        client.mkdir()
        (client / "LegacyShipmentCaller.class").write_bytes(
            (original / "LegacyShipmentCaller.class").read_bytes())
        compile_java(library, [*sources, ROOT / "oracle/ShipmentCheck.java"])
        if mode != "semantics-only":
            run_java([client, library], "LegacyShipmentCaller")
        if mode != "compatibility-only":
            run_java([library], "ShipmentCheck")


def main():
    """Run a frozen local evaluation without relying on candidate-written tests."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", choices=CASES)
    parser.add_argument("workspace", type=Path)
    parser.add_argument("--section", choices=("side-effects", "unavailable", "invalid", "checkout",
                                               "semantics-only", "compatibility-only"))
    args = parser.parse_args()
    preview_sections = {"side-effects", "unavailable", "invalid", "checkout"}
    if args.section and ((args.section in preview_sections) != (args.case == "incompatible-reuse")):
        parser.error("The section does not belong to the selected contract")
    check(args.case, args.workspace.resolve(), args.section)


if __name__ == "__main__":
    main()
