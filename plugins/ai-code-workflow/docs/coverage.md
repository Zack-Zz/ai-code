# Tool coverage report (2026-10-03, overall review repairs)

Directory note (2026-10-07): this is the dated workflow baseline, now under
`plugins/ai-code-workflow/`. Original counts, commands and hashes below are
historical evidence; they do not validate the migration. Current navigation
and shared packaging are described in [the multi-plugin design](../../../docs/design/2026-10-07-multi-plugin-design.md).

Method: Python stdlib `trace` over the full Python suite, using
`--count --missing --summary`. Counts below come from the same annotated
`.cover` files: executed lines divided by executed plus missing executable
lines. This is line/statement coverage, not branch or model coverage.
The run used Python 3.13.3 and all 265 Python tests passed. Reproduce in a
fresh temporary cover directory. The following is the original 2026-10-03
command; the current workflow Python entry is
`plugins/ai-code-workflow/tests/run_python_tests.py` from the repository root:

```sh
python3 -m trace --count --missing --summary --coverdir /tmp/ai-code-coverage tests/run_python_tests.py
```

## Traced core modules

| Module | Covered | Rate |
|---|---|---|
| scripts/workflow/build.py | 254/272 | 93.4% |
| scripts/workflow/policy.py | 90/98 | 91.8% |
| scripts/workflow/product.py | 283/321 | 88.2% |
| scripts/workflow/package_check.py | 163/191 | 85.3% |
| scripts/workflow/io.py | 239/268 | 89.2% |
| scripts/workflow/owned_files.py | 333/387 | 86.0% |
| scripts/workflow/state.py | 477/563 | 84.7% |
| **Aggregate** | **1839/2100** | **87.6%** |

All seven measured core modules exceed the 80% target. This is not a claim
that every executable entry point has measured 80% coverage.

## Measurement limits

CLI, eval preparation/collection, the CI distribution checker and most grade
paths run in real subprocesses with asserted results. This trace harness
does not instrument those children; the grader's small in-process regression
probe is also excluded from this seven-module aggregate. These paths are
exercised but do not have a complete coverage measurement here.

## Verification boundary

Executed lines do not prove branches, authorization semantics, real skill
selection, reviewer restrictions or business results. Host acceptance remains
separate; see [support matrix](support-matrix.md) and the
[current host probes](../evals/blocked-env-2026-10-02.md).
