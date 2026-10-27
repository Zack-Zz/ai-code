# 安装与验证记录

日期：2026-09-18，Asia/Shanghai。

## 2026-09-19：开发计划须先经用户确认

已将用户明确要求同步到全局规则、源码模板和项目模板：所有开发任务（包括 QUICK、紧急修复）先只读调查、梳理需求和现状，列出目标/范围、拟改模块/文件、实施步骤、TDD/验证和风险，等待明确确认后才开始写测试、改代码或配置。已有确认的适用计划无需重复询问；实质性范围或方案变更先更新计划并确认。计划确认不包含提交或推送授权。

此规则明确优先于插件 0.1.1 的 QUICK 可省计划等默认流程，插件未变，无需更新。20 项安装/静态检查通过，安装后预检查无变更，已读取实际全局文件核对；备份为 `~/.zcode/AGENTS.md.bel-backup-csxiqb6b`。本次仅落实用户明确要求的规则修改，未提交或推送，未验证真实 GLM 会话遵循效果。

## 2026-09-19：先交用户 Review，再按明确授权提交

已更新全局托管规则、规则源码及项目模板：默认保留未提交改动，交付摘要、关键文件/diff、验证与风险并标记待用户 Review；Agent 审查不能替代用户 Review。未明确授权不得 commit/amend、push、合并或创建 PR，也不得委托脚本/子代理代做。Review 通过不自动授权提交，commit 授权不包含 push，已有本次明确授权无需重复询问。

20 项现有安装/静态检查通过；全局安装后的预检查 `changed: false`，已读取实际文件核对。备份为 `~/.zcode/AGENTS.md.bel-backup-jf_7ozsf`。插件内容未变，仍为 0.1.1，无需重新安装；这是全局指令约束，未验证 GLM 实际遵循效果。本次未 commit 或 push。

## 最新状态：用户完成插件安装后复核

- 已确认 `backend-engineering-lite@backend-engineering-local` 版本 **0.1.1**，`enabled=true`，来源为本地市场安装缓存。包中 8 个文件（清单、许可证、5 个 Skills、1 个 Reviewer）逐个与维护源码校验一致。
- 安装后的第一次检查发现 5 个技能同时出现在用户级目录和插件目录。已通过带哈希保护的管理工具备份并移除 6 个旧组件，备份在 `~/.zcode/bel-backups/components-204cnvp2/`，保留全局 `~/.zcode/AGENTS.md` 中 TDD/Review 规则。
- 清理后 CLI 确认恰好 5 个 bel 技能，全部 `source=plugin`，名称无重复，技能 diagnostics 为空；更新了 [发现记录](skill-discovery.json)。再次组件移除预检查无变更，规则与模板一致。
- 插件内 Reviewer 文件与源文件一致，但仍未实际运行独立 Reviewer 或 GLM 开发会话；不把插件发现成功当作模型遵循规则的证明。内置 document-skills 的 `ZCODE_BASE_URL` 诊断与本插件无关，未改动。

下文为此前安装及排查历史，其中“未注册插件”的状态已被以上复核结果取代。

## 环境和改动范围

- macOS 26.6.2；`/Applications/ZCode.app` 版本 3.12.3（build 3.12.3.7463）。
- 随包 CLI：`/Applications/ZCode.app/Contents/Resources/glm/zcode.cjs`，版本 0.16.5；本地 Python 3.13、Node 22 可用。
- 当前 ai-mcp 是 TypeScript MCP 业务仓库，初始工作区无未提交变更。仅新增独立的 `zcode-workflow/`，未修改业务代码或根级项目规则，未提交或推送。
- 原先没有 `~/.zcode/AGENTS.md`、`~/.zcode/skills` 或 `~/.zcode/agents`。本次新增规则、5 个 Skills、1 个 Reviewer 和自有组件哈希清单。
- CLI 实际插件列表只有原有 8 个内置插件，没有 Superpowers，也没有 backend-engineering-lite 的插件安装记录。新组件只通过用户级原生入口加载。
- 现有插件配置备份：`~/.zcode/bel-backups/20260918-233103/`。备份了 config.json 和 known_marketplaces.json；未编辑这些配置或插件缓存。

## 已通过

