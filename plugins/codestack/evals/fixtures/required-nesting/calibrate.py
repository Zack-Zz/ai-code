#!/usr/bin/env python3
"""Calibrate new JDK visitor cases using actual Java outcomes, without a model."""

from pathlib import Path
import shutil
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parent
CALLBACKS = """
            /**
             * Prunes descendant staging directories before their files are visited.
             *
             * @param directory current directory
             * @param attributes attributes supplied by the JDK walk
             * @return whether the walk should enter this directory
             */
            @Override
            public java.nio.file.FileVisitResult preVisitDirectory(
                    Path directory, java.nio.file.attribute.BasicFileAttributes attributes) {
                return !directory.equals(root) && directory.getFileName().toString().equals(".staging")
                        ? java.nio.file.FileVisitResult.SKIP_SUBTREE
                        : java.nio.file.FileVisitResult.CONTINUE;
            }

            /**
             * Adds regular-file sizes while checking the inclusive quota without overflow.
             *
             * @param file visited path
             * @param attributes attributes supplied by the JDK walk
             * @return continuation after an accepted file
             * @throws IOException if the next regular file would exceed the quota
             */
            @Override
            public java.nio.file.FileVisitResult visitFile(
                    Path file, java.nio.file.attribute.BasicFileAttributes attributes) throws IOException {
                if (attributes.isRegularFile()) {
                    long bytes = attributes.size();
                    if (bytes > quota - total[0]) {
                        throw new IOException("Attachment quota exceeded");
                    }
                    total[0] += bytes;
                }
                return java.nio.file.FileVisitResult.CONTINUE;
            }
"""
ANONYMOUS_BODY = """
        long[] total = {0L};
        Files.walkFileTree(root, new java.nio.file.SimpleFileVisitor<Path>() {
CALLBACKS
        });
        return total[0];
""".replace("CALLBACKS", CALLBACKS)
LOCAL_BODY = """
        long[] total = {0L};
        /**
         * Keeps this invocation's JDK traversal adapter within its private owner.
         */
        class UsageVisitor extends java.nio.file.SimpleFileVisitor<Path> {
CALLBACKS
        }
        Files.walkFileTree(root, new UsageVisitor());
        return total[0];
""".replace("CALLBACKS", CALLBACKS)
TOP_LEVEL_BODY = """
        UsageVisitor visitor = new UsageVisitor(root, quota);
        Files.walkFileTree(root, visitor);
        return visitor.totalBytes();
"""
TOP_LEVEL_SOURCE = """import java.io.IOException;
import java.nio.file.Path;

/**
 * Adapts one JDK traversal using a narrow package-private construction boundary.
 */
final class UsageVisitor extends java.nio.file.SimpleFileVisitor<Path> {

    /**
     * Root used only to distinguish the configured root from staging descendants.
     */
    private final Path root;

    /**
     * Inclusive byte quota for this invocation.
     */
    private final long quota;

    /**
     * Accumulator owned only by this invocation.
     */
    private final long[] total = {0L};

    /**
     * Creates a visitor with only the values required by this scan.
     *
     * @param root scanner root
     * @param quota inclusive non-negative byte quota
     */
    UsageVisitor(Path root, long quota) {
        this.root = root;
        this.quota = quota;
    }

    /**
     * Returns the completed scan's byte total.
     *
     * @return bytes counted by this invocation
     */
    long totalBytes() {
        return total[0];
    }
CALLBACKS
}
""".replace("CALLBACKS", CALLBACKS)


def edit(project, before, after):
    """Apply an exact mutation to the production source of a hand control."""
    source = project / "src/AttachmentStore.java"
    text = source.read_text()
    if before not in text:
        raise AssertionError(f"Stale calibration mutation: {before}")
    source.write_text(text.replace(before, after, 1))


def implement(project, body=ANONYMOUS_BODY):
    """Replace the semantic stub with an operator-owned implementation."""
    edit(project, "        return 0L;", body)


def top_level(project):
    """Prove the oracle also accepts a compatible top-level JDK adapter."""
    implement(project, TOP_LEVEL_BODY)
    (project / "src/UsageVisitor.java").write_text(TOP_LEVEL_SOURCE)


