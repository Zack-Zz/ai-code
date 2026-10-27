#!/usr/bin/env python3
"""Calibrate incompatible-reuse and frozen-client checks with explicit hand controls."""

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parent
STUB = 'throw new UnsupportedOperationException("Preview is not implemented");'
READ_ONLY = '''if (units <= 0) {
            throw new IllegalArgumentException("Units must be positive");
        }
        OptionalLong price = inventory.unitPrice(tenant, sku);
        if (price.isEmpty() || inventory.availableUnits(tenant, sku) < units) {
            return OptionalLong.empty();
        }
        return OptionalLong.of(price.getAsLong() * units);'''
COMMAND_REUSE = "return OptionalLong.of(new CheckoutService(inventory).checkout(tenant, sku, units));"
NESTED = '''    /**
     * Immutable public quotation returned to existing clients.
     * @param feeCents total shipment fee in cents
     * @param estimatedDays expected delivery time in days
     */
    public record Quote(long feeCents, int estimatedDays) {
    }

'''


def replace(workspace, relative, before, after):
    """Apply one exact evaluator control edit to a disposable source tree."""
    path = workspace / relative
    source = path.read_text(encoding="utf-8")
    if source.count(before) != 1:
        raise AssertionError(f"Control edit is not unique: {relative}")
    path.write_text(source.replace(before, after), encoding="utf-8")


