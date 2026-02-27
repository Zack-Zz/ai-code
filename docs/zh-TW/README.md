# ai-code

[![Stars](https://img.shields.io/github/stars/Zack-Zz/ai-code?style=flat)](https://github.com/Zack-Zz/ai-code/stargazers)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Shell](https://img.shields.io/badge/-Shell-4EAA25?logo=gnu-bash&logoColor=white)
![TypeScript](https://img.shields.io/badge/-TypeScript-3178C6?logo=typescript&logoColor=white)
![Go](https://img.shields.io/badge/-Go-00ADD8?logo=go&logoColor=white)
![Markdown](https://img.shields.io/badge/-Markdown-000000?logo=markdown&logoColor=white)

---

<div align="center">

**🌐 Language / 语言 / 語言**

[**English**](../../README.md) | [简体中文](../../README.zh-CN.md) | [繁體中文](README.md) | [日本語](../../docs/ja-JP/README.md)

</div>

---

**面向 ChatGPT、Codex、Claude 等主流 AI 開發助手的多平台實用設定集合。**

經過 10 個月以上密集日常使用、打造真實產品所淬煉出的生產就緒代理程式、技能、鉤子、指令、規則和 MCP 設定。

---

## 專案定位

`ai-code` 是面向多助手協作的設定倉庫，不只針對 Claude。

- ChatGPT/Codex：`AGENTS.md` + `.codex/config.toml` + `codex.md`
- Claude Code：外掛/規則/鉤子工作流
- Cursor/OpenCode：相容設定與指令體系
- Java/Python 優先，其他語言可按需擴展

---

## 使用介紹

- 先選擇你要使用的助手棧：Codex/ChatGPT、Claude Code，或 Cursor/OpenCode。
- 在 `AGENTS.md` 維護專案級指令，並依語言補充具體工作流。
- Java/Python 專案建議從 `codex.md` 啟動，並遵循先測後改（TDD）。
- 按需啟用 `agents/`、`skills/`、`rules/`、`commands/`，避免一次全量接入。

### 統一執行期設定（Codex + Claude）

Hook/Session 腳本支援統一環境變數：

```bash
export AI_CODE_TOOL=codex      # codex | claude
export AI_CODE_HOME=/path/to/assistant-home
```

- `AI_CODE_HOME` 優先級最高。
- 未設定 `AI_CODE_HOME` 且 `AI_CODE_TOOL=codex` 時，預設目錄是 `~/.codex`。
- 其他情況預設目錄是 `~/.claude`。
- 也可在單次執行使用 `--tool`、`--home` 參數。

---

## 🚀 快速開始

### 方案 1：Codex / ChatGPT（推薦）

```bash
git clone https://github.com/Zack-Zz/ai-code.git
cd ai-code
cp .codex/config.toml ~/.codex/config.toml
```

在 Codex GUI 中開啟倉庫，首條訊息建議：
`請先閱讀 /codex.md，並按 Java/Python 工作流執行`

### 方案 2：Claude Code

```bash
git clone https://github.com/Zack-Zz/ai-code.git
cd ai-code
./install.sh typescript python golang
```

### 方案 3：Cursor / OpenCode

- Cursor：使用 `.cursor/`，可搭配 `./install.sh --target cursor ...`
- OpenCode：在倉庫根目錄執行並載入 `.opencode/` 設定

### 方案 4：Kiro GUI

```bash
git clone https://github.com/Zack-Zz/ai-code.git
cd ai-code
```

- 在 Kiro 中開啟此目錄。
- Kiro 會自動載入 `.kiro/steering/` 內的規則檔。
- 根目錄 `AGENTS.md` 也可作為全域指令被讀取。

---

## 🌐 跨平台支援

此外掛程式現已完整支援 **Windows、macOS 和 Linux**。所有鉤子和腳本已使用 Node.js 重寫以獲得最佳相容性。

### 套件管理器偵測

外掛程式會自動偵測您偏好的套件管理器（npm、pnpm、yarn 或 bun），優先順序如下：

1. **環境變數**：`CLAUDE_PACKAGE_MANAGER`
2. **專案設定**：`.claude/package-manager.json`
3. **package.json**：`packageManager` 欄位
4. **鎖定檔案**：從 package-lock.json、yarn.lock、pnpm-lock.yaml 或 bun.lockb 偵測
5. **全域設定**：`~/.claude/package-manager.json`
6. **備援方案**：第一個可用的套件管理器

設定您偏好的套件管理器：

```bash
# 透過環境變數
export CLAUDE_PACKAGE_MANAGER=pnpm

# 透過全域設定
node scripts/setup-package-manager.js --global pnpm

# 透過專案設定
node scripts/setup-package-manager.js --project bun

# 偵測目前設定
node scripts/setup-package-manager.js --detect
```

或在 Claude Code 中使用 `/setup-pm` 指令。

---

## 📦 內容概覽

本儲存庫是一個 **Claude Code 外掛程式** - 可直接安裝或手動複製元件。

```
ai-code/
|-- .claude-plugin/   # 外掛程式和市集清單
|   |-- plugin.json         # 外掛程式中繼資料和元件路徑
|   |-- marketplace.json    # 用於 /plugin marketplace add 的市集目錄
|
|-- agents/           # 用於委派任務的專門子代理程式
|   |-- planner.md           # 功能實作規劃
|   |-- architect.md         # 系統設計決策
|   |-- tdd-guide.md         # 測試驅動開發
|   |-- code-reviewer.md     # 品質與安全審查
|   |-- security-reviewer.md # 弱點分析
|   |-- build-error-resolver.md
|   |-- e2e-runner.md        # Playwright E2E 測試
|   |-- refactor-cleaner.md  # 無用程式碼清理
|   |-- doc-updater.md       # 文件同步
|   |-- go-reviewer.md       # Go 程式碼審查（新增）
|   |-- go-build-resolver.md # Go 建置錯誤解決（新增）
|
|-- skills/           # 工作流程定義和領域知識
|   |-- coding-standards/           # 程式語言最佳實務
|   |-- backend-patterns/           # API、資料庫、快取模式
|   |-- frontend-patterns/          # React、Next.js 模式
|   |-- continuous-learning/        # 從工作階段自動擷取模式（使用文件）
|   |-- continuous-learning-v2/     # 基於本能的學習與信心評分
|   |-- iterative-retrieval/        # 子代理程式的漸進式上下文精煉
|   |-- strategic-compact/          # 手動壓縮建議（使用文件）
|   |-- tdd-workflow/               # TDD 方法論
|   |-- security-review/            # 安全性檢查清單
|   |-- eval-harness/               # 驗證迴圈評估（使用文件）
|   |-- verification-loop/          # 持續驗證（使用文件）
|   |-- golang-patterns/            # Go 慣用語法和最佳實務（新增）
|   |-- golang-testing/             # Go 測試模式、TDD、基準測試（新增）
|
|-- commands/         # 快速執行的斜線指令
|   |-- tdd.md              # /tdd - 測試驅動開發
|   |-- plan.md             # /plan - 實作規劃
|   |-- e2e.md              # /e2e - E2E 測試生成
|   |-- code-review.md      # /code-review - 品質審查
|   |-- build-fix.md        # /build-fix - 修復建置錯誤
|   |-- refactor-clean.md   # /refactor-clean - 移除無用程式碼
|   |-- learn.md            # /learn - 工作階段中擷取模式（使用文件）
|   |-- checkpoint.md       # /checkpoint - 儲存驗證狀態（使用文件）
|   |-- verify.md           # /verify - 執行驗證迴圈（使用文件）
|   |-- setup-pm.md         # /setup-pm - 設定套件管理器
|   |-- go-review.md        # /go-review - Go 程式碼審查（新增）
|   |-- go-test.md          # /go-test - Go TDD 工作流程（新增）
|   |-- go-build.md         # /go-build - 修復 Go 建置錯誤（新增）
|
|-- rules/            # 必須遵守的準則（複製到 ~/.claude/rules/）
|   |-- security.md         # 強制性安全檢查
|   |-- coding-style.md     # 不可變性、檔案組織
|   |-- testing.md          # TDD、80% 覆蓋率要求
|   |-- git-workflow.md     # 提交格式、PR 流程
|   |-- agents.md           # 何時委派給子代理程式
|   |-- performance.md      # 模型選擇、上下文管理
|
|-- hooks/            # 基於觸發器的自動化
|   |-- hooks.json                # 所有鉤子設定（PreToolUse、PostToolUse、Stop 等）
|   |-- memory-persistence/       # 工作階段生命週期鉤子（使用文件）
|   |-- strategic-compact/        # 壓縮建議（使用文件）
|
|-- scripts/          # 跨平台 Node.js 腳本（新增）
|   |-- lib/                     # 共用工具
|   |   |-- utils.js             # 跨平台檔案/路徑/系統工具
|   |   |-- package-manager.js   # 套件管理器偵測與選擇
|   |-- hooks/                   # 鉤子實作
|   |   |-- session-start.js     # 工作階段開始時載入上下文
|   |   |-- session-end.js       # 工作階段結束時儲存狀態
|   |   |-- pre-compact.js       # 壓縮前狀態儲存
|   |   |-- suggest-compact.js   # 策略性壓縮建議
|   |   |-- evaluate-session.js  # 從工作階段擷取模式
|   |-- setup-package-manager.js # 互動式套件管理器設定
|
|-- tests/            # 測試套件（新增）
|   |-- lib/                     # 函式庫測試
|   |-- hooks/                   # 鉤子測試
|   |-- run-all.js               # 執行所有測試
|
|-- contexts/         # 動態系統提示注入上下文（使用文件）
|   |-- dev.md              # 開發模式上下文
|   |-- review.md           # 程式碼審查模式上下文
|   |-- research.md         # 研究/探索模式上下文
|
|-- examples/         # 範例設定和工作階段
|   |-- CLAUDE.md           # 專案層級設定範例
|   |-- user-CLAUDE.md      # 使用者層級設定範例
|
|-- mcp-configs/      # MCP 伺服器設定
|   |-- mcp-servers.json    # GitHub、Supabase、Vercel、Railway 等
|
|-- marketplace.json  # 自託管市集設定（用於 /plugin marketplace add）
```

---

## 🛠️ 生態系統工具

### github.com/Zack-Zz/ai-code - 技能建立器

從您的儲存庫自動生成 Claude Code 技能。

[安裝 GitHub App](https://github.com/apps/skill-creator) | [github.com/Zack-Zz/ai-code](https://github.com/Zack-Zz/ai-code)

分析您的儲存庫並建立：
- **SKILL.md 檔案** - 可直接用於 Claude Code 的技能
- **本能集合** - 用於 continuous-learning-v2
- **模式擷取** - 從您的提交歷史學習

```bash
# 安裝 GitHub App 後，技能會出現在：
~/.claude/skills/generated/
```

與 `continuous-learning-v2` 技能無縫整合以繼承本能。

---

## 📥 安裝

### 選項 1：以外掛程式安裝（建議）

使用本儲存庫最簡單的方式 - 安裝為 Claude Code 外掛程式：

```bash
# 將此儲存庫新增為市集
/plugin marketplace add Zack-Zz/ai-code

# 安裝外掛程式
/plugin install ai-code@ai-code
```

或直接新增到您的 `~/.claude/settings.json`：

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

這會讓您立即存取所有指令、代理程式、技能和鉤子。

---

### 🔧 選項 2：手動安裝

如果您偏好手動控制安裝內容：

```bash
# 複製儲存庫
git clone https://github.com/Zack-Zz/ai-code.git

# 將代理程式複製到您的 Claude 設定
cp ai-code/agents/*.md ~/.claude/agents/

# 複製規則
cp ai-code/rules/*.md ~/.claude/rules/

# 複製指令
cp ai-code/commands/*.md ~/.claude/commands/

# 複製技能
cp -r ai-code/skills/* ~/.claude/skills/
```

#### 將鉤子新增到 settings.json

將 `hooks/hooks.json` 中的鉤子複製到您的 `~/.claude/settings.json`。

#### 設定 MCP

將 `mcp-configs/mcp-servers.json` 中所需的 MCP 伺服器複製到您的 `~/.claude.json`。

**重要：** 將 `YOUR_*_HERE` 佔位符替換為您實際的 API 金鑰。

---

## 🎯 核心概念

### 代理程式（Agents）

子代理程式以有限範圍處理委派的任務。範例：

```markdown
---
name: code-reviewer
description: Reviews code for quality, security, and maintainability
tools: ["Read", "Grep", "Glob", "Bash"]
model: opus
---

You are a senior code reviewer...
```

### 技能（Skills）

技能是由指令或代理程式調用的工作流程定義：

```markdown
# TDD Workflow

1. Define interfaces first
2. Write failing tests (RED)
3. Implement minimal code (GREEN)
4. Refactor (IMPROVE)
5. Verify 80%+ coverage
```

### 鉤子（Hooks）

鉤子在工具事件時觸發。範例 - 警告 console.log：

```json
{
  "matcher": "tool == \"Edit\" && tool_input.file_path matches \"\\\\.(ts|tsx|js|jsx)$\"",
  "hooks": [{
    "type": "command",
    "command": "#!/bin/bash\ngrep -n 'console\\.log' \"$file_path\" && echo '[Hook] Remove console.log' >&2"
  }]
}
```

### 規則（Rules）

規則是必須遵守的準則。保持模組化：

```
~/.claude/rules/
  security.md      # 禁止寫死密鑰
  coding-style.md  # 不可變性、檔案限制
  testing.md       # TDD、覆蓋率要求
```

---

## 🧪 執行測試

外掛程式包含完整的測試套件：

```bash
# 執行所有測試
node tests/run-all.js

# 執行個別測試檔案
node tests/lib/utils.test.js
node tests/lib/package-manager.test.js
node tests/hooks/hooks.test.js
```

---

## 🤝 貢獻

**歡迎並鼓勵貢獻。**

本儲存庫旨在成為社群資源。如果您有：
- 實用的代理程式或技能
- 巧妙的鉤子
- 更好的 MCP 設定
- 改進的規則

請貢獻！詳見 [CONTRIBUTING.md](CONTRIBUTING.md) 的指南。

### 貢獻想法

- 特定語言的技能（Python、Rust 模式）- Go 現已包含！
- 特定框架的設定（Django、Rails、Laravel）
- DevOps 代理程式（Kubernetes、Terraform、AWS）
- 測試策略（不同框架）
- 特定領域知識（ML、資料工程、行動開發）

---

## 📖 背景

本儲存庫作為可二次客製的實用設定基線維護。
建議依你的專案需求裁剪並持續演進。

---

## ⚠️ 重要注意事項

### 上下文視窗管理

**關鍵：** 不要同時啟用所有 MCP。啟用過多工具會讓您的 200k 上下文視窗縮減至 70k。

經驗法則：
- 設定 20-30 個 MCP
- 每個專案啟用少於 10 個
- 啟用的工具少於 80 個

在專案設定中使用 `disabledMcpServers` 來停用未使用的 MCP。

### 自訂

這些設定適合我的工作流程。您應該：
1. 從您認同的部分開始
2. 根據您的技術堆疊修改
3. 移除不需要的部分
4. 添加您自己的模式

---

## 🔗 連結

- **本地使用文件：** [USAGE.md](../USAGE.md)
- **Fork 儲存庫：** [Zack-Zz/ai-code](https://github.com/Zack-Zz/ai-code)
- **技能目錄：** awesome-agent-skills（社區維護的智能體技能目錄）

---

## 📄 授權

MIT - 自由使用、依需求修改、如可能請回饋貢獻。

---

**依你的專案需求取用並持續迭代即可。**
