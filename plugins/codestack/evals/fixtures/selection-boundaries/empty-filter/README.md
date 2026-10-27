# Tenant directory

This Java 17 JDBC fixture has three deliberately distinct filter contracts:

- `findByRequiredIds`: IDs are a required positive inclusion condition. An empty
  list must return no rows without issuing SQL. The starting implementation has
  a defect in this case.
- `excludingIds`: an empty exclusion list excludes nothing.
- `findByOptionalIds`: an empty optional list omits only this optional filter.

Every query retains trusted tenant isolation, descending ID order, the supplied
offset, and a page limit from 1 through 3. Lists accept at most 20 nonnull IDs.
The caller owns the database connection. Do not change these existing contracts.

No dependency download, server, project rule file, or Git operation is needed.
