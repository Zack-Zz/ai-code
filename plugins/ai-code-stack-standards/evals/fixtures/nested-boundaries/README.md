# Nested-type boundary evaluation inputs

These anonymous Java 17 projects separate a new business result type from a
small existing JDK contract implementation. Only `business-result` or
`jdk-iterator` enters a disposable model workspace. Keep this README, `check.py`,
`calibrate.py`, and `oracle` outside it. These local evaluator resources are
outside the plugin package allowlist and uniform package test gate.

## Ordinary tasks and frozen judgments

Freeze the rendered task, initial source, enabled skills, host, model and settings
before each matched run. Never name CodeStack or prescribe a type shape in the
ordinary task. The following task text was supplied to the native-run operator;
keep it identical within each before/after pair.

| Case | Seed and exact ordinary task | External behavior check | Separate trace and diff judgment |
| --- | --- | --- | --- |
| R28 | `business-result`: 请在 DispatchService 中增加 public quote(int parcelCount, int distanceKm)，返回包含 feeCents() 和 estimatedDays() 的结构化结果。费用沿用现有规则，50 公里以内预计 1 天，超过 50 公里预计 3 天；继续拒绝范围外输入并保留现有 feeCents 方法的行为。仅修改或新增 src 下的 Java 文件。实现方案已确认，请直接完成并编译验证，不要操作 Git、安装依赖或修改其他目录。 | `DispatchCheck` invokes the requested public operation, checks 15 valid parcel/distance combinations including the 50 km boundary, checks both APIs against six invalid input pairs, and requires a structured result with the requested accessors. The returned type's name, source file and nesting are unrestricted. | Read Java rules for this ordinary Java task. Inspect the real source diff for a clear top-level business result or a concrete justification for nesting. Convenience, one caller, private visibility and fewer files alone do not establish necessity. A behavior pass cannot establish this structural judgment. |
| R29 | `jdk-iterator`: MessageWindow 用 hasNext 遍历时会漏掉最后一条消息，请修复边界行为。保留 README 中的快照、独立迭代、耗尽异常和只读契约，以及现有公开 API。仅修改 src/MessageWindow.java。实现方案已确认，请直接完成并编译验证，不要操作 Git、安装依赖或修改其他目录。 | `IteratorCheck` checks empty, single, duplicate and multiple-message iteration; repeated hasNext; next without hasNext; repeated exhaustion; unsupported removal; caller-array isolation; independent interleaved iterators; null rejection; and the unchanged public member surface. It does not assert that Cursor exists or is removed. | Existing Cursor implements the JDK Iterator protocol with per-iterator advancement over the enclosing object's private snapshot. Keeping this small local protocol implementation can be justified by that state/contract relationship and the limited boundary repair; being private alone is insufficient. A simpler equivalent JDK iterator is also acceptable. Do not force extraction that exposes the private array, adds a public helper, or expands the task. |

`DispatchService` represents application business code with a reused service
instance. No fake Spring annotation, container or framework stub is provided.
These outcomes therefore do not establish Spring Bean lifecycle behavior.

`MessageWindow` starts with a real non-static member Cursor and a defective
hasNext boundary. Its cursor directly reads the enclosing private array and owns
its own advancement state. The case tests that a preference against nesting does
not become an unconditional ban or an excuse to expose state. Because an
equivalent standard-library implementation exists, this case does not establish
that a custom nested iterator is the only possible design. Review whether the
candidate's actual choice is the smaller, clear solution for this task.

## Run the independent checks

Use an existing Java 17+ toolchain. The checker compiles candidate production
source together with an evaluator-owned frozen oracle into a temporary directory.
It does not trust candidate-written tests or download dependencies.

```sh
python3 -B <evaluator>/check.py business-result <candidate>
python3 -B <evaluator>/check.py jdk-iterator <candidate>
```

The checker preserves seed README bytes and permits only the task's declared
source changes. A staged `.agents` skill subtree is evaluation setup, excluded
from source-scope judgment; compare its final bytes with the staged bytes
separately. The candidate cannot use this exception as permission to create or
edit rule files. Inspect actual completed tool commands for skill/reference reads
and the actual diff for nesting, reuse and scope. Do not classify model outcomes
using grep keywords, its final claims, or a prescribed class name.

## Calibrate without a model

```sh
python3 -B <evaluator>/calibrate.py
```

The 12 hand-control outcomes include the missing quote operation and the omitted
last iterator item as valid semantic RED. Top-level and nested quote records both
pass behavior checks, deliberately showing that structural quality is outside
the oracle. Wrong quote fees, the 51 km day boundary and missing quote rejection
fail their specific semantic assertions. Both a minimally repaired private Cursor
and an equivalent JDK iterator pass. A shared cursor, caller-array aliasing and an
extra public operation fail their corresponding behavior or API assertions.

Compilation, missing tooling and environment failures do not count as semantic
RED. Hand-written controls calibrate these checks; they are never model passes.
A single before/after pair per case is a pilot. It cannot demonstrate reliability,
improvement, installed-plugin discovery or any other host's behavior. Keep those
claims separate from observed skill reads, independent task outcomes and manual
structural judgment.
