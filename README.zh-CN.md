# ai-code

[![Stars](https://img.shields.io/github/stars/Zack-Zz/ai-code?style=flat)](https://github.com/Zack-Zz/ai-code/stargazers)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Shell](https://img.shields.io/badge/-Shell-4EAA25?logo=gnu-bash&logoColor=white)
![TypeScript](https://img.shields.io/badge/-TypeScript-3178C6?logo=typescript&logoColor=white)
![Go](https://img.shields.io/badge/-Go-00ADD8?logo=go&logoColor=white)
![Markdown](https://img.shields.io/badge/-Markdown-000000?logo=markdown&logoColor=white)

---

<div align="center">

**🌐 Language / 语言**

[**English**](README.md) | [简体中文](README.zh-CN.md)

</div>

---

**面向 ChatGPT、Codex、Claude 等主流 AI 开发助手的多平台实用配置集合。**

生产级代理、技能、钩子、命令、规则和 MCP 配置，经过 10 多个月构建真实产品的密集日常使用而演化。

---

## 项目定位

`ai-code` 是一个面向多助手协同的配置仓库，不只针对 Claude。

- ChatGPT/Codex：`AGENTS.md` + `.codex/config.toml` + `.codex/codex.md`
- Claude Code：插件/规则/钩子工作流
- Cursor/OpenCode：兼容配置和命令体系
- 多语言工作流：TypeScript/JavaScript、Java、Python、Go、Rust

---

## 使用文档索引

- 入门必读：[快速开始](#-快速开始)、[使用介绍](#使用介绍)、[跨平台支持](#-跨平台支持)
- Bootstrap 与同步：[`scripts/bootstrap-project.sh`](scripts/bootstrap-project.sh)、[`scripts/sync-project.sh`](scripts/sync-project.sh)、[`scripts/sync-codex-global-config.sh`](scripts/sync-codex-global-config.sh)
- 工具专章：[Codex GUI 适配（多语言）](#codex-gui-适配多语言)、[Kiro 集成指南](docs/KIRO_INTEGRATION.md)、[Claude 插件工作流](.claude-plugin/README.md)
- 规则与命令：[规则总览](rules/README.md)、[`commands/` 命令目录](commands)、[`agents/` 代理目录](agents)
- 技能体系：[`skills/` 技能目录](skills)、[技能生成命令](commands/skill-create.md)
- 进阶文档：[用法细节](docs/USAGE.md)、[Token 优化](docs/token-optimization.md)、[示例集合](examples)
- 中文文档入口：[中文总览](docs/zh-CN/README.md)、[中文规则](docs/zh-CN/rules/README.md)、[中文命令](docs/zh-CN/commands)

---

## 使用介绍

- 先选择你要用的助手栈：Codex/ChatGPT、Claude Code，或 Cursor/OpenCode。
- 在 `AGENTS.md` 维护项目级指令，按语言再补充具体工作流。
- 建议从 `.codex/codex.md` 启动并坚持先测后改（TDD）。
- 按需启用目录（`agents/`、`skills/`、`rules/`、`commands/`），避免一次性全量接入。

### 组件适配矩阵（Claude / Codex / Kiro）

状态说明：
- 原生：该助手会直接加载/执行
- 参考：可作为指引使用，但不是原生执行能力
- 不支持：该助手不直接消费

| 组件 | 主要作用 | Claude Code | Codex | Kiro |
|------|----------|-------------|-------|------|
| `commands/` | 斜杠命令工作流（`/tdd`、`/plan` 等） | 原生 | 不支持 | 不支持 |
| `rules/` | 始终遵循的编码/安全/测试规则 | 原生 | 不支持 | 不支持（改用 `.kiro/steering/`） |
| `skills/*/SKILL.md` | 可复用的工作流知识 | 原生 | 原生（通过项目 `.agents/skills/`） | 参考 |
| `skills/*/agents/openai.yaml` | Codex 技能自动识别元数据 | 不支持 | 原生 | 不支持 |
| `agents/` | 专项子代理角色说明 | 原生 | 参考 | 参考 |
| `hooks/` + `scripts/hooks/` | 事件触发自动化 | 原生 | 不支持（Codex CLI 暂无 hooks） | 不支持（使用 `.kiro/hooks/hooks.json`） |
| `.codex/*` | Codex 配置与会话引导 | 参考 | 原生 | 参考 |
| `.kiro/steering/*` + `.kiro/hooks/*` + `.kiro/settings/mcp.json` | Kiro 的 steering/hooks/MCP 集成 | 参考 | 参考 | 原生 |
| `mcp-configs/` | MCP 模板集合（主要面向 Claude 风格配置） | 原生/参考 | 参考（Codex 使用 `.codex/config.toml`） | 参考（Kiro 使用 `.kiro/settings/mcp.json`） |

### Bootstrap 映射（`scripts/bootstrap-project.sh`）

| `--tool` 模式 | 会复制的能力 |
|---------------|--------------|
| `claude` | `global-first`：`CLAUDE.md`、`.claude/package-manager.json`；`project-full`：额外复制 `agents/`、`commands/`、`rules/`、`hooks/`、`scripts/hooks`、`scripts/lib` |
| `codex` | `global-first`：`.codex/codex.md`、`.codex/AGENTS.md`（可选 `.codex/config.toml`）；`project-full`：额外复制选定 `.agents/skills/*` |
| `kiro` | `global-first`：`.kiro/steering/ai-code-core.md`；`project-full`：额外复制完整 steering/hooks/settings/docs |
| `both` | 同时复制 Codex + Kiro 资产 |
| `all` | 同时复制 Codex + Kiro + Claude 资产 |

`--layout` 模式：
- `global-first`（默认）：仅同步项目入口文件；`commands/rules/hooks/skills` 维持全局维护。
- `project-full`：同步完整项目内资产。

当 `--langs` 包含 `go` 时，还会额外复制与工具无关的 Go 约束模板：
`Makefile`、`.golangci.yml`、`.github/workflows/go-ci.yml`（不会影响非 Go 语言项目）。

### 统一运行时配置（Codex + Claude）

Hook/Session 脚本支持统一环境变量：

```bash
export AI_CODE_TOOL=codex      # codex | claude
export AI_CODE_HOME=/path/to/assistant-home
```

- `AI_CODE_HOME` 优先级最高。
- 未设置 `AI_CODE_HOME` 且 `AI_CODE_TOOL=codex` 时，默认目录是 `~/.codex`。
- 其他情况默认目录是 `~/.claude`。
- 也可对单次执行使用 `--tool`、`--home` 参数。

---

## 🚀 快速开始

### 一键 Bootstrap（新项目）

```bash
scripts/bootstrap-project.sh --target /path/to/your-project --langs js
scripts/bootstrap-project.sh --target /path/to/your-project --langs java,python,go
# 可选 tool 模式：--tool auto|codex|kiro|claude|both|all
# auto 只会选择一个工具（优先已有目录，其次 AI_CODE_TOOL，否则 codex）
# 可选 layout 模式：--layout global-first|project-full（默认：global-first）
# both = codex + kiro，all = codex + kiro + claude
# 可选复制项目级 codex 配置：
# scripts/bootstrap-project.sh --target /path/to/your-project --langs js --tool codex --copy-codex-config
# 使用 manifest 回放并覆盖更新：
# scripts/sync-project.sh --target /path/to/your-project
# 更新全局 Codex 配置参考（安全默认，不覆盖 active config）：
# scripts/sync-codex-global-config.sh
# 仅在需要时显式覆盖 active config：
# scripts/sync-codex-global-config.sh --apply-config
```

### 方案 1：Codex / ChatGPT（推荐）

```bash
git clone https://github.com/Zack-Zz/ai-code.git
cd ai-code
scripts/sync-codex-global-config.sh
# 默认仅更新 ~/.codex/config.toml.reference
# 如需覆盖 ~/.codex/config.toml，请显式加 --apply-config
```

在 Codex GUI 中打开仓库，首条消息建议：
`请先阅读 /.codex/codex.md，并按多语言工作流执行`

### 方案 2：Claude Code

```bash
git clone https://github.com/Zack-Zz/ai-code.git
cd ai-code
./install.sh typescript python golang
# 或直接对目标项目执行 bootstrap：
# scripts/bootstrap-project.sh --target /path/to/project --langs java --tool claude
# 全量同步到项目目录：
# scripts/bootstrap-project.sh --target /path/to/project --langs java --tool claude --layout project-full
```

### 方案 3：Cursor / OpenCode

- Cursor：使用 `.cursor/`，可配合 `./install.sh --target cursor ...`
- OpenCode：在仓库根目录运行并加载 `.opencode/` 配置

### 方案 4：Kiro GUI

```bash
git clone https://github.com/Zack-Zz/ai-code.git
cd ai-code

# 为新项目引导 Kiro 支持
scripts/bootstrap-project.sh --target /path/to/your-project --langs java,python --tool kiro
# 全量同步到项目目录：
# scripts/bootstrap-project.sh --target /path/to/your-project --langs java,python --tool kiro --layout project-full

# 或直接使用本仓库
# 在 Kiro 中打开该目录 - steering 文件自动加载
```

**默认安装内容（`global-first`）：**
- `.kiro/steering/ai-code-core.md`（项目入口文件）

**`--layout project-full` 额外内容：**
- `.kiro/steering/` 全套 steering（核心原则、安全、TDD、编码标准）
- `.kiro/hooks/hooks.json` Hooks 配置（自动格式化、安全检查）
- `.kiro/settings/mcp.json` MCP 模板（文件系统、GitHub、PostgreSQL、搜索）

**后续步骤：**
1. 在 Kiro 中打开项目 - steering 文件自动加载
2. 配置 `.kiro/settings/mcp.json` 中的 MCP 服务器（将 `YOUR_*_HERE` 替换为实际 API 密钥）
3. 查看 `.kiro/hooks/hooks.json` 中的 hooks（fileEdited、promptSubmit、agentStop）

详细的 Kiro 配置指南请参阅 [`.kiro/README.md`](.kiro/README.md)。

### 各工具单独维护（Global-First）

- Codex：可复用资产维护在 `~/.codex`（或 `AI_CODE_HOME`），项目内保持最小入口（`AGENTS.md`、`.codex/*`）。
- Claude：`commands/`、`rules/`、`hooks/`、`skills/` 维护在全局目录，项目默认仅保留入口文件。
- Kiro：共享 steering/hook/MCP 模板维护在全局来源，项目默认仅保留 `.kiro/steering/ai-code-core.md`。

当仓库需要完全自包含（离线、交接）时，使用 `--layout project-full`。

---

## Codex GUI 适配（多语言）

本仓库已补充 Codex GUI 可直接使用的配置与会话模板，适合 TypeScript/JavaScript、Java、Python、Go、Rust 项目。

### 快速开始

```bash
# 1) 首次配置 Codex
scripts/sync-codex-global-config.sh
# 默认仅更新 ~/.codex/config.toml.reference
# 如需覆盖 ~/.codex/config.toml，请显式加 --apply-config

# 2) 在 Codex GUI 中打开本仓库
# 3) 首条消息建议：
#    "请先阅读 /.codex/codex.md，并按多语言工作流执行"
```

### 已包含内容

- `.codex/config.toml`：Codex CLI/GUI 通用配置（权限、MCP、持久指令）
- `.codex/AGENTS.md`：Codex 专用补充指引（含多语言默认流程）
- `.codex/codex.md`：Codex GUI 会话启动模板（测试优先、安全优先、验证命令）

---

## 🌐 跨平台支持

该工具集现在完全支持 **Windows、macOS 和 Linux**。所有钩子和脚本都已用 Node.js 重写，以实现最大的兼容性。

### 包管理器检测

在 Claude Code 工作流中，包管理器检测优先级如下：

1. **环境变量**: `AI_CODE_PACKAGE_MANAGER`（向后兼容 `CLAUDE_PACKAGE_MANAGER`）
2. **项目配置**: `.claude/package-manager.json`
3. **package.json**: `packageManager` 字段
4. **锁文件**: 从 package-lock.json、yarn.lock、pnpm-lock.yaml 或 bun.lockb 检测
5. **全局配置**: `$AI_CODE_HOME/package-manager.json`
6. **回退**: `npm`

要设置你首选的包管理器：

```bash
# 通过环境变量
export AI_CODE_PACKAGE_MANAGER=pnpm

# 通过全局配置
node scripts/setup-package-manager.js --global pnpm

# 通过项目配置
node scripts/setup-package-manager.js --project bun

# 检测当前设置
node scripts/setup-package-manager.js --detect
```

或在 Claude Code 中使用 `/setup-pm` 命令。

---

## 📦 里面有什么

这个仓库是一个 **多助手工具集**，包含 Claude Code 插件资产、Codex 配置和 Kiro steering 文件。

```
ai-code/
|-- .claude-plugin/   # 插件和市场清单
|   |-- plugin.json         # 插件元数据和组件路径
|   |-- marketplace.json    # /plugin marketplace add 的市场目录
|
|-- agents/           # 用于委托的专业子代理
|   |-- planner.md           # 功能实现规划
|   |-- architect.md         # 系统设计决策
|   |-- tdd-guide.md         # 测试驱动开发
|   |-- code-reviewer.md     # 质量和安全审查
|   |-- security-reviewer.md # 漏洞分析
|   |-- build-error-resolver.md
|   |-- e2e-runner.md        # Playwright E2E 测试
|   |-- refactor-cleaner.md  # 死代码清理
|   |-- doc-updater.md       # 文档同步
|   |-- go-reviewer.md       # Go 代码审查（新增）
|   |-- go-build-resolver.md # Go 构建错误解决（新增）
|
|-- skills/           # 工作流定义和领域知识
|   |-- coding-standards/           # 语言最佳实践
|   |-- backend-patterns/           # API、数据库、缓存模式
|   |-- frontend-patterns/          # React、Next.js 模式
|   |-- continuous-learning/        # 从会话中自动提取模式（使用文档）
|   |-- continuous-learning-v2/     # 基于直觉的学习与置信度评分
|   |-- iterative-retrieval/        # 子代理的渐进式上下文细化
|   |-- strategic-compact/          # 手动压缩建议（使用文档）
|   |-- tdd-workflow/               # TDD 方法论
|   |-- security-review/            # 安全检查清单
|   |-- eval-harness/               # 验证循环评估（使用文档）
|   |-- verification-loop/          # 持续验证（使用文档）
|   |-- golang-patterns/            # Go 惯用语和最佳实践（新增）
|   |-- golang-testing/             # Go 测试模式、TDD、基准测试（新增）
|   |-- cpp-testing/                # C++ 测试模式、GoogleTest、CMake/CTest（新增）
|
|-- commands/         # 用于快速执行的斜杠命令
|   |-- tdd.md              # /tdd - 测试驱动开发
|   |-- plan.md             # /plan - 实现规划
|   |-- e2e.md              # /e2e - E2E 测试生成
|   |-- code-review.md      # /code-review - 质量审查
|   |-- build-fix.md        # /build-fix - 修复构建错误
|   |-- refactor-clean.md   # /refactor-clean - 死代码移除
|   |-- learn.md            # /learn - 会话中提取模式（使用文档）
|   |-- checkpoint.md       # /checkpoint - 保存验证状态（使用文档）
|   |-- verify.md           # /verify - 运行验证循环（使用文档）
|   |-- setup-pm.md         # /setup-pm - 配置包管理器
|   |-- go-review.md        # /go-review - Go 代码审查（新增）
|   |-- go-test.md          # /go-test - Go TDD 工作流（新增）
|   |-- go-build.md         # /go-build - 修复 Go 构建错误（新增）
|   |-- skill-create.md     # /skill-create - 从 git 历史生成技能（新增）
|   |-- instinct-status.md  # /instinct-status - 查看学习的直觉（新增）
|   |-- instinct-import.md  # /instinct-import - 导入直觉（新增）
|   |-- instinct-export.md  # /instinct-export - 导出直觉（新增）
|   |-- evolve.md           # /evolve - 将直觉聚类到技能中（新增）
|
|-- rules/            # 始终遵循的指南（复制到 $AI_CODE_HOME/rules/）
|   |-- README.md            # 结构说明与安装指南
|   |-- common/              # 通用原则
|   |   |-- security.md        # 强制性安全检查
|   |   |-- coding-style.md    # 不可变性、文件组织
|   |   |-- testing.md         # TDD、80% 覆盖率要求
|   |   |-- git-workflow.md    # 提交格式、PR 流程
|   |   |-- agents.md          # 何时委托给子代理
|   |   |-- performance.md     # 模型选择、上下文管理
|   |-- typescript/          # TypeScript/JavaScript 专用
|   |   |-- comments.md        # 注释、JSDoc、TODO/FIXME 规范
|   |-- python/              # Python 专用
|   |-- golang/              # Go 专用
|
|-- hooks/            # 基于触发器的自动化
|   |-- hooks.json                # 所有钩子配置（PreToolUse、PostToolUse、Stop 等）
|   |-- memory-persistence/       # 会话生命周期钩子（使用文档）
|   |-- strategic-compact/        # 压缩建议（使用文档）
|
|-- scripts/          # 跨平台 Node.js 脚本（新增）
|   |-- lib/                     # 共享工具
|   |   |-- utils.js             # 跨平台文件/路径/系统工具
|   |   |-- package-manager.js   # 包管理器检测和选择
|   |-- hooks/                   # 钩子实现
|   |   |-- session-start.js     # 会话开始时加载上下文
|   |   |-- session-end.js       # 会话结束时保存状态
|   |   |-- pre-compact.js       # 压缩前状态保存
|   |   |-- suggest-compact.js   # 战略性压缩建议
|   |   |-- evaluate-session.js  # 从会话中提取模式
|   |-- setup-package-manager.js # 交互式 PM 设置
|
|-- tests/            # 测试套件（新增）
|   |-- lib/                     # 库测试
|   |-- hooks/                   # 钩子测试
|   |-- run-all.js               # 运行所有测试
|
|-- contexts/         # 动态系统提示注入上下文（使用文档）
|   |-- dev.md              # 开发模式上下文
|   |-- review.md           # 代码审查模式上下文
|   |-- research.md         # 研究/探索模式上下文
|
|-- examples/         # 示例配置和会话
|   |-- CLAUDE.md           # 示例项目级配置
|   |-- user-CLAUDE.md      # 示例用户级配置
|
|-- mcp-configs/      # MCP 服务器配置
|   |-- mcp-servers.json    # GitHub、Supabase、Vercel、Railway 等
|
|-- marketplace.json  # 自托管市场配置（用于 /plugin marketplace add）
```

---

## 🛠️ 生态系统工具

### 技能创建器

两种从你的仓库生成 Claude Code 技能的方法：

#### 选项 A：本地分析（内置）

使用 `/skill-create` 命令进行本地分析，无需外部服务：

```bash
/skill-create                    # 分析当前仓库
/skill-create --instincts        # 还为 continuous-learning 生成直觉
```

这在本地分析你的 git 历史并生成 SKILL.md 文件。

#### 选项 B：GitHub 应用（高级）

用于高级功能（10k+ 提交、自动 PR、团队共享）：

[安装 GitHub 应用](https://github.com/apps/skill-creator) | [github.com/Zack-Zz/ai-code](https://github.com/Zack-Zz/ai-code)

```bash
# 在任何问题上评论：
/skill-creator analyze

# 或在推送到默认分支时自动触发
```

两个选项都创建：
- **SKILL.md 文件** - 可直接用于 Claude Code 的技能
- **直觉集合** - 用于 continuous-learning-v2
- **模式提取** - 从你的提交历史中学习

### 🧠 持续学习 v2

基于直觉的学习系统自动学习你的模式：

```bash
/instinct-status        # 显示带有置信度的学习直觉
/instinct-import <file> # 从他人导入直觉
/instinct-export        # 导出你的直觉以供分享
/evolve                 # 将相关直觉聚类到技能中
```

完整文档见 `skills/continuous-learning-v2/`。

---

## 📥 安装

### 选项 1：作为插件安装（推荐）

使用此仓库的最简单方法 - 作为 Claude Code 插件安装：

```bash
# 将此仓库添加为市场
/plugin marketplace add Zack-Zz/ai-code

# 安装插件
/plugin install ai-code@ai-code
```

或直接添加到你的 `$AI_CODE_HOME/settings.json`：

```json
{
  "extraKnownMarketplaces": {
    "ai-code": {
      "source": {
        "source": "github",
        "repo": "Zack-Zz/ai-code"
      }
    }
  },
  "enabledPlugins": {
    "ai-code@ai-code": true
  }
}
```

这让你可以立即访问所有命令、代理、技能和钩子。

> **注意：** Claude Code 插件系统不支持通过插件分发 `rules`（[上游限制](https://code.claude.com/docs/en/plugins-reference)）。你需要手动安装规则：
>
> ```bash
> # 首先克隆仓库
> git clone https://github.com/Zack-Zz/ai-code.git
>
> # 选项 A：用户级规则（应用于所有项目）
> cp -r ai-code/rules/* $AI_CODE_HOME/rules/
>
> # 选项 B：项目级规则（仅应用于当前项目）
> mkdir -p .claude/rules
> cp -r ai-code/rules/* .claude/rules/
> ```

---

### 🔧 选项 2：手动安装

如果你希望对安装的内容进行手动控制：

```bash
# 克隆仓库
git clone https://github.com/Zack-Zz/ai-code.git

# 将代理复制到你的 Claude 配置
cp ai-code/agents/*.md $AI_CODE_HOME/agents/

# 复制规则
cp ai-code/rules/*.md $AI_CODE_HOME/rules/

# 复制命令
cp ai-code/commands/*.md $AI_CODE_HOME/commands/

# 复制技能
cp -r ai-code/skills/* $AI_CODE_HOME/skills/
```

#### 将钩子添加到 settings.json

将 `hooks/hooks.json` 中的钩子复制到你的 `$AI_CODE_HOME/settings.json`。

#### 配置 MCP

将所需的 MCP 服务器从 `mcp-configs/mcp-servers.json` 复制到你的 `$AI_CODE_HOME/config.json`。

**重要：** 将 `YOUR_*_HERE` 占位符替换为你的实际 API 密钥。

---

## 🎯 关键概念

### 代理

子代理以有限范围处理委托的任务。示例：

```markdown
---
name: code-reviewer
description: 审查代码的质量、安全性和可维护性
tools: ["Read", "Grep", "Glob", "Bash"]
model: opus
---

你是一名高级代码审查员...
```

### 技能

技能是由命令或代理调用的工作流定义：

```markdown
# TDD 工作流

1. 首先定义接口
2. 编写失败的测试（RED）
3. 实现最少的代码（GREEN）
4. 重构（IMPROVE）
5. 验证 80%+ 的覆盖率
```

### 钩子

钩子在工具事件时触发。示例 - 警告 console.log：

```json
{
  "matcher": "tool == \"Edit\" && tool_input.file_path matches \"\\\\.(ts|tsx|js|jsx)$\"",
  "hooks": [{
    "type": "command",
    "command": "#!/bin/bash\ngrep -n 'console\\.log' \"$file_path\" && echo '[Hook] 移除 console.log' >&2"
  }]
}
```

### 规则

规则是始终遵循的指南。保持模块化，复制整个目录而不是扁平化文件：

```text
$AI_CODE_HOME/rules/
  common/
    security.md
    coding-style.md
    testing.md
  typescript/
    coding-style.md
    comments.md
    patterns.md
    hooks.md
    security.md
    testing.md
```

---

## 🧪 运行测试

插件包含一个全面的测试套件：

```bash
# 运行所有测试
node tests/run-all.js

# 运行单个测试文件
node tests/lib/utils.test.js
node tests/lib/package-manager.test.js
node tests/hooks/hooks.test.js
```

---

## 🤝 贡献

**欢迎并鼓励贡献。**

这个仓库旨在成为社区资源。如果你有：
- 有用的代理或技能
- 聪明的钩子
- 更好的 MCP 配置
- 改进的规则

请贡献！请参阅 [CONTRIBUTING.md](CONTRIBUTING.md) 了解指南。

### 贡献想法

- 特定语言的技能（Python、Rust 模式）- 现已包含 Go！
- 特定框架的配置（Django、Rails、Laravel）
- DevOps 代理（Kubernetes、Terraform、AWS）
- 测试策略（不同框架）
- 特定领域的知识（ML、数据工程、移动）

---

## 📖 背景

本仓库作为可二次定制的实用配置基线维护。
建议按你的项目需求裁剪并持续演进。

---

## ⚠️ 重要说明

### 上下文窗口管理

**关键：** 不要一次启用所有 MCP。如果启用了太多工具，你的 200k 上下文窗口可能会缩小到 70k。

经验法则：
- 配置 20-30 个 MCP
- 每个项目保持启用少于 10 个
- 活动工具少于 80 个

在项目配置中使用 `disabledMcpServers` 来禁用未使用的。

### 定制化

这些配置适用于我的工作流。你应该：
1. 从适合你的开始
2. 为你的技术栈进行修改
3. 删除你不使用的
4. 添加你自己的模式

---

## 🔗 链接

- **本地使用文档：** [docs/USAGE.md](docs/USAGE.md)
- **Fork 仓库：** [Zack-Zz/ai-code](https://github.com/Zack-Zz/ai-code)
- **技能目录：** awesome-agent-skills（社区维护的智能体技能目录）

---

## 📄 许可证

MIT - 自由使用，根据需要修改，如果可以请回馈。

---

**按你的项目需求取用并持续迭代即可。**
