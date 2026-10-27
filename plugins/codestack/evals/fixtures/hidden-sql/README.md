# Tenant user report

This fixture intentionally contains a hidden query-per-user defect. It is
evaluation input, not recommended implementation. `UserReport.names` preserves
request order and duplicate IDs, returns `<missing>` for an unknown or foreign
tenant user, and accepts at most 200 IDs. Empty input produces no database work.

Use Java 17 or later and an already available H2 2.3.232 jar. The fixture does
not download dependencies. Set `H2_JAR` to that existing jar and compile into a
temporary directory outside the fixture:

```sh
javac -d <temporary-classes> src/UserReport.java test/UserReportCheck.java test/SqlCountCalibration.java
java -cp "<temporary-classes>:$H2_JAR" SqlCountCalibration
java -cp "<temporary-classes>:$H2_JAR" UserReportCheck --observe
java -cp "<temporary-classes>:$H2_JAR" UserReportCheck
```

`--observe` checks the current result contract and prints the actual H2 statement
execution increment without enforcing the improvement budget. The default mode
also requires at most one user lookup statement for the four-item request. It is
expected to fail on the deliberately flawed starting implementation.

The checker sums H2's `INFORMATION_SCHEMA.QUERY_STATISTICS` execution counters
before and after the operation, excluding only its exact observation statement.
It does not classify queries by their first keyword, whitespace or comments.
Setup statements are included in cumulative counters but precede the operation's
starting snapshot. It disables H2 result reuse in this disposable database so
repeated observation queries return current statistics. This is engine-observed SQL execution evidence for this
small in-memory fixture, not Mapper-call counting, a production query plan, a
database performance benchmark, or evidence of real ORM behavior. The fixture
has no triggers, ORM, server, credentials or external services.

Run `SqlCountCalibration` before evaluating candidates when a local H2 jar is
available. It checks ordinary SELECT, CTE, leading comments, a newline following
SELECT, repeated execution, and a query containing the observation table's name
as data. Each must add one engine-recorded execution; observation alone adds
none. Calibration and H2 remain optional local checks, outside the uniform
package test gate. They never download dependencies or invoke a model.
