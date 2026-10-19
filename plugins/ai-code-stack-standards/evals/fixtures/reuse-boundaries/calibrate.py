#!/usr/bin/env python3
"""Calibrate behavior checks using explicit controls, without classifying abstraction."""

import argparse
import json
from pathlib import Path
import shutil
import subprocess
import tempfile


ROOT = Path(__file__).resolve().parent


def replace(workspace, relative, before, after):
    """Make one exact evaluator-owned control edit in a disposable project."""
    path = workspace / relative
    original = path.read_text(encoding="utf-8")
    if original.count(before) != 1:
        raise AssertionError(f"Control edit is not unique: {relative}")
    path.write_text(original.replace(before, after), encoding="utf-8")


def policy_class(name, signature, body, description):
    """Render a tiny documented control class with a known policy implementation."""
    return (
        f"/**\n * {description}\n */\npublic final class {name} {{\n"
        "    /**\n     * Prevents construction.\n     */\n"
        f"    private {name}() {{\n    }}\n"
        "    /**\n     * Applies the evaluator control policy.\n"
        "     * @param subtotalCents subtotal in cents\n"
        "     * @param loyaltyMember whether the customer is a loyalty member\n"
        "     * @return discount in cents\n"
        "     * @throws IllegalArgumentException if the subtotal is negative\n     */\n"
        f"    {signature} {{\n{body}\n    }}\n}}\n"
    )


