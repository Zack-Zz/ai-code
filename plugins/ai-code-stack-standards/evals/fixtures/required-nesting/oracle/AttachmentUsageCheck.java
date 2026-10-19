import java.io.IOException;
import java.lang.reflect.Modifier;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.concurrent.Callable;
import java.util.concurrent.Executors;

/**
 * Exercises the frozen storage contract without selecting a private type layout.
 */
public final class AttachmentUsageCheck {

    /**
     * Prevents construction of the evaluator entry point.
     */
    private AttachmentUsageCheck() {
    }

    /**
     * Runs API and real-filesystem checks against candidate production code.
     *
     * @param args compiled class directory
     * @throws Exception if a contract check or filesystem operation fails
     */
    public static void main(String[] args) throws Exception {
        checkPublicApi(Path.of(args[0]));
        Path workspace = Files.createTempDirectory("attachment-usage-oracle-");
        try {
            checkUsage(workspace);
            checkValidation(workspace);
            checkStagingRoot(workspace);
            checkUnavailableRoot(workspace);
        } finally {
            removeTree(workspace);
        }
        System.out.println("Attachment usage contracts passed; private layout was not scored");
    }

    /**
     * Rejects observable API expansion while accepting private or package-private helpers.
     *
     * @param classes directory containing only candidate and oracle class files
     * @throws Exception if reflection or a contract assertion fails
     */
    private static void checkPublicApi(Path classes) throws Exception {
        for (var declared : AttachmentStore.class.getDeclaredConstructors()) {
            if (!Modifier.isPublic(declared.getModifiers()) && !Modifier.isProtected(declared.getModifiers())) {
                continue;
            }
            require(java.util.Arrays.equals(declared.getParameterTypes(), new Class<?>[] {Path.class, long.class}),
                    "Construction was expanded beyond the existing storage contract");
        }
        var constructor = AttachmentStore.class.getConstructor(Path.class, long.class);
        require(Modifier.isPublic(constructor.getModifiers()), "Storage construction became unavailable");
        for (var method : AttachmentStore.class.getDeclaredMethods()) {
            if (!Modifier.isPublic(method.getModifiers()) && !Modifier.isProtected(method.getModifiers())) {
                continue;
            }
            require(method.getName().equals("usedBytes") && method.getParameterCount() == 0
                            && method.getReturnType() == long.class,
                    "The scan added an unrelated public or protected method");
        }
        require(AttachmentStore.class.getMethod("usedBytes").getReturnType() == long.class,
                "The requested storage usage method is absent");
        for (var field : AttachmentStore.class.getDeclaredFields()) {
            require(Modifier.isPrivate(field.getModifiers()), "Scanner state was exposed outside its owner");
        }
        try (var paths = Files.walk(classes)) {
            for (Path path : paths.filter(file -> file.toString().endsWith(".class")).toList()) {
                String relative = classes.relativize(path).toString();
                String binaryName = relative.substring(0, relative.length() - 6)
                        .replace(java.io.File.separatorChar, '.');
                Class<?> type = Class.forName(binaryName, false, AttachmentStore.class.getClassLoader());
                if (type == AttachmentStore.class || type == AttachmentUsageCheck.class) {
                    continue;
                }
                require(!Modifier.isPublic(type.getModifiers()) && !Modifier.isProtected(type.getModifiers()),
                        "The scan exposed a new public or protected helper type");
            }
        }
    }

