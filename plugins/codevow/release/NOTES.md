# CodeVow release notes / CodeVow 发布说明

[English](#english) | [简体中文](#中文)

Current distribution uses the `ai-code` public main marketplace. Shared local
builds and Release download packages use `ai-code-local`; CodeVow's standalone
build helper uses `codevow-local`. See the
[installation guide](https://github.com/Zack-Zz/ai-code/blob/main/docs/installation.md).
The entries below retain their dated release context, including earlier migration plans.

## 1.0.7

### English

- Declare DeepSeek Harness `0.2.1-rc.2` as the minimum runtime (`>=0.2.1-rc.2`) and align DSH peer dependency ranges, so RC3 and later runtimes are no longer rejected by an exact RC2 requirement.
- Carry the minimum range through release validation and marketplace generation, with regression checks using the official DSH compatibility evaluator. Complete Desktop/Web runtime acceptance remains pending.

### 中文

- 将 DeepSeek Harness `0.2.1-rc.2` 声明为最低运行版本（`>=0.2.1-rc.2`），并统一 DSH peer 依赖范围，避免 RC3 及更高运行版本被精确 RC2 要求拒绝。
- 发行校验与市场生成保留最低版本范围，并使用 DSH 官方兼容性判定器补齐回归检查。完整 Desktop/Web 宿主运行验收仍待完成。

## 1.0.6

### English

- Unify the plugin identity as `codevow`. Uninstall `ai-code-workflow` through the host's native interface before installing `codevow`; retain project `.ai-workflow/` data and start a new session.
- Add a DeepSeek Harness bundle targeting `0.2.1-rc.2`, an independent official skill provider, and a native read-only Reviewer preset and spawn tool. Required Web-profile services must be available; host acceptance remains pending.
- Keep shared authorization and review contracts across hosts, with policy and execution detail in a reachable reference for long sessions. Python tools retain their existing project-data contract.
- Ground design and review concurrency findings in reachable execution chains, and assess protection responsibilities against existing guarantees, correctness, reliability and maintenance cost.

### 中文

- 插件身份统一为 `codevow`。先通过宿主原生界面卸载 `ai-code-workflow`，再安装 `codevow`；保留项目 `.ai-workflow/` 数据并开启新会话。
- 新增目标为 `0.2.1-rc.2` 的 DeepSeek Harness bundle、独立官方技能提供方，以及原生只读 Reviewer preset 和 spawn 工具。Web profile 必须提供所需服务，真实宿主验收仍待完成。
- 各端共享授权和审查合同；策略和执行细节转入明确可达的引用以支持长会话。Python 工具保持既有项目数据契约。
- 设计与审查中的并发问题须有可达执行链路；结合现有保障、正确性、可靠性和维护成本，核对各项保护机制的明确职责。

## 1.0.5

### English

- Require applicable user authorization and plan confirmation before the first project write, including tests, diagnostic files and delegated writes. Reuse an already confirmed scope without asking again for ordinary implementation details.
- Clarify mixed requests for advice and development, and keep workflow mode selection separate from implementation authorization.
- Document ZCode's workspace instruction entry and the distinction between CodeVow workflow modes and native execution modes.
- Add A34–A36 scenarios and strengthen A03 evidence requirements for confirmation boundaries.
- Real Claude Code, Codex and ZCode installation, upgrade, implicit selection and runtime behavior for these release bytes remain unverified.

### 中文

- 首次项目写入前检查适用的用户授权和方案确认，覆盖测试、诊断文件及委派写入；已有确认范围内的普通实现细节不重复询问。
- 明确同时包含咨询与开发意愿的请求如何处理，并区分工作流模式选择与实际开发授权。
- 补充 ZCode 工作区指令入口，区分 CodeVow 工作流模式与宿主原生执行模式。
- 增加 A34–A36 场景，并强化 A03 的首次写入确认边界证据要求。
- 本次发行字节在 Claude Code、Codex 和 ZCode 的真实安装、升级、自动选用及运行行为仍未验证。

## 1.0.4

### English

- Add lightweight guidance for native subagent collaboration: define task scope, coordinate overlapping writes, preserve others' changes, and inspect partial work before taking over interrupted tasks.
- Clarify that returned artifacts and the integrated result need verification; local passing tests and subagent completion messages alone do not establish delivery readiness.
- Respect existing host, role and model settings for independent review, while preserving authorization boundaries and risk-based review requirements.
- Add bilingual usage guidance and internal MA1–MA6 evaluation scenarios with a two-module integration fixture. Keep policy fields, management tools and host adapters unchanged.
- Real Claude Code, Codex and ZCode installation, upgrade and runtime acceptance for these release bytes remain unverified. Limited task probes do not establish a general improvement or host acceptance.

### 中文

- 为宿主原生子智能体协作补充轻量提醒：明确任务范围，协调重叠写入，保留他人修改，并在接管中断任务前核查已有工作。
- 明确需要核实返回产物及整合后的结果；局部测试通过和子智能体的完成消息不能单独证明可交付。
- 独立审查尊重已有宿主、角色及模型设置，同时保留授权边界和按风险触发审查的要求。
- 补充双语使用说明、内部 MA1–MA6 验收场景和两模块集成样例；保持策略字段、管理工具及宿主适配配置不变。
- 本次发行字节在 Claude Code、Codex 和 ZCode 的真实安装、升级及运行验收仍未完成；有限任务试跑不能证明普遍改善或宿主验收通过。

## 1.0.3

### English

- Add intent routing at workflow entry and direct skill entry points. Load rules when the current phase needs them, and check authorization before moving from analysis into development.
- Clarify collaborative and continuous modes, including which plans require confirmation and how existing user authorization carries forward.
- Shorten the Codex entry prompt to fit the native listing limit.
- Add repository tooling to preview and apply version and bilingual release-note updates while invalidating stale acceptance bindings and preserving private evidence and published history.
- Provide one GitHub build/publish entry with fixed plugin and operation choices. Publishing derives the canonical tag, verifies uploaded bytes and the Release page, and automatically synchronizes the stable marketplace; previews remain Release-only.
- Report host acceptance separately from technical publication readiness. Preserve immutable versions and support verified retries after partial publication or marketplace failures.
- Real Claude Code, Codex and ZCode installation, upgrade and runtime behavior for these bytes remain unverified; repository tests and package checks do not establish host acceptance.

### 中文

- 补齐工作流入口和技能直接入口的意图路由，按当前阶段读取规则，并在从分析转入开发前检查用户授权。
- 明确 collaborative 与 continuous 模式，说明哪些方案需要确认，以及已有用户授权如何继续生效。
- 缩短 Codex 入口提示，满足原生发布清单的长度限制。
- 增加仓库发版准备工具，预览并应用版本和中英说明，明确使旧验收绑定失效，同时保留私有材料和已发布历史。
- 统一 GitHub 构建/发布入口，仅选择插件和操作；发布时自动派生规范标签、核对上传字节与 Release 页面，并自动同步正式市场，预览版只公开 Release。
- 将宿主实测与技术发布就绪分别报告，保持公开版本不可变，支持发布或市场更新部分失败后的核验重试。
- 本版本在 Claude Code、Codex 与 ZCode 的真实安装、升级和运行行为仍未验证；仓库测试和包检查不能代表宿主验收通过。

## 1.0.2 — 2026-10-08 candidate

- Prepares GitHub marketplace distribution with schema 2 release bundles and separate plugin-only native installer ZIPs, including artifact.json.
- Provides local-market download ZIPs and separate submission source kits.
- Adds local distribution plans for independent plugin releases and channel-specific market sources: Claude archive, ZCode ZIP URL/path, and Codex version directories pinned to a distribution commit.
- Separates draft preparation, human Publish and reviewed marketplace deployment. Plans bind release assets and the previous market snapshot; deployment preserves other plugins and immutable old version directories.
- Keeps the candidate in preview with all native transport, installation, upgrade and workflow behavior acceptance unverified. Existing dist and ai-code-local entry points remain available until the new native transports pass acceptance.
- Records no remote Release, marketplace deployment or host acceptance result in these notes. Dated 1.0.1 verification remains historical evidence for its own bytes.

## 1.0.1 — 2026-10-08

- Accepts Claude Code, Codex and ZCode in task host-run evidence and evaluation input contracts while preserving conservative results for unverified runs.
- Prepares A23/A24/A25 package fixtures for every host declared by this plugin; A23/A24 exercise the selected package's file staging, update, removal and recovery tools.
- Extends A25 to verify every declared host package, source metadata and all common resources, including licenses and shared reviewer content where applicable.
- A25 compares complete reviewer bodies and checks source drift.
- Rebuilds the three host distributions and repository marketplace entries from the current source at version 1.0.1.
- Keeps native installation, skill invocation, model behavior and reviewer enforcement unverified. File staging and package parity are separate from real-host acceptance.

## 1.0.0 — initial preview

- Starts CodeVow at 1.0.0 after the maintainer confirmed the new plugin had not been installed.
- Provides declarative packages for Claude Code, Codex and ZCode from the same six skill sources.
- Adds publisher-derived native metadata, a PNG listing icon with an SVG alternative and portable package guides.
- Preserves collaboration policies, workspace-bound task records, evidence checks and owned-file protection.
- Adds native repository marketplace entry points for self-hosted preview distribution.
- All native host acceptance remains unverified; package checks and script tests do not establish runtime acceptance.

The release version, source identity and package hashes are supplied by the release builder.
