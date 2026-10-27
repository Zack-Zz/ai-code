# CodeStack

[English](README.md) | 简体中文

当前新 ID `codestack` 是尚未发布的源码候选。线上入口仍以 `published/` 中旧 ID 的已发布快照为准；本页的新安装命令须在新发行上线后使用。

<img src="assets/codestack.png" alt="CodeStack 图标" width="96" />

CodeStack 为编码助手提供多个语言和技术栈中精选的项目规范，当前覆盖 Java 写法、
SQL/JPA/MyBatis 易错点及前端共享的多语言文案组织约定。插件 ID 为
`codestack`。正式版通过同一个 `ai-code` 市场分发，
可安装版本以[当前发行记录](https://github.com/Zack-Zz/ai-code/blob/main/published/index.json)为准。

## 使用

通过宿主原生插件机制安装、启用后，直接描述普通开发或审查任务：

- “为已有 Java 类增加这个字段和访问方法。”
- “沿用生产构造方式，为这个服务增加测试。”
- “修复订单列表逐条查询客户信息的问题。”
- “审查这份 MyBatis Mapper 与 XML 的参数绑定。”
- “为这个支持多语言的 React 页面增加确认弹窗和操作反馈。”
- “审查这个多语言 Vue 表单的校验提示文案。”

`code-standards` 技能以相关任务自动选用为目标，也可以在需要时显式调用。
原生发现和实际行为需要在宿主中验证，安装成功不代表每次任务都会使用技能。
按[安装指南](https://github.com/Zack-Zz/ai-code/blob/main/docs/installation.zh-CN.md)
从 `ai-code` 市场选择 `codestack`，各插件分别安装。CodeStack 可以独立于 CodeVow 与 Agent Delegation 使用，无需依赖这两个插件。

## 具体要求

- 注释语言按用户要求、项目或模块语言、宿主或系统语言的顺序选择；英文规则不强制英文注释。
- 手写字段、方法、构造函数和参数完整写多行 Javadoc；方法内只注释核心逻辑。
- 特殊测试实例在测试类内部准备，不增加生产代码中的测试专用构造函数或变相入口。
- 优先复用适用的已有实现，同一业务规则集中维护；语义不同的实现保持独立。
- 业务类型和 Spring 组件优先顶级类型，确有具体必要性才保留嵌套，不迁移无关历史代码。
- SQL 访问有边界，禁止逐条查询及懒加载、并行或缓存兜底中的隐藏变体；成本结论需要相应证据。
- 按本次实际机制选择 JPA、MyBatis 规则，可以同时应用；MapStruct Mapper 或无关 XML 不代表 MyBatis。
- 前端产品已经支持或明确要求多语言时，本次涉及的固定用户可见文案必须收敛到独立、统一维护的语言资源区域，页面、组件和动作通过 key 引用。覆盖标签、占位符、可访问性文案、弹窗、校验和反馈；动态业务数据保持为数据。资源可以沿用既有国际化方案，按语言或业务域拆分。

前端约定由 JavaScript/TypeScript、React、Vue 等技术栈共用。单语言产品、仅涉及后端的
TypeScript 任务和不涉及文案的改动不因此引入国际化要求；Java 约定不泛化到前端代码。
没有额外获批规则时，不建立独立的 TypeScript、React 或 Vue 规则引用。

执行内容只有一个英文技能及按需读取的英文规则，不要求项目新增配置、AGENTS 指令、
运行时、Hook 或独立 Agent。沿用当前任务的工作流、工具与依赖；审查请求按授权范围报告发现。
本插件不提供排版规则、通用教程或超出明确支持范围的规则。这些是明确采用的项目约定；
行为改善和宿主自动选择需要实测证据，不能从规则文件存在推导。

## 资源与许可证

- [技能入口](skills/code-standards/SKILL.md)
- [Java](skills/code-standards/references/java.md)、[数据访问](skills/code-standards/references/data-access.md)、[JPA](skills/code-standards/references/jpa.md)、[MyBatis](skills/code-standards/references/mybatis.md)、[前端](skills/code-standards/references/frontend.md)
- [评测用例](evals/cases.md)：仅用于源码评测的输入和验收标准

执行资源按显式白名单打包，包括技能、规则、图标与许可证，并附带可移植的中英 README。
评测输入不进入安装包。正式发布与真实宿主验收分别报告。

[MIT](LICENSE)，维护者 Zack-Zz。

## DeepSeek Harness

DSH 原生 bundle 声明目标为 `0.2.1-rc.2`，实际加载、自动选择、长会话和生命周期验收仍待完成。
使用现有 Web profile，按官方方式安装构建目录或 Release 的 `codestack-<version>-dsh-plugin.tgz`；
构建和包检查不能代替宿主验收。技能使用官方 `/code-standards` 显式调用。两个插件通过各自的官方文件系统提供方读取包内资源，启停互不替代。

身份变更的卸载和重装步骤见[本次迁移说明](https://github.com/Zack-Zz/ai-code/blob/main/plugins/codestack/docs/2026-10-27-identity-migration.zh-CN.md)。