    /**
     * Checks traversal semantics, quota, refresh, instance isolation and parallel calls.
     *
     * @param workspace directory owned by the evaluator
     * @throws Exception if scanning or a contract assertion fails
     */
    private static void checkUsage(Path workspace) throws Exception {
        Path root = Files.createDirectory(workspace.resolve("attachments"));
        Path nested = Files.createDirectory(root.resolve("nested"));
        Path visible = root.resolve("visible.bin");
        byte[] visibleBytes = {1, 2, 3};
        Files.write(visible, visibleBytes);
        Files.write(nested.resolve("nested.bin"), new byte[5]);
        Files.write(Files.createDirectory(root.resolve(".staging")).resolve("ignored.bin"), new byte[97]);
        Files.write(Files.createDirectory(nested.resolve(".staging")).resolve("ignored.bin"), new byte[101]);
        Path outside = Files.createDirectory(workspace.resolve("outside"));
        Files.write(outside.resolve("external.bin"), new byte[211]);
        Files.createSymbolicLink(root.resolve("directory-link"), outside);
        Files.createSymbolicLink(root.resolve("file-link"), outside.resolve("external.bin"));
        Files.createSymbolicLink(root.resolve("broken-link"), outside.resolve("absent.bin"));

        AttachmentStore unlimited = new AttachmentStore(root, Long.MAX_VALUE);
        require(unlimited.usedBytes() == 8, "Regular bytes, staging pruning or symlink isolation was violated");
        require(unlimited.usedBytes() == 8, "A repeated call reused mutable scan state");
        AttachmentStore store = new AttachmentStore(root, 8);
        require(store.usedBytes() == 8, "The inclusive quota rejected a valid tree");
        expectIOException(() -> new AttachmentStore(root, 7).usedBytes(), "The scan accepted bytes above its quota");
        Path empty = Files.createDirectory(workspace.resolve("empty"));
        require(new AttachmentStore(empty, 0).usedBytes() == 0, "An empty zero-quota store did not return zero");
        Files.write(root.resolve("new.bin"), new byte[2]);
        require(new AttachmentStore(root, 10).usedBytes() == 10, "A later scan did not observe current files");
        expectIOException(store::usedBytes, "A refreshed tree bypassed the original instance quota");

        var executor = Executors.newFixedThreadPool(4);
        try {
            AttachmentStore parallel = new AttachmentStore(root, 10);
            List<Callable<Long>> scans = new ArrayList<>();
            for (int index = 0; index < 20; index++) {
                scans.add(parallel::usedBytes);
            }
            for (var result : executor.invokeAll(scans)) {
                require(result.get() == 10, "Concurrent calls shared mutable traversal progress");
            }
        } finally {
            executor.shutdownNow();
        }
        require(new AttachmentStore(empty, 0).usedBytes() == 0, "Independent stores shared traversal progress");
        require(java.util.Arrays.equals(Files.readAllBytes(visible), visibleBytes), "The scan modified attachment content");
        require(Files.size(outside.resolve("external.bin")) == 211, "The scan modified an outside file");
    }

    /**
     * Preserves constructor rejection of null, file, symlink and negative-quota inputs.
     *
     * @param workspace directory owned by the evaluator
     * @throws IOException if fixture preparation fails
     */
    private static void checkValidation(Path workspace) throws IOException {
        try {
            new AttachmentStore(null, 1);
            throw new AssertionError("A null root was accepted");
        } catch (NullPointerException expected) {
            // Null remains distinct from an invalid existing root.
        }
        for (Path invalid : List.of(workspace.resolve("absent"), workspace.resolve("attachments/visible.bin"),
                workspace.resolve("attachments/directory-link"))) {
            try {
                new AttachmentStore(invalid, 1);
                throw new AssertionError("A non-directory or symbolic root was accepted");
            } catch (IllegalArgumentException expected) {
                // The original constructor rejects these inputs before scanning.
            }
        }
        try {
            new AttachmentStore(workspace, -1);
            throw new AssertionError("A negative quota was accepted");
        } catch (IllegalArgumentException expected) {
            // The quota is an inclusive non-negative bound.
        }
    }

    /**
     * Ensures pruning applies to descendants rather than the configured root itself.
     *
     * @param workspace directory owned by the evaluator
     * @throws IOException if scanning or fixture preparation fails
     */
    private static void checkStagingRoot(Path workspace) throws IOException {
        Path root = Files.createDirectory(workspace.resolve(".staging"));
        Files.write(root.resolve("live.bin"), new byte[4]);
        require(new AttachmentStore(root, 4).usedBytes() == 4, "A configured staging-named root was pruned");
    }

    /**
     * Requires checked I/O propagation when a previously valid root disappears.
     *
     * @param workspace directory owned by the evaluator
     * @throws Exception if fixture preparation or a contract assertion fails
     */
    private static void checkUnavailableRoot(Path workspace) throws Exception {
        Path root = Files.createDirectory(workspace.resolve("removed"));
        AttachmentStore store = new AttachmentStore(root, 1);
        Files.delete(root);
        expectIOException(store::usedBytes, "An unavailable root was silently treated as empty");
    }

    /**
     * Verifies an operation signals checked I/O rather than a fabricated result.
     *
     * @param operation scan to exercise
     * @param message assertion diagnostic when checked I/O is absent
     * @throws Exception if the operation fails with an unexpected exception
     */
    private static void expectIOException(Callable<Long> operation, String message) throws Exception {
        try {
            operation.call();
            throw new AssertionError(message);
        } catch (IOException expected) {
            // A real checked I/O failure is the scanner's published contract.
        }
    }

    /**
     * Removes the evaluator tree without following its symbolic links.
     *
     * @param root owned temporary directory
     * @throws IOException if cleanup fails
     */
    private static void removeTree(Path root) throws IOException {
        try (var paths = Files.walk(root)) {
            for (Path path : paths.sorted(Comparator.reverseOrder()).toList()) {
                Files.delete(path);
            }
        }
    }

    /**
     * Fails independently of JVM assertion settings.
     *
     * @param condition contract condition
     * @param message diagnostic for a failed condition
     */
    private static void require(boolean condition, String message) {
        if (!condition) {
            throw new AssertionError(message);
        }
    }
}
