# managed_package fixture

Not a static file tree: `evals/prepare.py` materializes this fixture per run by

1. building real packages from the current source for every host declared by
   `product.json`, then
2. creating an empty isolated target root and recording the package baseline.

`collect.py` binds the run to the package named by the manifest's `host`.
`grade.py` runs that package's CLI to stage files and plant A23/A24 props:

- an un-owned file inside the managed root (`unowned-extra.txt`),
- a user-edited managed file (scripted edit after first staging),
- update interruption, backups and concurrent writers for A24.

Everything stays inside the one-shot output directory; the product source
repository is never touched. A25 checks all declared host builds and their
common resources. File staging is not native plugin installation; these
scenarios do not start a host or model and do not establish host acceptance.