def main():
    """Require each control to fail at its intended contract rather than tooling."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    output = args.output or Path(tempfile.mkdtemp(prefix="codestack-contract-calibration-", dir="/private/tmp"))
    output.mkdir(parents=True, exist_ok=True)
    results = []

    def seed(case, label):
        """Copy only an ordinary project input for a separate hand control."""
        workspace = output / label
        shutil.copytree(ROOT / case, workspace)
        return workspace

    def run(case, label, workspace, expected=0, markers=(), section=None):
        """Record a concrete check result and require its exact failure category."""
        command = ["python3", "-B", str(ROOT / "check.py"), case, str(workspace)]
        if section:
            command.extend(["--section", section])
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        log = completed.stdout + completed.stderr
        (output / f"{label}.log").write_text(log, encoding="utf-8")
        if completed.returncode != expected or any(marker not in log for marker in markers):
            raise AssertionError(f"{label}: unexpected outcome; see {output}")
        results.append({"control": label, "command": command, "exit_code": completed.returncode,
                        "required_markers": markers})
        print(f"{label}: exit {completed.returncode} (expected {expected})", flush=True)

    workspace = seed("incompatible-reuse", "preview-starting-defect")
    run("incompatible-reuse", "preview-starting-defect", workspace, 1,
        ("AssertionError: Preview operation violated requested contract", "UnsupportedOperationException"))

    workspace = seed("incompatible-reuse", "preview-read-only-positive")
    replace(workspace, "src/PreviewService.java", STUB, READ_ONLY)
    run("incompatible-reuse", "preview-read-only-positive", workspace)

    workspace = seed("incompatible-reuse", "preview-command-side-effect")
    replace(workspace, "src/PreviewService.java", STUB, COMMAND_REUSE)
    run("incompatible-reuse", "preview-command-side-effect", workspace, 1,
        ("AssertionError: preview must not reserve inventory",))
    run("incompatible-reuse", "preview-command-wrong-exception", workspace, 1,
        ("AssertionError: Preview operation violated requested contract", "IllegalStateException: Inventory unavailable"),
        section="unavailable")

    workspace = seed("incompatible-reuse", "preview-command-caught-exception")
    replace(workspace, "src/PreviewService.java", STUB,
            "try {\n            " + COMMAND_REUSE +
            "\n        } catch (IllegalStateException unavailable) {\n"
            "            return OptionalLong.empty();\n        }")
    run("incompatible-reuse", "preview-command-caught-exception", workspace, 1,
        ("AssertionError: preview must not reserve inventory",))

    workspace = seed("incompatible-reuse", "preview-foreign-tenant-leak")
    replace(workspace, "src/PreviewService.java", STUB, READ_ONLY.replace(
        "inventory.unitPrice(tenant, sku)", 'inventory.unitPrice("north", sku)').replace(
        "inventory.availableUnits(tenant, sku)", 'inventory.availableUnits("north", sku)'))
    run("incompatible-reuse", "preview-foreign-tenant-leak", workspace, 1,
        ("AssertionError: foreign tenant must receive empty",), section="unavailable")

    workspace = seed("incompatible-reuse", "preview-invalid-units-empty")
    replace(workspace, "src/PreviewService.java", STUB, READ_ONLY.replace(
        'throw new IllegalArgumentException("Units must be positive");', "return OptionalLong.empty();"))
    run("incompatible-reuse", "preview-invalid-units-empty", workspace, 1,
        ("AssertionError: nonpositive units must be rejected",), section="invalid")

    workspace = seed("incompatible-reuse", "preview-pure-helper-positive")
    replace(workspace, "src/PreviewService.java", STUB,
            READ_ONLY.replace("price.getAsLong() * units", "amount(price.getAsLong(), units)"))
    helper = '''
    /**
     * Calculates an available purchase amount without side effects.
     * @param unitPriceCents price of one unit in cents
     * @param units available positive number of units
     * @return requested amount in cents
     */
    private static long amount(long unitPriceCents, int units) {
        return unitPriceCents * units;
    }
'''
    path = workspace / "src/PreviewService.java"
    source = path.read_text(encoding="utf-8")
    path.write_text(source[:-2] + helper + "}\n", encoding="utf-8")
    run("incompatible-reuse", "preview-pure-helper-positive", workspace)

    workspace = seed("public-nested-api", "shipment-starting-defect")
    run("public-nested-api", "shipment-existing-linkage-positive", workspace, section="compatibility-only")
    run("public-nested-api", "shipment-starting-defect", workspace, 1,
        ("Frozen legacy caller passed", "AssertionError: delivery days for 1"))

    workspace = seed("public-nested-api", "shipment-preserved-api-positive")
    replace(workspace, "src/ShipmentService.java", "parcelCount * 800L, 0", "parcelCount * 800L, parcelCount <= 10 ? 1 : 3")
    run("public-nested-api", "shipment-preserved-api-positive", workspace)

    workspace = seed("public-nested-api", "shipment-relocated-type")
    replace(workspace, "src/ShipmentService.java", "parcelCount * 800L, 0", "parcelCount * 800L, parcelCount <= 10 ? 1 : 3")
    replace(workspace, "src/ShipmentService.java", NESTED, "")
    (workspace / "src/Quote.java").write_text(
        "/**\n * Relocated quotation used by the deliberately incompatible control.\n"
        " * @param feeCents total fee in cents\n * @param estimatedDays expected delivery days\n */\n"
        "public record Quote(long feeCents, int estimatedDays) {\n}\n", encoding="utf-8")
    run("public-nested-api", "shipment-relocated-semantics-positive", workspace, section="semantics-only")

    migrated = output / "migrated-client"
    migrated.mkdir()
    caller = (ROOT / "oracle/LegacyShipmentCaller.java").read_text(encoding="utf-8")
    caller = caller.replace("ShipmentService.Quote", "Quote").replace('"ShipmentService$Quote"', '"Quote"')
    (migrated / "LegacyShipmentCaller.java").write_text(caller, encoding="utf-8")
    sources = [*sorted((workspace / "src").glob("*.java")), migrated / "LegacyShipmentCaller.java"]
    completed = subprocess.run(["javac", "-encoding", "UTF-8", "-Xlint:all", "-d", str(migrated),
                                *map(str, sources)], capture_output=True, text=True, check=True)
    completed = subprocess.run(["java", "-cp", os.pathsep.join([str(migrated)]), "LegacyShipmentCaller"],
                               capture_output=True, text=True, check=True)
    (output / "shipment-migrated-recompiled-client.log").write_text(completed.stdout + completed.stderr, encoding="utf-8")
    results.append({"control": "shipment-migrated-recompiled-client", "exit_code": 0,
                    "judgment": "Migrated/recompiled caller passes; this is not deployed-bytecode compatibility"})
    print("shipment-migrated-recompiled-client: exit 0 (expected 0)", flush=True)
    run("public-nested-api", "shipment-relocated-frozen-client-fails", workspace, 1,
        ("NoSuchMethodError", "ShipmentService$Quote ShipmentService.quote(int)"))

    workspace = seed("public-nested-api", "shipment-wrong-day-boundary")
    replace(workspace, "src/ShipmentService.java", "parcelCount * 800L, 0", "parcelCount * 800L, parcelCount < 10 ? 1 : 3")
    run("public-nested-api", "shipment-wrong-day-boundary", workspace, 1,
        ("Frozen legacy caller passed", "AssertionError: delivery days for 10"))

    (output / "calibration.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(f"Contract calibration controls passed: {len(results)}; {output}")


if __name__ == "__main__":
    main()
