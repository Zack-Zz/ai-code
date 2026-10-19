# CodeStack 契约与嵌套边界补充验证

日期：2026-10-19（Asia/Shanghai）。状态：补充验证与独立 Review 完成，保留未提交改动，等待用户 Review。

## 1. 授权与变更范围

本轮仅补充用户确认的三类反例、外部判定器及行为验证：既有实现契约不匹配时不强行复用、
保留公开嵌套类型的兼容性、确有 SDK 适配和封装理由时允许新建嵌套实现。
英文 Skill、四份 reference 和中文 Java 规则正文均未扩写。

新增 [R30—R32](../../plugins/ai-code-stack-standards/evals/cases.md)，同步插件设计稿的验收矩阵和证据导航。
没有增加运行时、依赖、安装代码或审批流程；未执行提交、推送、标签、PR、安装或发布。
先前规则交付及 R25—R29 的结果保留在
[复用、抽取与嵌套类型报告](2026-10-18-codestack-reuse-and-nesting.md)。

## 2. 反例与判定器校准

| 场景 | 实际契约 | 独立判定与反例 |
| --- | --- | --- |
| R30 契约不匹配 | 购买预览只读；结账会预留库存，且缺货异常语义不同 | 核对金额、重复预览、真实预留量、结账后剩余库存、租户、缺货和非法输入。直接调用结账即使金额正确，也因副作用失败；捕获异常仍不能消除副作用 |
| R31 公开嵌套 API | 独立部署的客户已调用 `ShipmentService$Quote`、其构造和访问器，以及 `quote(int)` | 先针对原库编译客户，只保留该客户 class，再与候选库运行。把 record 移到顶级后，业务检查和迁移重编客户均可通过，但未重编旧客户真实发生 `NoSuchMethodError` |
| R32 新建必要局部实现 | 用既有 JDK `FileVisitor` 协议遍历私有附件根目录，按调用隔离累计量和配额 | 实测递归、暂存目录、符号链接、边界、刷新、并发、I/O 和 API。匿名访客、局部访客、等价顶级适配器均可通过；漏剪枝、跟随链接、共享状态、漏配额、吞 I/O 或暴露 API 的控制失败 |

[契约场景操作说明](../../plugins/ai-code-stack-standards/evals/fixtures/contract-boundaries/README.md)
和 [JDK 访客操作说明](../../plugins/ai-code-stack-standards/evals/fixtures/required-nesting/README.md)
给出冻结的普通任务、允许范围、命令和局限。候选工作区只放普通项目 seed 及所选 Skill 快照；
操作说明、预期结果、校准代码和 Java oracle 均在候选工作区外。

冻结判定器后重新校准，共 26 项手工控制观察：9 项通过、17 项预期失败，全部符合预期。
起始缺陷在成功编译后产生语义断言失败，未把编译、环境或工具错误计作有效 RED。
R31 的旧客户迁移反例是刻意制造的链接失败，单独归类，不与起始报价缺陷混为一谈。
这些是判定器校准，不计作模型通过次数。

