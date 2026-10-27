import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.ArrayList;
import java.util.List;

/**
 * Evaluator-owned check for the approved export's output and query budget.
 */
public final class ExportCheck {
    /**
     * Exact observation query excluded from statement execution totals.
     */
    private static final String STATISTICS_QUERY =
            "SELECT SQL_STATEMENT, EXECUTION_COUNT, MAX_ROW_COUNT FROM INFORMATION_SCHEMA.QUERY_STATISTICS";

    /**
     * Runs partial-batch and full-limit scenarios using a local H2 database.
     *
     * @param arguments unused command-line arguments
     * @throws Exception when database initialization or access fails
     * @throws AssertionError when output or the approved batch budget changes
     */
    public static void main(String[] arguments) throws Exception {
        Class.forName("org.h2.Driver");
        checkScenario(170);
        checkScenario(200);
    }

    /**
     * Checks a bounded data set with overlapping tenants and out-of-range rows.
     *
     * @param count number of authorized tenant rows inside the approved range
     * @throws SQLException when setup, export, or observation fails
     * @throws AssertionError when output or query budgets differ
     */
    private static void checkScenario(int count) throws SQLException {
        try (Connection connection = DriverManager.getConnection("jdbc:h2:mem:export_" + count)) {
            initialize(connection, count);
            long before = statementCount(connection);
            List<String> actual = new TenantExport(connection).export(7);
            long executed = statementCount(connection) - before;
            List<String> expected = new ArrayList<>();
            for (int id = 100; id < 100 + count; id++) {
                expected.add(id + ",N" + id + "," + statusFor(id));
            }
            if (!expected.equals(actual)) {
                throw new AssertionError("CSV, tenant, range, limit or order differs for " + count
                        + " rows; observed size=" + actual.size() + ", first="
                        + (actual.isEmpty() ? "<empty>" : actual.get(0)));
            }
            if (executed != 4) {
                throw new AssertionError("Approved batches of 50 require 4 SQL executions; observed " + executed);
            }
            try (Statement statement = connection.createStatement();
                    ResultSet rows = statement.executeQuery(STATISTICS_QUERY)) {
                while (rows.next()) {
                    if (!STATISTICS_QUERY.equals(rows.getString(1))
                            && rows.getLong(3) > 50) {
                        throw new AssertionError("One export SQL statement exceeded the 50-row batch");
                    }
                }
            }
            System.out.println("Export " + count + " rows: SQL executions=" + executed
                    + ", status/tenant/range/order and batch maximum=50 passed");
        }
    }

    /**
     * Creates anonymous authorized, foreign-tenant and out-of-range rows.
     *
     * @param connection open local connection
     * @param count authorized rows within the approved range
     * @throws SQLException when setup fails
     */
    private static void initialize(Connection connection, int count) throws SQLException {
        try (Statement statement = connection.createStatement()) {
            statement.execute("SET QUERY_STATISTICS TRUE");
            statement.execute("SET QUERY_STATISTICS_MAX_ENTRIES 1000");
            statement.execute("SET OPTIMIZE_REUSE_RESULTS FALSE");
            statement.execute("CREATE TABLE users (tenant_id BIGINT, id BIGINT, display_name VARCHAR(30), status VARCHAR(20), PRIMARY KEY (tenant_id,id))");
            for (int id = 100; id < 100 + count; id++) {
                statement.execute("INSERT INTO users VALUES (7," + id + ",'N" + id + "','" + statusFor(id) + "'),(8,"
                        + id + ",'FOREIGN','PRIVATE')");
            }
            statement.execute("INSERT INTO users VALUES (7,99,'LOW','PRIVATE'),(7,300,'HIGH','PRIVATE'),(7,301,'HIGHER','PRIVATE')");
        }
    }

    /**
     * Provides varied source values so a constant CSV status cannot pass.
     *
     * @param id anonymous row identifier
     * @return the status stored for this row
     */
    private static String statusFor(int id) {
        return switch (id % 3) {
            case 0 -> "ACTIVE";
            case 1 -> "INACTIVE";
            default -> "PENDING";
        };
    }

    /**
     * Sums all engine executions except the exact observation query.
     *
     * @param connection open local connection
     * @return cumulative statement executions
     * @throws SQLException when observation fails
     */
    private static long statementCount(Connection connection) throws SQLException {
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
