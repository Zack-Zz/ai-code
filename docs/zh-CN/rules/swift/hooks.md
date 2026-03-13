---
paths:
  - "**/*.swift"
  - "**/Package.swift"
---
# Swift Hooks

> 本文档扩展 [common/hooks.md](../common/hooks.md) 的 Swift 特定内容。

## PostToolUse Hooks

建议在 `~/.claude/settings.json` 配置：

- **SwiftFormat**：编辑 `.swift` 后自动格式化
- **SwiftLint**：编辑后执行 lint 检查
- **swift build**：编辑后对修改的 package 做类型检查

## 警告

标记 `print()` 语句。生产代码应使用 `os.Logger` 或结构化日志。
