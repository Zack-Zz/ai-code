# Contract boundaries: reuse and public nested APIs

These anonymous Java 17 projects add counterexamples to the existing reuse and
nesting evaluations. Copy only `incompatible-reuse` or `public-nested-api` into a
disposable candidate workspace. Keep this operator README, `check.py`,
`calibrate.py`, and `oracle` outside that workspace. These evaluator resources are
not runtime instructions and are outside the plugin package allowlist.

## Ordinary tasks and independent judgments

Freeze the ordinary task, seed bytes, enabled skills, host, model and settings
before each matched run. Keep the exact task identical within each pair. Do not
name CodeStack, name a preferred helper, forbid nesting in the prompt, or provide
the evaluator to the candidate. The seed README states application contracts;
it does not prescribe an implementation.

| Case | Seed and exact ordinary task | External behavior check | Separate trace and diff judgment |
| --- | --- | --- | --- |
| R30 | `incompatible-reuse`: 请按 README 完成 PreviewService.preview，提供购买前的只读金额预览，并保留现有结账行为。仅修改 src/PreviewService.java。实现方案已确认，请直接完成并编译验证，不要操作 Git、安装依赖或修改其他目录。 | `PreviewCheck` checks totals, repeated previews, reservation state, stock remaining after a genuine checkout, unknown/foreign items, insufficient stock, large requests, invalid units, and the unchanged checkout command contract. An implementation that returns the right initial total by running checkout still fails on its observable reservation side effect. Direct checkout exception leakage fails separately. | Inspect actual reads of the existing source and its real contract before judging the choice. A compatible read-only accessor or pure calculation can be reused; the mismatched state-changing command must not be used merely because its result looks suitable. The checker does not infer reuse from method names or grep. This fixture exercises side effects, exceptions and tenant ownership; it does not simulate a transaction manager, database or framework permission system. |
| R31 | `public-nested-api`: ShipmentService 的报价预计天数一直是 0，请按 README 修复交付天数，保留费用、输入校验和现有已部署调用者的兼容性。仅修改或新增 src 下的 Java 文件。实现方案已确认，请直接完成并编译验证，不要操作 Git、安装依赖或修改其他目录。 | `check.py` first compiles `LegacyShipmentCaller.class` against the untouched original library, keeps only that client class, then compiles the candidate library separately and runs the original client without recompiling it. Constructor/accessor calls and the `quote(int)` return descriptor exercise the existing public `ShipmentService$Quote` API. `ShipmentCheck` independently checks fees, 10/11-parcel delivery boundaries, and invalid counts; it intentionally accepts a relocated result type for semantic checks so the linkage control can distinguish compatibility. | Inspect the candidate diff for preservation of the deployed public type and method descriptors. Keeping the nested API is justified by real existing clients, even if a top-level result would otherwise be preferred. An extra implementation type behind the same compatible public API is allowed. Functional success with a migrated/recompiled caller cannot establish compatibility with old deployed bytecode. |

The R30 immutable checkout and inventory sources are real task context. Only
`src/PreviewService.java` may change. R31 allows Java source changes/additions
under `src`, while preserving the original input files. Both tasks preserve their
README bytes. A staged `.agents` subtree is operator setup, excluded from source
scope checking; compare its bytes separately and do not treat this exclusion as
permission for the candidate to edit rule files.

## Run the frozen checks

Use an existing Java 17+ toolchain. No network requests, downloads or third-party
dependencies are needed. The checker compiles into temporary directories and
uses evaluator-owned checks rather than candidate-written tests.

```sh
python3 -B <evaluator>/check.py incompatible-reuse <candidate>
python3 -B <evaluator>/check.py public-nested-api <candidate>
```

Optional `--section side-effects|unavailable|invalid|checkout` selects one R30
contract. `--section compatibility-only|semantics-only` selects one R31 contract.
These sections calibrate exact failure categories; a full candidate verdict uses
the complete default command.

The original R30 seed has an unfinished preview, producing a specific semantic
failure after successful compilation. The original R31 seed passes the real
old-client linkage check, then fails the delivery-days assertion. Compilation,
tooling, setup and classpath errors are not valid starting behavioral RED.

## Calibrate the evaluator without a model

```sh
python3 -B <evaluator>/calibrate.py
```

Fifteen hand-control observations exercise these boundaries:

- An unfinished preview fails; the read-only implementation and one using a pure
  private calculation helper pass. The latter is only a behavior control, not an
  assertion that an extra helper is needed.
- Direct reuse of the checkout command returns a correct initial amount but
  fails the reservation-state assertion. A separate unavailable-item invocation
  exposes its incompatible exception. Catching that exception does not remove
  the command's state-changing side effect.
- A tenant leak and returning empty for invalid units fail their specific
  contract assertions.
- The original library passes the frozen-client check and fails its existing
  delivery-days defect. Preserving the public nested record while fixing days
  passes both checks. A wrong 10-parcel boundary fails only semantics after
  linkage has passed.
- Relocating the record to a top-level `Quote` passes quotation semantics. An
  explicitly migrated and recompiled client also passes; its source references
  and expected type name have been updated, so this is not an old-client pass.
  The unchanged, precompiled old client fails with `NoSuchMethodError` for
  `ShipmentService$Quote ShipmentService.quote(int)`. That expected compatibility
  failure is a deliberate negative control, distinct from the seed's semantic
  RED and from environment errors.

Calibration preserves commands and logs in an operator temporary directory.
Hand controls are not model runs. Actual native results must report observed
Skill/reference reads, independent task outcomes, source scope and manual diff
judgment separately. A matched pilot cannot establish reliability, improvement,
installed-plugin discovery or behavior in another host. No extra runtime rule is
introduced by these evaluation inputs.
