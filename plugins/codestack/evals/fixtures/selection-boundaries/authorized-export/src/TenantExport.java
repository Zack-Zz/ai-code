import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.util.ArrayList;
import java.util.List;

/**
 * Produces the already authorized bounded tenant export.
 */
public final class TenantExport {
    /**
     * Approved maximum rows read in a database batch.
     */
    private static final int BATCH_SIZE = 50;

    /**
     * Approved maximum rows returned by one export.
     */
    private static final int MAX_ROWS = 200;

    /**
     * Caller-owned connection.
     */
    private final Connection connection;

    /**
     * Creates an exporter on an existing connection.
     *
     * @param connection caller-owned database connection
     */
    public TenantExport(Connection connection) {
        this.connection = connection;
    }

    /**
     * Exports the approved ID range for one trusted tenant.
     *
     * @param tenantId trusted tenant identifier
     * @return CSV records in ascending ID order
     * @throws SQLException when database access fails
     */
    public List<String> export(long tenantId) throws SQLException {
        long afterId = 99;
        List<String> records = new ArrayList<>();
        while (records.size() < MAX_ROWS) {
            int pageSize = Math.min(BATCH_SIZE, MAX_ROWS - records.size());
            int found = 0;
            try (PreparedStatement statement = connection.prepareStatement(
                    "SELECT id, display_name, status FROM users WHERE tenant_id = ? AND id > ? AND id < 300 ORDER BY id ASC LIMIT ?")) {
                statement.setLong(1, tenantId);
                statement.setLong(2, afterId);
                statement.setInt(3, pageSize);
                try (ResultSet rows = statement.executeQuery()) {
                    while (rows.next()) {
                        afterId = rows.getLong("id");
                        records.add(afterId + "," + rows.getString("display_name"));
                        found++;
                    }
                }
            }
            if (found < pageSize) {
                break;
            }
        }
        return records;
    }
}