def main():
    """Require real semantic failures and distinguish behavior from structural review."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    output = args.output or Path(tempfile.mkdtemp(prefix="codestack-reuse-calibration-", dir="/private/tmp"))
    output.mkdir(parents=True, exist_ok=True)
    results = []

    def copy(case, label):
        """Copy only an ordinary seed for one concrete manual control."""
        workspace = output / label
        shutil.copytree(ROOT / case, workspace)
        return workspace

    def run(case, label, workspace, expected, assertion="", extra=(), structural_expectation=""):
        """Check an exit code and specific semantic failure, preserving its actual output."""
        command = ["python3", "-B", str(ROOT / "check.py"), case, str(workspace), *extra]
        completed = subprocess.run(command, capture_output=True, text=True, check=False)
        (output / f"{label}.log").write_text(completed.stdout + completed.stderr, encoding="utf-8")
        if completed.returncode != expected:
            raise AssertionError(f"{label}: expected {expected}, got {completed.returncode}; see {output}")
        if expected and ("AssertionError" not in completed.stderr or assertion not in completed.stderr):
            raise AssertionError(f"{label}: failure is not the expected semantic assertion; see {output}")
        results.append({"control": label, "exit_code": completed.returncode,
                        "expected_assertion": assertion, "command": command,
                        "structural_expectation_for_independent_review": structural_expectation})
        print(f"{label}: exit {completed.returncode} (expected {expected})")

    workspace = copy("existing-implementation", "reuse-starting-defect")
    run("existing-implementation", "reuse-starting-defect", workspace, 1, "Confirmed checkout must return a fee")
    workspace = copy("existing-implementation", "reuse-positive")
    replace(workspace, "src/Checkout.java", 'throw new UnsupportedOperationException("confirmed quote is unfinished");',
            "return DeliveryFees.quote(subtotalCents);")
    run("existing-implementation", "reuse-positive", workspace, 0,
        structural_expectation="Accept: both entry points use the existing policy without an extra abstraction")
    workspace = copy("existing-implementation", "reuse-same-values-duplicate")
    replace(workspace, "src/Checkout.java", 'throw new UnsupportedOperationException("confirmed quote is unfinished");',
            'if (subtotalCents < 0) {\n            throw new IllegalArgumentException("subtotal must be nonnegative");\n'
            '        }\n        return subtotalCents < 5000L ? 800L : 0L;')
    run("existing-implementation", "reuse-same-values-duplicate", workspace, 1,
        "Both checkout paths must follow the active delivery policy",
        structural_expectation="Reject: duplicated policy has matching original values but misses the active-policy perturbation")

    workspace = copy("same-rule", "same-rule-starting-defect")
    run("same-rule", "same-rule-starting-defect", workspace, 1,
        "Both entry points must apply the active loyalty discount")
    workspace = copy("same-rule", "same-rule-duplicate-functional-pass")
    for name in ("WebOrders", "PhoneOrders"):
        replace(workspace, f"src/{name}.java", "subtotalCents >= 10000L ? 500L : 0L;",
                "subtotalCents >= 15000L ? 700L : 0L;")
    run("same-rule", "same-rule-duplicate-functional-pass", workspace, 0,
        structural_expectation="Reject after diff review: behavior is correct, but the same policy still has two owners")
    changed = output / "same-rule-duplicate-one-edit"
    shutil.copytree(workspace, changed)
    replace(changed, "src/WebOrders.java", "? 700L :", "? 1100L :")
    run("same-rule", "same-rule-duplicate-one-edit", changed, 1,
        "Both entry points must apply the active loyalty discount", ("--discount", "1100"))
    workspace = copy("same-rule", "same-rule-extracted-positive")
    for name in ("WebOrders", "PhoneOrders"):
        replace(workspace, f"src/{name}.java",
                'if (subtotalCents < 0) {\n            throw new IllegalArgumentException("subtotal must be nonnegative");\n'
                '        }\n        return loyaltyMember && subtotalCents >= 10000L ? 500L : 0L;',
                "return LoyaltyDiscount.amount(subtotalCents, loyaltyMember);")
    (workspace / "src/LoyaltyDiscount.java").write_text(policy_class(
        "LoyaltyDiscount", "public static long amount(long subtotalCents, boolean loyaltyMember)",
        '        if (subtotalCents < 0) {\n            throw new IllegalArgumentException("subtotal must be nonnegative");\n'
        '        }\n        return loyaltyMember && subtotalCents >= 15000L ? 700L : 0L;',
        "Owns the single loyalty discount policy used by both order entry points."), encoding="utf-8")
    run("same-rule", "same-rule-extracted-positive", workspace, 0,
        structural_expectation="Accept after diff review: one small domain policy, two direct delegations, no framework")
    changed = output / "same-rule-extracted-one-edit"
    shutil.copytree(workspace, changed)
    replace(changed, "src/LoyaltyDiscount.java", "? 700L :", "? 1100L :")
    run("same-rule", "same-rule-extracted-one-edit", changed, 0, extra=("--discount", "1100"),
        structural_expectation="Accept: one recorded policy edit changes both public entry points")

    workspace = copy("different-semantics", "different-starting-defect")
    run("different-semantics", "different-starting-defect", workspace, 1, "must reject invalid input")
    workspace = copy("different-semantics", "different-independent-positive")
    validation = ('if (status == null || elapsedMinutes < 0) {\n'
                  '            throw new IllegalArgumentException("invalid eligibility input");\n        }\n'
                  '        return "PENDING".equals(status) && elapsedMinutes <= 30L;')
    for name in ("OrderCancellation", "RefundWithdrawal"):
        replace(workspace, f"src/{name}.java", 'return "PENDING".equals(status) && elapsedMinutes <= 30L;', validation)
    run("different-semantics", "different-independent-positive", workspace, 0,
        structural_expectation="Accept after diff review: different business policies remain independently owned")
    changed = output / "different-cross-domain-delegation"
    shutil.copytree(workspace, changed)
    replace(changed, "src/RefundWithdrawal.java", validation,
            "return OrderCancellation.canCancel(status, elapsedMinutes);")
    run("different-semantics", "different-cross-domain-delegation", changed, 1,
        "withdrawal changed legal eligibility behavior",
        structural_expectation="Reject: unrelated refund policy follows the changed order entry point")
    changed = output / "different-boolean-policy-functional-pass"
    shutil.copytree(workspace, changed)
    for name, flag in (("OrderCancellation", "false"), ("RefundWithdrawal", "true")):
        replace(changed, f"src/{name}.java", validation,
                f"return EligibilityPolicy.permitted({flag}, status, elapsedMinutes);")
    (changed / "src/EligibilityPolicy.java").write_text(
        "/**\n * Deliberately wrong control joining unrelated business policy owners.\n */\n"
        "public final class EligibilityPolicy {\n"
        "    /**\n     * Prevents construction.\n     */\n"
        "    private EligibilityPolicy() {\n    }\n"
        "    /**\n     * Uses an unnecessary mode flag to combine independent business rules.\n"
        "     * @param refund whether this is refund withdrawal\n"
        "     * @param status current entity status\n"
        "     * @param elapsedMinutes elapsed entity age\n"
        "     * @return current eligibility\n"
        "     * @throws IllegalArgumentException if status is null or elapsed time is negative\n     */\n"
        "    public static boolean permitted(boolean refund, String status, long elapsedMinutes) {\n"
        '        if (status == null || elapsedMinutes < 0) {\n'
        '            throw new IllegalArgumentException("invalid eligibility input");\n        }\n'
        '        return "PENDING".equals(status) && elapsedMinutes <= 30L;\n    }\n}\n', encoding="utf-8")
    run("different-semantics", "different-boolean-policy-functional-pass", changed, 0,
        structural_expectation="Reject after diff review: behavior and perturbation pass, but an unused mode flag joins independent policies")

    (output / "calibration.json").write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(f"Behavior calibration controls passed: {len(results)}; structural verdicts require independent diff review: {output}")


if __name__ == "__main__":
    main()
