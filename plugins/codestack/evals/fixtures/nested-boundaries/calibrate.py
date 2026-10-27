#!/usr/bin/env python3
"""Calibrate semantic checks with hand-written controls, without invoking a model."""

from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parent
QUOTE_METHOD = """
    /**
     * Creates a quote using the existing fee policy and distance estimate.
     *
     * @param parcelCount number of parcels from 1 through 100
     * @param distanceKm delivery distance from 1 through 1,000 km
     * @return fee and estimated delivery days
     * @throws IllegalArgumentException if either input is outside its range
     */
    public DispatchQuote quote(int parcelCount, int distanceKm) {
        long fee = feeCents(parcelCount, distanceKm);
        return new DispatchQuote(fee, distanceKm <= 50 ? 1 : 3);
    }
"""
QUOTE_TYPE = """/**
 * Carries the fee and delivery estimate for a dispatch request.
 *
 * @param feeCents fee in cents
 * @param estimatedDays estimated delivery days
 */
public record DispatchQuote(long feeCents, int estimatedDays) {
}
"""


def put_quote(project, nested=False):
    """Create a behaviorally correct quote without making its shape an oracle."""
    source = project / "src/DispatchService.java"
    text = source.read_text()
    insertion = QUOTE_METHOD
    if nested:
        insertion += "\n" + "\n".join("    " + line for line in QUOTE_TYPE.splitlines()) + "\n"
    else:
        (project / "src/DispatchQuote.java").write_text(QUOTE_TYPE)
    source.write_text(text[:text.rfind("}")] + insertion + "}\n")


def edit(project, relative, before, after):
    """Apply one exact hand-control mutation and reject a stale fixture."""
    path = project / relative
    text = path.read_text()
    if before not in text:
        raise AssertionError(f"Calibration input not found: {before}")
    path.write_text(text.replace(before, after, 1))


def fix_iterator(project):
    """Correct only the known iterator boundary while retaining its private cursor."""
    edit(project, "src/MessageWindow.java", "nextIndex < messages.length - 1", "nextIndex < messages.length")


def simplify_iterator(project):
    """Provide an equivalent JDK implementation without a private cursor class."""
    path = project / "src/MessageWindow.java"
    text = path.read_text()
    text = text.replace("import java.util.Iterator;", "import java.util.Arrays;\nimport java.util.Iterator;")
    text = text.replace("return new Cursor();", "return Arrays.asList(messages).iterator();")
    marker = "    /**\n     * Holds iteration progress while reading the enclosing snapshot privately."
    text = text[:text.index(marker)] + "}\n"
    path.write_text(text)


def run_case(root, name, case, mutate, expected_message=None):
    """Require actual Java outcomes; tool failures cannot serve as semantic RED."""
    project = root / name
    shutil.copytree(ROOT / case, project)
    mutate(project)
    result = subprocess.run(
        [sys.executable, "-B", str(ROOT / "check.py"), case, str(project)],
        text=True, capture_output=True,
    )
    if expected_message is None:
        if result.returncode != 0:
            raise AssertionError(f"{name}: expected GREEN\n{result.stdout}\n{result.stderr}")
    elif result.returncode == 0 or expected_message not in result.stderr:
        raise AssertionError(f"{name}: expected semantic RED {expected_message!r}\n"
                             f"{result.stdout}\n{result.stderr}")
    print(f"{name}: exit {result.returncode}, {'GREEN' if expected_message is None else 'expected semantic RED'}")


def main():
    """Check missing features, correct alternatives and targeted incorrect controls."""
    with tempfile.TemporaryDirectory(prefix="codestack-nested-calibration-") as directory:
        root = Path(directory)
        run_case(root, "quote-seed", "business-result", lambda project: None,
                 "The requested public quote method is absent")
        run_case(root, "quote-top-level", "business-result", put_quote)
        run_case(root, "quote-nested-neutral", "business-result",
                 lambda project: put_quote(project, nested=True))
        run_case(root, "quote-wrong-fee", "business-result",
                 lambda project: (put_quote(project), edit(project, "src/DispatchService.java",
                     "new DispatchQuote(fee,", "new DispatchQuote(fee + 1,")),
                 "Quote fee does not preserve the existing policy")
        run_case(root, "quote-wrong-days", "business-result",
                 lambda project: (put_quote(project), edit(project, "src/DispatchService.java",
                     "distanceKm <= 50 ? 1 : 3", "distanceKm <= 51 ? 1 : 3")),
                 "Estimated days violate the 50 km boundary")
        run_case(root, "quote-unchecked-input", "business-result",
                 lambda project: (put_quote(project), edit(project, "src/DispatchService.java",
                     "long fee = feeCents(parcelCount, distanceKm);",
                     "long fee = 200L * parcelCount + 10L * distanceKm;")),
                 "Quote accepted an out-of-range input")
        run_case(root, "iterator-seed", "jdk-iterator", lambda project: None,
                 "hasNext traversal omitted or reordered messages")
        run_case(root, "iterator-private-cursor", "jdk-iterator", fix_iterator)
        run_case(root, "iterator-jdk-alternative", "jdk-iterator", simplify_iterator)
        run_case(root, "iterator-shared-cursor", "jdk-iterator",
                 lambda project: (fix_iterator(project), edit(project, "src/MessageWindow.java",
                     "    private final String[] messages;",
                     "    private final String[] messages;\n\n"
                     "    /**\n     * Shares one cursor incorrectly across consumers.\n     */\n"
                     "    private final Iterator<String> shared = new Cursor();"),
                     edit(project, "src/MessageWindow.java", "return new Cursor();", "return shared;")),
                 "A fresh iterator did not provide independent traversal")
        run_case(root, "iterator-leaked-snapshot", "jdk-iterator",
                 lambda project: (fix_iterator(project), edit(project, "src/MessageWindow.java",
                     'Objects.requireNonNull(messages, "messages").clone()',
                     'Objects.requireNonNull(messages, "messages")')),
                 "Caller array mutation leaked into the snapshot")
        run_case(root, "iterator-expanded-api", "jdk-iterator",
                 lambda project: (fix_iterator(project), edit(project, "src/MessageWindow.java",
                     "    public int size() {",
                     "    public int unrelatedOperation() {\n        return 1;\n    }\n\n"
                     "    /**\n     * Returns the snapshot size.\n     *\n"
                     "     * @return snapshot size\n     */\n    public int size() {")),
                 "The fix added an unrelated public method")
    print("12 hand-control outcomes matched; no model or structural preference was scored")


if __name__ == "__main__":
    main()
