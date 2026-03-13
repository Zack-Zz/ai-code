---
description: 启动 NanoClaw 代理 REPL：一个基于 claude CLI 的持久化、会话感知 AI 助手。
---

# Claw 命令

**Tool Scope:** `claude` / `codex` / `kiro`

启动一个交互式 AI 会话，支持将历史记录持久化到磁盘，并可选加载 ai-code skill 上下文。

## 用法

```bash
node scripts/claw.js
```

或通过 npm：

```bash
npm run claw
```

## 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `CLAW_SESSION` | `default` | 会话名（字母数字 + 连字符） |
| `CLAW_SKILLS` | *(空)* | 要加载的 skill 名称，逗号分隔 |

## REPL 命令

在提示符中可直接输入：

```text
/clear      清空当前会话历史
/history    打印完整会话历史
/sessions   列出所有已保存会话
/help       显示可用命令
exit        退出 REPL
```

## 工作机制

1. 读取 `CLAW_SESSION` 选择会话（默认 `default`）
2. 从 `$AI_CODE_HOME/claw/{session}.md` 加载历史
3. 可选读取 `CLAW_SKILLS` 作为系统上下文
4. 进入阻塞式循环，每条消息通过 `claude -p` 发送（附完整历史）
5. 回答追加写入会话文件，重启后可继续

## 会话存储

会话以 Markdown 存储在 `$AI_CODE_HOME/claw/`：

```text
$AI_CODE_HOME/claw/default.md
$AI_CODE_HOME/claw/my-project.md
```

每轮格式：

```markdown
### [2025-01-15T10:30:00.000Z] User
这个函数是做什么的？
---
### [2025-01-15T10:30:05.000Z] Assistant
这个函数用于计算...
---
```

## 示例

```bash
# 默认会话
node scripts/claw.js

# 指定会话
CLAW_SESSION=my-project node scripts/claw.js

# 加载 skill 上下文
CLAW_SKILLS=tdd-workflow,security-review node scripts/claw.js
```
