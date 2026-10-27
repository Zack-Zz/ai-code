import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;

/**
 * Calibrates the evaluator against real H2 executions with different SQL spellings.
 */
public final class SqlCountCalibration {
    /**
     * Verifies observation exclusion and one increment per executed statement.
     *
     * @param arguments unused command-line arguments
     * @throws Exception when driver loading or database operations fail
     * @throws AssertionError when an observation or execution count is incorrect
     */
    public static void main(String[] arguments) throws Exception {
        Class.forName("org.h2.Driver");
        try (Connection connection = DriverManager.getConnection("jdbc:h2:mem:codestack_count_calibration")) {
            try (Statement statement = connection.createStatement()) {
                statement.execute("SET QUERY_STATISTICS TRUE");
                statement.execute("SET OPTIMIZE_REUSE_RESULTS FALSE");
            }
            long beforeObservation = UserReportCheck.statementCount(connection);
            if (UserReportCheck.statementCount(connection) != beforeObservation) {
                throw new AssertionError("The exact observation statement must not count itself");
            }

            assertOneExecution(connection, "plain SELECT", "SELECT 42 AS answer");
            assertOneExecution(connection, "CTE", "WITH answer(result_value) AS (SELECT 42) SELECT result_value FROM answer");
            assertOneExecution(connection, "leading comment", "/* report lookup */ SELECT 42 AS answer");
            assertOneExecution(connection, "newline after SELECT", "SELECT\n42 AS answer");
            assertOneExecution(connection, "repeated statement", "SELECT 42 AS answer");
            assertOneExecution(connection, "observation name in data",
                    "SELECT 42 AS answer, 'INFORMATION_SCHEMA.QUERY_STATISTICS' AS note");
        }
    }

    /**
     * Executes one real query and checks the resulting statistics increment.
     *
     * @param connection open calibration database connection
     * @param label human-readable description of this SQL shape
     * @param sql query returning one row whose first column is 42
     * @throws SQLException when execution or statistics reading fails
     * @throws AssertionError when the query result or execution increment is incorrect
     */
    private static void assertOneExecution(Connection connection, String label, String sql) throws SQLException {
        long before = UserReportCheck.statementCount(connection);
        try (Statement statement = connection.createStatement();
                ResultSet result = statement.executeQuery(sql)) {
            if (!result.next() || result.getInt(1) != 42 || result.next()) {
                throw new AssertionError("Unexpected calibration result for " + label);
            }
        }
        long executed = UserReportCheck.statementCount(connection) - before;
        if (executed != 1) {
            throw new AssertionError(label + " must count once, observed " + executed);
        }
        System.out.println(label + ": " + executed);
    }
}
