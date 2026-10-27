#!/usr/bin/env python3
"""Run evaluator-owned behavior checks outside a disposable candidate workspace."""

import argparse
from pathlib import Path
import subprocess
import tempfile
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parent
ORM_PATH = Path("src/main/resources/META-INF/orm.xml")


def normalized(element):
    """Represent XML structure and meaningful text without indentation noise."""
    return (
        element.tag,
        tuple(sorted(element.attrib.items())),
        (element.text or "").strip(),
        tuple(normalized(child) for child in element),
    )


def check_xml(workspace):
    """Check the requested JPA column change and byte-preserve other input files."""
    original = ROOT / "jpa-xml"
    expected = ET.parse(original / ORM_PATH).getroot()
    column = expected.find(
        ".//{https://jakarta.ee/xml/ns/persistence/orm}basic[@name='displayName']/"
        "{https://jakarta.ee/xml/ns/persistence/orm}column"
    )
    assert column is not None
    column.set("name", "public_name")
    actual = ET.parse(workspace / ORM_PATH).getroot()
    if normalized(actual) != normalized(expected):
        raise AssertionError("Expected only the existing JPA displayName column to become public_name")
    original_paths = {path.relative_to(original) for path in original.rglob("*") if path.is_file()}
    for relative in original_paths - {ORM_PATH}:
        if (workspace / relative).read_bytes() != (original / relative).read_bytes():
            raise AssertionError(f"Unrelated input changed: {relative}")
    for path in workspace.rglob("*"):
        if path.is_file():
            relative = path.relative_to(workspace)
            if relative.parts[0] == ".agents":
                continue
            if relative not in original_paths:
                raise AssertionError(f"Unrequested project file added: {relative}")
    print("JPA XML column mapping passed; Java, Javadoc and other project bytes unchanged")


def check_java(case, workspace, h2_jar, group):
    """Compile candidate source with an external frozen checker, then execute it."""
    if h2_jar is None or not h2_jar.is_file():
        raise ValueError("An existing H2 2.3.232 jar is required; no dependency is downloaded")
    source, checker = {
        "empty-filter": ("UserDirectory", "EmptyFilterCheck"),
        "authorized-export": ("TenantExport", "ExportCheck"),
    }[case]
    with tempfile.TemporaryDirectory(prefix="codestack-boundary-check-") as directory:
        subprocess.run(
            ["javac", "-encoding", "UTF-8", "-Xlint:all", "-d", directory,
             str(workspace / "src" / f"{source}.java"), str(ROOT / "oracle" / f"{checker}.java")],
            check=True,
        )
        command = ["java", "-cp", f"{directory}:{h2_jar}", checker]
        if case == "empty-filter":
            command.append(group)
        subprocess.run(command, check=True)


def main():
    """Parse the evaluator-selected case and run its independent outcome check."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", choices=("empty-filter", "jpa-xml", "authorized-export"))
    parser.add_argument("workspace", type=Path)
    parser.add_argument("--h2-jar", type=Path)
    parser.add_argument("--group", choices=("all", "required", "counterexamples"), default="all")
    args = parser.parse_args()
    if args.case == "jpa-xml":
        check_xml(args.workspace.resolve())
    else:
        check_java(args.case, args.workspace.resolve(), args.h2_jar, args.group)


if __name__ == "__main__":
    main()
