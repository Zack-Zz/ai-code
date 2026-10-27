# CodeStack release notes / CodeStack 发布说明

[English](#english) | [简体中文](#中文)

Stable releases use the shared `ai-code` marketplace. Versions and availability
are recorded in the [release index](https://github.com/Zack-Zz/ai-code/blob/main/published/index.json).

## 1.0.1

### English

- Declare DeepSeek Harness `0.2.1-rc.2` as the minimum runtime (`>=0.2.1-rc.2`) and align DSH peer dependency ranges, so RC3 and later runtimes are no longer rejected by an exact RC2 requirement.
- Carry the minimum range through release validation and marketplace generation, with regression checks using the official DSH compatibility evaluator. Complete Desktop/Web runtime acceptance remains pending.

### 中文

- 将 DeepSeek Harness `0.2.1-rc.2` 声明为最低运行版本（`>=0.2.1-rc.2`），并统一 DSH peer 依赖范围，避免 RC3 及更高运行版本被精确 RC2 要求拒绝。
- 发行校验与市场生成保留最低版本范围，并使用 DSH 官方兼容性判定器补齐回归检查。完整 Desktop/Web 宿主运行验收仍待完成。

## 1.0.0

### English

- Unify the plugin identity as `codestack`. Uninstall `ai-code-stack-standards` through the host's native interface before installing `codestack`, then start a new session.
- Add a declarative DeepSeek Harness bundle targeting `0.2.1-rc.2`, using an independent official skill-filesystem provider with no custom JavaScript runtime. Native host acceptance remains pending.
- Split the shared Java rules into shorter linked references while preserving comment, test-construction, reuse and type-placement requirements for all hosts.

### 中文

- 插件身份统一为 `codestack`。先通过宿主原生界面卸载 `ai-code-stack-standards`，再安装 `codestack`，并开启新会话。
- 新增目标为 `0.2.1-rc.2` 的声明式 DeepSeek Harness bundle，使用独立官方技能文件系统提供方，不新增自定义 JavaScript 运行逻辑。真实宿主验收仍待完成。
- 将共享 Java 规则拆为较短且明确关联的引用，保留各端的注释、测试构造、复用和类型放置要求。

## 0.1.0

### English

- Introduce CodeStack as an independent plugin in the shared ai-code stable marketplace for Claude Code, Codex and ZCode.
- Provide one skill that selects relevant Java, SQL/data-access, JPA, MyBatis and multilingual frontend copy conventions from the actual task and stack.
- Keep rule selection instruction-based, preserve existing project mechanisms and authorization, and add no runtime, hooks, agents or plugin dependencies.
- Include the CodeStack icon and portable English and Chinese guides, with complete release configuration and independently verified host installer packages.
- Strengthen the frontend evaluation oracle to reject a valid invitation that bypasses explicit false confirmation; hand-authored calibration controls are not model outcomes.
- Real host installation, upgrade, implicit selection and task outcomes for these release bytes remain unverified. Package and fixture checks do not establish model improvement.

### 中文

- 首次将 CodeStack 作为独立插件接入同一个 ai-code 正式市场，提供 Claude Code、Codex 和 ZCode 三宿主包。
- 通过单个技能，按实际任务和技术栈选读 Java、SQL/数据访问、JPA、MyBatis 及多语言前端文案约定。
- 保持指令式规则选择，沿用项目现有机制和授权边界，不增加运行时、Hook、Agent 或插件依赖。
- 附带 CodeStack 图标和可移植的中英说明，补齐发行配置，并独立检查三宿主安装包。
- 加强前端评测检查器，拒绝合法邀请显式传入 false 时绕过确认的实现；手写校准控制不代表模型成绩。
- 本次发行字节的真实宿主安装、升级、自动选用及任务结果仍未验证；包检查和样例检查不证明模型效果改善。
