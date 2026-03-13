---
paths:
  - "**/*.swift"
  - "**/Package.swift"
---
# Swift 安全

> 本文档扩展 [common/security.md](../common/security.md) 的 Swift 特定内容。

## 密钥管理

- 敏感数据（token、密码、密钥）使用 **Keychain Services**，不要放 `UserDefaults`
- 构建期密钥使用环境变量或 `.xcconfig`
- 不要在源码硬编码密钥，反编译可轻易提取

```swift
let apiKey = ProcessInfo.processInfo.environment["API_KEY"]
guard let apiKey, !apiKey.isEmpty else {
    fatalError("API_KEY not configured")
}
```

## 传输安全

- ATS（App Transport Security）默认开启，不要关闭
- 关键端点启用证书固定（certificate pinning）
- 校验所有服务端证书

## 输入校验

- 展示前清洗所有用户输入，防止注入
- 使用 `URL(string:)` 并验证，不要强制解包
- 外部来源数据（API、deep link、剪贴板）处理前先校验
