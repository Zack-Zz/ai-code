---
paths:
  - "**/*.swift"
  - "**/Package.swift"
---
# Swift 测试

> 本文档扩展 [common/testing.md](../common/testing.md) 的 Swift 特定内容。

## 测试框架

新测试优先使用 **Swift Testing**（`import Testing`），搭配 `@Test` 和 `#expect`：

```swift
@Test("User creation validates email")
func userCreationValidatesEmail() throws {
    #expect(throws: ValidationError.invalidEmail) {
        try User(email: "not-an-email")
    }
}
```

## 测试隔离

每个测试使用全新实例。初始化放 `init`，清理放 `deinit`，不要共享可变状态。

## 参数化测试

```swift
@Test("Validates formats", arguments: ["json", "xml", "csv"])
func validatesFormat(format: String) throws {
    let parser = try Parser(format: format)
    #expect(parser.isValid)
}
```

## 覆盖率

```bash
swift test --enable-code-coverage
```

## 参考

查看技能 `swift-protocol-di-testing`，了解基于协议的依赖注入与 mock 模式。