def shared_state(project):
    """Move a per-call accumulator into reusable instance state incorrectly."""
    implement(project)
    edit(project, "    private final long quota;", """    private final long quota;

    /**
     * Incorrectly retains progress between otherwise independent scans.
     */
    private final long[] accumulated = {0L};""")
    edit(project, "long[] total = {0L};", "long[] total = accumulated;")


def leaked_root(project):
    """Expose enclosing state unnecessarily while moving the adapter out."""
    top_level(project)
    edit(project, "    public long usedBytes() throws IOException {", """    public Path root() {
        return root;
    }

    /**
     * Measures the current regular-file usage.
     *
     * @return regular-file bytes
     * @throws IOException if the scan fails
     */
    public long usedBytes() throws IOException {""")


def exposed_accumulator(project):
    """Expose mutable state while extracting an otherwise functioning adapter."""
    top_level(project)
    edit(project, "    private final long quota;", """    private final long quota;

    /**
     * Unnecessarily exposes writable scanner state to external callers.
     */
    public final long[] scanProgress = {0L};""")


def run_case(root, name, mutate, expected_message=None):
    """Require a real runtime outcome; compilation/tool errors never count as RED."""
    project = root / name
    shutil.copytree(ROOT / "seed", project)
    mutate(project)
    result = subprocess.run(
        [sys.executable, "-B", str(ROOT / "check.py"), str(project)],
        text=True, capture_output=True,
    )
    if expected_message is None:
        if result.returncode != 0:
            raise AssertionError(f"{name}: expected GREEN\n{result.stdout}\n{result.stderr}")
    elif result.returncode == 0 or f"java.lang.AssertionError: {expected_message}" not in result.stderr:
        raise AssertionError(f"{name}: expected semantic/API RED {expected_message!r}\n"
                             f"{result.stdout}\n{result.stderr}")
    print(f"{name}: exit {result.returncode}, {'GREEN' if expected_message is None else 'expected runtime RED'}")


def main():
    """Exercise two new nested forms, an equivalent alternative and invalid controls."""
    with tempfile.TemporaryDirectory(prefix="codestack-visitor-calibration-") as directory:
        root = Path(directory)
        run_case(root, "seed", lambda project: None,
                 "Regular bytes, staging pruning or symlink isolation was violated")
        run_case(root, "new-anonymous-visitor", implement)
        run_case(root, "new-method-local-visitor", lambda project: implement(project, LOCAL_BODY))
        run_case(root, "equivalent-top-level-adapter", top_level)
        run_case(root, "unpruned-staging", lambda project: (
            implement(project), edit(project, "? java.nio.file.FileVisitResult.SKIP_SUBTREE",
                                     "? java.nio.file.FileVisitResult.CONTINUE")),
            "Regular bytes, staging pruning or symlink isolation was violated")
        run_case(root, "followed-file-link", lambda project: (
            implement(project), edit(project, "if (attributes.isRegularFile())", "if (Files.isRegularFile(file))"),
            edit(project, "long bytes = attributes.size();", "long bytes = Files.size(file);")),
            "Regular bytes, staging pruning or symlink isolation was violated")
        run_case(root, "shared-accumulator", shared_state,
                 "A repeated call reused mutable scan state")
        run_case(root, "unguarded-quota", lambda project: (
            implement(project), edit(project, "if (bytes > quota - total[0])", "if (false)")),
            "The scan accepted bytes above its quota")
        run_case(root, "swallowed-root-io", lambda project: (
            implement(project), edit(project, "long[] total = {0L};",
                "if (!Files.exists(root)) { return 0L; }\n        long[] total = {0L};")),
            "An unavailable root was silently treated as empty")
        run_case(root, "extracted-root-api", leaked_root,
                 "The scan added an unrelated public or protected method")
        run_case(root, "extracted-writable-progress", exposed_accumulator,
                 "Scanner state was exposed outside its owner")
    print("11 hand-control outcomes matched; no model or private type layout was scored")


if __name__ == "__main__":
    main()
