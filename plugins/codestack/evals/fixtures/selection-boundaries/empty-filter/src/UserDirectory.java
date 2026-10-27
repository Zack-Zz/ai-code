import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;

/**
 * Reads bounded pages of tenant-owned user identifiers.
 */
public final class UserDirectory {
    /**
     * Connection whose lifecycle belongs to the caller.
     */
    private final Connection connection;

    /**
     * Creates a directory on an existing connection.
     *
     * @param connection caller-owned database connection
     */
    public UserDirectory(Connection connection) {
        this.connection = connection;
    }

    /**
     * Finds a page restricted to the required positive identifier set.
     *
     * @param tenantId trusted tenant identifier
     * @param userIds required identifiers; empty means no matching users
     * @param offset nonnegative page offset
     * @param limit page size from one through three
     * @return matching identifiers in descending order
     * @throws IllegalArgumentException when a size or page bound is invalid
     * @throws SQLException when database access fails
     */
    public List<Long> findByRequiredIds(long tenantId, List<Long> userIds, int offset, int limit)
            throws SQLException {
        validate(userIds, offset, limit);
        return query(tenantId, userIds, false, offset, limit);
    }

    /**
     * Finds a page after excluding the given identifiers.
     *
     * @param tenantId trusted tenant identifier
     * @param excludedIds identifiers to exclude; empty excludes nothing
     * @param offset nonnegative page offset
     * @param limit page size from one through three
     * @return remaining identifiers in descending order
     * @throws IllegalArgumentException when a size or page bound is invalid
     * @throws SQLException when database access fails
     */
    public List<Long> excludingIds(long tenantId, List<Long> excludedIds, int offset, int limit)
            throws SQLException {
        validate(excludedIds, offset, limit);
        return query(tenantId, excludedIds, true, offset, limit);
    }

    /**
     * Finds a page with an optional positive identifier filter.
     *
     * @param tenantId trusted tenant identifier
     * @param optionalIds optional identifiers; empty omits only this filter
     * @param offset nonnegative page offset
     * @param limit page size from one through three
     * @return matching identifiers in descending order
     * @throws IllegalArgumentException when a size or page bound is invalid
     * @throws SQLException when database access fails
     */
    public List<Long> findByOptionalIds(long tenantId, List<Long> optionalIds, int offset, int limit)
            throws SQLException {
        validate(optionalIds, offset, limit);
        return query(tenantId, optionalIds, false, offset, limit);
    }

    /**
     * Rejects unsupported input before database access.
     *
     * @param ids nonnull identifiers with no null elements
     * @param offset requested page offset
     * @param limit requested page size
     * @throws IllegalArgumentException when a size or page bound is invalid
     */
    private static void validate(List<Long> ids, int offset, int limit) {
        if (ids.size() > 20 || offset < 0 || limit < 1 || limit > 3) {
            throw new IllegalArgumentException("Invalid bounded page request");
        }
    }

    /**
     * Executes one bounded tenant query using the supplied filter semantics.
     *
     * @param tenantId trusted tenant identifier
     * @param ids identifiers for an optional SQL condition
     * @param exclude whether the condition excludes the identifiers
     * @param offset validated page offset
     * @param limit validated page size
     * @return identifiers in descending order
     * @throws SQLException when database access fails
     */
    private List<Long> query(long tenantId, List<Long> ids, boolean exclude, int offset, int limit)
            throws SQLException {
        String sql = "SELECT id FROM users WHERE tenant_id = ?";
        if (!ids.isEmpty()) {
            String placeholders = String.join(",", Collections.nCopies(ids.size(), "?"));
            sql += " AND id " + (exclude ? "NOT IN" : "IN") + " (" + placeholders + ")";
        }
        sql += " ORDER BY id DESC LIMIT ? OFFSET ?";
        try (PreparedStatement statement = connection.prepareStatement(sql)) {
            int index = 1;
            statement.setLong(index++, tenantId);
            for (long id : ids) {
                statement.setLong(index++, id);
            }
            statement.setInt(index++, limit);
            statement.setInt(index, offset);
            try (ResultSet rows = statement.executeQuery()) {
                List<Long> result = new ArrayList<>();
                while (rows.next()) {
                    result.add(rows.getLong(1));
                }
                return result;
            }
        }
    }
}