1. 两个安装/回滚工具先写测试、对占位实现运行并观察预期功能断言失败，再实现并跑绿。最终 `python3 -m unittest discover -s zcode-workflow/tests -v`：**20 项通过**。
2. 测试覆盖原文保留、备份、幂等、中文/空格路径、无副作用预检查、保留用户后续内容、托管内容被修改时拒绝覆盖、符号链接拒绝、异常编码、清单/版本/frontmatter/引用和 Reviewer 工具白名单。包静态检查不等于桌面实际启用。
3. 用户规则和原生组件实际安装成功；再次检查返回 `changed: false`。安装后 6 个组件与源码哈希一致。无 Hook、MCP 或后台服务新增。
4. **ZCode 自带 CLI 实际发现 5 个 bel Skills，scope=user/source=zcode，diagnostics=[]，没有同名重复。** 原始筛选结果见 [evidence/skill-discovery.json](skill-discovery.json)。命令：

   ```sh
   node '/Applications/ZCode.app/Contents/Resources/glm/zcode.cjs' skills list --json
   ```

5. 有限的 Codex 行为推演：基线对“一行映射变更”和“紧急鉴权修复”没有明确先 RED；读取新规则后，这两项明确先失败测试，缺依赖时暂停依赖 RED 的正式实现。另检查了用户修改保护、验证后修改、上下文不足的审查、只读解释和纯重构。**不是 GLM/ZCode 模型实测，不据此宣称自动触发稳定。**
6. 已复制一次性示例项目并运行基线：3 项测试通过。目录：`/var/folders/sn/vgw15ftd0tq_gxv6smkn59qw0000gn/T/bel-acceptance-2av9pspr`。这些基线测试故意不覆盖后续待修复的租户漏洞，不证明授权逻辑完整。

## 实际遇到的限制

- 桌面控制的 AX 控件树与截图不同步，出现失效控件 ID 和 noWindowsAvailable。没有可靠完成市场注册/插件安装，不把设置页中间状态当作安装成功。
- 使用随包 CLI 发起限轮数只读会话，最初报“无法定位 CLI ZCode Built-in Provider Config”。随后从本机 CLI 源码核实 `ZCODE_BUILTIN_PROVIDER_CONFIG_FILE`，仅对该进程指定应用已有的 `Resources/config/provider/zcode-builtin.json`，没有永久修改模型配置。
- 路径问题消除后，CLI 报 `Unknown option '--allowed-tools'`，尽管自己的 `--help` 列出了该选项。未移除计划中的工具限制去继续执行，未把失败当成会话验证通过，也未修补应用安装目录。
- 本机配套指南称部分插件 agent 字段只登记，而在线文档描述支持插件 Agent。本次采用明确支持的 `~/.zcode/agents/` 原生入口，避免依赖尚未实测的插件内 Agent 机制。

## 0.1.1 Review 约束更新

- 已同步用户规则、task-flow/backend-review/verification 三个技能与只读 Reviewer。CRITICAL 可调用时必须实际调用独立审查；不可用/失败时报告原因、自查范围与未覆盖部分。确认严重问题未解决时不得宣称完成，修复后必须复验。
- 20 项安装工具和静态配置测试再次通过；安装后两项预检查均 `changed: false`。规则备份：`~/.zcode/AGENTS.md.bel-backup-g0jpx80r`；组件备份：`~/.zcode/bel-backups/components-cdkwpslk/`。
- 更新前的 Codex 推演指出旧规则存在可选语气和缺少明确完成门槛，但没有实际复现错误行为。更新后检查赶工跳过、严重缺陷未修复、无子代理、普通建议/未知风险四类场景，未发现规则冲突。这仍不是 GLM/ZCode 实测。
- 再次尝试桌面“插件市场”，控件状态变化但截图仍在首页，坐标点击报 `noWindowsAvailable`。读取本机 CLI 分发代码确认 plugins 子命令只有 list/enable/disable/uninstall，没有 install/add。未直接改写内部注册文件。
- CLI 再次发现 5 个用户级 bel 技能，技能 diagnostics 为空；插件列表仍只有原有 8 个，没有本插件。插件列表另外报告内置 document-skills 缺少 `ZCODE_BASE_URL`，与 bel 技能发现结果分开记录，未擅自修改。

## 待用户验证

1. 在桌面 ZCode 设置 → 技能刷新，确认 5 个 bel 技能；设置 → 子智能体确认 bel-backend-reviewer 继承模型、只读工具白名单。
2. 新建 GLM-5.3 会话，在临时示例中请求“给 label 增加 code=2 对应 fault”，观察是否先写失败测试、后实现并跑绿。可先从 `/` 技能菜单手动选择 bel-task-flow/bel-tdd，再单独验证自动触发。
3. 按 [ACCEPTANCE.md](ACCEPTANCE.md) 完成其余场景和 Reviewer 实际工具边界验收。未确认桌面会话已注入全局规则，也未确认模型始终执行 TDD。

停用、回滚和可选的插件模式迁移见 [README.md](README.md)。用户级规则独立于插件/技能开关；完整回滚应同时移除组件和托管规则。
