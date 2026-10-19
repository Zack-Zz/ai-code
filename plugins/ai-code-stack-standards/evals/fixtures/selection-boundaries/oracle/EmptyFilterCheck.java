import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.Collections;
import java.util.List;

/**
 * Evaluator-owned checks for three different empty-filter contracts.
 */
public final class EmptyFilterCheck {
    /**
     * Exact statistics query excluded from the observed execution sum.
     */
    private static final String STATISTICS_QUERY =
            "SELECT SQL_STATEMENT, EXECUTION_COUNT FROM INFORMATION_SCHEMA.QUERY_STATISTICS";

    /**
     * Checks behavior against a fresh local H2 database.
     *
     * @param arguments optional group: required, counterexamples, or all
     * @throws Exception when database initialization or an operation fails
     * @throws AssertionError when a contract is violated
     */
    public static void main(String[] arguments) throws Exception {
        String group = arguments.length == 0 ? "all" : arguments[0];
        if (!List.of("required", "counterexamples", "all").contains(group)) {
            throw new IllegalArgumentException("Unknown check group: " + group);
        }
        Class.forName("org.h2.Driver");
        try (Connection connection = DriverManager.getConnection("jdbc:h2:mem:empty_filter")) {
            initialize(connection);
            UserDirectory directory = new UserDirectory(connection);
            if (!group.equals("counterexamples")) {
                long before = statementCount(connection);
                assertRows("required empty", List.of(), directory.findByRequiredIds(7, List.of(), 0, 3));
                assertExecutions(connection, before, 0, "required empty");
                before = statementCount(connection);
                assertRows("required nonempty", List.of(4L, 2L),
                        directory.findByRequiredIds(7, List.of(2L, 4L, 6L), 0, 3));
                assertExecutions(connection, before, 1, "required nonempty");
                System.out.println("Required positive empty/nonempty contracts passed");
            }
            if (!group.equals("required")) {
                long before = statementCount(connection);
                assertRows("empty exclusion", List.of(4L, 3L), directory.excludingIds(7, List.of(), 1, 2));
                assertExecutions(connection, before, 1, "empty exclusion");
                before = statementCount(connection);
                assertRows("empty optional filter", List.of(4L, 3L),
                        directory.findByOptionalIds(7, List.of(), 1, 2));
                assertExecutions(connection, before, 1, "empty optional filter");
                before = statementCount(connection);
                assertRows("nonempty exclusion", List.of(5L, 3L),
                        directory.excludingIds(7, List.of(4L), 0, 2));
                assertExecutions(connection, before, 1, "nonempty exclusion");
                before = statementCount(connection);
                assertRows("optional inclusion with offset", List.of(3L),
                        directory.findByOptionalIds(7, List.of(1L, 3L, 5L, 6L), 1, 1));
                assertExecutions(connection, before, 1, "optional inclusion with offset");
                System.out.println("Exclusion/optional semantics, tenant, page and order passed");
            }
            assertBounds(connection, directory);
        }
    }

    /**
     * Creates tenant-overlapping IDs and enables fresh query statistics.
     *
     * @param connection open local database connection
     * @throws SQLException when setup fails
     */
    private static void initialize(Connection connection) throws SQLException {
        try (Statement statement = connection.createStatement()) {
            statement.execute("SET QUERY_STATISTICS TRUE");
            statement.execute("SET OPTIMIZE_REUSE_RESULTS FALSE");
            statement.execute("CREATE TABLE users (tenant_id BIGINT, id BIGINT, PRIMARY KEY (tenant_id, id))");
            statement.execute("INSERT INTO users VALUES (7,1),(7,2),(7,3),(7,4),(7,5),(8,1),(8,6)");
        }
    }

    /**
     * Compares a complete bounded result with its expected IDs.
     *
     * @param label operation description
     * @param expected expected ordered identifiers
     * @param actual observed ordered identifiers
     * @throws AssertionError when identifiers or their order differ
     */
    private static void assertRows(String label, List<Long> expected, List<Long> actual) {
        if (!expected.equals(actual)) {
            throw new AssertionError(label + " expected " + expected + " but got " + actual);
        }
    }

    /**
     * Verifies an operation's engine execution increment.
     *
     * @param connection open local connection
     * @param before execution sum before the operation
     * @param expected expected execution increment
     * @param label operation description
     * @throws SQLException when observation fails
     * @throws AssertionError when the execution increment differs
     */
    private static void assertExecutions(Connection connection, long before, long expected, String label)
            throws SQLException {
        long actual = statementCount(connection) - before;
        if (actual != expected) {
            throw new AssertionError(label + " expected SQL executions=" + expected + " but got " + actual);
        }
        System.out.println(label + " SQL executions=" + actual);
    }

    /**
     * Checks size and page rejection before database access.
     *
     * @param connection open local connection
     * @param directory candidate directory under evaluation
     * @throws SQLException when an unexpected database failure occurs
     * @throws AssertionError when invalid input is accepted or reaches SQL
     */
    private static void assertBounds(Connection connection, UserDirectory directory) throws SQLException {
        long before = statementCount(connection);
        int rejected = 0;
        try {
            directory.findByRequiredIds(7, Collections.nCopies(21, 1L), 0, 3);
        } catch (IllegalArgumentException expected) {
            rejected++;
        }
        try {
            directory.excludingIds(7, List.of(), 0, 4);
        } catch (IllegalArgumentException expected) {
            rejected++;
        }
        try {
            directory.findByOptionalIds(7, List.of(), -1, 2);
        } catch (IllegalArgumentException expected) {
            rejected++;
        }
        if (rejected != 3) {
            throw new AssertionError("All three invalid requests must be rejected");
        }
        assertExecutions(connection, before, 0, "invalid request bounds");
    }

    /**
     * Sums engine-observed statements, including every SQL shape.
     *
     * @param connection open local connection
     * @return cumulative execution sum excluding the exact observer statement
     * @throws SQLException when statistics cannot be read
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
