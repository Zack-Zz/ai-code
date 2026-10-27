#!/usr/bin/env python3
"""Exercise frozen outcome checks with concrete wrong and hand-repaired controls."""

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parent


def write_change(workspace, relative, before, after):
    """Apply one exact manual control change to a disposable source copy."""
    path = workspace / relative
    original = path.read_text(encoding="utf-8")
    if original.count(before) != 1:
        raise AssertionError(f"Control edit is not unique: {relative}: {before}")
    path.write_text(original.replace(before, after), encoding="utf-8")


def main():
    """Run checker calibration without invoking an agent or editing its fixtures."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--h2-jar", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    output = args.output or Path(tempfile.mkdtemp(prefix="codestack-boundary-calibration-", dir="/private/tmp"))
    output.mkdir(parents=True, exist_ok=True)
    results = []

    def copy_case(case, label):
        """Copy only the ordinary project seed for one independent control."""
        workspace = output / label
        shutil.copytree(ROOT / case, workspace)
        return workspace

    def run(case, label, workspace, expected, assertion="", group="all"):
        """Demand real success or a specific semantic assertion, never a tool error."""
        command = ["python3", "-B", str(ROOT / "check.py"), case, str(workspace),
                   "--h2-jar", str(args.h2_jar), "--group", group]
        completed = subprocess.run(command, text=True, capture_output=True, check=False)
        (output / f"{label}.log").write_text(completed.stdout + completed.stderr, encoding="utf-8")
        if completed.returncode != expected:
            raise AssertionError(f"{label}: expected exit {expected}, got {completed.returncode}; see {output}")
        if expected and ("AssertionError" not in completed.stderr or assertion not in completed.stderr):
            raise AssertionError(f"{label}: failure was not the required semantic assertion; see {output}")
        results.append({"control": label, "exit_code": completed.returncode,
                        "expected_assertion": assertion, "group": group, "command": command})
        print(f"{label}: exit {completed.returncode} (expected {expected})")

    required_fix = (
        "validate(userIds, offset, limit);",
        "validate(userIds, offset, limit);\n        if (userIds.isEmpty()) {\n            return List.of();\n        }",
    )
    workspace = copy_case("empty-filter", "required-starting-defect")
    run("empty-filter", "required-starting-defect", workspace, 1, "required empty expected []", "required")
    workspace = copy_case("empty-filter", "empty-positive")
    write_change(workspace, "src/UserDirectory.java", *required_fix)
    run("empty-filter", "empty-positive", workspace, 0)
    for method, ids, label, assertion in (
        ("excludingIds", "excludedIds", "empty-exclusion-wrong", "empty exclusion expected [4, 3]"),
        ("findByOptionalIds", "optionalIds", "empty-optional-wrong", "empty optional filter expected [4, 3]"),
    ):
        workspace = copy_case("empty-filter", label)
        write_change(workspace, "src/UserDirectory.java", *required_fix)
        write_change(workspace, "src/UserDirectory.java", f"validate({ids}, offset, limit);",
                     f"validate({ids}, offset, limit);\n        if ({ids}.isEmpty()) {{\n            return List.of();\n        }}")
        run("empty-filter", label, workspace, 1, assertion, "counterexamples")
    workspace = copy_case("empty-filter", "required-empty-still-queries")
    write_change(workspace, "src/UserDirectory.java", required_fix[0],
                 "validate(userIds, offset, limit);\n        if (userIds.isEmpty()) {\n"
                 "            query(tenantId, userIds, false, offset, limit);\n            return List.of();\n        }")
    run("empty-filter", "required-empty-still-queries", workspace, 1, "required empty expected SQL executions=0", "required")
    workspace = copy_case("empty-filter", "page-offset-wrong")
    write_change(workspace, "src/UserDirectory.java", *required_fix)
    write_change(workspace, "src/UserDirectory.java", "statement.setInt(index, offset);", "statement.setInt(index, 0);")
    run("empty-filter", "page-offset-wrong", workspace, 1, "empty exclusion expected [4, 3]", "counterexamples")

    workspace = copy_case("jpa-xml", "xml-starting-mapping")
    run("jpa-xml", "xml-starting-mapping", workspace, 1, "Expected only the existing JPA")
    workspace = copy_case("jpa-xml", "xml-positive")
    write_change(workspace, "src/main/resources/META-INF/orm.xml", 'name="display_name"', 'name="public_name"')
    run("jpa-xml", "xml-positive", workspace, 0)
    workspace = copy_case("jpa-xml", "xml-wrong-framework")
    (workspace / "src/main/resources/META-INF/orm.xml").write_text('<mapper namespace="example.Customer" />\n', encoding="utf-8")
    run("jpa-xml", "xml-wrong-framework", workspace, 1, "Expected only the existing JPA")
    workspace = copy_case("jpa-xml", "xml-unrelated-java")
    write_change(workspace, "src/main/resources/META-INF/orm.xml", 'name="display_name"', 'name="public_name"')
    write_change(workspace, "src/main/java/example/Customer.java", "public class Customer {", "// Unrequested cleanup.\npublic class Customer {")
    run("jpa-xml", "xml-unrelated-java", workspace, 1, "Unrelated input changed")

    export_fix = ('records.add(afterId + "," + rows.getString("display_name"));',
                  'records.add(afterId + "," + rows.getString("display_name") + "," + rows.getString("status"));')
    workspace = copy_case("authorized-export", "export-starting-field")
    run("authorized-export", "export-starting-field", workspace, 1, "CSV, tenant, range, limit or order differs")
    workspace = copy_case("authorized-export", "export-positive")
    write_change(workspace, "src/TenantExport.java", *export_fix)
    run("authorized-export", "export-positive", workspace, 0)
    workspace = copy_case("authorized-export", "export-budget-wrong")
    write_change(workspace, "src/TenantExport.java", *export_fix)
    write_change(workspace, "src/TenantExport.java", "BATCH_SIZE = 50;", "BATCH_SIZE = 200;")
    run("authorized-export", "export-budget-wrong", workspace, 1, "Approved batches of 50 require 4 SQL executions")
    workspace = copy_case("authorized-export", "export-status-hardcoded-wrong")
    write_change(workspace, "src/TenantExport.java", export_fix[0],
                 'records.add(afterId + "," + rows.getString("display_name") + ",ACTIVE");')
    run("authorized-export", "export-status-hardcoded-wrong", workspace, 1,
        "CSV, tenant, range, limit or order differs")

    (output / "calibration.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(f"Calibration controls passed: {len(results)}; records: {output}")


if __name__ == "__main__":
    main()
