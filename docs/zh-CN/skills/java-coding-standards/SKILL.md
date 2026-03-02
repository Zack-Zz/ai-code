---
name: java-coding-standards
description: Java coding standards for Spring Boot services: naming, immutability, Javadoc conventions, Optional usage, streams, exceptions, generics, and project layout.
---

# Java 编码规范

适用于 Spring Boot 服务中可读、可维护的 Java (17+) 代码的规范。

## 核心原则

* 清晰优于巧妙
* 默认不可变；最小化共享可变状态
* 快速失败并提供有意义的异常
* 一致的命名和包结构

## 命名

```java
// ✅ Classes/Records: PascalCase
public class MarketService {}
public record Money(BigDecimal amount, Currency currency) {}

// ✅ Methods/fields: camelCase
private final MarketRepository marketRepository;
public Market findBySlug(String slug) {}

// ✅ Constants: UPPER_SNAKE_CASE
private static final int MAX_PAGE_SIZE = 100;
```

## 文档注释规范（Javadoc）

* 对外可见的类/接口/枚举/record 必须有类级 Javadoc。
* 类级 Javadoc 应描述业务职责与边界，不要写实现细节。
* 公共顶级类型应包含 `@author` 与 `@since`。
* public/protected 方法在“行为非平凡、有副作用、会抛出领域异常”时必须写 Javadoc。
* 公共常量若语义不是“看名字就完全明确”，必须写 Javadoc。
* private 方法、getter/setter 一般可不写；仅在逻辑复杂时补充。

```java
/**
 * 市场生命周期应用服务。
 * 负责协调校验、持久化与领域事件发布。
 *
 * @author ai-code
 * @since 1.0.0
 */
public class MarketService {

  /**
   * 单次查询允许的最大分页大小。
   */
  public static final int MAX_PAGE_SIZE = 100;

  /**
   * 原子化创建市场并持久化。
   *
   * @param request 已完成校验的创建请求
   * @return 已持久化的市场聚合
   * @throws MarketAlreadyExistsException 当 slug 已存在时抛出
   */
  public Market createMarket(CreateMarketRequest request) { ... }
}
```

### Javadoc 标签规则

* `@param`：文档化的方法/构造函数中，每个参数都要有。
* `@return`：非 `void` 返回值必须写，说明业务语义而不是类型名。
* `@throws`：受检异常必写；有业务意义的运行时异常也应写。
* `@since`：公共顶级类型和新增公共 API 必写。
* `@author`：公共顶级类型必写（建议团队/组织标识，避免个人隐私信息）。
* `@implNote` / `@apiNote`：用于补充实现约束和调用约束。

### Javadoc 质量要求

* 不要机械复述方法名（低信息量注释应避免）。
* 重点描述“意图、约束、副作用”。
* 代码变更时同步更新注释；过期注释按缺陷处理。
* 若无项目特殊约定，API/Javadoc 建议统一英文。

## 不可变性

```java
// ✅ Favor records and final fields
public record MarketDto(Long id, String name, MarketStatus status) {}

public class Market {
  private final Long id;
  private final String name;
  // getters only, no setters
}
```

## Optional 使用

```java
// ✅ Return Optional from find* methods
Optional<Market> market = marketRepository.findBySlug(slug);

// ✅ Map/flatMap instead of get()
return market
    .map(MarketResponse::from)
    .orElseThrow(() -> new EntityNotFoundException("Market not found"));
```

## Streams 最佳实践

```java
// ✅ Use streams for transformations, keep pipelines short
List<String> names = markets.stream()
    .map(Market::name)
    .filter(Objects::nonNull)
    .toList();

// ❌ Avoid complex nested streams; prefer loops for clarity
```

## 异常

* 领域错误使用非受检异常；包装技术异常时提供上下文
* 创建特定领域的异常（例如，`MarketNotFoundException`）
* 避免宽泛的 `catch (Exception ex)`，除非在中心位置重新抛出/记录

```java
throw new MarketNotFoundException(slug);
```

## 泛型和类型安全

* 避免原始类型；声明泛型参数
* 对于可复用的工具类，优先使用有界泛型

```java
public <T extends Identifiable> Map<Long, T> indexById(Collection<T> items) { ... }
```

## 项目结构 (Maven/Gradle)

```
src/main/java/com/example/app/
  config/
  controller/
  service/
  repository/
  domain/
  dto/
  util/
src/main/resources/
  application.yml
src/test/java/... (mirrors main)
```

## 格式化和风格

* 一致地使用 2 或 4 个空格（项目标准）
* 每个文件一个公共顶级类型
* 保持方法简短且专注；提取辅助方法
* 成员顺序：常量、字段、构造函数、公共方法、受保护方法、私有方法

## 需要避免的代码坏味道

* 长参数列表 → 使用 DTO/构建器
* 深度嵌套 → 提前返回
* 魔法数字 → 命名常量
* 静态可变状态 → 优先使用依赖注入
* 静默捕获块 → 记录日志并处理或重新抛出

## 日志记录

```java
private static final Logger log = LoggerFactory.getLogger(MarketService.class);
log.info("fetch_market slug={}", slug);
log.error("failed_fetch_market slug={}", slug, ex);
```

## Null 处理

* 仅在不可避免时接受 `@Nullable`；否则使用 `@NonNull`
* 在输入上使用 Bean 验证（`@NotNull`, `@NotBlank`）

## 测试期望

* 使用 JUnit 5 + AssertJ 进行流畅的断言
* 使用 Mockito 进行模拟；尽可能避免部分模拟
* 倾向于确定性测试；没有隐藏的休眠

**记住**：保持代码意图明确、类型安全且可观察。除非证明有必要，否则优先考虑可维护性而非微优化。
