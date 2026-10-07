# managed_package fixture

Not a static file tree: `evals/prepare.py` materializes this fixture per run by

1. building a minimal real package from the current source
   (`scripts/workflow_tool.py build --host zcode --output <run>/pkg`), then
2. staging it into an isolated target root, and
3. planting the scenario props used by A23/A24:
   - an un-owned file inside the managed root (`unowned-extra.txt`),
   - a user-edited managed file (scripted edit after first staging).

Everything stays inside the one-shot output directory; the product source
repository is never touched. A25 uses the two real host builds directly.