结构判断不由检查器自动评分：R30 审阅真实调用的副作用契约；R31 审阅公开描述符；
R32 审阅新访客的具体 SDK 适配与私有状态封装理由。没有按类名、行数或 `class` 数量判定。
Java 的二进制名称和方法描述符规则见
[JLS 17 二进制兼容章节](https://docs.oracle.com/javase/specs/jls/se17/html/jls-13.html#jls-13.1)。
[JDK FileVisitor](https://docs.oracle.com/en/java/javase/17/docs/api/java.base/java/nio/file/FileVisitor.html)
具有多个回调；嵌套可以是适当的最小实现，但不是 Java 语法强制要求。

## 3. 原生行为试运行

使用 Codex CLI `0.163.0`、本机 Java `17.0.18`；读取当前配置为 `gpt-6.1-sol`、
`openai` provider、`ultra` reasoning。未指定其他模型或修改全局配置。
每个普通任务各运行历史规则和当前规则一次，共六次，最多两次并行。
每组任务文本与 seed 字节相同，使用新的临时工作区和 `--ephemeral` 会话。

这是历史规则 / 当前规则的比较，两边都提供 CodeStack 源 Skill，**不是插件启用 / 禁用实验**。
历史快照为复用与嵌套扩展前的 Skill/Java reference，其他三份 reference 相同。
Java reference 的 SHA-256 分别为：

- 历史：`cec0104c67296618de682fe9bc583049b458a39df46326d1654161c375e16493`
- 当前：`0dcdb49101fc97c4db84fd2870d765172b489e42aba650aedb5fd03aa47dc950`

宿主原有 CodeVow 技能、用户指令和记忆仍可读取；轨迹中确实有相关读取。
未将这些环境因素隔离，因此不能把结果差异因果归于 Java reference。
候选自己编写的检查与外部冻结 oracle 分开记录，不用候选自述替代验证。

| 场景 | 历史规则 | 当前规则 | 实际结构审阅 |
| --- | --- | --- | --- |
| R30 | 外部检查通过 | 外部检查通过 | 都读取既有实现，以库存读取接口计算预览，没有调用结账命令；只修改预览方法 |
| R31 | 旧客户链接及业务检查通过 | 旧客户链接及业务检查通过 | 都保留公开嵌套 record；生产修复仅调整天数表达式，另在允许的 src 范围新增独立验证类 |
| R32 | 外部检查通过；新建方法局部 `UsageVisitor` | 外部检查通过；新建匿名 `SimpleFileVisitor` | 均以私有根目录/配额适配 JDK 回调，累计状态属于单次调用；没有外移或暴露状态，没有新增公开 API |

六次原生命令最终均退出 0，六份产物的外部检查均退出 0。
实际内容输出确认每次都读取了 CodeStack Skill 和 Java reference；未观察到读取其他三份 reference 正文，
或读取外部 oracle、操作说明和预期答案。普通任务没有显式点名插件或规则。
全量候选 `.agents` 树与原始快照一致，项目改动均在各自允许范围，README 及受保护输入未变。
新增或修改的手写声明沿用英文多行 Javadoc；没有为测试添加生产构造入口。

R32 的当前产物将累计字段置于新建匿名访客中，直接读取封闭实例的私有根目录和配额，
实现目录剪枝和文件计数两个 SDK 回调；访客只在该方法调用内存在。
这是具体协议和状态封装理由，不是因“类短”或“只有一个使用点”便允许嵌套业务结果。
R31/R32 历史运行及 R31 当前运行另增验证类，均在允许的 src Java 范围；
当前 R32 的验证类留在外部临时目录，只有生产扫描源码变化。

三组历史规则下也都满足目标，因此本轮没有展示规则改善幅度。
结果只支持“当前规则在这些任务中未强行复用、未破坏公开嵌套兼容性、未一律拒绝新嵌套”。
候选过程中的预期 RED、旧 R32 一次已修复的编译错误及 diff 的非零退出均保留在轨迹，
不计作新增有效 RED 或额外模型尝试。六次均有宿主开发中特性提示，但任务正常完成；未为消除提示修改配置。
候选自行声称的覆盖率不作为本轮外部验收证据。

## 4. 当前源码和本地门禁

`validate --all` 通过。CodeStack 入包源码哈希保持
`559abd868c86d0687b4e9514d1d6f65d48a71ce3b0836eece7a3f40cfe84527b`，
版本仍为 `0.1.0-preview.1`。三宿主重新构建并从可信仓库独立包检查通过，内容哈希均与上一轮一致：

| 宿主包 | 内容 SHA-256 |
| --- | --- |
| Claude | `bc8266ab3125485f9e6688487ba444b5959233490ef5281328c36ebad5c80b81` |
| Codex | `ef64e1c52be8b4fda0c45d16a3e091ddf13a07f2b59545735f55e1811b762f6f` |
| ZCode | `be9cbc9fb61366f06b19c396130210daaea9fe13b9fb2e3b991a5c8644552b2c` |

`npm test` 统一门禁六组全部通过，包括汇总器 13 项、公共 Python 320 项、
CodeVow 技能契约及 Python 324 项、委派插件 Python 35 项、CodeStack 9 项契约检查。
`npm run lint`、`check_no_dist.py`、`git diff --check` 通过。
补充文档的本地链接有效，新 fixture 未产生 class、jar 或 Python 缓存；
五份执行指令和中文 Java 规则稿与本轮开始时字节一致。

独立 Review 未发现确认可行动缺陷：审阅者独立重放 26 项校准及六份最终产物，
核对轨迹/产物哈希、18 个冻结评测文件、五份执行指令和实际调用/类型结构，
并复核本报告对历史/当前条件、单次 pilot、CodeVow/记忆环境及 pending 边界的表述。
独立日志保存在 `/private/tmp/codestack-contract-independent-review-4ak0zzep`。
统一门禁和三包检查由本轮主执行者完成，审阅者核阅结果，没有声称独立再跑全套门禁。

## 5. 证据位置与验收边界

本轮临时原始材料位于 `/private/tmp/codestack-contract-verification-srqs6m9f`：
`runs.json` 冻结任务和 seed 哈希，`old/`、`current/` 及对应 instruction-files 清单固定规则字节，
`evaluator/` 和 `evaluator-files.json` 固定 18 个判定器及输入文件。
`native-results.json` 保存实际命令、配置和退出状态，`outcomes.json` 绑定产物和轨迹哈希，
每个 run 保存实际 diff、外部检查日志及读取观察；校准和包索引分别保留。
机器本地路径仅供本轮复核，临时材料可能被清理，原始宿主日志不进入公开包。

| 原生轨迹 | events.jsonl SHA-256 |
| --- | --- |
| R30 历史 | `9587746884e582177006ce7ca7033a0876779c96b826b9261b831d37d496ead4` |
| R30 当前 | `13a39e08fad05fa913877f89289f57728004d971b78be713f170bfa83f905e96` |
| R31 历史 | `9199ffe160c24e6f1d531a5a16153d37de55637b32158184b95bf7f171a48687` |
| R31 当前 | `1eaf84d28ad0f6a610b3d772006769b7df5e650aac4fc9a01bbfefad43689d42` |
| R32 历史 | `623d86450485154d15b273c2d4dc3d9c1ce8626f49deb4d4e5a8867029933bb6` |
| R32 当前 | `142fcf88a8b3629bead281f71c9a3c01794711cb7e17d6ca51f914a2a6f6c97d` |

本轮新增三组单次 pilot；完整 R01—R32 矩阵、三次重复及三宿主原生安装验收仍 pending。
Codex 的临时源 Skill 发现和实际内容读取不能证明已安装插件的生命周期或其他宿主行为。
R30 没有模拟数据库事务或完整权限系统；R31 只覆盖冻结的既有公开客户调用；
R32 的必要性结论限于该 SDK 适配，不推广为允许嵌套业务 DTO 或 Spring Bean。
未因补充验收样例而修改发布配置或启动发行流程。
