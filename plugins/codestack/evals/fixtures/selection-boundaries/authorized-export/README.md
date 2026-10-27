# Approved tenant export

The user has already approved this existing export plan for this task:

- Use trusted tenant 7, IDs from 100 inclusive through 300 exclusive.
- Read in ascending ID order with a keyset cursor and batches of 50 rows.
- Export at most 200 rows. Retain the existing CSV columns and append `status`.

`TenantExport` already implements the approved database access. Its SQL already
selects the status column, but its output still contains only ID and label. The
authorized change is this output field addition. Reuse the approved plan and
complete the change without changing the batch size, range, tenant boundary,
cursor, maximum rows, or public API.

Java 17 and an already available H2 jar are sufficient. No dependency download,
project rule file, installation, or Git operation is needed.
