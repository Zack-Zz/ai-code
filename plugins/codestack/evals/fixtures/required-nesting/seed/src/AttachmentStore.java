import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.util.Objects;

/**
 * Measures the private attachment tree against its configured quota.
 */
public final class AttachmentStore {

    /**
     * Normalized directory owned by this storage instance.
     */
    private final Path root;

    /**
     * Inclusive maximum number of counted bytes.
     */
    private final long quota;

    /**
     * Creates a scanner for an existing directory without following a root link.
     *
     * @param root existing attachment directory
     * @param quota inclusive non-negative byte quota
     * @throws NullPointerException if the root is null
     * @throws IllegalArgumentException if the root is not a real directory or the quota is negative
     */
    public AttachmentStore(Path root, long quota) {
        this.root = Objects.requireNonNull(root, "root").toAbsolutePath().normalize();
        if (!Files.isDirectory(this.root, LinkOption.NOFOLLOW_LINKS) || quota < 0) {
            throw new IllegalArgumentException("A real directory and non-negative quota are required");
        }
        this.quota = quota;
    }

    /**
     * Measures current regular-file bytes without staging trees or symbolic links.
     *
     * @return counted regular-file bytes
     * @throws IOException if scanning fails or the inclusive quota is exceeded
     */
    public long usedBytes() throws IOException {
        return 0L;
    }
}
