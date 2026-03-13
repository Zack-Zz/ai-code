---
paths:
  - "**/*.swift"
  - "**/Package.swift"
---
# Swift 模式

> 本文档扩展 [common/patterns.md](../common/patterns.md) 的 Swift 特定内容。

## 协议导向设计

定义小而专注的协议，用协议扩展提供默认实现：

```swift
protocol Repository: Sendable {
    associatedtype Item: Identifiable & Sendable
    func find(by id: Item.ID) async throws -> Item?
    func save(_ item: Item) async throws
}
```

## 值类型优先

- DTO 和模型优先使用 `struct`
- 使用带关联值的 `enum` 表达离散状态：

```swift
enum LoadState<T: Sendable>: Sendable {
    case idle
    case loading
    case loaded(T)
    case failed(Error)
}
```

## Actor 模式

共享可变状态优先用 actor，不要直接用锁或队列：

```swift
actor Cache<Key: Hashable & Sendable, Value: Sendable> {
    private var storage: [Key: Value] = [:]

    func get(_ key: Key) -> Value? { storage[key] }
    func set(_ key: Key, value: Value) { storage[key] = value }
}
```

## 依赖注入

通过协议注入依赖并提供默认实现，生产环境用默认值，测试注入 mock：

```swift
struct UserService {
    private let repository: any UserRepository

    init(repository: any UserRepository = DefaultUserRepository()) {
        self.repository = repository
    }
}
```

## 参考

- `swift-actor-persistence`：基于 actor 的持久化模式
- `swift-protocol-di-testing`：协议 DI 与测试模式
