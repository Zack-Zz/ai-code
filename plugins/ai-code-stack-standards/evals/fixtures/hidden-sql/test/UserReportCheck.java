import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.Collections;
import java.util.List;

/**
 * Checks result semantics and engine-observed SQL counts on a local H2 database.
 */
public final class UserReportCheck {
    /**
     * Exact observation statement excluded from the fixture's execution count.
     */
    private static final String STATISTICS_QUERY =
            "SELECT SQL_STATEMENT, EXECUTION_COUNT FROM INFORMATION_SCHEMA.QUERY_STATISTICS";

    /**
     * Runs the fixture checks without any external database connection.
     *
     * @param arguments optionally {@code --observe} to report the initial query count
     * @throws Exception when driver loading or database operations fail
     * @throws AssertionError when a result or execution budget differs from the contract
     */
    public static void main(String[] arguments) throws Exception {
        boolean observeOnly = arguments.length == 1 && arguments[0].equals("--observe");
        Class.forName("org.h2.Driver");
        try (Connection connection = DriverManager.getConnection("jdbc:h2:mem:codestack_report")) {
            initialize(connection);
            UserReport report = new UserReport(connection);
            long before = statementCount(connection);
            List<String> names = report.names(7, List.of(1L, 2L, 1L, 3L));
            long executed = statementCount(connection) - before;
            if (!names.equals(List.of("Ada", "Lin", "Ada", "<missing>"))) {
                throw new AssertionError("Tenant isolation, duplicates, missing users and order must be preserved: " + names);
            }
            System.out.println("Observed user lookup SQL statement executions: " + executed);

            long emptyBefore = statementCount(connection);
            if (!report.names(7, List.of()).isEmpty() || statementCount(connection) != emptyBefore) {
                throw new AssertionError("Empty input must return no rows without database statements");
            }
            boolean rejected = false;
            long oversizedBefore = statementCount(connection);
            try {
                report.names(7, Collections.nCopies(201, 1L));
            } catch (IllegalArgumentException expected) {
                rejected = true;
            }
            if (!rejected || statementCount(connection) != oversizedBefore) {
                throw new AssertionError("Oversized input must be rejected before database access");
            }
            if (!observeOnly && executed > 1) {
                throw new AssertionError("Expected at most one lookup SQL statement, observed " + executed);
            }
        }
    }

    /**
     * Creates anonymous test rows and enables engine query statistics.
     *
     * @param connection open test connection
     * @throws SQLException when initialization fails
     */
    private static void initialize(Connection connection) throws SQLException {
        try (Statement statement = connection.createStatement()) {
            statement.execute("SET QUERY_STATISTICS TRUE");
            // Reused observation results would hide newly executed statements.
            statement.execute("SET OPTIMIZE_REUSE_RESULTS FALSE");
            statement.execute("CREATE TABLE users (tenant_id BIGINT, id BIGINT, display_name VARCHAR(40), PRIMARY KEY (tenant_id, id))");
            statement.execute("INSERT INTO users VALUES (7, 1, 'Ada'), (7, 2, 'Lin'), (8, 3, 'Other tenant')");
        }
    }

    /**
     * Sums engine-recorded executions excluding only the exact observation statement.
     *
     * @param connection open test connection
     * @return cumulative statement executions, including setup work before the measured operation
     * @throws SQLException when statistics cannot be read
     */
    static long statementCount(Connection connection) throws SQLException {
        long count = 0;
        try (Statement statement = connection.createStatement();
                ResultSet rows = statement.executeQuery(STATISTICS_QUERY)) {
            while (rows.next()) {
                if (!STATISTICS_QUERY.equals(rows.getString(1))) {
                    count += rows.getLong(2);
                }
            }
        }
        return count;
    }
}
