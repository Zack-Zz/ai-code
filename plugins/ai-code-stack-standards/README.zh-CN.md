# CodeStack

[English](README.md) | 简体中文

CodeStack 为编码助手提供明确的 Java 写法及持久化易错点提醒，插件 ID 为
`ai-code-stack-standards`。当前为开发预览，尚未发布到正式市场。

## 使用

通过宿主原生插件机制安装、启用后，直接描述普通 Java 开发或审查任务：

- “为已有 Java 类增加这个字段和访问方法。”
- “沿用生产构造方式，为这个服务增加测试。”
- “修复订单列表逐条查询客户信息的问题。”
- “审查这份 MyBatis Mapper 与 XML 的参数绑定。”

`code-standards` 技能以相关任务自动选用为目标，也可以在需要时显式调用。
原生发现和实际行为需要在宿主中验证，安装成功不代表每次任务都会使用技能。
本地包与试用方式见仓库[开发指南](../../CONTRIBUTING.zh-CN.md)，
仓库[安装指南](../../docs/installation.zh-CN.md)列出发行记录与市场来源，当前预览尚未列入
正式市场。CodeStack 可以独立于 CodeVow 与 Agent Delegation 使用，无需依赖这两个插件。

## 具体要求

- 注释语言按用户要求、项目或模块语言、宿主或系统语言的顺序选择；英文规则不强制英文注释。
- 手写字段、方法、构造函数和参数完整写多行 Javadoc；方法内只注释核心逻辑。
- 特殊测试实例在测试类内部准备，不增加生产代码中的测试专用构造函数或变相入口。
- 优先复用适用的已有实现，同一业务规则集中维护；语义不同的实现保持独立。
- 业务类型和 Spring 组件优先顶级类型，确有具体必要性才保留嵌套，不迁移无关历史代码。
- SQL 访问有边界，禁止逐条查询及懒加载、并行或缓存兜底中的隐藏变体；成本结论需要相应证据。
- 按本次实际机制选择 JPA、MyBatis 规则，可以同时应用；MapStruct Mapper 或无关 XML 不代表 MyBatis。

执行内容只有一个英文技能及按需读取的英文规则，不要求项目新增配置、AGENTS 指令、
运行时、Hook 或独立 Agent。沿用当前任务的工作流、工具与依赖；审查请求按授权范围报告发现。
本预览不提供 Java 排版规则、通用教程或其他语言的规则库。

## 资源与许可证

- [技能入口](skills/code-standards/SKILL.md)
- [Java](skills/code-standards/references/java.md)、[数据访问](skills/code-standards/references/data-access.md)、[JPA](skills/code-standards/references/jpa.md)、[MyBatis](skills/code-standards/references/mybatis.md)
- [评测用例](evals/cases.md)：仅用于源码评测的输入和验收标准

执行资源按显式白名单打包，仅包括技能、规则与许可证；人类使用说明和评测输入不进入执行包。
发行工作流接入与公开发布是本地预览开发之外的步骤。

[MIT](LICENSE)，维护者 Zack-Zz。
