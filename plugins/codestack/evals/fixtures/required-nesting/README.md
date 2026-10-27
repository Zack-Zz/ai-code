# R32: a new local JDK visitor implementation

This positive boundary case asks for a new implementation, not repair of an
existing cursor. Copy only `seed/` into the candidate workspace. Keep `oracle/`,
`check.py`, `calibrate.py` and this operator guide outside it. Freeze these inputs
before model runs; baseline and candidate get identical seeds and task text.

Use this ordinary task prompt verbatim:

> 请实现 `src/AttachmentStore.java` 的 `usedBytes()`：按项目已有的 JDK 文件访问协议统计附件目录当前占用，排除暂存目录和符号链接，超出配额或遇到 I/O 错误时失败。保留 README 中的隔离、公开 API 和无副作用约定。允许修改或新增 `src` 下的 Java 文件；实现方案已确认，请直接完成并在临时目录编译验证，不要修改 README、安装依赖或操作 Git。

The JDK `FileVisitor` protocol has several methods and is not a functional
interface. A small method-local, anonymous or private visitor can implement its
callbacks while directly using the enclosing scanner's private root/quota and
keeping the per-call accumulator hidden. This is a concrete SDK adaptation and
encapsulation need, rather than a business DTO hidden inside a service merely to
save a file. No visitor exists in the seed, so a retained visitor is newly created.

Nesting is a reasonable minimal boundary here; it is **not a Java language
requirement**. An equivalent top-level adapter using narrow private capabilities
can also preserve the contracts. The oracle must not award a nesting preference,
reject an equivalent implementation merely for being top-level, or interpret a
correct hand-written nested control as a model outcome. Review the actual diff
to decide whether a new nested implementation is small, justified and localized,
and whether extracting it would require extra state plumbing or relaxed access.
The seed's walk protocol is a real JDK contract, not a custom framework invented
to force a type name or nesting choice.

The evaluator uses Java 17 reflection and actual filesystem operations. It checks
recursive byte totals, staging pruning, both file and directory symlinks, a root
named `.staging`, inclusive and exceeded quotas, constructor validation, checked
I/O after the root disappears, refreshed results, repeated and concurrent calls,
independent instances, unchanged file content, and the allowed public constructor
and method. It permits private types and additional package-private source files;
it never scores `class` occurrences or expected private helper names.

```sh
python3 -B plugins/codestack/evals/fixtures/required-nesting/check.py /private/tmp/WORKSPACE
python3 -B plugins/codestack/evals/fixtures/required-nesting/calibrate.py
```

The hand controls include anonymous and method-local JDK visitors and an
equivalent top-level adapter. Negative controls compile successfully, then fail
the real oracle for an empty result, unpruned staging files, followed links,
shared accumulator, missing quota guard, swallowed I/O, exposed root/accumulator,
and unrelated public API. Functional failure and public contract failure are
reported separately. Neither constitutes automatic proof of maintainable shape.

References: [JDK 17 FileVisitor](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/nio/file/FileVisitor.html),
[JDK 17 Files.walkFileTree](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/nio/file/Files.html#walkFileTree(java.nio.file.Path,java.nio.file.FileVisitor)).
