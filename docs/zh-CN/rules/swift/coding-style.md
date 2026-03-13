---
paths:
  - "**/*.swift"
  - "**/Package.swift"
---
# Swift 编码风格

> 本文档扩展 [common/coding-style.md](../common/coding-style.md) 的 Swift 特定内容。

## 格式化

- 使用 **SwiftFormat** 自动格式化，使用 **SwiftLint** 执行风格检查
- `swift-format` 在 Xcode 16+ 中已内置，可作为替代

## 不可变性

- 优先 `let` 而非 `var`，仅在编译器要求可变时再改为 `var`
- 默认使用 `struct`（值语义）；仅在需要身份语义或引用语义时使用 `class`

## 命名

遵循 [Apple API 设计指南](https://www.swift.org/documentation/api-design-guidelines/)：

- 在使用点保持清晰，省略冗余词
- 方法与属性按“角色”命名，而非按“类型”命名
- 常量优先使用 `static let`，避免全局常量

## 错误处理

使用 Swift 6+ typed throws 与模式匹配：

```swift
func load(id: String) throws(LoadError) -> Item {
    guard let data = try? read(from: path) else {
        throw .fileNotFound(id)
    }
    return try decode(data)
}
```

## 并发

开启 Swift 6 严格并发检查，优先：

- 跨隔离边界传递数据时使用 `Sendable` 值类型
- 共享可变状态使用 `actor`
- 优先结构化并发（`async let`、`TaskGroup`），谨慎使用无结构 `Task {}`
