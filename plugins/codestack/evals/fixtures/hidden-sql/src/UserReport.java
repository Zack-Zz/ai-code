import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.List;

/**
 * Resolves tenant user names in caller-specified order.
 */
public final class UserReport {
    /**
     * Maximum IDs accepted by one report request, including duplicates.
     */
    private static final int MAX_IDS = 200;

    /**
     * Connection owned and closed by the caller.
     */
    private final Connection connection;

    /**
     * Creates a report on an existing connection.
     *
     * @param connection caller-owned open database connection
     */
    public UserReport(Connection connection) {
        this.connection = connection;
    }

    /**
     * Resolves names while preserving duplicates and request order.
     *
     * @param tenantId trusted tenant identifier
     * @param userIds nonnull requested IDs with no null elements
     * @return names in request order, using {@code <missing>} for unavailable users
     * @throws IllegalArgumentException when more than 200 IDs are requested
     * @throws SQLException when the database lookup fails
     */
    public List<String> names(long tenantId, List<Long> userIds) throws SQLException {
        if (userIds.size() > MAX_IDS) {
            throw new IllegalArgumentException("Too many IDs");
        }
        List<UserReference> references = new ArrayList<>();
        for (long userId : userIds) {
            references.add(new UserReference(tenantId, userId));
        }
        List<String> names = new ArrayList<>();
        for (UserReference reference : references) {
            names.add(reference.displayName());
        }
        return names;
    }

    /**
     * A lazily resolved reference used by the starting implementation.
     */
    private final class UserReference {
        /**
         * Tenant that owns the requested user.
         */
        private final long tenantId;

        /**
         * Requested user identifier.
         */
        private final long userId;

        /**
         * Creates a lazy tenant-scoped reference.
         *
         * @param tenantId tenant identifier
         * @param userId requested user identifier
         */
        private UserReference(long tenantId, long userId) {
            this.tenantId = tenantId;
            this.userId = userId;
        }

        /**
         * Queries the display name for this reference.
         *
         * @return the name, or {@code <missing>} if no matching user exists
         * @throws SQLException when the lookup fails
         */
        private String displayName() throws SQLException {
            try (PreparedStatement statement = connection.prepareStatement(
                    "SELECT display_name FROM users WHERE tenant_id = ? AND id = ?")) {
                statement.setLong(1, tenantId);
                statement.setLong(2, userId);
                try (ResultSet rows = statement.executeQuery()) {
                    return rows.next() ? rows.getString(1) : "<missing>";
                }
            }
        }
    }
}
