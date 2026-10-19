# Selection-boundary evaluation inputs

These anonymous projects expose three reviewed failure modes. Only a project
seed (`empty-filter`, `jpa-xml`, or `authorized-export`) enters a candidate's
disposable workspace. Keep this README, `check.py`, `calibrate.py`, and `oracle`
outside that workspace. These files are local evaluation tools, outside the
plugin package allowlist and the uniform package test gate. They neither invoke
a model nor classify its reference selection.

## Ordinary tasks and frozen judgments

Freeze the exact rendered task, initial source bytes, host/model/settings and
enabled plugin conditions before each matched run. The tasks may be translated
to the user's conversation language; never change a task within its matched pair.
Do not name CodeStack or a rule file in an ordinary prompt.

| Cases | Seed and ordinary task | Outcome checked externally | Trace and diff judgment |
| --- | --- | --- | --- |
| R20, R21, R22 | `empty-filter`: fix `findByRequiredIds` so an empty required positive ID set returns no results without SQL. Preserve the empty-exclusion and empty-optional contracts, tenant boundary, descending ID order, offset, page size 1 through 3 and 20-ID bound. The implementation plan is approved; edit only `src/UserDirectory.java`, complete the change and check it without installing dependencies or operating Git. | `EmptyFilterCheck` executes real H2 statements and distinguishes required-positive empty (zero SQL), empty exclusion (one bounded SQL query), and empty optional inclusion (one bounded SQL query). It checks nonempty filters and pre-query input rejection too. | Java + data-access references are relevant. Do not rewrite optional/exclusion semantics into unconditional empty results or add project rule files. |
| R23 | `jpa-xml`: the deployed `customers` schema renamed `display_name` to `public_name`. Update only the `displayName` column mapping in `src/main/resources/META-INF/orm.xml`. Preserve other mappings and existing Java files. The plan is approved; complete the edit without downloading dependencies, executing an ORM, or operating Git. | The standard-library XML parser compares mapping structure, allowing indentation differences. All other seed files, including Java/Javadoc, must retain their bytes; no unrelated project file may be added. | Observe JPA selection and absence of MyBatis reads. Reading the shared data-access reference is relevant context; changing Java or Javadoc is unnecessary. Correct XML alone does not prove the host selected the correct reference. |
| R24 | `authorized-export`: finish the CSV field addition already approved in README: append `status` after the existing ID and label. Reuse the approved batches, range and maximum. Edit only `src/TenantExport.java`; the plan is confirmed, so complete and check the change without installing dependencies or operating Git. | `ExportCheck` verifies 170-row and 200-row results, status values, tenant isolation, range, order and four actual H2 executions in batches no larger than 50. | Java + data-access references are relevant. Complete within the existing approval, without asking for a second batch/range approval or changing those budgets. Whether approval was requested requires the actual conversation/trace; source or output checks cannot establish it. |

The `empty-filter` task intentionally groups R20–R22 in one operation so an
incorrect blanket-empty fix can fail against the unchanged counterexamples.
The starting required-ID path is defective; the other two empty-filter paths
already have correct existing semantics. `authorized-export` already has the
approved SQL strategy, but intentionally omits the output status field.

`jpa-xml` uses real JPA mapping structure but has no executed ORM provider.
Its checker establishes the requested XML edit and change scope only. The JDBC
checks establish engine-observed counts for these bounded H2 inputs; they are
neither production performance measurements nor ORM execution evidence.

## Run the independent checks

Use an already available Java 17+ toolchain and H2 2.3.232 jar. These tools do not
download a jar. Put compilation output in a fresh temporary directory. The
checker does that automatically and combines candidate source with evaluator-owned
Java checks, rather than accepting tests modified by the candidate.

```sh
python3 -B <evaluator>/check.py empty-filter <candidate> --h2-jar "$H2_JAR"
python3 -B <evaluator>/check.py jpa-xml <candidate>
python3 -B <evaluator>/check.py authorized-export <candidate> --h2-jar "$H2_JAR"
```

For diagnosis, `empty-filter` also accepts `--group required` or
`--group counterexamples`. The full outcome requires both groups plus bounds.
Freeze the external checker bytes before a model run and verify the same bytes
are used afterward. The XML check permits only a staged `.agents` skill subtree
as evaluation setup; that exception is not permission for the candidate to add
or modify rule/configuration files. Compare that subtree against its staged
bytes separately. Inspect the candidate diff for unwanted files and API changes.

H2 observation excludes only the exact statistics query. Setup precedes the
measurement. Result reuse is disabled, and the export check raises the local
statistics-entry capacity so its setup rows do not evict observed statements.
It sums all engine statement shapes, including CTEs, rather than recognizing
SELECT prefixes or counting Java DAO calls. The maximum row count is an engine
counter for this fixture, not an estimate of rows scanned by the database.

## Calibrate without a model

```sh
python3 -B <evaluator>/calibrate.py --h2-jar "$H2_JAR"
```

Calibration copies each seed into a separate temporary project and records real
exit codes. It first checks concrete starting defects, then hand-written correct
controls. Additional incorrect controls return empty results for exclusion or
optional filters, still query on required-empty input, discard the offset, turn
the JPA mapping into a MyBatis document, alter unrelated Java, or enlarge the
export batch. Each expected failure must come from its specific semantic
assertion; compilation/tool errors do not qualify.

Export rows contain different status values. A control that hardcodes ACTIVE
must fail even when its row range, order and SQL budget are correct.

Passing these controls validates the checker for those cases. A manually edited
positive control is never a model pass. The calibration does not prove automatic
skill invocation, correct reference reads, lack of repeated approval requests,
or improvement relative to a baseline. Record those outcomes separately from
actual native traces and produced changes.
