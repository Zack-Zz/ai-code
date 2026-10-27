#!/usr/bin/env python3
"""Compile candidate code with frozen checks; leave abstraction judgment to diff review."""

import argparse
from pathlib import Path
import shutil
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parent
CHECKERS = {
    "existing-implementation": "ExistingImplementationCheck",
    "same-rule": "SameRuleCheck",
    "different-semantics": "DifferentSemanticsCheck",
}


def check_scope(case, workspace):
    """Preserve seed files outside the permitted source scope and reject extra files."""
    seed = ROOT / case
    original = {path.relative_to(seed) for path in seed.rglob("*") if path.is_file()}
    actual = {path.relative_to(workspace) for path in workspace.rglob("*") if path.is_file()
              and path.relative_to(workspace).parts[0] != ".agents"}
    if not original.issubset(actual):
        raise AssertionError("An existing input file was removed")
    for relative in actual:
        permitted = (relative == Path("src/Checkout.java") if case == "existing-implementation"
                     else relative.parts[0] == "src" and relative.suffix == ".java")
        if not permitted and (relative not in original
                              or (workspace / relative).read_bytes() != (seed / relative).read_bytes()):
            raise AssertionError(f"Unrequested input or file changed: {relative}")


def run_java(case, workspace, mode):
    """Compile all candidate source files with one evaluator-owned behavior check."""
    checker = CHECKERS[case]
    with tempfile.TemporaryDirectory(prefix="codestack-reuse-classes-") as directory:
        subprocess.run(["javac", "-encoding", "UTF-8", "-Xlint:all", "-d", directory,
                        *map(str, sorted((workspace / "src").rglob("*.java"))),
                        str(ROOT / "oracle" / f"{checker}.java")], check=True)
        subprocess.run(["java", "-cp", directory, checker, *mode], check=True)


def main():
    """Run ordinary behavior checks and narrowly defined evaluator perturbations."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("case", choices=tuple(CHECKERS))
    parser.add_argument("workspace", type=Path)
    parser.add_argument("--discount", type=int, default=700,
                        help="expected amount after a separately recorded one-owner policy edit")
    args = parser.parse_args()
    workspace = args.workspace.resolve()
    check_scope(args.case, workspace)
    run_java(args.case, workspace, [str(args.discount)] if args.case == "same-rule" else [])
    if args.case == "existing-implementation":
        with tempfile.TemporaryDirectory(prefix="codestack-reuse-policy-") as directory:
            changed = Path(directory) / "project"
            shutil.copytree(workspace, changed)
            path = changed / "src/DeliveryFees.java"
            original = path.read_text(encoding="utf-8")
            old = "return subtotalCents < 5000L ? 800L : 0L;"
            if original.count(old) != 1:
                raise AssertionError("The immutable delivery policy seed changed")
            path.write_text(original.replace(old, "return subtotalCents < 9000L ? 317L : 29L;"), encoding="utf-8")
            run_java(args.case, changed, ["changed"])
    if args.case == "different-semantics":
        with tempfile.TemporaryDirectory(prefix="codestack-reuse-order-") as directory:
            changed = Path(directory) / "project"
            shutil.copytree(workspace, changed)
            (changed / "src/OrderCancellation.java").write_text(
                "/**\n * Evaluator substitute for an independently changed order policy.\n */\n"
                "public final class OrderCancellation {\n"
                "    /**\n     * Prevents construction.\n     */\n"
                "    private OrderCancellation() {\n    }\n"
                "    /**\n     * Rejects cancellation after an independent fulfillment change.\n"
                "     * @param status current order status\n"
                "     * @param elapsedMinutes elapsed order age\n"
                "     * @return false under the evaluator's changed order contract\n     */\n"
                "    public static boolean canCancel(String status, long elapsedMinutes) {\n"
                "        return false;\n    }\n}\n", encoding="utf-8")
            run_java(args.case, changed, ["refund-only"])
        print("Order-entry-point perturbation passed; shared internal policy still needs independent review")


if __name__ == "__main__":
    main()
